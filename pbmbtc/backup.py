import json
import logging
import sqlalchemy.orm
from . import db
from . import config
from telegram.ext import ContextTypes
from telegram import InputMediaPhoto, InputMediaDocument, Message
from .utils import retry, compress_image_if_needed
from . import pixiv
from typing import Dict, List, Union
import traceback

logger = logging.getLogger("backup")


# 单个作品的备份与删除操作


def get_introduce(illust: db.Illust):
    tags = ' '.join([i.rsplit('=>', 1)[1] for i in illust.tags.split('\n')])
    ugoira_tip = "\n<i>此作品为动图</i>" if config.gif_preview and illust.type == 2 else ""
    introduce = f"""Tags: {tags}
作者: <a href=\"https://www.pixiv.net/users/{illust.user_id}\">{illust.user_name}</a>
原链接: <a href=\"https://www.pixiv.net/artworks/{illust.id}\">{illust.title}</a>{ugoira_tip}"""

    return introduce


async def send_medias(illust: str, page, session: sqlalchemy.orm.Session, context: ContextTypes.DEFAULT_TYPE,
                      send_preview: Union[List, bytes], send_file: List, introduce, is_ugoira, have_sent: List,
                      spoiler=False):
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
                                          parse_mode='HTML'
                                          , caption=introduce, has_spoiler=spoiler
                                          , pool_timeout=600, read_timeout=600, write_timeout=600
                                          , connect_timeout=600)
            have_sent.append({"message_id": preview_message.message_id, "channel": channel})

        file_message = await retry(context.bot.sendMediaGroup, 5, 0, chat_id=channel, media=send_file,
                                   reply_to_message_id=preview_message[0].message_id
                                   , pool_timeout=600, read_timeout=600, write_timeout=600
                                   , connect_timeout=600)
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
            m = file_message[i]
            record = db.Backup()
            record.id = illust
            record.message_id = m.message_id
            record.page = page
            record.index = i
            record.channel = channel
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
                      have_sent: List):
    illusts = await retry(pixiv.get_illust, 5, 0, pid=illust.id, u_cookie=config.cookie)

    # 按张排序(虽然应该是已经排序好了的)
    illusts = sorted(illusts, key=lambda x: int(x['file_name'].split('.', 1)[0].split('_p')[1]))

    page = 0
    while page * 10 < len(illusts):
        await send_one_page(illust, session, context, illusts[page * 10:page * 10 + 10], page, have_sent)

        page += 1

    illust.backup = 1
    illust.saved = 1


async def send_manga(illust: db.Illust, session: sqlalchemy.orm.Session, context: ContextTypes.DEFAULT_TYPE,
                     have_sent: List):
    await send_illust(illust, session, context, have_sent)


async def send_ugoira(illust: db.Illust, session: sqlalchemy.orm.Session, context: ContextTypes.DEFAULT_TYPE,
                      have_sent: List):
    ugoira = await retry(pixiv.get_ugoira, 5, 0, pid=illust.id, u_cookie=config.cookie)

    ugoira_meta = ugoira['meta']
    ugoira_src = ugoira['file']
    ugoira_file_name = ugoira['file_name']

    spoiler = 'R-18' in illust.tags

    introduce = get_introduce(illust)
    send_file = [InputMediaDocument(ugoira_src, filename=ugoira_file_name),
                 InputMediaDocument(json.dumps(ugoira_meta, ensure_ascii=False).encode('utf-8'),
                                    filename=f"{ugoira_file_name.split('.', 1)[0]}_meta.txt")]
    if config.gif_preview:
        gif = await pixiv.get_ugoira_gif(ugoira_src, ugoira_meta, config.tmp_path)
        await send_medias(illust.id, 0, session, context, gif, send_file, introduce, True, have_sent, spoiler)
    else:
        preview_image = await retry(pixiv.get_illust, 5, 0, u_cookie=config.cookie, pid=illust.id)
        send_preview = [InputMediaPhoto(preview_image[0]['file'], has_spoiler=spoiler)]
        await send_medias(illust.id, 0, session, context, send_preview, send_file, introduce, False, have_sent)

    illust.backup = 1
    illust.saved = 1


async def send_unavailable(illust: db.Illust, context: ContextTypes.DEFAULT_TYPE, session: sqlalchemy.orm.Session,
                           have_sent: List):
    for channel in config.get_channel_id():
        sent_message = await retry(context.bot.sendMessage, 5, 0, chat_id=channel, text=f"已失效作品: {illust.id}")

        have_sent.append(sent_message)

        record = db.PreviewBackup()
        record.id = illust.id
        record.page = 1
        record.channel = channel
        record.message_id = sent_message.message_id
        record.index = 1
        session.add(record)

        illust.backup = 1


async def send_backup(illust_id: str, context: ContextTypes.DEFAULT_TYPE):
    have_sent: List[Message] = []
    error_illust_id = "0"
    try:
        with db.start_session() as session:
            illust = session.query(db.Illust).filter_by(id=illust_id).first()
            error_illust_id = illust.id

            if illust.unavailable == 1:
                await send_unavailable(illust, context, session, have_sent)

            elif illust.type == 0:
                await send_illust(illust, session, context, have_sent)

            elif illust.type == 1:
                await send_manga(illust, session, context, have_sent)

            elif illust.type == 2:
                await send_ugoira(illust, session, context, have_sent)

            else:
                raise Exception(f"Unknown illust type: {illust.type}, id: {error_illust_id}")

            raise Exception("test")

    except Exception as e:
        for m in have_sent:
            await retry(context.bot.deleteMessage, 5, 0, chat_id=m['channel'], message_id=m['message_id'])
            logger.debug(f"delete message: {m}")
        logger.error(f"error: {e}")
        traceback.print_exception(type(e), e, e.__traceback__)
        await retry(context.bot.sendMessage, 5, 0, chat_id=config.admin, text=f"发生错误: {e}, illust: {error_illust_id}")


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
