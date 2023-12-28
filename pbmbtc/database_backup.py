import datetime
import os
import traceback
from . import db
import asyncio
import aiofiles
from telegram.ext import ContextTypes
from . import lock
from . import config
import logging

logger = logging.getLogger("database_backup")
logger.setLevel(logging.DEBUG)


async def start_backup(context: ContextTypes.DEFAULT_TYPE):

    asyncio.create_task(start_backup_task(context))


async def start_backup_task(context: ContextTypes.DEFAULT_TYPE):
    while lock.isLock:
        await asyncio.sleep(0.1)
    lock.lock()
    try:
        if config.db_backup_option == "shell":
            stdout = await backup_in_shell(config.db_backup_shell_command)

            # if len(stdout) < 4000:
            #     await context.bot.sendMessage(chat_id=config.admin, text=f"stdout: {stdout}")
            # else:
            #     await context.bot.sendDocument(chat_id=config.admin, document=stdout, filename="info.log")
        elif config.db_backup_option == "path":
            # 将数据库文件命名为原名+格式化时间然后再复制到新路径
            await backup_to_new_path(os.path.join(config.db_backup_path, f"{db.database_file_name.split('.')[0]}-{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.db"))
        elif config.db_backup_option == "post":
            await backup_by_post(config.db_backup_post_url, config.db_backup_post_header, config.db_backup_post_data)
        logger.info("backup db success")
        # await context.bot.sendMessage(chat_id=config.admin, text="备份成功")
    except Exception as e:
        if len(str(e)) < 4000:
            await context.bot.sendMessage(chat_id=config.admin, text=f"备份发生错误: {e}")
        else:
            await context.bot.sendDocument(chat_id=config.admin, document=str(e), filename="error.log")
        traceback.print_exception(type(e), e, e.__traceback__)
        logger.error(f"backup db error: {e}")
        return
    lock.unlock()


async def backup_in_shell(shell_command):
    db_path = db.database_path
    db_name = db.database_file_name
    old_db_full_path = os.path.join(db_path, db_name)
    new_db_name = f"{db_name.split('.')[0]}-{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.db"

    shell_command = shell_command.replace("{db_path}", old_db_full_path).replace("{new_name}", new_db_name)
    logger.info(f"shell command: {shell_command}")

    process = await asyncio.create_subprocess_shell(shell_command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, shell=True)
    stdout, stderr = await process.communicate()

    logger.info(f"stdout: {stdout.decode('utf-8')}\n--------------------------\nstderr: {stderr.decode('utf-8')}")
    if process.returncode != 0:
        raise Exception(f"stdout: {stdout.decode('utf-8')}\n--------------------------\nstderr: {stderr.decode('utf-8')}")
    else:
        return stdout.decode('utf-8')


async def backup_to_new_path(new_path):
    db_path = db.database_path
    db_name = db.database_file_name
    size = 0
    async with aiofiles.open(os.path.join(db_path, db_name), 'rb') as source_file:
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
