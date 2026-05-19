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
                              completion_date, review_notes: str = "", screenshot_path: str = None) -> Record:
        """
        保存用户的通关记录
        """
        try:
            # 1. 检查游戏是否已存在于本地拓扑结构中
            existing_game = self.db.query(Game).filter(Game.id == rawg_game_data['id']).first()

            if existing_game:
                game = existing_game
                print(f"[Service] 游戏《{game.title_en}》在本地已存在，直接绑定关联。")
            else:
                # 万一传入的是字符串形式的游戏发售日期，在此处做最后的转换兜底
                r_date = rawg_game_data.get('release_date')
                if isinstance(r_date, str) and r_date.strip() != "":
                    try:
                        r_date = datetime.datetime.strptime(r_date.strip(), "%Y-%m-%d").date()
                    except ValueError:
                        r_date = None

                game = Game(
                    id=rawg_game_data['id'],
                    title_en=rawg_game_data['title_en'],
                    slug=rawg_game_data.get('slug', ''),
                    boxart_url=rawg_game_data.get('boxart_url', ''),
                    release_date=r_date
                )
                self.db.add(game)
                self.db.flush()  # 迫使 SQLAlchemy 分配主键，但不提交整个事务
                print(f"[Service] 发现全新卡带《{game.title_en}》，成功同步至本地游戏字典。")

            # 对用户的通关日期进行最后的类型检查
            if isinstance(completion_date, str) and completion_date.strip() != "":
                try:
                    completion_date = datetime.datetime.strptime(completion_date.strip(), "%Y-%m-%d").date()
                except ValueError:
                    completion_date = datetime.date.today()
            elif not completion_date:
                completion_date = datetime.date.today()

            # 2. 正式实例化持久化通关记录模型
            record = Record(
                user_id=user_id,
                game_id=game.id,
                completion_date=completion_date,
                play_time=play_time,
                screenshot_path=screenshot_path,
                review_notes=review_notes
            )

            self.db.add(record)
            self.db.commit()  # 提交整体事务，确保原子性
            print(f"[Service] 事务提交：用户 {user_id} 的通关记录落盘成功。")
            return record

        except Exception as e:
            self.db.rollback()  # 触发异常时必须回滚数据库连接，防止破坏连接池状态
            print(f"[Service 事务回滚] 保存通关记录失败: {e}")
            raise e


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