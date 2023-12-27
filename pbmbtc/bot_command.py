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
from . import search_utils
from . import database_backup

logger = logging.getLogger("bot_command")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.sendMessage(chat_id=update.effective_chat.id, parse_mode='MarkdownV2',
                                  text="""pixiv收藏管理bot
命令指南:
/rand
随机涩图,范围仅为频道内的内容,支持目标tag过滤和黑名单tag过滤,检索关键字为作品标题、作者名、作者用户名、作品tag,多关键字使用逗号隔开,全角半角逗号均可,用法示例:
`/rand` 无任何限制随机作品
`/rand 萝莉` 随机包含'萝莉'关键字的作品
`/rand 萝莉，双马尾，兽耳` 随机包含'萝莉''双马尾''兽耳'的作品
`/rand 萝莉|R\-18` 随机包含'萝莉'且不包含'R\-18'关键字的作品\(注:关键字大小写不敏感\)
`/rand |R\-18` 随机不包含'R\-18'的作品
/search
搜索涩图,范围仅为频道内的内容,也支持tag和黑名单tag过滤,用法与/rand类似,区别在于返回的是消息链接,且最多包含10条,也是随机,与/rand不同的是可以按作品id或作者id搜索,用法:
`/search 111111|R\-18` 搜索作品id或作者id为111111且不包含'R\-18'关键字的作品
`/search 111111，兽耳|R\-18` 搜索作品id或者作者id为111111且包含'兽耳'不包含'R\-18'标签的作品
如果想要按id搜索,则id必须是tag的第一个,如`/search 兽耳，111111`不会搜索id为111111的作品""")
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
    logger.info(
        f"search: user: {update.effective_user.id}, name: {update.effective_user.username}, args: {context.args}")
    try:
        if context.args:
            a = (" ".join(context.args)).split("|")
            if len(a) <= 1:
                tags = re.split(r"[,，]", a[0])
                black_list = []

            else:
                tags = re.split(r"[,，]", a[0])
                black_list = re.split(r"[,，]", a[1])

        else:
            tags = []
            black_list = []

        random_illust = await search_utils.random_saved_illsust(tags, black_list)

        if random_illust:

            channel, message_id = await search_utils.random_preview(random_illust[0], 1)

            if channel:
                await context.bot.forwardMessage(chat_id=update.effective_chat.id, from_chat_id=channel
                                                 , message_id=message_id)
                return

        if update.effective_chat.type == "private":
            await context.bot.sendMessage(chat_id=update.effective_chat.id, text="没有找到对应的作品~")
        else:
            await context.bot.sendMessage(chat_id=update.effective_chat.id, text="没有找到对应的作品~"
                                          , reply_to_message_id=update.effective_message.id)

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
    logger.info(
        f"search: user: {update.effective_user.id}, name: {update.effective_user.username}, args: {context.args}")
    if context.args:
        a = (" ".join(context.args)).split("|")
        if len(a) <= 1:
            tags = re.split(r"[,，]", a[0])
            black_list = []

        else:
            tags = re.split(r"[,，]", a[0])
            black_list = re.split(r"[,，]", a[1])

        if len(tags) >= 1 and tags[0].isdigit():
            illusts_list = await search_utils.random_saved_illsust(tags, black_list, 10, True)
        else:
            illusts_list = await search_utils.random_saved_illsust(tags, black_list, 10)

        if illusts_list:
            result = ""
            for i in illusts_list:
                channel, message_id = await search_utils.first_preview(i)
                result += f"<a href=\"https://t.me/c/{channel[4:]}/{message_id}\">{i}</a>\n"

            if update.effective_chat.type == "private":
                await context.bot.sendMessage(chat_id=update.effective_chat.id, text="搜索结果:\n" + result, parse_mode="HTML")
            else:
                await context.bot.sendMessage(chat_id=update.effective_chat.id, text="搜索结果:\n" + result, parse_mode="HTML"
                                              , reply_to_message_id=update.effective_message.id)

        else:
            if update.effective_chat.type == "private":
                await context.bot.sendMessage(chat_id=update.effective_chat.id, text="没有找到想要的内容")
            else:
                await context.bot.sendMessage(chat_id=update.effective_chat.id, text="没有找到想要的内容"
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
        result = await backup.just_delete_backup(context.args[0], context)
        if result:
            await context.bot.sendMessage(chat_id=update.effective_chat.id, text="删除成功")
    else:
        await context.bot.sendMessage(chat_id=update.effective_chat.id, text="参数不足")


async def backup_database(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user.id == int(config.admin):
        await context.bot.sendMessage(reply_to_message_id=update.effective_message.message_id,
                                      chat_id=update.effective_chat.id, text="你不是bot管理员")
        logger.info(f"some one use admin command start_database_backup: {update.effective_user.id}")
        return

    try:
        await database_backup.start_backup(context)
        logger.info("force db backup completed")
    except Exception as e:
        await context.bot.sendMessage(chat_id=update.effective_chat.id, text=f"备份发生错误: {e}")
        traceback.print_exception(type(e), e, e.__traceback__)
        return


async def start_db_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user.id == int(config.admin):
        await context.bot.sendMessage(reply_to_message_id=update.effective_message.message_id,
                                      chat_id=update.effective_chat.id, text="你不是bot管理员")
        logger.info(f"some one use admin command start_database_backup_task: {update.effective_user.id}")
        return

    context.job_queue.run_repeating(database_backup.start_backup, interval=config.db_backup_interval, name="db_backup_task"
                                    , first=config.backup_interval)
    logger.info("start db backup task")

    await context.bot.sendMessage(chat_id=update.effective_chat.id, text="操作成功")


async def stop_db_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user.id == int(config.admin):
        await context.bot.sendMessage(reply_to_message_id=update.effective_message.message_id,
                                      chat_id=update.effective_chat.id, text="你不是bot管理员")
        logger.info(f"some one use admin command stop_database_backup_task: {update.effective_user.id}")
        return

    task = context.job_queue.get_jobs_by_name("db_backup_task")
    for job in task:
        job.schedule_removal()
    logger.info("delete task")
    await context.bot.sendMessage(chat_id=update.effective_chat.id, text="操作成功")
