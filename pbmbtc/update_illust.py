import asyncio

from telegram.ext import ContextTypes
from . import db
from . import config
from . import backup
import logging

logger = logging.getLogger("update backup")


async def updateBackup(context: ContextTypes.DEFAULT_TYPE):

    for i in range(config.backup_number_ontime):
        with db.start_session() as session:
            not_backup = session.query(db.Illust).filter_by(backup=0).first()
            not_backup_id = not_backup.id

        await backup.send_backup(not_backup_id, context)

        logger.info(f"backup completed, illust: {not_backup_id}")

    logger.info("backup task completed")


async def update_backup(context: ContextTypes.DEFAULT_TYPE):

    logger.info("start backup task")
    asyncio.create_task(updateBackup(context))


