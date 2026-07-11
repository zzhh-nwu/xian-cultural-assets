"""
SQLite 数据库模块
管理用户、上传、审核日志
"""

import sqlite3
import os
from datetime import datetime

DB_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(DB_DIR, 'data', 'platform.db')


def get_db() -> sqlite3.Connection:
    """获取数据库连接"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """初始化数据库表"""
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT    UNIQUE NOT NULL,
            password    TEXT    NOT NULL,
            email       TEXT    DEFAULT '',
            role        TEXT    DEFAULT 'user',
            avatar      TEXT    DEFAULT '',
            created_at  TEXT    DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS uploads (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            asset_name  TEXT    NOT NULL,
            asset_type  TEXT    DEFAULT 'cultural_relic',
            description TEXT    DEFAULT '',
            city        TEXT    DEFAULT '',
            province    TEXT    DEFAULT '陕西',
            image_path  TEXT    DEFAULT '',
            status      TEXT    DEFAULT 'pending',
            reject_reason TEXT  DEFAULT '',
            created_at  TEXT    DEFAULT (datetime('now','localtime')),
            reviewed_at TEXT    DEFAULT '',
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS audit_logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            upload_id   INTEGER NOT NULL,
            reviewer_id INTEGER NOT NULL,
            action      TEXT    NOT NULL,
            remark      TEXT    DEFAULT '',
            created_at  TEXT    DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (upload_id)   REFERENCES uploads(id),
            FOREIGN KEY (reviewer_id) REFERENCES users(id)
        );
    ''')

    # 创建默认管理员账号（如不存在）
    import hashlib
    existing = conn.execute("SELECT id FROM users WHERE username='admin'").fetchone()
    if not existing:
        pwd = hashlib.sha256('admin123'.encode()).hexdigest()
        conn.execute(
            "INSERT INTO users (username, password, email, role) VALUES (?,?,?,?)",
            ('admin', pwd, 'admin@xian-culture.cn', 'admin')
        )
        conn.commit()
        print('[DB] 默认管理员已创建: admin / admin123')

    conn.commit()
    conn.close()
    print(f'[DB] 数据库初始化完成: {DB_PATH}')


# 启动时自动初始化
if __name__ != '__main__':
    init_db()
