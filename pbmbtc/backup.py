import logging
import sqlalchemy.orm
from . import db
from . import config


logger = logging.getLogger("backup")


async def send_illust(illust: db.Illust, session: sqlalchemy.orm.Session):
    pass


async def send_manga(illust: db.Illust, session: sqlalchemy.orm.Session):
    await send_illust(illust, session)


async def send_ugoira(illust: db.Illust, session: sqlalchemy.orm.Session):
    pass


async def send_backup(illust: str | db.Illust, session: sqlalchemy.orm.Session):
    if isinstance(illust, str):
        illust = session.query(db.Illust).filter_by(id=illust).one()

    if illust.type == 0:
        await send_illust(illust, session)

    elif illust.type == 1:
        await send_manga(illust, session)

    elif illust.type == 2:
        await send_ugoira(illust, session)

    else:
        raise Exception(f"Unknown illust type: {illust.type}, id: {illust.id}")


async def delete_backup(illust: str | db.Illust, session: sqlalchemy.orm.Session):
    if isinstance(illust, str):
        illust = session.query(db.Illust).filter_by(id=illust).one()


