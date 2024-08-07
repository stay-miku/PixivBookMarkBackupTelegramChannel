import json
import logging
import os

import aiofiles
import sqlalchemy.orm
from . import db
from . import config
from telegram.ext import ContextTypes
from telegram import InputMediaPhoto, InputMediaDocument, Message
from .utils import retry, compress_image_if_needed, format_tags, get_illust_from_file, get_ugoira_from_file, \
    divide_pages, zip_divide_file
from . import pixiv
from typing import Dict, List, Union, Tuple
import traceback
from sqlalchemy.future import select
import html

logger = logging.getLogger("backup")


# 单个作品的备份与删除操作


def get_introduce(illust: db.Illust):
    tags = ' '.join([i.rsplit('=>', 1)[-1] for i in illust.tags.split('\n')])
    ugoira_tip = "\n<i>此作品为动图</i>" if config.gif_preview and illust.type == 2 else ""
    r18g_tip = "\n<b>R-18G警告</b>" if 'R-18G' in illust.tags else ""
    introduce = f"""Tags: {html.escape(tags)}
作者: <a href=\"https://www.pixiv.net/users/{illust.user_id}\">{html.escape(illust.user_name)}</a>
原链接: <a href=\"https://www.pixiv.net/artworks/{illust.id}\">{html.escape(illust.title)}</a>{ugoira_tip}{r18g_tip}"""

    return introduce


# multi_send_file 为多个文件的情况, send_file为None, 为动图
async def send_medias(illust: str, page, session: sqlalchemy.orm.Session, context: ContextTypes.DEFAULT_TYPE,
                      send_preview: Union[List, bytes], send_file: Union[List, None], introduce, is_ugoira, have_sent: List,
                      spoiler=False, thumbnail=None, multi_send_file=None):
    channels = config.get_channel_id()

    for channel in channels:
        if not is_ugoira:
            preview_message = await retry(context.bot.sendMediaGroup, 5, 0, chat_id=channel, media=send_preview,
                                          parse_mode='HTML'
                                          , caption=introduce
                                          , pool_timeout=600, read_timeout=600, write_timeout=600
                                          , connect_timeout=600)
            have_sent += [{"message_id": i.message_id, "channel": channel} for i in preview_message]

        else:
            preview_message = await retry(context.bot.sendAnimation, 5, 0, chat_id=channel, animation=send_preview,
                                          parse_mode='HTML', filename=f"{illust}.gif"
                                          , caption=introduce, has_spoiler=spoiler, thumbnail=thumbnail
                                          , pool_timeout=600, read_timeout=600, write_timeout=600
                                          , connect_timeout=600)
            have_sent.append({"message_id": preview_message.message_id, "channel": channel})
            preview_message = [preview_message]  # 对下面reply_to_message_id=preview_message[0]的兼容

        if send_file:
            file_message = await retry(context.bot.sendMediaGroup, 5, 0, chat_id=channel, media=send_file,
                                       reply_to_message_id=preview_message[0].message_id
                                       , pool_timeout=600, read_timeout=600, write_timeout=600
                                       , connect_timeout=600)
        elif multi_send_file:
            file_message = []
            for i in multi_send_file:
                file_message += await retry(context.bot.sendMediaGroup, 5, 0, chat_id=channel, media=i,
                                            reply_to_message_id=preview_message[0].message_id
                                            , pool_timeout=600, read_timeout=600, write_timeout=600
                                            , connect_timeout=600)
        else:
            raise ValueError("no file to send")
        have_sent += [{"message_id": i.message_id, "channel": channel} for i in file_message]

        for i in range(len(preview_message)):
            m = preview_message[i]
            record = db.PreviewBackup()
            record.id = illust
            record.message_id = m.message_id
            record.page = page
            record.index = i
            record.channel = channel
            session.add(record)

        for i in range(len(file_message)):
            m: Message = file_message[i]
            record = db.Backup()
            record.id = illust
            record.message_id = m.message_id
            record.page = page
            record.index = i
            record.channel = channel
            record.size = m.document.file_size
            session.add(record)


