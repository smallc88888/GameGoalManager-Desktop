import os
import sys
import threading
import time
import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from sqlalchemy.orm import scoped_session
import shutil
import webview
from PIL import Image
from models import SessionLocal, init_db, User, Game, Record
from record_service import RecordService
from rawg_client import RAWGClient
from werkzeug.security import generate_password_hash, check_password_hash
from playwright.sync_api import sync_playwright
from dotenv import set_key, load_dotenv
import uuid

# 初始化 Flask
app = Flask(__name__)
app.secret_key = "game_goal_manager_secret_key_fc"  # 用于支持 Session 会话

# 💡使用 scoped_session 确保 Flask 多线程环境下的数据库连接线程安全
db_session = scoped_session(SessionLocal)

def get_current_user_id():
    """从 session 中动态获取当前登录用户 ID，未登录则返回 None"""
    return session.get('user_id')


@app.teardown_appcontext
def remove_session(exception=None):
    """每个 HTTP 请求结束后，自动释放当前线程的数据库连接，防止连接池枯竭"""
    db_session.remove()



# GUI 页面路由映射层 (Controllers)
@app.route('/')
def index():
    """1. 极简的主页面"""
    return render_template('index.html')


@app.route('/api/search')
def api_search():
    """
    2. 异步搜索接口
    当用户在最上端输入框敲字时，JS 实时发起请求到这里
    """
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({"success": False, "results": []})

    try:
        # 实例化网关客户端并抓取 RAWG 数据
        client = RAWGClient()
        success, raw_games = client.search_games(query)

        if not success:
            # 如果是技术故障（如断网或Key失效），直接返回 success: False 和具体原因，不走后续逻辑
            return jsonify({"success": False, "message": raw_games})

        for game in raw_games:
            r_date = game.get('release_date')
            # 检查类型，如果是 datetime.date 对象，转换为 "YYYY-MM-DD" 字符串
            if isinstance(r_date, datetime.date):
                game['release_date'] = r_date.strftime('%Y-%m-%d')
            elif r_date is None:
                game['release_date'] = ""  #如果 RAWG 没给发售日，传空字符串

        # 这里的 raw_games 已经是在 rawg_client.py 里洗干净的单条字典列表
        return jsonify({"success": True, "results": raw_games})

    except Exception as e:
        print(f"联网检索或序列化管道崩溃: {str(e)}")
        return jsonify({"success": False, "message": f"联网检索失败: {str(e)}"})


