import datetime
import os
import traceback
import db
import asyncio
import aiofiles
from telegram.ext import ContextTypes
import lock
import config
import logging

logger = logging.getLogger("database_backup")
logger.setLevel(logging.DEBUG)


async def start_backup(context: ContextTypes.DEFAULT_TYPE):
    while lock.isLock:
        await asyncio.sleep(0.1)
    lock.lock()
    try:
        if config.db_backup_option == "shell":
            await backup_in_shell(config.db_backup_shell_command)
        elif config.db_backup_option == "path":
            # 将数据库文件命名为原名+格式化时间然后再复制到新路径
            await backup_to_new_path(os.path.join(config.db_backup_path, f"{os.path.basename(db.database_path).split('.')[0]}_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.db"))
        elif config.db_backup_option == "post":
            await backup_by_post(config.db_backup_post_url, config.db_backup_post_header, config.db_backup_post_data)
        logger.info("backup db success")
    except Exception as e:
        await context.bot.sendMessage(chat_id=config.admin, text=f"备份发生错误: {e}")
        traceback.print_exception(type(e), e, e.__traceback__)
        logger.error(f"backup db error: {e}")
        return
    lock.unlock()


async def backup_in_shell(shell_command):
    pass


async def backup_to_new_path(new_path):
    db_path = db.database_path
    size = 0
    async with aiofiles.open(db_path, 'rb') as source_file:
        async with aiofiles.open(new_path, 'wb') as destination_file:

            while True:
                chunk = await source_file.read(8192)
                if not chunk:
                    break
                size += len(chunk)
                await destination_file.write(chunk)
    return size


async def backup_by_post(post_url, headers=None, data=None):
    pass
