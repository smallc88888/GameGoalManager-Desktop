import os
import sys
import threading
import time
from flask import Flask, render_template, request, jsonify, redirect, url_for
from sqlalchemy.orm import scoped_session
import webview

from models import SessionLocal, init_db, User, Game, Record
from record_service import RecordService
from rawg_client import RAWGClient
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session

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
    """
    1. 极简的主页面
    按照你的天才构想：
    - 顶部自带全局搜索框
    - 中间只有一个大大的“开始添加游戏”红白机动效按钮
    - 点击后通过 JS 自动把光标吸上去
    """
    return render_template('index.html')


@app.route('/api/search')
def api_search():
    """
    2. 异步搜索接口 (Metacritic 翻版样式数据源)
    当用户在最上端输入框敲字时，JS 实时发起请求到这里
    """
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({"success": False, "results": []})

    try:
        # 实例化网关客户端并抓取 RAWG 数据
        client = RAWGClient()
        raw_games = client.search_games(query)

        # 这里的 raw_games 已经是在 rawg_client.py 里洗干净的单条字典列表
        return jsonify({"success": True, "results": raw_games})
    except Exception as e:
        return jsonify({"success": False, "message": f"联网检索失败: {str(e)}"})


@app.route('/api/record/add', methods=['POST'])
def api_add_record():
    """
    3. 提交通关记录接口
    对应点击最右侧带有红白边缘动效的「提交通关记录」按钮后触发的持久化逻辑
    """
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "message": "请先登录账户后再提交通关记录！"})

    # 接收前端传来的表单数据
    game_id = request.form.get('game_id')
    title_en = request.form.get('title_en')
    slug = request.form.get('slug')
    boxart_url = request.form.get('boxart_url')
    release_date = request.form.get('release_date')

    play_time_raw = request.form.get('play_time', '0')
    review_notes = request.form.get('review_notes', '').strip()

    # 接收上传的 WebP 截图文件 (暂留逻辑，后续补全文件本地保存)
    screenshot_file = request.files.get('screenshot')
    mock_screenshot_path = "static/uploads/mock_metroid.webp"

    # 数据格式严糙对接（面向 GUI 的防御性清洗）
    try:
        play_time = int(play_time_raw)
    except ValueError:
        return jsonify({"success": False, "message": "游玩时长必须是整数！"})

    rawg_game_data = {
        "id": int(game_id),
        "title_en": title_en,
        "slug": slug,
        "boxart_url": boxart_url,
        "release_date": release_date if release_date else None
    }

    # 动态注入当前线程安全的 db_session 到服务层
    service = RecordService(db_session)

    # 调用核心持久化逻辑
    # 把 add_completion_record 的返回值重构为了 (Object/None) 校验
    record = service.add_completion_record(user_id=get_current_user_id(), rawg_game_data=rawg_game_data, play_time=play_time,
                                           screenshot_path=mock_screenshot_path)

    if record:
        return jsonify({"success": True, "message": f"《{title_en}》通关成功记录！"})
    else:
        return jsonify({"success": False, "message": "事务提交失败，请检查控制台回滚日志。"})

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
    return jsonify({"success": True, "message": "已安全退出登录。"})

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


if __name__ == '__main__':
    main()