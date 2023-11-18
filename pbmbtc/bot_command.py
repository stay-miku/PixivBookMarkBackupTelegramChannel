import re
import traceback

import aiofiles
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
from sqlalchemy import func, and_, or_

logger = logging.getLogger("bot_command")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.sendMessage(chat_id=update.effective_chat.id,
                                  text="使用/rand获取随机收藏作品\n使用/search搜索想要的作品\n使用/plugin获取适用于pagermaid的快捷插件\n以上搜索和随机范围仅限于备份频道内")
    pass


async def reload_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user.id == int(config.admin):
        await context.bot.sendMessage(chat_id=update.effective_chat.id, text="你不是bot管理员")
        logger.info(f"some one use admin command reload_config: {update.effective_user.id}")
        return
    else:
        config.load_config()
        logger.info("reload config")
        await context.bot.sendMessage(chat_id=update.effective_chat.id, text="操作成功")


async def stop_update_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user.id == int(config.admin):
        await context.bot.sendMessage(reply_to_message_id=update.effective_message.message_id,
                                      chat_id=update.effective_chat.id, text="你不是bot管理员")
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
                                      chat_id=update.effective_chat.id, text="你不是bot管理员")
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
                                      chat_id=update.effective_chat.id, text="你不是bot管理员")
        logger.info(f"some one use admin command start_update_task: {update.effective_user.id}")
        return

    context.job_queue.run_repeating(update_bookmarks_record.update_task, interval=config.bookmarks_update_interval
                                    , name="bookmarks_task", first=config.bookmarks_update_interval)

    await context.bot.sendMessage(chat_id=update.effective_chat.id, text="操作成功")


async def start_async_update_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user.id == int(config.admin):
        await context.bot.sendMessage(reply_to_message_id=update.effective_message.message_id,
                                      chat_id=update.effective_chat.id, text="你不是bot管理员")
        logger.info(f"some one use admin command start_async_update_task: {update.effective_user.id}")
        return

    context.job_queue.run_repeating(update_bookmarks_record.async_update_task, interval=config.bookmarks_update_interval
                                    , name="bookmarks_task", first=config.bookmarks_update_interval)

    await context.bot.sendMessage(chat_id=update.effective_chat.id, text="操作成功")


async def start_backup_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user.id == int(config.admin):
        await context.bot.sendMessage(reply_to_message_id=update.effective_message.message_id,
                                      chat_id=update.effective_chat.id, text="你不是bot管理员")
        logger.info(f"some one use admin command start_backup_task: {update.effective_user.id}")
        return

    context.job_queue.run_repeating(update_illust.update_backup, interval=config.backup_interval, name="backup_task"
                                    , first=config.backup_interval)

    await context.bot.sendMessage(chat_id=update.effective_chat.id, text="操作成功")


async def force_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user.id == int(config.admin):
        await context.bot.sendMessage(reply_to_message_id=update.effective_message.message_id,
                                      chat_id=update.effective_chat.id, text="你不是bot管理员")
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
                                      chat_id=update.effective_chat.id, text="你不是bot管理员")
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
                                      chat_id=update.effective_chat.id, text="你不是bot管理员")
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
                                      chat_id=update.effective_chat.id, text="你不是bot管理员")
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
        if len(stderr.decode("utf-8")) > 4000:
            await context.bot.sendDocument(chat_id=update.effective_chat.id, document=stderr, filename="error.log")
        else:
            await context.bot.sendMessage(chat_id=update.effective_chat.id,
                                          text=f"sqlite> {sql_str} \n{stderr.decode('utf-8')}")
        return
    if len(stdout.decode("utf-8")) > 4000:
        await context.bot.sendDocument(chat_id=update.effective_chat.id, document=stdout, filename="sqlite.log")
    else:
        await context.bot.sendMessage(chat_id=update.effective_chat.id,
                                      text=f"sqlite> {sql_str} \n{stdout.decode('utf-8')}")


async def shell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user.id == int(config.admin):
        await context.bot.sendMessage(reply_to_message_id=update.effective_message.message_id,
                                      chat_id=update.effective_chat.id, text="你不是bot管理员")
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
        if len(stderr.decode("utf-8")) > 4000:
            await context.bot.sendDocument(chat_id=update.effective_chat.id, document=stderr, filename="error.log")
        else:
            await context.bot.sendMessage(chat_id=update.effective_chat.id,
                                          text=f"~# {shell_command} \n{stderr.decode('utf-8')}")
        return

    if len(stdout.decode("utf-8")) > 4000:
        await context.bot.sendDocument(chat_id=update.effective_chat.id, document=stdout, filename="shell.log")
    await context.bot.sendMessage(chat_id=update.effective_chat.id,
                                  text=f"~# {shell_command} \n{stdout.decode('utf-8')}")


