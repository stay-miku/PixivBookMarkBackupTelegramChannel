import asyncio
import traceback

from . import pixiv
from .utils import retry, format_tags
from . import config
from . import db
import sqlalchemy.orm
import json
import time
import logging
from . import backup
from telegram.ext import ContextTypes

logger = logging.getLogger("update bookmarks record")


# 更新单个作品, illust为简略meta(bookmarks api传递的作品meta数据) update_meta为是否强制更新meta
async def update_single(illust, update_meta):
    illust_id = str(illust['id'])
    user_id = int(illust['userId'])

    with db.start_session() as session:
        exists = session.query(db.Illust).filter_by(id=illust_id).first()

        # 存在记录
        if exists:
            # 失效作品
            if user_id == 0:
                logger.debug(f"unavailable illust: {illust_id}")
                exists.unavailable = 1
                exists.queried = 1
                # session.commit()
            else:
                # 更新meta 或 作品从失效到有效(这种情况只有作者把私有设为公开才行了)
                if update_meta or exists.unavailable == 1:
                    logger.debug(f"update meta: {illust_id}")
                    meta = await retry(pixiv.get_illust_meta, 5, 0, pid=illust_id, cookie=config.cookie)
                    exists.title = meta['illustTitle']
                    exists.type = meta['illustType']
                    exists.comment = meta['illustComment']
                    exists.tags = format_tags(pixiv.get_tags(meta))
                    exists.upload_date = meta['uploadDate']
                    exists.user_id = meta['userId']
                    exists.user_name = meta['userName']
                    exists.user_account = meta['userAccount']
                    exists.page_count = meta['pageCount']
                    exists.ai = meta['aiType']
                    exists.detail = json.dumps(meta, ensure_ascii=False)
                    exists.unavailable = 0
                    exists.queried = 1
                    # session.commit()
                # 不更新meta
                else:
                    logger.debug(f"don't update: {illust_id}")
                    exists.queried = 1
                    # session.commit()

        # 记录不存在
        else:
            # 失效作品
            if user_id == 0:
                logger.debug(f"unavailable and not saved: {illust_id}")
                i = db.Illust()
                i.id = illust_id
                i.title = ""
                i.type = illust['illustType']
                i.comment = ""
                i.tags = ""
                i.upload_date = ""
                i.user_id = ""
                i.user_name = ""
                i.user_account = ""
                i.page_count = 0
                i.ai = 0
                i.detail = json.dumps(illust, ensure_ascii=False)
                i.backup = 0
                i.unavailable = 1
                i.saved = 0
                i.queried = 1
                session.add(i)
                # session.commit()
            else:
                logger.debug(f"need backup: {illust_id}")
                meta = await retry(pixiv.get_illust_meta, 5, 0, cookie=config.cookie, pid=illust_id)
                i = db.Illust()
                i.id = illust_id
                i.title = meta['illustTitle']
                i.type = meta['illustType']
                i.comment = meta['illustComment']
                i.tags = format_tags(pixiv.get_tags(meta))
                i.upload_date = meta['uploadDate']
                i.user_id = meta['userId']
                i.user_name = meta['userName']
                i.user_account = meta['userAccount']
                i.page_count = meta['pageCount']
                i.ai = meta['aiType']
                i.detail = json.dumps(meta, ensure_ascii=False)
                i.backup = 0
                i.unavailable = 0
                i.saved = 0
                i.queried = 1
                session.add(i)
                # session.commit()


# update_meta用于指定是否强制更新已有记录的meta(默认task是False,可以手动运行,会很慢)
async def update(update_meta: bool, delay: int, context: ContextTypes.DEFAULT_TYPE):
    start_time = time.time()
    logger.info(f"start update, update_meta: {update_meta}, delay: {delay}")
    user = await retry(pixiv.cookie_verify, 5, 0, cookie=config.cookie)

    bookmarks = await retry(pixiv.get_bookmarks, 5, 0, cookie=config.cookie, user=user["userId"])
    logger.info(f"update, total illusts: {bookmarks['total']}")

    total = bookmarks['total']
    i = 1
    for illust in bookmarks["illust"]:
        await update_single(illust, update_meta)
        i += 1
        logger.info(f"{i}/{total}, process: {i/total}")
        time.sleep(delay)

    with db.start_session() as session:
        # 删除所有未被更新的作品
        unlike = session.query(db.Illust).filter_by(queried=0).all()
        for un in unlike:
            await backup.delete_backup(un.id, session, context)
        # session.commit()  with内最好别手动commit

        session.query(db.Illust).update({"queried": 0})

    end_time = time.time()
    logger.info(f"completed update, exc time: {end_time - start_time} sec")


async def updateTask(context: ContextTypes.DEFAULT_TYPE):
    try:
        await update(False, 1, context)
    except Exception as e:
        traceback.print_exception(type(e), e, e.__traceback__)
        logger.error(f"Update error: {e}")
        await context.bot.sendMessage(chat_id=config.admin, text=f"更新收藏列表发送错误: {e}, 详情查看后台日志")

    logger.info("update task completed")


async def update_task(context: ContextTypes.DEFAULT_TYPE):

    logger.info("start update record")
    asyncio.create_task(updateTask(context))

