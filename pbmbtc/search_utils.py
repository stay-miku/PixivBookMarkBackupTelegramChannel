from . import db
from typing import List
from sqlalchemy import not_, and_, or_
from sqlalchemy.future import select
from sqlalchemy import func
import random


# is_id作用为是否查询id user_id
async def random_saved_illsust(tags: List[str], black_list: List[str], limit=1, is_id=False) -> List[str]:
    async with db.start_async_session() as session:

        if is_id:

            conditions = [not_((db.Illust.title + " " + db.Illust.tags + " " + db.Illust.user_name
                                + " " + db.Illust.user_account).ilike(f"%{i}%")) for i in black_list]

            query = select(db.Illust).filter(or_(db.Illust.id == tags[0], db.Illust.user_id == tags[0])
                                             ).filter(and_(*conditions)).filter_by(saved=1).order_by(func.random()
                                                                                                     ).limit(limit)

        else:
            conditions = []

            for tag in tags:
                conditions.append((db.Illust.title + " " + db.Illust.tags + " " + db.Illust.user_name
                                   + " " + db.Illust.user_account).ilike(f"%{tag}%"))

            for black in black_list:
                conditions.append(not_((db.Illust.title + " " + db.Illust.tags + " " + db.Illust.user_name
                                        + " " + db.Illust.user_account).ilike(f"%{black}%")))

            conditions.append(db.Illust.saved == 1)

            query = select(db.Illust).filter(and_(*conditions)).order_by(func.random()).limit(limit)

        select_object = await session.execute(query)

        result = select_object.all()

        illusts_id = []

        for i in result:
            illusts_id.append(i[0].id)

        return illusts_id


# 这里的limit是倒数几个不要作为结果
async def random_preview(illust_id, limit: int):
    async with db.start_async_session() as session:

        query = select(db.PreviewBackup).filter_by(id=illust_id)

        result_object = await session.execute(query)

        result = result_object.all()

        if result:
            if len(result) <= limit:

                obj = result[0][0]

                return obj.channel, obj.message_id

            else:
                obj = random.choice(result[:-limit])[0]

                return obj.channel, obj.message_id

        else:
            return None, None


async def first_preview(illust_id):
    async with db.start_async_session() as session:
        query = select(db.PreviewBackup).filter_by(id=illust_id).limit(1)

        result_object = await session.execute(query)

        result = result_object.first()

        if result:
            return result[0].channel, result[0].message_id

        else:
            return None, None
