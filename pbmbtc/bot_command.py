import traceback

from telegram import Update
from telegram.ext import ContextTypes
from . import config
from . import update_illust
from . import update_bookmarks_record
import logging
from . import db
import asyncio

logger = logging.getLogger("bot_command")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass


async def reload_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user.id == int(config.admin):
        await context.bot.sendMessage(chat_id=update.effective_chat.id, text="你不是管理员")
        logger.info(f"some one use admin command reload_config: {update.effective_user.id}")
        return
    else:
        config.load_config()
        logger.info("reload config")
        await context.bot.sendMessage(chat_id=update.effective_chat.id, text="操作成功")


async def stop_update_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user.id == int(config.admin):
        await context.bot.sendMessage(reply_to_message_id=update.effective_message.message_id,
                                      chat_id=update.effective_chat.id, text="你不是管理员")
        logger.info(f"some one use admin command reload_config: {update.effective_user.id}")
        return

    task = context.job_queue.get_jobs_by_name("bookmarks_task")
    for job in task:
        job.schedule_removal()
    logger.info("delete task")

    await context.bot.sendMessage(chat_id=update.effective_chat.id, text="操作成功")


async def stop_backup_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user.id == int(config.admin):
        await context.bot.sendMessage(reply_to_message_id=update.effective_message.message_id,
                                      chat_id=update.effective_chat.id, text="你不是管理员")
        logger.info(f"some one use admin command reload_config: {update.effective_user.id}")
        return

    task = context.job_queue.get_jobs_by_name("backup_task")
    for job in task:
        job.schedule_removal()
    logger.info("delete task")

    await context.bot.sendMessage(chat_id=update.effective_chat.id, text="操作成功")


async def start_update_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user.id == int(config.admin):
        await context.bot.sendMessage(reply_to_message_id=update.effective_message.message_id,
                                      chat_id=update.effective_chat.id, text="你不是管理员")
        logger.info(f"some one use admin command reload_config: {update.effective_user.id}")
        return

    context.job_queue.run_repeating(update_bookmarks_record.update_task, interval=config.bookmarks_update_interval
                                    , name="bookmarks_task", first=config.bookmarks_update_interval)

    await context.bot.sendMessage(chat_id=update.effective_chat.id, text="操作成功")


async def start_async_update_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user.id == int(config.admin):
        await context.bot.sendMessage(reply_to_message_id=update.effective_message.message_id,
                                      chat_id=update.effective_chat.id, text="你不是管理员")
        logger.info(f"some one use admin command reload_config: {update.effective_user.id}")
        return

    context.job_queue.run_repeating(update_bookmarks_record.async_update_task, interval=config.bookmarks_update_interval
                                    , name="bookmarks_task", first=config.bookmarks_update_interval)

    await context.bot.sendMessage(chat_id=update.effective_chat.id, text="操作成功")


async def start_backup_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user.id == int(config.admin):
        await context.bot.sendMessage(reply_to_message_id=update.effective_message.message_id,
                                      chat_id=update.effective_chat.id, text="你不是管理员")
        logger.info(f"some one use admin command reload_config: {update.effective_user.id}")
        return

    context.job_queue.run_repeating(update_illust.update_backup, interval=config.backup_interval, name="backup_task"
                                    , first=config.backup_interval)

    await context.bot.sendMessage(chat_id=update.effective_chat.id, text="操作成功")


async def force_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user.id == int(config.admin):
        await context.bot.sendMessage(reply_to_message_id=update.effective_message.message_id,
                                      chat_id=update.effective_chat.id, text="你不是管理员")
        logger.info(f"some one use admin command reload_config: {update.effective_user.id}")
        return

    await context.bot.sendMessage(chat_id=update.effective_chat.id, text="操作成功,等待更新")
    logger.info("force update start")
    await update_bookmarks_record.update_task(context)
    # logger.info("force update completed")
    # await context.bot.sendMessage(chat_id=update.effective_chat.id, text="操作成功")


async def force_async_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user.id == int(config.admin):
        await context.bot.sendMessage(reply_to_message_id=update.effective_message.message_id,
                                      chat_id=update.effective_chat.id, text="你不是管理员")
        logger.info(f"some one use admin command reload_config: {update.effective_user.id}")
        return

    await context.bot.sendMessage(chat_id=update.effective_chat.id, text="操作成功,等待更新")
    logger.info("force update start")
    await update_bookmarks_record.async_update_task(context)
    # logger.info("force update completed")
    # await context.bot.sendMessage(chat_id=update.effective_chat.id, text="操作成功")


async def force_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user.id == int(config.admin):
        await context.bot.sendMessage(reply_to_message_id=update.effective_message.message_id,
                                      chat_id=update.effective_chat.id, text="你不是管理员")
        logger.info(f"some one use admin command reload_config: {update.effective_user.id}")
        return

    await context.bot.sendMessage(chat_id=update.effective_chat.id, text="操作成功,等待备份")
    logger.info("force backup start")
    await update_illust.update_backup(context)
    # logger.info("force backup completed")
    # await context.bot.sendMessage(chat_id=update.effective_chat.id, text="操作成功")


# 需安装sqlite3
async def sql(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user.id == int(config.admin):
        await context.bot.sendMessage(reply_to_message_id=update.effective_message.message_id,
                                      chat_id=update.effective_chat.id, text="你不是管理员")
        logger.info(f"some one use admin command reload_config: {update.effective_user.id}")
        return
    sql_str = ' '.join(context.args)
    logger.info(f"execute sql {sql_str}")

    process = await asyncio.create_subprocess_shell(f"sqlite3 {db.database_path}data.db '{sql_str}'"
                                                    , stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                                                    , shell=True)
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        logger.warning(f"execute failed: {stderr}")
        await context.bot.sendMessage(chat_id=update.effective_chat.id, text=f"发生错误: {stderr[:4000]}")
        return

    await context.bot.sendMessage(chat_id=update.effective_chat.id, text=f"执行成功: \n {stdout[:4000]}")


async def shell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user.id == int(config.admin):
        await context.bot.sendMessage(reply_to_message_id=update.effective_message.message_id,
                                      chat_id=update.effective_chat.id, text="你不是管理员")
        logger.info(f"some one use admin command reload_config: {update.effective_user.id}")
        return

    shell_command = ' '.join(context.args)
    logger.info(f"execute command: {shell_command}")

    process = await asyncio.create_subprocess_shell(shell_command
                                                    , stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                                                    , shell=True)
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        logger.warning(f"execute failed: {stderr}")
        await context.bot.sendMessage(chat_id=update.effective_chat.id, text=f"发生错误: {stderr[:4000]}")
        return

    await context.bot.sendMessage(chat_id=update.effective_chat.id, text=f"执行成功: \n {stdout[:4000]}")


# 手动添加备份,需要提前放好备份文件
async def add_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user.id == int(config.admin):
        await context.bot.sendMessage(reply_to_message_id=update.effective_message.message_id,
                                      chat_id=update.effective_chat.id, text="你不是管理员")
        logger.info(f"some one use admin command reload_config: {update.effective_user.id}")
        return

    try:
        illust_id = context.args[0]
        path = context.args[1]

    except Exception as e:
        await context.bot.sendMessage(chat_id=update.effective_chat.id, text=f"发生错误: {e}")
        traceback.print_exception(type(e), e, e.__traceback__)
