import os
import requests
from datetime import datetime
from dotenv import load_dotenv
from config import get_data_dir

env_path = os.path.join(get_data_dir(), '.env')
load_dotenv(env_path)

class RAWGClient:
    def __init__(self):
        # 使用 os.environ.get 而不是 os.getenv，确保能读取到 app.py 刚刚热更新的内存变量
        self.api_key = os.environ.get("RAWG_API_KEY")
        self.base_url = "https://api.rawg.io/api/games"

        if not self.api_key:
            print("[警告] 未检测到 RAWG API Key，请检查API Key配置！")

    def search_games(self, query: str, page_size: int = 20):
        if not self.api_key:
            return False, "系统未检测到 API Key，请点击主页下方修改配置！"

        """
        根据关键字搜索游戏
        :param query: 搜索关键词
        :param page_size: 返回的结果条数，默认20条
        :return: 清洗后的游戏数据列表
        """
        params = {
            'key': self.api_key,
            'search': query,
            'page_size': page_size
        }

        try:
            # 发起 GET 请求，设置 10 秒超时防止网络卡死
            response = requests.get(self.base_url, params=params, timeout=10)

            # 拦截 API Key 无效的 401 鉴权错误
            if response.status_code == 401:
                return False, "您的 RAWG API Key 似乎无效，请检查并重新配置！"

            # 如果 HTTP 状态码不是 200，直接抛出异常
            response.raise_for_status()

            data = response.json()
            results = data.get('results', [])

            # 如果请求成功但列表为空，才是真正的查无此游戏
            if not results:
                return True, []

            cleaned_games = []
            for item in results:
                # 核心：数据清洗与安全提取
                game_id = item.get('id')
                name = item.get('name')
                slug = item.get('slug')
                bg_image = item.get('background_image')
                released_str = item.get('released')  # 格式一般为 "YYYY-MM-DD"

                # 防御性编程：必须有 id、name 和 slug 才能算作有效游戏数据
                if not game_id or not name or not slug:
                    continue

                # 将字符串格式的时间转化为 Python 的 date 对象
                release_date = None
                if released_str:
                    try:
                        release_date = datetime.strptime(released_str, "%Y-%m-%d").date()
                    except ValueError:
                        pass  # 如果日期格式有变，容错处理

                cleaned_games.append({
                    "id": game_id,
                    "title_en": name,
                    "slug": slug,
                    "boxart_url": bg_image,
                    "release_date": release_date
                })
            return True, cleaned_games

        except requests.exceptions.Timeout:
            return False, "连接超时：网络不稳定，请重试或使用科学上网！"
        except requests.exceptions.ConnectionError:
            return False, "网络断开：无法连接到 RAWG 数据库，请确保您的电脑已联网！"
        except requests.exceptions.RequestException as e:
            print(f"[错误] 请求 RAWG API 失败: {e}")
            return False, f"联网检索失败: {str(e)}"


# 快速本地测试
if __name__ == "__main__":
    # 填入你注册好的 RAWG API Key
    client = RAWGClient()

    print("正在向 RAWG 发起搜索测试...")
    # 拿一个游戏测试 (适配解包)
    success, test_results = client.search_games("Super Mario Galaxy")

    if not success:
        print(f"❌ 搜索测试遇到技术性故障: {test_results}")
    else:
        print(f"共搜到 {len(test_results)} 个结果：\n")
        for game in test_results:
            print(f"ID: {game['id']}")
            print(f"名称: {game['title_en']}")
            print(f"Slug: {game['slug']}")
            print(f"发售日期: {game['release_date']}")
            print(f"封面URL: {game['boxart_url']}")
            print("-" * 30)