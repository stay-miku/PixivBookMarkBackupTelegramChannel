from . import db


def init():
    with db.start_session() as session:
        if session.query(db.Bot).first() or session.query(db.Backup).first():
            print("There is already content in the database. Do you want to continue?(y/N):", end="")
            if not input().lower() == 'y':
                print("exit.")
                return

        api_key = input("Bot api key:")
        admin = input("The telegram id of the bot administrator:")
        cookie = input("The pixiv account cookie:")
        gif_preview = 0 if input("Use gif as ugoira type preview(Y/n):").lower() == "n" else 1
        tmp_path = input("Cache directory path, don't end with '/' (default:'./tmp'):")
        if tmp_path == "":
            tmp_path = "./tmp"

        bookmarks_update_interval = input("Bookmarks table update interval(sec)(default: 43200):")
        if bookmarks_update_interval == "":
            bookmarks_update_interval = 43200
        else:
            bookmarks_update_interval = int(bookmarks_update_interval)

        backup_interval = input("Backup operation interval(sec)(default: 300):")
        if backup_interval == "":
            backup_interval = 300
        else:
            backup_interval = int(backup_interval)

        backup_number_ontime = input("Number of works backed up each time(default: 3):")
        if backup_number_ontime == "":
            backup_number_ontime = 3
        else:
            backup_number_ontime = int(backup_number_ontime)

        delete_if_not_like = input("Whether to delete illusts that have been canceled from bookmarks(y/N):")
        if delete_if_not_like.lower() == "y":
            delete_if_not_like = 1
        else:
            delete_if_not_like = 0

        # config

        bot = db.Bot()
        bot.key = api_key
        bot.admin = admin
        bot.cookie = cookie
        bot.gif_preview = gif_preview
        bot.bookmarks_update_interval = bookmarks_update_interval
        bot.backup_interval = backup_interval
        bot.tmp_path = tmp_path
        bot.backup_number_ontime = backup_number_ontime
        bot.delete_if_not_like = delete_if_not_like
        session.add(bot)

    print("Bot setup completed.")


def update():
    with db.start_session() as session:
        if not session.query(db.Bot).first():
            print("Bot has not been set up yet.")
            return

        t = input("The config that need to be update(key/admin/cookie/gif_preview/tmp_path/bookmarks_update_interval/backup_interval/backup_number_ontime):")

        v = input("New config value:")

        session.query(db.Bot).update({t: v})

    print("Update completed.")


def add_channel(channel: str):
    with db.start_session() as session:

        c = db.Channel()
        c.id = channel
        session.add(c)

    print("added")


def delete_channel(channel: str):
    with db.start_session() as session:
        c = session.query(db.Channel).filter_by(id=channel).one()

        if c:
            session.query(db.Channel).filter_by(id=channel).delete()
            print("delete successfully")

        else:
            print("channel does not exists")
