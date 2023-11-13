from telegram.ext import ContextTypes
from . import db
from . import config
from . import backup


async def update_backup(context: ContextTypes.DEFAULT_TYPE):

    with db.start_session() as session:
        not_backup = session.query(db.Illust).filter_by(backup=0).all()[0:config.backup_number_ontime]
        not_backup_id = [i.id for i in not_backup]

    for i in not_backup_id:
        await backup.send_backup(i, context)