# 手动添加备份,需要提前放好备份文件
async def add_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user.id == int(config.admin):
        await context.bot.sendMessage(reply_to_message_id=update.effective_message.message_id,
                                      chat_id=update.effective_chat.id, text="你不是bot管理员")
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
    logger.info(update.effective_chat.type)
    try:
        # 有参数
        if context.args:
            search_keywords = re.split(r'[,，]', " ".join(context.args))
            logger.info(f"{update.effective_user.id}:{update.effective_user.username} rand tag: {search_keywords}")

            condition = [db.Illust.tags.like(f"%{keyword}%") for keyword in search_keywords]  # 关键词
            condition.append(db.Illust.saved == 1)  # 需被保存

            async with db.start_async_session() as session:
                query = select(db.PreviewBackup).join(db.Illust).filter(and_(*condition)).order_by(func.random()).limit(
                    1)
                result = await session.execute(query)

                illust = result.first()

                if illust:
                    logger.info(f"find: {illust[0].id}")
                    await context.bot.forwardMessage(chat_id=update.effective_chat.id, from_chat_id=illust[0].channel
                                                     , message_id=illust[0].message_id)

                else:
                    logger.info("cannot find illust")
                    if update.effective_chat.type == "private":
                        await context.bot.sendMessage(chat_id=update.effective_chat.id, text="没有找到对应的作品~")
                    else:
                        await context.bot.sendMessage(chat_id=update.effective_chat.id, text="没有找到对应的作品~"
                                                      , reply_to_message_id=update.effective_message.id)

        # 无参数
        else:
            async with db.start_async_session() as session:
                query = select(db.PreviewBackup).join(db.Illust).filter_by(saved=1).order_by(func.random()).limit(1)
                result = await session.execute(query)

                illust = result.first()[0]

                await context.bot.forwardMessage(chat_id=update.effective_chat.id, from_chat_id=illust.channel
                                                 , message_id=illust.message_id)
                if update.effective_user.name:
                    logger.info(
                        f"rand backup: {illust.id}, user: {update.effective_user.id}, username: {update.effective_user.username}")
                else:
                    logger.info(f"rand backup: {illust.id}, user: {update.effective_user.id}")
    except telegram.error.RetryAfter as e:
        # 按理来说出现retry after后下面这个应该执行不了,但是还是先写上好了
        await context.bot.sendMessage(chat_id=update.effective_chat.id
                                      , reply_to_message_id=update.effective_message.message_id
                                      , text=f"发送过快,等待{e.retry_after}秒后再试")

    except Exception as e:
        logger.warning(f"rand exception: {e}")
        await context.bot.sendMessage(chat_id=update.effective_chat.id
                                      , reply_to_message_id=update.effective_message.message_id
                                      , text=f"发生错误: {e}")
        traceback.print_exception(type(e), e, e.__traceback__)


