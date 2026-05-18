import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Date, Text, ForeignKey, true
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now().astimezone())

    records = relationship("Record", back_populates='user')


class Game(Base):
    __tablename__ = 'games'

    id = Column(Integer, primary_key=True)

    # 游戏名字
    title_en = Column(String(150), nullable=False)  # 游戏英文名 (RAWG 默认返回的 name)
    title_cn = Column(String(150), nullable=True)  # 用户或后续汉化补上的中文名

    # 游戏在 RAWG 里的唯一文本标识
    slug = Column(String(100), unique=True, nullable=False)

    # RAWG 对应的封面/背景图 URL，字段对应 background_image
    boxart_url = Column(String(255), nullable=True)

    # RAWG 返回的发售日期，字段对应released
    release_date = Column(Date, nullable=True)

    # 建立反向关联
    records = relationship('Record', back_populates='game')


class Record(Base):
    __tablename__ = 'records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    game_id = Column(Integer, ForeignKey('games.id'), nullable=False)

    completion_date = Column(Date, nullable=False)  # 用户通关时间
    play_time = Column(Integer, nullable=True)  # 游玩时长(小时)
    screenshot_path = Column(String(255), nullable=False)  # WebP截图的本地存储路径
    review_notes = Column(Text, nullable=True)  # 心得体会
    created_at = Column(DateTime, default=lambda: datetime.datetime.now().astimezone())

    # 建立双向绑定
    user = relationship('User', back_populates='records')
    game = relationship('Game', back_populates='records')

DATABASE_URL = "sqlite:///game_goal.db"
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    print("正在初始化本地数据库...")
    _validate_models = [User, Game, Record]
    init_db()
    print("数据库表结构创建成功！")