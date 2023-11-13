from telegram import Update
from telegram.ext import ContextTypes
from . import config
from . import update_illust
from . import update_bookmarks_record
import logging

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


async def reload_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user.id == int(config.admin):
        await context.bot.sendMessage(reply_to_message_id=update.effective_message.message_id,
                                      chat_id=update.effective_chat.id, text="你不是管理员")
        logger.info(f"some one use admin command reload_config: {update.effective_user.id}")
        return

    # reload
    task = context.job_queue.get_jobs_by_name("bookmarks_task")
    for job in task:
        job.schedule_removal()
    task = context.job_queue.get_jobs_by_name("backup_task")
    for job in task:
        job.schedule_removal()
    logger.info("delete task")

    context.job_queue.run_repeating(update_bookmarks_record.update_task, interval=config.bookmarks_update_interval
                                    , name="bookmarks_task", first=config.bookmarks_update_interval)
    context.job_queue.run_repeating(update_illust.update_backup, interval=config.backup_interval, name="backup_task"
                                    , first=config.backup_interval)
    logger.info("start task")
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
    logger.info("force update completed")


async def force_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user.id == int(config.admin):
        await context.bot.sendMessage(reply_to_message_id=update.effective_message.message_id,
                                      chat_id=update.effective_chat.id, text="你不是管理员")
        logger.info(f"some one use admin command reload_config: {update.effective_user.id}")
        return

    await context.bot.sendMessage(chat_id=update.effective_chat.id, text="操作成功,等待备份")
    logger.info("force backup start")
    await update_illust.update_backup(context)
    logger.info("force backup completed")
