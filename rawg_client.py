import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class RAWGClient:
    def __init__(self):
        self.api_key = os.getenv("RAWG_API_KEY")
        self.base_url = "https://api.rawg.io/api/games"

        if not self.api_key:
            print("[警告] 未检测到 RAWG_API_KEY 环境变量，请检查 .env 文件配置！")

    def search_games(self, query: str, page_size: int = 20):
        if not self.api_key:
            print("[错误] 缺少 API Key，无法发起请求。")
            return []

        """
        根据关键字搜索游戏
        :param query: 搜索关键词
        :param page_size: 返回的结果条数，默认5条
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

            # 如果 HTTP 状态码不是 200，直接抛出异常
            response.raise_for_status()

            data = response.json()
            results = data.get('results', [])

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

            return cleaned_games

        except requests.exceptions.RequestException as e:
            print(f"[错误] 请求 RAWG API 失败: {e}")
            return []


# 本地快速本地测试
if __name__ == "__main__":
    # 填入你注册好的 RAWG API Key
    client = RAWGClient()

    print("正在向 RAWG 发起搜索测试...")
    # 拿一个游戏测试
    test_results = client.search_games("Super Mario Galaxy")

    print(f"共搜到 {len(test_results)} 个结果：\n")
    for game in test_results:
        print(f"ID: {game['id']}")
        print(f"名称: {game['title_en']}")
        print(f"Slug: {game['slug']}")
        print(f"发售日期: {game['release_date']}")
        print(f"封面URL: {game['boxart_url']}")
        print("-" * 30)