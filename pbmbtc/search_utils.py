import json
import re

from . import db
from typing import List, Union, Tuple
from sqlalchemy import not_, and_, or_
from sqlalchemy.future import select
from sqlalchemy import func
import random


# is_id作用为是否查询id user_id
# inline作用为inline模式的查询
async def random_saved_illsust(tags: List[str], black_list: List[str], limit=1, is_id=False, inline=False) -> Union[List[str], Tuple[List[str], List[int]]]:
    # 因为split原因,将['']的tags修正为[]
    if len(tags) == 1 and tags[0] == "":
        tags = []

    async with db.start_async_session() as session:

        if is_id:

            conditions = [not_((db.Illust.title + " " + db.Illust.tags + " " + db.Illust.user_name
                                + " " + db.Illust.user_account).ilike(f"%{i}%")) for i in black_list]

            [conditions.append((db.Illust.title + " " + db.Illust.tags + " " + db.Illust.user_name
                                + " " + db.Illust.user_account).ilike(f"%{i}%")) for i in tags[1:]]

            query = select(db.Illust).filter(or_(db.Illust.id == tags[0], db.Illust.user_id == tags[0])
                                             ).filter(and_(*conditions)).filter_by(saved=1).order_by(func.random()
                                                                                                     ).limit(limit)

        else:
            # r-18g tag需要显式提供,否则默认不包含,id查询模式不做此限制
            if 'r-18g' not in [i.lower() for i in tags]:
                black_list.append("r-18g")

            conditions = []

            for tag in tags:
                conditions.append((db.Illust.title + " " + db.Illust.tags + " " + db.Illust.user_name
                                   + " " + db.Illust.user_account).ilike(f"%{tag}%"))

            for black in black_list:
                conditions.append(not_((db.Illust.title + " " + db.Illust.tags + " " + db.Illust.user_name
                                        + " " + db.Illust.user_account).ilike(f"%{black}%")))

            if not inline:
                conditions.append(db.Illust.saved == 1)
            else:
                conditions.append(db.Illust.unavailable == 0)
                conditions.append(db.Illust.type != 2)          # 排除动图

            query = select(db.Illust).filter(and_(*conditions)).order_by(func.random()).limit(limit)

        select_object = await session.execute(query)

        result = select_object.all()

        illusts_id = []
        illusts_pages = []

        for i in result:
            illusts_id.append(i[0].id)
            illusts_pages.append(i[0].page_count)
        if not inline:
            return illusts_id
        else:
            return illusts_id, illusts_pages


# 这里的limit是倒数几个不要作为结果
# inline: inline模式使用,用于标记多图片作品的索引
async def random_preview(illust_id, limit: int, inline=-1):
    async with db.start_async_session() as session:

        query = select(db.PreviewBackup).filter_by(id=illust_id)

        result_object = await session.execute(query)

        result = result_object.all()

        if result:
            if inline != -1:
                if inline >= len(result):
                    return None, None
                obj = result[inline][0]
                return obj.channel, obj.message_id
            if len(result) <= limit:

                obj = result[0][0]

                return obj.channel, obj.message_id

            else:
                obj = random.choice(result[:-limit])[0]

                return obj.channel, obj.message_id

        else:
            return None, None


async def get_illust_info(illust_id, get_size=False):
    async with db.start_async_session() as session:
        query = select(db.Illust).filter_by(id=illust_id)

        result_object = await session.execute(query)

        result = result_object.scalar()

        if get_size:
            detail = json.loads(result.detail)
            width = detail["width"]
            height = detail["height"]
            if not isinstance(width, int) or not isinstance(height, int):
                width, height = 100, 100

        if result:
            if get_size:
                return result.user_id, result.user_name, result.title, width, height
            return result.user_id, result.user_name, result.title

        else:
            if get_size:
                return None, None, None, None, None
            return None, None, None


async def first_preview(illust_id):
    async with db.start_async_session() as session:
        query = select(db.PreviewBackup).filter_by(id=illust_id).limit(1)

        result_object = await session.execute(query)

        result = result_object.first()

        if result:
            return result[0].channel, result[0].message_id

        else:
            return None, None


def extract_tags(tag_str: str):
    if tag_str:
        a = tag_str.split("|")
        if len(a) <= 1:
            tags = re.split(r"[,，]", a[0])
            black_list = []

        else:
            tags = re.split(r"[,，]", a[0])
            black_list = re.split(r"[,，]", a[1])

    else:
        tags = []
        black_list = []

    return tags, black_list
