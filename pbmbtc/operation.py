from . import db


def init():
    with db.start_session() as session:
        if session.query(db.Bot).first() or session.query(db.Backup).first():
            print("There is already content in the database. Do you want to continue?(y/N):")
            if not input().lower() == 'y':
                print("exit.")
                return

        api_key = input("Bot api key:")
        admin = input("The telegram id of the bot administrator:")
        cookie = input("The pixiv account cookie:")

        bot = db.Bot(key=api_key, admin=admin, cookie=cookie)
        session.add(bot)
    print("Bot setup completed.")


def update():
    with db.start_session() as session:
        if not session.query(db.Bot).first():
            print("Bot has not been set up yet.")
            return

        t = input("The item that need to be update(key/admin/cookie):")
        if t != "key" and t != "admin" and t != "cookie":
            print(f"Error item: {t}")
            return

        v = input("New item value:")

        session.query(db.Bot).update({t: v})

    print("Update completed.")

