import sqlite3
from config import DB_PATH
from db import queries


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(queries.CREATE_TABLE_ITEMS)
    conn.commit()
    conn.close()


def get_items(filter_type="all"):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if filter_type == 'purchased':
        cursor.execute(queries.SELECT_purchased)
    elif filter_type == "unpurchased":
        cursor.execute(queries.SELECT_unpurchased)
    else:
        cursor.execute(queries.SELECT_ITEMS)
    items = cursor.fetchall()
    conn.close()
    return items

def add_item(label,amount=1):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(queries.INSERT_ITEM, (label,))
    conn.commit()
    item_id = cursor.lastrowid
    conn.close()
    return item_id

def delete_item(item_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(queries.DELETE_ITEM, (item_id,))
    conn.commit()
    conn.close()

def update_item(item_id, new_item = None, purchased = None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if new_item is not None:
        cursor.execute(queries.UPDATE_ITEM, (new_item, item_id))
    if purchased is not None:
        cursor.execute(queries.UPDATE_ITEM, (purchased, item_id))

    conn.commit()
    conn.close()
    
def get_purchased_items():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(queries.SELECT_purchased)
    items = cursor.fetchall()
    conn.close()
    return items

def get_unpurchased_items():    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(queries.SELECT_unpurchased)
    items = cursor.fetchall()
    conn.close()
    return items