from . import db
import logging

logger = logging.getLogger("config")


api_key = ""
admin = ""
cookie = ""
gif_preview = False
tmp_path = ""
bookmarks_update_interval = 0
backup_interval = 0
backup_number_ontime = 0


def load_config():
    with db.start_session() as session:
        bot = session.query(db.Bot).first()

        global api_key, admin, cookie, gif_preview, tmp_path, bookmarks_update_interval, backup_interval, backup_number_ontime

        api_key = bot.key
        admin = bot.admin
        cookie = bot.cookie
        gif_preview = bot.gif_preview
        tmp_path = bot.tmp_path
        bookmarks_update_interval = bot.bookmarks_update_interval
        backup_interval = bot.backup_interval
        backup_number_ontime = bot.backup_number_ontime

    logger.debug(f"api_key: {api_key}, admin: {admin}")