async def send_one_page(illust: db.Illust, session: sqlalchemy.orm.Session, context: ContextTypes.DEFAULT_TYPE,
                        files: List[Dict], page, have_sent: List):
    introduce = get_introduce(illust)
    need_spoiler = 'R-18' in illust.tags
    preview_images = [compress_image_if_needed(i['file']) for i in files]
    send_preview = [InputMediaPhoto(i, has_spoiler=need_spoiler) for i in preview_images]
    send_file = [InputMediaDocument(i['file'], filename=i['file_name']) for i in files]

    await send_medias(illust.id, page, session, context, send_preview, send_file, introduce, False, have_sent)


async def send_illust(illust: db.Illust, session: sqlalchemy.orm.Session, context: ContextTypes.DEFAULT_TYPE,
                      have_sent: List, file_path=""):
    if file_path:
        illusts = await get_illust_from_file(file_path)
    else:
        illusts = await retry(pixiv.get_illust, 5, 0, pid=illust.id, u_cookie=config.cookie)

    # 按张排序(虽然应该是已经排序好了的)(从文件读应该就不会排序好了)
    illusts = sorted(illusts, key=lambda x: int(x['file_name'].split('.', 1)[0].split('_p')[1]))

    pages = divide_pages(illusts)

    for page in pages:
        logger.debug(f"send page: size: {page['size']}, page: {page['page']}, page_count: {len(page['illusts'])}")
        if page["size"] >= 1024 * 1024 * 50:
            raise Exception("page size > 50MB")
        await send_one_page(illust, session, context, page["illusts"], page["page"], have_sent)

    # page = 0
    # while page * 10 < len(illusts):
    #     await send_one_page(illust, session, context, illusts[page * 10:page * 10 + 10], page, have_sent)
    #
    #     page += 1

    illust.backup = 1
    illust.saved = 1


async def send_manga(illust: db.Illust, session: sqlalchemy.orm.Session, context: ContextTypes.DEFAULT_TYPE,
                     have_sent: List, file_path=""):
    await send_illust(illust, session, context, have_sent, file_path)


async def send_ugoira(illust: db.Illust, session: sqlalchemy.orm.Session, context: ContextTypes.DEFAULT_TYPE,
                      have_sent: List, file_path="", max_size=1024 * 1024 * 50):
    if file_path:
        ugoira = await get_ugoira_from_file(file_path)
    else:
        ugoira = await retry(pixiv.get_ugoira, 5, 0, pid=illust.id, u_cookie=config.cookie)

    ugoira_meta = ugoira['meta']
    ugoira_src = ugoira['file']
    ugoira_file_name = ugoira['file_name']

    segments, segments_name = zip_divide_file(ugoira_src, ugoira_file_name, max_size)

    spoiler = 'R-18' in illust.tags

    introduce = get_introduce(illust)
    # send_file = [InputMediaDocument(i, filename=j) for i, j in zip(segments, segments_name)]
    # send_file.append(InputMediaDocument(json.dumps(ugoira_meta, ensure_ascii=False).encode('utf-8'),
    #                                     filename=f"{ugoira_file_name.split('.', 1)[0]}_meta.txt"))

    multi_send_file = [[InputMediaDocument(i, filename=j)] for i, j in zip(segments, segments_name)]
    if len(segments[-1]) + len(json.dumps(ugoira_meta, ensure_ascii=False).encode('utf-8')) < max_size:
        multi_send_file[-1].append(InputMediaDocument(json.dumps(ugoira_meta, ensure_ascii=False).encode('utf-8'),
                                                      filename=f"{ugoira_file_name.split('.', 1)[0]}_meta.txt"))
    else:
        multi_send_file.append([InputMediaDocument(json.dumps(ugoira_meta, ensure_ascii=False).encode('utf-8'),
                                                   filename=f"{ugoira_file_name.split('.', 1)[0]}_meta.txt")])

    if config.gif_preview:
        if file_path:
            async with aiofiles.open(
                    os.path.join(file_path, "images", os.listdir(os.path.join(file_path, "images"))[0]), "rb") as f:
                preview_image = await f.read()
            thumbnail = preview_image
        else:
            preview_image = await retry(pixiv.get_illust, 5, 0, u_cookie=config.cookie, pid=illust.id)
            thumbnail = preview_image[0]['file']
        gif = await pixiv.get_ugoira_gif(ugoira_src, ugoira_meta, config.tmp_path)
        await send_medias(illust.id, 0, session, context, gif, None, introduce, True, have_sent, spoiler,
                          thumbnail=thumbnail, multi_send_file=multi_send_file)
    else:
        if file_path:
            async with aiofiles.open(
                    os.path.join(file_path, "images", os.listdir(os.path.join(file_path, "images"))[0]), "rb") as f:
                preview_image = await f.read()
            send_preview = [InputMediaPhoto(preview_image, has_spoiler=spoiler)]
        else:
            preview_image = await retry(pixiv.get_illust, 5, 0, u_cookie=config.cookie, pid=illust.id)
            send_preview = [InputMediaPhoto(preview_image[0]['file'], has_spoiler=spoiler)]
        await send_medias(illust.id, 0, session, context, send_preview, None, introduce, False, have_sent, spoiler, multi_send_file=multi_send_file)

    illust.backup = 1
    illust.saved = 1