@app.route('/api/record/add', methods=['POST'])
def api_add_record():
    """3. 完善的通关记录数据落盘接口（含完备的 Date 类型防御转化）"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "message": "核心防御触发：检测到未登录会话，请先登录！"}), 401

    try:
        # 提取并转化 RAWG 游戏元数据
        game_id = request.form.get('game_id', type=int)
        title_en = request.form.get('title_en')
        slug = request.form.get('slug', default="")
        boxart_url = request.form.get('boxart_url', default="")

        # 解析 RAWG 游戏发售日期 (release_date)
        release_date_raw = request.form.get('release_date')
        release_date = None
        if release_date_raw and release_date_raw != "None" and release_date_raw.strip() != "":
            try:
                # 将前端传回的字符串 "YYYY-MM-DD" 转化为 Python date 对象
                release_date = datetime.datetime.strptime(release_date_raw.strip(), "%Y-%m-%d").date()
            except ValueError:
                print(f"[警告] 传入的游戏发售日期格式异常: {release_date_raw}，已降级为 None")
                release_date = None

        # 组装完整的游戏字典数据
        rawg_game_data = {
            "id": game_id,
            "title_en": title_en,
            "slug": slug,
            "boxart_url": boxart_url,
            "release_date": release_date
        }

        # 2. 提取并安全转化用户录入的通关数据
        play_time = request.form.get('play_time', type=int, default=0)
        review_notes = request.form.get('review_notes', default="")

        # 解析用户填写的通关时间
        completion_date_raw = request.form.get('completion_date')
        if completion_date_raw and completion_date_raw.strip() != "":
            try:
                # 转化用户自选的日期字符串为 Python date 对象
                completion_date = datetime.datetime.strptime(completion_date_raw.strip(), "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"success": False, "message": "校验失败：通关日期格式不合法，必须为 YYYY-MM-DD！"}), 400
        else:
            # 如果玩家没有选择日期，默认转换为当天日期
            completion_date = datetime.date.today()

        # 3. 处理截图资产流（Pillow 内存强转 WebP 压缩落盘）
        screenshot_file = request.files.get('screenshot')

        # 如果文件不存在或文件名为空，中断请求，返回 400 校验错误
        if not screenshot_file or screenshot_file.filename == '':
            return jsonify({"success": False, "message": "校验失败：截图未上传！"}), 400

        # 校验通过
        upload_dir = os.path.join(app.root_path, 'static', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)

        timestamp = int(time.time())
        filename = f"user_{user_id}_game_{game_id}_{timestamp}.webp"
        file_path = os.path.join(upload_dir, filename)

        img = Image.open(screenshot_file)
        img.save(file_path, 'WEBP', quality=80)
        screenshot_path = f"/static/uploads/{filename}"

        # 4. 交付 Service 业务层进行持久化事务处理
        record_service = RecordService(db_session)
        new_record = record_service.add_completion_record(
            user_id=user_id,
            rawg_game_data=rawg_game_data,
            play_time=play_time,
            completion_date=completion_date,  # 传入已洗净的 date 对象
            review_notes=review_notes,
            screenshot_path=screenshot_path
        )

        return jsonify({
            "success": True,
            "message": f"恭喜！《{title_en}》的通关记录已成功提交！"
        })

    except Exception as e:
        print(f"[严重系统异常] 提交通关记录失败，详情: {e}")
        return jsonify({"success": False, "message": f"服务器内部事务崩溃: {str(e)}"}), 500

@app.route('/api/record/list', methods=['GET'])
def api_list_records():
    """4. 获取当前玩家的通关历史记录"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "message": "会话已过期，请重新登录！"}), 401

    try:
        # 1. 核心联表查询：联结 Record 与 Game 表，并通过 user_id 过滤，最后按通关日期倒序
        # 这里 db_session.query(Record, Game) 会返回一个元组的列表：[(record_obj, game_obj), ...]
        records = db_session.query(Record, Game).join(Game, Record.game_id == Game.id)\
            .filter(Record.user_id == user_id)\
            .order_by(Record.completion_date.desc()).all()

        # 2. 组装响应字典
        result_list = []
        for rec, game in records:
            result_list.append({
                "record_id": rec.id,
                "game_title": game.title_en,
                "boxart_url": game.boxart_url if game.boxart_url else "https://via.placeholder.com/70x95?text=No+Cover",
                # 防御 JSON 序列化：将 Date 对象转回 YYYY-MM-DD 字符串
                "completion_date": rec.completion_date.strftime('%Y-%m-%d') if rec.completion_date else "未知时间",
                "play_time": rec.play_time,
                "screenshot_path": rec.screenshot_path,
                "review_notes": rec.review_notes
            })

        return jsonify({"success": True, "data": result_list})

    except Exception as e:
        print(f"[严重] 获取历史记录失败: {e}")
        return jsonify({"success": False, "message": "获取时间轴失败，内部服务器异常"}), 500


