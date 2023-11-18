import asyncio
# import contextvars
# import functools
import logging

import telegram

# import time
from . import config
from . import update_illust
from . import update_bookmarks_record
from . import bot_command


from telegram import __version__ as TG_VER

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )

from telegram import Update, InputMediaPhoto, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters


logger = logging.getLogger("bot")

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.INFO)
logging.getLogger("aiosqlite").setLevel(logging.WARNING)
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


do_stop_bot = False


async def stop_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("stop attempt")
    if not update.effective_user.id == int(config.admin):
        await context.bot.sendMessage(chat_id=update.effective_chat.id, text="你不是管理员")
        logger.info(f"some one use admin command stop_bot: {update.effective_user.id}")
        return
    else:
        logger.info("stop")
        await context.bot.sendMessage(chat_id=update.effective_chat.id, text="操作成功")
        global do_stop_bot
        do_stop_bot = True


# def block_thread():
#     while not do_stop_bot:
#         time.sleep(1)
#
#
# async def to_thread(func, /, *args, **kwargs):
#     loop = asyncio.get_running_loop()
#     ctx = contextvars.copy_context()
#     func_call = functools.partial(ctx.run, func, *args, **kwargs)
#     return await loop.run_in_executor(None, func_call)


async def block():
    while not do_stop_bot:
        await asyncio.sleep(1)


async def run_bot():
    application = Application.builder().token(config.api_key).build()

    application.add_handler(CommandHandler("stop_bot", stop_bot))
    application.add_handler(CommandHandler("rand", bot_command.rand))
    application.add_handler(CommandHandler("add_backup", bot_command.add_backup))
    application.add_handler(CommandHandler("sql", bot_command.sql))
    application.add_handler(CommandHandler("shell", bot_command.shell))
    application.add_handler(CommandHandler("reload_config", bot_command.reload_config))
    application.add_handler(CommandHandler("stop_update_task", bot_command.stop_update_task))
    application.add_handler(CommandHandler("stop_backup_task", bot_command.stop_backup_task))
    application.add_handler(CommandHandler("start_update_task", bot_command.start_update_task))
    application.add_handler(CommandHandler("start_async_update_task", bot_command.start_async_update_task))
    application.add_handler(CommandHandler("start_backup_task", bot_command.start_backup_task))
    application.add_handler(CommandHandler("force_update", bot_command.force_update))
    application.add_handler(CommandHandler("force_backup", bot_command.force_backup))
    application.add_handler(CommandHandler("start", bot_command.start))
    application.add_handler(CommandHandler("force_backup_one", bot_command.force_backup_one))
    application.add_handler(CommandHandler("update_status", bot_command.update_status))
    application.add_handler(CommandHandler("backup_status", bot_command.backup_status))
    application.add_handler(CommandHandler("plugin", bot_command.plugin_))
    application.add_handler(CommandHandler("admin_plugin", bot_command.admin_plugin))
    application.add_handler(CommandHandler("search", bot_command.search))


    # 开始运行bot
    await application.initialize()
    await application.start()
    await application.updater.start_polling(allowed_updates=Update.ALL_TYPES, read_timeout=600, write_timeout=600
                                            , pool_timeout=600, connect_timeout=600, timeout=600)

    # 两个后台任务
    # application.job_queue.run_repeating(update_bookmarks_record.update_task, interval=config.bookmarks_update_interval
    #                                     , name="bookmarks_task", first=config.bookmarks_update_interval)
    # application.job_queue.run_repeating(update_illust.update_backup, interval=config.backup_interval, name="backup_task"
    #                                     , first=config.backup_interval)
    logger.info("bot start")

    await application.bot.set_my_commands([
        BotCommand("start", "开始与帮助"),
        BotCommand("rand", "随机收藏涩图~,可选tag过滤:/rand tag tag..."),
        BotCommand("search", "搜索想要的作品,对于纯数字会搜索作品id或者作者id,目前最多提供10条记录"),
        BotCommand("plugin", "获取快捷rand search的pagermaid插件")
    ], scope=telegram.BotCommandScopeDefault())

    await application.bot.set_my_commands([
        BotCommand("start", "开始与帮助"),
        BotCommand("rand", "随机收藏涩图~,可选tag过滤:/rand tag tag..."),
        BotCommand("search", "搜索想要的作品,对于纯数字会搜索作品id或者作者id,目前最多提供10条记录"),
        BotCommand("plugin", "获取快捷rand search的pagermaid插件"),
        BotCommand("admin_plugin", "管理员专用的pagermaid插件"),
        BotCommand("add_backup", "管理员命令,手动补全已失效作品的备份(pbrm联动)"),     # pip install pbrm 本地备份工具
        BotCommand("sql", "管理员命令,执行sql语句"),
        BotCommand("shell", "管理员命令,执行shell命令"),
        BotCommand("update_status", "管理员命令,查询更新任务状态"),
        BotCommand("backup_status", "管理员命令,查询备份任务状态"),
        BotCommand("reload_config", "管理员命令,重新载入配置"),
        BotCommand("stop_update_task", "管理员命令,停止更新收藏列表后台任务"),
        BotCommand("stop_backup_task", "管理员命令,停止备份收藏后台任务"),
        BotCommand("start_update_task", "管理员命令,开始更新收藏列表后台任务"),
        BotCommand("start_async_update_task", "管理员命令,开始更新收藏列表后台任务,但并发程度更高(没有delay的话会被ban号)"),
        BotCommand("start_backup_task", "管理员命令,开始备份收藏后台任务"),
        BotCommand("force_update", "管理员命令,强制启动一次更新收藏列表操作"),
        BotCommand("force_backup", "管理员命令,强制启动一次备份操作"),
        BotCommand("force_backup_one", "管理员命令,强制更新指定作品"),
        BotCommand("stop_bot", "管理员命令,停止bot")
    ], scope=telegram.BotCommandScopeAllPrivateChats())

    await application.bot.set_my_description(description="一个pixiv账号收藏备份bot,也可以发送随机收藏涩图和查询收藏")

    # 阻塞
    # block = to_thread(block_thread)
    # await block

    await block()

    # 停止bot
    await application.updater.stop()
    await application.stop()
    await application.shutdown()

    logger.info("bot stop")


def run():

    asyncio.run(run_bot())
