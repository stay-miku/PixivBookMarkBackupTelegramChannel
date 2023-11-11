import contextlib

from sqlalchemy import Column, String, create_engine, Integer, ForeignKey
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy.orm
# from sqlalchemy.orm import declarative_base
import os


database_path = "data/"
debug = False

if not os.path.exists(database_path):
    os.makedirs(database_path)


Base = declarative_base()


# 正常情况下这个表只有一行
class Bot(Base):
    __tablename__ = "bots"

    key = Column(String, primary_key=True)  # bot的apikey
    admin = Column(String)                  # 拥有者的id
    cookie = Column(String)                 # pixiv cookie


class Illust(Base):
    __tablename__ = "illusts"

    id = Column(String, primary_key=True)   # pid
    title = Column(String)                  # 标题
    type = Column(Integer)                  # 类型: 有插画 漫画 小说 动图
    comment = Column(String)                # 作品描述,由画师设置
    tags = Column(String)                   # tag 格式为tag=>translated_tag=>translated_tag \n tag=>translated_tag \n tag ...
    upload_date = Column(String)            # 上传时间
    user_id = Column(String, index=True)    # 作者id
    user_name = Column(String)              # 作者昵称
    user_account = Column(String, index=True)           # 作者用户名
    page_count = Column(Integer)            # 张数
    ai = Column(Integer)                    # ai类型
    detial = Column(String)                 # 作品详细信息,为json字符串(实际上就是pixiv api返回的值)
    backup = Column(Integer, index=True)    # 是否已备份 用于检索未备份作品
    unavailable = Column(Integer, index=True)           # 作品是否失效(删除或者受限) 即使失效也需要备份(一个提示作品失效消息)
    saved = Column(Integer, index=True)     # 是否备份成功(已备份但是因作品失效而备份失败)

# backup = 1 unavailable = 0 saved = 1 正常已备份状态
# backup = 1 unavailable = 1 saved = ? 不执行
# backup = 0 unavailable = ? saved = ? 执行备份操作  unavailable = 1 => saved = 0 并发送一个提示消息
# backup = 1 unavailable = 0 saved = 0 执行备份操作 saved = 1 删除提示消息


class Channel(Base):
    __tablename__ = "channels"

    id = Column(String, primary_key=True)   # channel id


class PreviewBackup(Base):
    __tablename__ = "illust_backup_previews"

    message = Column(String, primary_key=True)                              # chat_id + message_id
    id = Column(String, ForeignKey(f"{Illust.__tablename__}.id"), index=True)           # 作品id
    channel = Column(String, ForeignKey(f"{Channel.__tablename__}.id"))     # channel id
    message_id = Column(String, index=True)                                 # 对应消息id


class Backup(Base):
    __tablename__ = "illust_backups"

    message = Column(String, primary_key=True)                              # chat_id + message_id
    id = Column(String, ForeignKey(f"{Illust.__tablename__}.id"), index=True)           # 作品id
    channel = Column(String, ForeignKey(f"{Channel.__tablename__}.id"))     # channel id
    message_id = Column(String, index=True)                                 # 对应消息id


engine = create_engine(f"sqlite:///{database_path}data.db", echo=debug)

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)


@contextlib.contextmanager
def start_session() -> sqlalchemy.orm.Session:
    s = Session()
    try:
        yield s
        s.commit()
    except Exception as e:
        s.rollback()
        raise e
    finally:
        s.close()


