from sqlalchemy import Column, String, create_engine, Integer, ForeignKey
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


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
    user_id = Column(String)                # 作者id
    user_name = Column(String)              # 作者昵称
    user_account = Column(String)           # 作者用户名
    page_count = Column(Integer)            # 张数
    ai = Column(Integer)                    # ai类型


class Channel(Base):
    __tablename__ = "channels"

    id = Column(String, primary_key=True)   # channel id


class PreviewBackup(Base):
    __tablename__ = "illust_backup_previews"

    id = Column(String, ForeignKey(f"{Illust.__tablename__}.id"))           # 作品id
    channel = Column(String, ForeignKey(f"{Channel.__tablename__}.id"))     # channel id
    message_id = Column(String)                                             # 对应消息id


class Backup(Base):
    __tablename__ = "illust_backups"

    id = Column(String, ForeignKey(f"{Illust.__tablename__}.id"))           # 作品id
    channel = Column(String, ForeignKey(f"{Channel.__tablename__}.id"))     # channel id
    message_id = Column(String)                                             # 对应消息id

