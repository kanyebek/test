CREATE_TABLE_ITEMS = """
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        label TEXT NOT NULL,
        purchased INTEGER NOT NULL DEFAULT 0
        )
"""

SELECT_ITEMS = 'SELECT * FROM items'

INSERT_ITEM = 'INSERT INTO items (label)  VALUES (?)'

UPDATE_ITEM = "UPDATE items SET purchased = ? WHERE id = ?"

DELETE_ITEM = 'DELETE FROM items WHERE id = ?'

SELECT_purchased = 'SELECT * FROM items WHERE purchased = 1'

SELECT_unpurchased = 'SELECT * FROM items WHERE purchased = 0'

