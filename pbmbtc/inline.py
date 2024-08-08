from uuid import uuid4
from telegram import InlineQueryResultPhoto, Update, InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from . import search_utils
import logging
import random


logger = logging.getLogger("inline")


domain = 'pixiv.mikudesu.best'
max_size = '3MB'


async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query

    logger.info(f"inline query: {query}, by {update.effective_user.id}")

    if not query:
        query = ""

    if query.startswith("http"):
        logger.info("url query, unsupported temporarily")
        await update.inline_query.answer([
            InlineQueryResultArticle(
                id=str(uuid4()),
                title="不支持的查询",
                input_message_content=InputTextMessageContent("暂不支持url查询")
            )
        ])
        return

    if query.isnumeric():
        tags = [query]
        black_tags = []
        is_id = True
    else:
        tags, black_tags = search_utils.extract_tags(query)
        is_id = False

    pid, page_counts = await search_utils.random_saved_illsust(tags, black_tags, limit=1, inline=True, is_id=is_id)
    if not pid:
        await update.inline_query.answer([
            InlineQueryResultArticle(
                id=str(uuid4()),
                title="没有找到符合条件的作品",
                input_message_content=InputTextMessageContent("没有找到符合条件的作品")
            )
        ])
        return

    pid = pid[0]
    page_counts = page_counts[0]

    page = random.randint(0, page_counts - 1)

    user_id, user_name, title, width, height = await search_utils.get_illust_info(pid, get_size=True)

    keyboards = [InlineKeyboardButton("source", url=f"https://www.pixiv.net/artworks/{pid}")]

    if not user_id:
        logger.warning("no illust info found")
        title = "unknown"
        user_name = "unknown"
    else:
        keyboards.append(InlineKeyboardButton("author", url=f"https://www.pixiv.net/users/{user_id}"))

    channel, message_id = await search_utils.random_preview(pid, 1, inline=page)

    if not channel:
        logger.warning("no preview found, maybe the illust is not backuped")
    else:
        keyboards.append(InlineKeyboardButton("channel", url=f"https://t.me/c/{channel[4:]}/{message_id}"))

    logger.debug(f"inline query: pid: {pid}, page: {page}, user_name: {user_name}, title: {title}")

    await update.inline_query.answer([
        InlineQueryResultPhoto(
            id=str(uuid4()),
            photo_url=f"https://{domain}/{pid}-{page}/{max_size}",
            thumbnail_url=f"https://{domain}/{pid}-{page}/{max_size}",
            title=title,
            caption=f"{user_name} - {title}",
            reply_markup=InlineKeyboardMarkup([keyboards]),
            photo_width=width,
            photo_height=height
        )
    ], is_personal=True, cache_time=0)



