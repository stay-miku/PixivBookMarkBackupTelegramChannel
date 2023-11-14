import asyncio

from telegram.ext import ContextTypes
from . import db
from . import config
from . import backup
import logging

logger = logging.getLogger("update backup")


async def updateBackup(context: ContextTypes.DEFAULT_TYPE):

    for i in range(config.backup_number_ontime):

        await backup.send_backup(None, context)

    logger.info("backup task completed")


async def update_backup(context: ContextTypes.DEFAULT_TYPE):

    logger.info("start backup task")
    asyncio.create_task(updateBackup(context))


