
import sqlite3


class Database:
    def __init__(self, db_path="database.db"):
        self.db_path = db_path
        self.setup_database()

    def setup_database(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("""CREATE TABLE IF NOT EXISTS unbanned_users
                     (user_id INTEGER PRIMARY KEY, 
                      chat_id INTEGER)""")
        
        conn.commit()
        conn.close()

    def add_to_unbanned(self, user_id, chat_id):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            INSERT OR REPLACE INTO unbanned_users 
            (user_id, chat_id) VALUES (?, ?)
        """, (user_id, chat_id))
        conn.commit()
        conn.close()

    def is_user_unbanned(self, user_id, chat_id):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            SELECT 1 FROM unbanned_users 
            WHERE user_id = ? AND chat_id = ?
        """, (user_id, chat_id))
        result = c.fetchone() is not None
        conn.close()
        return result

    def remove_from_unbanned(self, user_id, chat_id):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            DELETE FROM unbanned_users 
            WHERE user_id = ? AND chat_id = ?
        """, (user_id, chat_id))
        conn.commit()
        conn.close()
