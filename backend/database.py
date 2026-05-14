"""SQLite 資料庫初始化與連線。"""
import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), 'coffee.db')


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db_cursor():
    conn = get_conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """建立資料表;如已存在則略過。第一次啟動時自動 seed 預設菜單。"""
    with db_cursor() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS menu_items (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            category      TEXT    NOT NULL,
            icon          TEXT    NOT NULL DEFAULT '☕',
            name          TEXT    NOT NULL,
            description   TEXT    NOT NULL DEFAULT '',
            base_price    INTEGER NOT NULL,
            customizable  INTEGER NOT NULL DEFAULT 1,
            has_temp      INTEGER NOT NULL DEFAULT 1,
            has_sweet     INTEGER NOT NULL DEFAULT 1,
            is_available  INTEGER NOT NULL DEFAULT 1,
            sort_order    INTEGER NOT NULL DEFAULT 0,
            created_at    TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS orders (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            order_no       TEXT    NOT NULL UNIQUE,
            total          INTEGER NOT NULL,
            cash_received  INTEGER NOT NULL,
            change_given   INTEGER NOT NULL,
            status         TEXT    NOT NULL DEFAULT 'pending',
            created_at     TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
            updated_at     TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS order_items (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id      INTEGER NOT NULL,
            menu_item_id  INTEGER,
            name          TEXT    NOT NULL,
            qty           INTEGER NOT NULL,
            unit_price    INTEGER NOT NULL,
            options       TEXT    NOT NULL DEFAULT '',
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_orders_created ON orders(created_at);
        CREATE INDEX IF NOT EXISTS idx_orders_status  ON orders(status);
        """)

        # 第一次啟動 seed 預設菜單
        cnt = conn.execute("SELECT COUNT(*) FROM menu_items").fetchone()[0]
        if cnt == 0:
            seed_default_menu(conn)


DEFAULT_MENU = [
    # (category, icon, name, description, base_price, customizable, has_temp, has_sweet)
    ('咖啡', '☕', '濃縮咖啡', '單份義式濃縮', 60, 1, 0, 0),
    ('咖啡', '☕', '美式咖啡', '濃縮加熱水', 75, 1, 1, 1),
    ('咖啡', '🥛', '拿鐵', '濃縮配蒸奶,綿密奶香', 90, 1, 1, 1),
    ('咖啡', '☕', '卡布奇諾', '經典奶泡咖啡', 90, 1, 1, 1),
    ('咖啡', '🍫', '摩卡', '巧克力與咖啡的融合', 100, 1, 1, 1),
    ('咖啡', '🍯', '焦糖瑪奇朵', '焦糖香氣濃郁', 110, 1, 1, 1),
    ('茶飲', '🍵', '英式紅茶', '錫蘭紅茶', 60, 1, 1, 1),
    ('茶飲', '🍵', '日式煎茶', '甘醇綠茶', 70, 1, 1, 1),
    ('茶飲', '🥛', '鮮奶茶', '紅茶配上鮮奶', 85, 1, 1, 1),
    ('茶飲', '🍑', '水蜜桃水果茶', '果香繽紛', 95, 1, 1, 1),
    ('特調', '🍫', '熱可可', '醇厚比利時可可', 95, 1, 0, 0),
    ('特調', '🍵', '抹茶拿鐵', '京都宇治抹茶', 110, 1, 1, 1),
    ('特調', '🌾', '燕麥拿鐵', '植物奶 · 低負擔', 120, 1, 1, 1),
    ('點心', '🥐', '法式可頌', '層次酥香', 55, 0, 0, 0),
    ('點心', '🍰', '提拉米蘇', '經典義式甜點', 120, 0, 0, 0),
    ('點心', '🧀', '紐約起司蛋糕', '濃郁起司風味', 130, 0, 0, 0),
    ('點心', '🍪', '巧克力餅乾', '手工烘焙', 45, 0, 0, 0),
    ('點心', '🥯', '原味貝果', '紐約風味', 65, 0, 0, 0),
]


def seed_default_menu(conn):
    for i, row in enumerate(DEFAULT_MENU):
        conn.execute("""
            INSERT INTO menu_items
                (category, icon, name, description, base_price, customizable, has_temp, has_sweet, sort_order)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (*row, i))


if __name__ == '__main__':
    init_db()
    print(f'資料庫已初始化:{DB_PATH}')