async def send_unavailable(illust: db.Illust, context: ContextTypes.DEFAULT_TYPE, session: sqlalchemy.orm.Session,
                           have_sent: List):
    for channel in config.get_channel_id():
        sent_message = await retry(context.bot.sendMessage, 5, 0, chat_id=channel, text=f"已失效作品: {illust.id}")

        have_sent.append({"message": sent_message.message_id, "channel": channel})

        record = db.PreviewBackup()
        record.id = illust.id
        record.page = 0
        record.channel = channel
        record.message_id = sent_message.message_id
        record.index = 0
        session.add(record)

        illust.backup = 1
        session.flush()


# None为不指定id
async def send_backup(illust_id: Union[str, None], context: ContextTypes.DEFAULT_TYPE):
    if not await db.verify():
        logger.warning("last task is running, skip")
        await retry(context.bot.sendMessage, 5, 0, chat_id=config.admin, text="数据库被锁定,更新备份跳过")
        return
    have_sent: List[Message] = []
    error_illust_id = "0"
    try:
        with db.start_session() as session:
            if illust_id:
                illust = session.query(db.Illust).filter_by(id=illust_id, backup=0).first()
            else:
                illust = session.query(db.Illust).filter_by(backup=0).first()

            if illust is None:
                # await context.bot.sendMessage(chat_id=config.admin, text="所有收藏均已备份,或者可以强制更新一次收藏列表")
                return
            error_illust_id = illust.id
            illust.backup = 1  # 防止多个任务重复出现操作同一备份对象
            session.flush()  # 其实这个没这个作用,防止同时操作由判断数据库是否被锁来处理了

            if illust.unavailable == 1:
                await send_unavailable(illust, context, session, have_sent)

            elif illust.type == 0:
                await send_illust(illust, session, context, have_sent)

            elif illust.type == 1:
                await send_manga(illust, session, context, have_sent)

            elif illust.type == 2:
                await send_ugoira(illust, session, context, have_sent)

            else:
                raise Exception(f"Unknown illust type: {illust.type}, id: {illust.id}")

            logger.info(f"backup completed, illust: {illust.id}")

    except Exception as e:

        task = context.job_queue.get_jobs_by_name("backup_task")
        for job in task:
            job.schedule_removal()
        logger.info("delete task because of task error")

        for m in have_sent:
            await retry(context.bot.deleteMessage, 5, 0, chat_id=m['channel'], message_id=m['message_id'])
            logger.debug(f"delete message: {m}")
        logger.error(f"error: {e}")
        traceback.print_exception(type(e), e, e.__traceback__)
        await retry(context.bot.sendMessage, 5, 0, chat_id=config.admin,
                    text=f"发生错误: {e}, illust: {error_illust_id}")