@app.route('/api/record/delete/<int:record_id>', methods=['POST'])
def api_delete_record(record_id):
    """5. 删除通关记录接口"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "message": "请先登录后再进行删除操作！"}), 401

    db = db_session()
    try:
        # 除了匹配 record_id，还必须严格匹配当前登录的 user_id，防止越权删除他人数据
        record = db.query(Record).filter(Record.id == record_id, Record.user_id == user_id).first()

        if not record:
            return jsonify({"success": False, "message": "未找到相关通关记录或您无权操作！"}), 444

        # 如果在本地发现了关联的截图，执行物理空间销毁，防止撑爆硬盘
        if record.screenshot_path and record.screenshot_path.startswith('/static/'):
            # 拼接出本机的绝对物理物理路径
            relative_path = record.screenshot_path.lstrip('/')
            absolute_disk_path = os.path.join(app.root_path, relative_path)
            if os.path.exists(absolute_disk_path):
                os.remove(absolute_disk_path)
                print(f"[系统资产回收] 成功删除处理后的webp图片: {absolute_disk_path}")

        # 从 ORM 字典中移除并提交事务
        db.delete(record)
        db.commit()
        return jsonify({"success": True, "message": "该通关记录及关联webp图片已删除！"})

    except Exception as e:
        db.rollback()
        print(f"[严重] 删除记录事务崩溃: {e}")
        return jsonify({"success": False, "message": f"服务器内部销毁失败: {str(e)}"}), 500


@app.route('/api/record/update/<int:record_id>', methods=['POST'])
def api_update_record(record_id):
    """6. 修改已有通关记录接口"""
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "message": "鉴权失败：会话过期，请重新登录！"}), 401

    db = db_session()
    try:
        # 纵向权限核验：锁死属于该玩家的记录
        record = db.query(Record).filter(Record.id == record_id, Record.user_id == user_id).first()
        if not record:
            return jsonify({"success": False, "message": "目标记录不存在或非法篡改！"}), 404

        # 1. 接收并转化常规文本字段
        comp_date_raw = request.form.get('completion_date')
        play_time_raw = request.form.get('play_time', '0')
        review_notes = request.form.get('review_notes', '').strip()

        # 日期安全对齐转化
        if comp_date_raw:
            record.completion_date = datetime.datetime.strptime(comp_date_raw.strip(), "%Y-%m-%d").date()

        # 游玩时间转化防御
        record.play_time = int(play_time_raw) if play_time_raw else 0
        record.review_notes = review_notes

        # 2. 查看玩家本次是否上传了新荣誉截图来覆盖原图
        new_screenshot = request.files.get('screenshot')
        if new_screenshot and new_screenshot.filename != '':
            # 第一步：物理清除原本残留在 static/uploads 中的老 WebP 图，防止留存冗余碎片
            if record.screenshot_path and record.screenshot_path.startswith('/static/'):
                old_path = os.path.join(app.root_path, record.screenshot_path.lstrip('/'))
                if os.path.exists(old_path):
                    os.remove(old_path)

            # 第二步：压缩并写入新图片
            upload_dir = os.path.join(app.root_path, 'static', 'uploads')
            timestamp = int(time.time())
            filename = f"user_{user_id}_game_{record.game_id}_edit_{timestamp}.webp"
            file_path = os.path.join(upload_dir, filename)

            img = Image.open(new_screenshot)
            img.save(file_path, 'WEBP', quality=80)
            record.screenshot_path = f"/static/uploads/{filename}"

        # 3. 递交 ORM 整体变更事务
        db.commit()
        return jsonify({"success": True, "message": "您的通关记录已成功修改！"})

    except Exception as e:
        db.rollback()
        print(f"[严重] 微调更新事务崩溃: {e}")
        return jsonify({"success": False, "message": f"服务器内部修改失败: {str(e)}"}), 500

@app.route('/api/auth/status')
def auth_status():
    """检查当前会话的登录状态"""
    if 'user_id' in session:
        return jsonify({
            "logged_in": True,
            "username": session.get('username'),
            "user_id": session.get('user_id')
        })
    return jsonify({"logged_in": False})

@app.route('/api/auth/register', methods=['POST'])
def api_register():
    """用户注册接口"""
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    if not username or not password:
        return jsonify({"success": False, "message": "用户名和密码不能为空！"})

    db = db_session()
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        return jsonify({"success": False, "message": "该用户名已被注册，换一个吧！"})

    try:
        # 使用 werkzeug 哈希加密密码
        password_hash = generate_password_hash(password)
        new_user = User(username=username, password_hash=password_hash)
        db.add(new_user)
        db.commit()
        return jsonify({"success": True, "message": "注册成功！请前往登录。"})
    except Exception as e:
        db.rollback()
        return jsonify({"success": False, "message": f"注册失败，数据库异常: {str(e)}"})


@app.route('/api/auth/login', methods=['POST'])
def api_login():
    """用户登录接口"""
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    db = db_session()
    user = db.query(User).filter(User.username == username).first()

    # 验证用户存在且密码哈希匹配
    if user and check_password_hash(user.password_hash, password):
        # 写入 Flask 状态 Session
        session['user_id'] = user.id
        session['username'] = user.username
        return jsonify({
            "success": True,
            "username": user.username
        })

    return jsonify({"success": False, "message": "用户名或密码错误！"})


@app.route('/api/auth/logout', methods=['POST'])
def api_logout():
    """用户登出接口"""
    session.clear()
    return jsonify({"success": True})

# CEF 桌面外壳内核管理层 (Main Window)

def run_flask():
    """在后台线程启动 Flask Web 服务器"""
    # 禁用 Werkzeug 的默认重载器
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)


def main():
    # 1. 初始化本地 SQLite 数据库拓扑
    print("[系统] 正在检查并初始化本地数据库拓扑...")
    init_db()

    # 2. 启动 Flask 后台线程
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    time.sleep(0.5)  # 给后端一瞬间的启动时间

    # 3. pywebview 强行拉起干净、高颜值的任天堂红白机桌面外壳窗口
    print("[系统] 正在通过 pywebview 拉起独立桌面看版...")
    webview.create_window(
        title="GameGoalManager",
        url="http://127.0.0.1:5000/",
        width=1200,
        height=750,
        resizable=True
    )

    # 启动 webview 引擎循环，这行代码会阻塞主线程，直到用户点击窗口的 [X] 关闭软件
    webview.start()
    print("[系统] 软件窗口已关闭，安全退出进程。")

@app.route('/api/milestone/save_native', methods=['POST'])
def api_save_native():
    """
    利用 pywebview 唤醒操作系统原生【另存为...】对话框
    """
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "message": "鉴权失败"}), 401

    data = request.json
    filename = data.get('filename')
    if not filename:
        return jsonify({"success": False, "message": "参数缺失：未知文件名"}), 400

    # 定位刚刚通过 Playwright 生成的原始图片路径
    source_path = os.path.join(app.root_path, 'static', 'exports', filename)
    if not os.path.exists(source_path):
        return jsonify({"success": False, "message": "缓存文件已丢失，请重新生成长图！"}), 404

    try:
        # 获取当前运行的 pywebview 主窗口实例
        window = webview.windows[0]

        # 唤起系统原生保存
        result = window.create_file_dialog(
            webview.SAVE_DIALOG,
            save_filename="My_Game_Milestone.png",  # 默认提供的文件名
            file_types=('PNG 图片 (*.png)', '所有文件 (*.*)')
        )

        # result 会返回一个元组，如果用户点击了取消，result 为 None 或空
        if result and len(result) > 0:
            target_path = result[0]
            # 物理复制文件到用户选择的绝对路径
            shutil.copy(source_path, target_path)
            return jsonify({"success": True, "message": "保存成功！", "saved_path": target_path})
        else:
            return jsonify({"success": False, "message": "用户取消了保存"})

    except Exception as e:
        print(f"[原生保存异常] {e}")
        return jsonify({"success": False, "message": f"跨界调用系统存盘失败: {str(e)}"}), 500

@app.route('/api/milestone/export', methods=['POST'])
def api_export_milestone():
    """
    基于 Playwright 无头浏览器的 Echarts 长图自动化渲染与导出
    """
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "message": "鉴权失败：请先登录！"}), 401

    try:
        # 1. 捞取并拼装正序的时间轴数据
        records = db_session.query(Record, Game).join(Game, Record.game_id == Game.id) \
            .filter(Record.user_id == user_id) \
            .order_by(Record.completion_date.asc()).all()

        if not records:
            return jsonify({"success": False, "message": "您的记录为空，赶快去打通第一款游戏吧！"}), 400

        # 获取当前运行的本地服务器根地址 (例如 http://127.0.0.1:5000)
        base_url = request.host_url.rstrip('/')

        timeline_data = []
        for rec, game in records:
            timeline_data.append({
                "date": rec.completion_date.strftime('%Y-%m-%d') if rec.completion_date else "",
                "title": game.title_en,
                "play_time": rec.play_time,
                "screenshot_path": base_url + rec.screenshot_path if rec.screenshot_path else ""
            })

        # 2. 利用 Flask 的 Jinja2 引擎，将数据与刚才写好的 Echarts 模板合成为完整的 HTML 文本流
        # 获取当前玩家真实的通关游戏总数
        total_count = len(records)

        # 将 timeline_data 和 total_count 一同灌入 Jinja2 模板中
        html_content = render_template(
            'milestone_template.html',
            timeline_data=timeline_data,
            total_count=total_count  # 把数字传给长图模板
        )

        # 3. 确立本机的物理存储路径（专门放在 exports 目录下）
        export_dir = os.path.join(app.root_path, 'static', 'exports')
        os.makedirs(export_dir, exist_ok=True)

        # 用时间戳保证文件名绝对不重复
        filename = f"milestone_{user_id}_{int(time.time())}.png"
        file_path = os.path.join(export_dir, filename)

        # 4. 核心高光：Playwright 无头浏览器执行静默渲染与精准截图
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            # 1：CSS 锁死了 1200px 宽度，所以视口需要留点余量给 1250px
            page = browser.new_page(viewport={"width": 1250, "height": 800})

            # 2：直接注入 HTML，并强行等待网络空闲（确保所有 webp 图片都下载并渲染完毕）
            page.set_content(html_content, wait_until="networkidle")

            # 3：等待全新的纯 CSS 外层容器
            page.wait_for_selector('.timeline-container')

            # 定位到网页的 <body> 标签，执行元素级快照
            page.locator('body').screenshot(path=file_path)

            # 关闭内核，释放系统内存
            browser.close()

        print(f"[Milestone] 成功为用户 {user_id} 生成长图：{filename}")

        # 5. 将相对可访问的网络路径抛回给前端
        return jsonify({
            "success": True,
            "message": "里程碑长图生成成功！",
            "export_url": f"/static/exports/{filename}",
            "filename": filename
        })

    except Exception as e:
        print(f"[严重] Playwright 渲染引擎崩溃: {e}")
        return jsonify({"success": False, "message": f"渲染引擎异常: {str(e)}"}), 500


@app.route('/api/system/check_apikey')
def check_api_key():
    """检查当前运行环境是否已配置 RAWG API Key"""
    # 尝试从环境变量获取
    api_key = os.environ.get('RAWG_API_KEY')
    return jsonify({"has_key": bool(api_key and api_key.strip())})


@app.route('/api/system/save_apikey', methods=['POST'])
def save_api_key():
    """接收用户输入的 API Key 并物理落盘到 .env 文件"""
    new_key = request.form.get('api_key', '').strip()
    if not new_key:
        return jsonify({"success": False, "message": "API Key 不能为空！"})

    try:
        # 定位或创建 .env 文件
        env_path = os.path.join(app.root_path, '.env')

        # 利用 dotenv 动态写入文件，永久保存
        set_key(env_path, 'RAWG_API_KEY', new_key)

        # 同步更新当前运行中的内存环境变量，使其立即生效
        os.environ['RAWG_API_KEY'] = new_key

        return jsonify({"success": True, "message": "API Key 配置成功，系统已就绪！"})
    except Exception as e:
        print(f"[严重] 写入 API Key 失败: {e}")
        return jsonify({"success": False, "message": f"配置文件写入失败: {str(e)}"})

if __name__ == '__main__':
    main()