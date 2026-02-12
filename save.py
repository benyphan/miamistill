import sqlite3

DB_NAME = "game_save.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS save (
        id INTEGER PRIMARY KEY,
        level INTEGER,
        kills INTEGER
    )
    """)

    # создаём запись если её нет
    cur.execute("SELECT * FROM save WHERE id = 1")
    if cur.fetchone() is None:
        cur.execute(
            "INSERT INTO save (id, level, kills) VALUES (1, 1, 0)"
        )

    conn.commit()
    conn.close()


def save_game(level, kills):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        UPDATE save
        SET level = ?, kills = ?
        WHERE id = 1
    """, (level, kills))

    conn.commit()
    conn.close()


def load_game():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("SELECT level, kills FROM save WHERE id = 1")
    data = cur.fetchone()

    conn.close()

    if data:
        return data  # (level, kills)
    else:
        return 1, 0


def reset_save():
    save_game(1, 0)
