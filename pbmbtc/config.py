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
delete_if_not_like = 0
db_backup_option = ""
db_backup_path = ""
db_backup_post_url = ""
db_backup_post_header = ""
db_backup_post_data = ""
db_backup_shell_command = ""
db_backup_interval = 0


def load_config():
    with db.start_session() as session:
        bot = session.query(db.Bot).first()

        global api_key, admin, cookie, gif_preview, tmp_path, bookmarks_update_interval, backup_interval
        global backup_number_ontime, delete_if_not_like, db_backup_option, db_backup_path, db_backup_post_url
        global db_backup_post_header, db_backup_post_data, db_backup_shell_command, db_backup_interval

        api_key = bot.key
        admin = bot.admin
        cookie = bot.cookie
        gif_preview = bot.gif_preview
        tmp_path = bot.tmp_path
        bookmarks_update_interval = bot.bookmarks_update_interval
        backup_interval = bot.backup_interval
        backup_number_ontime = bot.backup_number_ontime
        delete_if_not_like = bot.delete_if_not_like
        db_backup_option = bot.db_backup_option
        db_backup_path = bot.db_backup_path
        db_backup_post_url = bot.db_backup_post_url
        db_backup_post_header = bot.db_backup_post_header
        db_backup_post_data = bot.db_backup_post_data
        db_backup_shell_command = bot.db_backup_shell_command
        db_backup_interval = bot.db_backup_interval

    logger.debug(f"api_key: {api_key}, admin: {admin}")


def get_channel_id():
    with db.start_session() as session:
        channels = session.query(db.Channel).all()

        return [i.id for i in channels]
