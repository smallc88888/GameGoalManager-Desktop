from sqlalchemy.orm import Session
import datetime
from models import Game, Record


class RecordService:
    def __init__(self, db_session: Session):
        """
        初始化服务层，注入数据库 Session
        """
        self.db = db_session

    def add_completion_record(self, user_id: int, rawg_game_data: dict, play_time: int,
                              screenshot_path: str = None) -> Record:
        """
        核心业务：保存用户的通关记录
        :param user_id: 用户 ID
        :param rawg_game_data: 从 rawg_client 拿到的单个游戏清洗后的字典数据
        :param play_time: 游玩时长
        :param screenshot_path: 通关截图的本地保存路径
        """
        try:
            # 1. 防御机制：检查该游戏是否已经存在于本地数据库中（通过 RAWG 唯一的 ID 检查）
            existing_game = self.db.query(Game).filter(Game.id == rawg_game_data['id']).first()

            if existing_game:
                game = existing_game
                print(f"[提示] 游戏《{game.title_en}》已存在于数据库中，直接复用。")
            else:
                # 如果没有，就新建一个 Game 对象并存入
                game = Game(
                    id=rawg_game_data['id'],
                    title_en=rawg_game_data['title_en'],
                    slug=rawg_game_data['slug'],
                    boxart_url=rawg_game_data['boxart_url'],
                    release_date=rawg_game_data['release_date']
                )
                self.db.add(game)
                print(f"[成功] 新游戏《{game.title_en}》入库。")

            # 2. 创建通关记录对象
            # 默认状态：完成
            new_record = Record(
                user_id=user_id,
                game_id=game.id,
                play_time=play_time,
                screenshot_path=screenshot_path,  # 暂存本地路径
                review_notes="100% Completed",
                completion_date=datetime.datetime.now().astimezone().date(),  # 记录今天通关的日期
            )

            self.db.add(new_record)

            # 3. 提交事务，两张表的数据同时真正写入 .db 文件
            self.db.commit()
            print(f"[成功] 成功为用户 ID:{user_id} 绑定《{game.title_en}》的100%通关记录！")
            return new_record

        except Exception as e:
            # 如果中间任何一步崩了（比如数据库断开、字段溢出），立刻回滚
            self.db.rollback()
            print(f"[重大错误] 保存记录失败，数据库已安全回Rollback。错误信息: {e}")
            return None


if __name__ == "__main__":
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from models import Base, User
    from rawg_client import RAWGClient

    print("================ 联调测试开始 ================")

    # 1. 初始化数据库连接并自动建表（如果表不存在的话）
    DATABASE_URL = "sqlite:///game_goal.db"
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(bind=engine)  # 防御机制：确保表结构已被物理创建

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    # 2. 建立测试用户
    test_user = db.query(User).filter(User.id == 1).first()
    if not test_user:
        # 传入 id 和 username
        test_user = User(id=1, username="small_c_88888", password_hash="mocked_password_hash_sha256", created_at=datetime.datetime.now().astimezone())
        db.add(test_user)
        db.commit()
        print("[初始化] 已成功创建合规的测试用户")

    # 3. 实例化 RAWG 客户端并在线搜索游戏
    rawg = RAWGClient()
    search_keyword = "Metroid Dread"
    print(f"正在联网从 RAWG 搜索: '{search_keyword}' ...")
    search_results = rawg.search_games(search_keyword, page_size=1)

    if search_results:
        target_game_data = search_results[0]
        print(f"搜索命中成功: {target_game_data['title_en']} (ID: {target_game_data['id']})")

        # 4. 实例化记录服务，执行持久化
        service = RecordService(db_session=db)

        # 模拟一条数据
        mock_screenshot = "/uploads/screenshots/metroid_dread_100.png"

        # 运行持久化服务
        service.add_completion_record(user_id=test_user.id, rawg_game_data=target_game_data, play_time=25,
                                      screenshot_path=mock_screenshot)
    else:
        print("[错误] 未能从 RAWG 搜到任何相关游戏，请检查网络或 .env 配置！")

    db.close()
    print("================ 联调测试结束 ================")