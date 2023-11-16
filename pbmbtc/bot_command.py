import traceback

import telegram
from telegram import Update
from telegram.ext import ContextTypes
from . import config
from . import update_illust
from . import update_bookmarks_record
import logging
from . import db
import asyncio
from . import backup
from sqlalchemy.future import select
from sqlalchemy import func

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
        logger.info(f"some one use admin command stop_update_task: {update.effective_user.id}")
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
        logger.info(f"some one use admin command stop_backup_task: {update.effective_user.id}")
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
        logger.info(f"some one use admin command start_update_task: {update.effective_user.id}")
        return

    context.job_queue.run_repeating(update_bookmarks_record.update_task, interval=config.bookmarks_update_interval
                                    , name="bookmarks_task", first=config.bookmarks_update_interval)

    await context.bot.sendMessage(chat_id=update.effective_chat.id, text="操作成功")


async def start_async_update_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user.id == int(config.admin):
        await context.bot.sendMessage(reply_to_message_id=update.effective_message.message_id,
                                      chat_id=update.effective_chat.id, text="你不是管理员")
        logger.info(f"some one use admin command start_async_update_task: {update.effective_user.id}")
        return

    context.job_queue.run_repeating(update_bookmarks_record.async_update_task, interval=config.bookmarks_update_interval
                                    , name="bookmarks_task", first=config.bookmarks_update_interval)

    await context.bot.sendMessage(chat_id=update.effective_chat.id, text="操作成功")


async def start_backup_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user.id == int(config.admin):
        await context.bot.sendMessage(reply_to_message_id=update.effective_message.message_id,
                                      chat_id=update.effective_chat.id, text="你不是管理员")
        logger.info(f"some one use admin command start_backup_task: {update.effective_user.id}")
        return

    context.job_queue.run_repeating(update_illust.update_backup, interval=config.backup_interval, name="backup_task"
                                    , first=config.backup_interval)

    await context.bot.sendMessage(chat_id=update.effective_chat.id, text="操作成功")


async def force_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user.id == int(config.admin):
        await context.bot.sendMessage(reply_to_message_id=update.effective_message.message_id,
                                      chat_id=update.effective_chat.id, text="你不是管理员")
        logger.info(f"some one use admin command force_update: {update.effective_user.id}")
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
        logger.info(f"some one use admin command force_async_update: {update.effective_user.id}")
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
        logger.info(f"some one use admin command force_backup: {update.effective_user.id}")
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
        logger.info(f"some one use admin command sql: {update.effective_user.id}")
        return
    sql_str = ' '.join(context.args)
    logger.info(f"execute sql {sql_str}")

    process = await asyncio.create_subprocess_shell(f"sqlite3 {db.database_path}data.db '{sql_str}'"
                                                    , stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                                                    , shell=True)
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        logger.warning(f"execute failed: {stderr.decode('utf-8')}")
        await context.bot.sendMessage(chat_id=update.effective_chat.id, text=f"发生错误: {stderr.decode('utf-8')[:4000]}")
        return

    await context.bot.sendMessage(chat_id=update.effective_chat.id, text=f"执行成功: \n {stdout.decode('utf-8')[:4000]}")


async def shell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user.id == int(config.admin):
        await context.bot.sendMessage(reply_to_message_id=update.effective_message.message_id,
                                      chat_id=update.effective_chat.id, text="你不是管理员")
        logger.info(f"some one use admin command shell: {update.effective_user.id}")
        return

    shell_command = ' '.join(context.args)
    logger.info(f"execute command: {shell_command}")

    process = await asyncio.create_subprocess_shell(shell_command
                                                    , stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                                                    , shell=True)
    stdout, stderr = await asyncio.wait_for(
        process.communicate(),
        timeout=60
    )

    if process.returncode != 0:
        logger.warning(f"execute failed: {stderr.decode('utf-8')}")
        await context.bot.sendMessage(chat_id=update.effective_chat.id, text=f"发生错误: {stderr.decode('utf-8')[:4000]}")
        return

    await context.bot.sendMessage(chat_id=update.effective_chat.id, text=f"执行成功: \n {stdout.decode('utf-8')[:4000]}")


# 手动添加备份,需要提前放好备份文件
async def add_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user.id == int(config.admin):
        await context.bot.sendMessage(reply_to_message_id=update.effective_message.message_id,
                                      chat_id=update.effective_chat.id, text="你不是管理员")
        logger.info(f"some one use admin command add_backup: {update.effective_user.id}")
        return

    try:
        illust_id = context.args[0]
        path = context.args[1]

        await backup.send_backup_from_file(illust_id, path, context)

        await context.bot.sendMessage(chat_id=update.effective_chat.id, text="备份成功")

    except Exception as e:
        await context.bot.sendMessage(chat_id=update.effective_chat.id, text=f"发生错误: {e}")
        traceback.print_exception(type(e), e, e.__traceback__)


async def rand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:

        async with db.start_async_session() as session:
            query = select(db.PreviewBackup).order_by(func.random()).limit(1)
            result = await session.execute(query)

            illust = result.first()[0]

            await context.bot.forwardMessage(chat_id=update.effective_chat.id, from_chat_id=illust.channel
                                             , message_id=illust.message_id)
            logger.info(f"rand backup: {illust.id}")
    except telegram.error.RetryAfter as e:
        # 按理来说出现retry after后下面这个应该执行不了,但是还是先写上好了
        await context.bot.sendMessage(chat_id=update.effective_chat.id
                                      , reply_to_message_id=update.effective_message.message_id
                                      , text=f"发送过快,等待{e.retry_after}秒后再试")

    except Exception as e:
        logger.warning(f"rand exception: {e}")
        traceback.print_exception(type(e), e, e.__traceback__)