async def send_backup_from_file(illust_id: str, file_path: str, context: ContextTypes.DEFAULT_TYPE):
    have_sent: List[Message] = []
    error_illust_id = "0"
    if not os.path.exists(os.path.join(file_path, "meta.json")):
        await context.bot.sendMessage(chat_id=config.admin, text="错误的路径")
        return
    try:
        with db.start_session() as session:
            illust = session.query(db.Illust).filter_by(id=illust_id).first()

            if illust is None:
                await context.bot.sendMessage(chat_id=config.admin,
                                              text="不存在的收藏")
                return
            elif illust.saved == 1:
                await context.bot.sendMessage(chat_id=config.admin, text="作品已备份,无需再次备份")
                return

            async with aiofiles.open(os.path.join(file_path, "meta.json"), "r") as f:
                meta = json.loads(await f.read())

            illust.id = illust_id
            illust.title = meta['illustTitle']
            illust.type = meta['illustType']
            illust.comment = meta['illustComment']
            illust.tags = format_tags(pixiv.get_tags(meta))
            illust.upload_date = meta['uploadDate']
            illust.user_id = meta['userId']
            illust.user_name = meta['userName']
            illust.user_account = meta['userAccount']
            illust.page_count = meta['pageCount']
            illust.ai = meta['aiType']
            illust.detail = json.dumps(meta, ensure_ascii=False)
            illust.backup = 0
            illust.unavailable = 1
            illust.saved = 0
            session.flush()

            error_illust_id = illust.id

            backup_messages = session.query(db.Backup).filter_by(id=illust.id).all()
            preview_message = session.query(db.PreviewBackup).filter_by(id=illust.id).all()

            for i in backup_messages:
                await retry(context.bot.deleteMessage, 5, 0, chat_id=i.channel, message_id=i.message_id)

            for i in preview_message:
                await retry(context.bot.deleteMessage, 5, 0, chat_id=i.channel, message_id=i.message_id)

            session.query(db.Backup).filter_by(id=illust.id).delete()
            session.query(db.PreviewBackup).filter_by(id=illust.id).delete()

            if illust.type == 0:
                await send_illust(illust, session, context, have_sent, file_path)

            elif illust.type == 1:
                await send_manga(illust, session, context, have_sent, file_path)

            elif illust.type == 2:
                await send_ugoira(illust, session, context, have_sent, file_path)

            else:
                raise Exception(f"Unknown illust type: {illust.type}, id: {illust.id}")

            logger.info(f"backup completed, illust: {illust.id}")

    except Exception as e:

        for m in have_sent:
            await retry(context.bot.deleteMessage, 5, 0, chat_id=m['channel'], message_id=m['message_id'])
            logger.debug(f"delete message: {m}")
        logger.error(f"error: {e}")
        traceback.print_exception(type(e), e, e.__traceback__)
        await retry(context.bot.sendMessage, 5, 0, chat_id=config.admin,
                    text=f"发生错误: {e}, illust: {error_illust_id}")


async def delete_backup(illust: Union[str, db.Illust], session: sqlalchemy.orm.Session,
                        context: ContextTypes.DEFAULT_TYPE):
    if isinstance(illust, str):
        illust = session.query(db.Illust).filter_by(id=illust).one()

    backup_messages = session.query(db.Backup).filter_by(id=illust.id).all()
    preview_message = session.query(db.PreviewBackup).filter_by(id=illust.id).all()

    for i in backup_messages:
        await retry(context.bot.deleteMessage, 5, 0, chat_id=i.channel, message_id=i.message_id)

    for i in preview_message:
        await retry(context.bot.deleteMessage, 5, 0, chat_id=i.channel, message_id=i.message_id)

    session.query(db.Backup).filter_by(id=illust.id).delete()
    session.query(db.PreviewBackup).filter_by(id=illust.id).delete()
    session.query(db.Illust).filter_by(id=illust.id).delete()


async def just_delete_backup(illust_id: str, context: ContextTypes.DEFAULT_TYPE):
    try:

        messages = []
        async with db.start_async_session() as session:
            query = select(db.Illust).filter_by(id=illust_id)
            result = await session.execute(query)

            illust = result.first()

            if illust:
                illust = illust[0]

                if illust.saved == 0:
                    await context.bot.sendMessage(chat_id=config.admin, text="作品未备份")
                    return

                else:
                    illust.saved = 0
                    illust.backup = 0

                    backup_message = (await session.execute(select(db.Backup).filter_by(id=illust_id))).all()
                    for message in backup_message:
                        messages.append({"channel": message[0].channel, "message_id": message[0].message_id})
                        await session.delete(message[0])
                    preview_message = (await session.execute(select(db.PreviewBackup).filter_by(id=illust_id))).all()
                    for message in preview_message:
                        messages.append({"channel": message[0].channel, "message_id": message[0].message_id})
                        await session.delete(message[0])

            else:
                await context.bot.sendMessage(chat_id=config.admin, text="不存在的作品id")
                return

        for message in messages:
            await retry(context.bot.deleteMessage, 5, 0, chat_id=message["channel"], message_id=message["message_id"])

        return True

    except Exception as e:
        await context.bot.sendMessage(chat_id=config.admin, text=f"发生错误: {e}")
        traceback.print_exception(type(e), e, e.__traceback__)
        return False