async def force_backup_one(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user.id == int(config.admin):
        await context.bot.sendMessage(reply_to_message_id=update.effective_message.message_id,
                                      chat_id=update.effective_chat.id, text="你不是bot管理员")
        logger.info(f"some one use admin command force_backup_one: {update.effective_user.id}")
        return

    try:
        illust_id = context.args[0]

        await backup.send_backup(illust_id, context)

        await context.bot.sendMessage(chat_id=update.effective_chat.id, text="操作完成")
    except Exception as e:
        await context.bot.sendMessage(chat_id=update.effective_chat.id, text=f"发生错误: {e}")
        traceback.print_exception(type(e), e, e.__traceback__)


async def update_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user.id == int(config.admin):
        await context.bot.sendMessage(reply_to_message_id=update.effective_message.message_id,
                                      chat_id=update.effective_chat.id, text="你不是bot管理员")
        logger.info(f"some one use admin command update_status: {update.effective_user.id}")
        return

    tasks = context.job_queue.get_jobs_by_name("bookmarks_task")

    if tasks:
        await context.bot.sendMessage(chat_id=update.effective_chat.id, text="周期任务已启动")
    else:
        await context.bot.sendMessage(chat_id=update.effective_chat.id, text="周期任务未启动")


async def backup_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user.id == int(config.admin):
        await context.bot.sendMessage(reply_to_message_id=update.effective_message.message_id,
                                      chat_id=update.effective_chat.id, text="你不是bot管理员")
        logger.info(f"some one use admin command backup_status: {update.effective_user.id}")
        return

    tasks = context.job_queue.get_jobs_by_name("backup_task")

    if tasks:
        await context.bot.sendMessage(chat_id=update.effective_chat.id, text="周期任务已启动")
    else:
        await context.bot.sendMessage(chat_id=update.effective_chat.id, text="周期任务未启动")


async def plugin_(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_username = context.bot.name.rsplit("@", 1)[-1]

    async with aiofiles.open("./pagermaid/plugin.py", "r") as f:
        plugin = await f.read()

    plugin = plugin.replace("pixivBookmarksBackupBot", bot_username)

    await context.bot.send_document(chat_id=update.effective_chat.id, document=plugin.encode("utf-8")
                                    , filename=f"{bot_username}_plugin.py"
                                    , caption="提供两条命令,一个ss,为/rand命令,一个search,为/search")


async def admin_plugin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user.id == int(config.admin):
        await context.bot.sendMessage(reply_to_message_id=update.effective_message.message_id,
                                      chat_id=update.effective_chat.id, text="你不是bot管理员")
        logger.info(f"some one use admin command admin_plugin: {update.effective_user.id}")
        return

    bot_username = context.bot.name.rsplit("@", 1)[-1]

    async with aiofiles.open("./pagermaid/admin.py", "r") as f:
        plugin = await f.read()

    plugin = plugin.replace("pixivBookmarksBackupBot", bot_username)

    await context.bot.send_document(chat_id=update.effective_chat.id, document=plugin.encode("utf-8")
                                    , filename=f"{bot_username}_admin_plugin.py")


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:

        try:
            number = int(" ".join(context.args))
            search_number = " ".join(context.args)
            conditions = [db.Illust.id == search_number, db.Illust.user_id == search_number]
            query = select(db.Illust).filter(or_(*conditions)).filter_by(saved=1).limit(10)

        except ValueError:
            search_keyword = re.split(r"[,，]", " ".join(context.args))

            conditions = [(db.Illust.title + " " + db.Illust.tags + " " + db.Illust.user_name + " " +
                           db.Illust.user_account).like(f"%{i}%") for i in search_keyword]
            conditions.append(db.Illust.saved == 1)
            query = select(db.Illust).filter(and_(*conditions)).order_by(func.random()).limit(10)

        async with db.start_async_session() as session:

            result = await session.execute(query)

            illusts = result.all()

            if illusts:
                messages = []
                for illust in illusts:
                    query = select(db.PreviewBackup).filter_by(id=illust[0].id).limit(1)
                    message_record_result = await session.execute(query)
                    message_reocrd = message_record_result.first()[0]
                    messages.append({"channel": message_reocrd.channel, "message_id": message_reocrd.message_id,
                                     "id": message_reocrd.id})
                send_text = "\n".join(
                    [f"<a href=\"https://t.me/c/{i['channel'][4:]}/{i['message_id']}\">{i['id']}</a>" for i in
                     messages])

                if update.effective_chat.type == "private":
                    await context.bot.sendMessage(chat_id=update.effective_chat.id, text="搜索结果:\n" + send_text, parse_mode="HTML")
                else:
                    await context.bot.sendMessage(chat_id=update.effective_chat.id, text="搜索结果:\n" + send_text, parse_mode="HTML"
                                                  , reply_to_message_id=update.effective_message.id)

            else:
                if update.effective_chat.type == "private":
                    await context.bot.sendMessage(chat_id=update.effective_chat.id, text="没有找到作品")
                else:
                    await context.bot.sendMessage(chat_id=update.effective_chat.id, text="没有找到作品"
                                                  , reply_to_message_id=update.effective_message.id)

    else:
        if update.effective_chat.type == "private":
            await context.bot.sendMessage(chat_id=update.effective_chat.id, text="需要输入想要搜索的内容")
        else:
            await context.bot.sendMessage(chat_id=update.effective_chat.id, text="需要输入想要搜索的内容"
                                          , reply_to_message_id=update.effective_message.id)


async def just_delete_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user.id == int(config.admin):
        await context.bot.sendMessage(reply_to_message_id=update.effective_message.message_id,
                                      chat_id=update.effective_chat.id, text="你不是bot管理员")
        logger.info(f"some one use admin command delete_backup: {update.effective_user.id}")
        return

    if context.args:
        await backup.just_delete_backup(context.args[0], context)

    else:
        await context.bot.sendMessage(chat_id=update.effective_chat.id, text="参数不足")
