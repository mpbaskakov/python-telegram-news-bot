import sqlite3
import config


def sql_command(sql, fetch):
    conn = sqlite3.connect('main.db')
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
    except sqlite3.OperationalError:
        pass
    if fetch == 'fetch_all':
        rows = cursor.fetchall()
        return rows
    elif fetch == 'fetch_one':
        rows = cursor.fetchone()
        return rows
    conn.commit()
    conn.close()


def write_to_base(item_text):
    sql_command("INSERT INTO {} (item) VALUES ('{}')".format(config.db_name, item_text), fetch=False)


def check_item_exist(item_text):
    if sql_command("SELECT item FROM {} WHERE item LIKE '{}'".format(config.db_name, item_text), fetch='fetch_one'):
        return True
    else:
        return False


def get_news():
    news = sql_command("SELECT item FROM {} WHERE posted LIKE 'False'".format(config.db_name), fetch='fetch_all')
    if len(news) >= 2:
        return news[0:5]


def make_posted(item):
    sql_command("UPDATE {} SET posted = 'True' WHERE item = '{}'".format(config.db_name, item), fetch=False)


def db_trash(bot, update):
    news = sql_command("SELECT item FROM {} WHERE posted LIKE 'True'".format(config.db_name), fetch='fetch_all')
    if len(news) >= 10:
        for n in news[10:]:
            sql_command("DELETE FROM {} WHERE item = '{}'".format(config.db_name, n), fetch=False)
