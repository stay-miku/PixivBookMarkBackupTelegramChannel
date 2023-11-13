import logging
import sqlalchemy.orm


logger = logging.getLogger("backup")


def send_backup(illust_id, session: sqlalchemy.orm.Session):
    pass


def delete_backup(illust_id, session: sqlalchemy.orm.Session):
    pass
