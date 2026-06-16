import aiosqlite
from config import DB_NAME

async def init_db():
    """Инициализация базы данных"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                content_type TEXT NOT NULL,
                text TEXT,
                file_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_read BOOLEAN DEFAULT 0,
                is_replied BOOLEAN DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS blocked_users (
                user_id INTEGER PRIMARY KEY,
                blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def save_message(user_id: int, content_type: str, text: str = None, file_id: str = None):
    """Сохранение сообщения в БД"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """INSERT INTO messages (sender_id, content_type, text, file_id)
               VALUES (?, ?, ?, ?)""",
            (user_id, content_type, text, file_id)
        )
        await db.commit()
        return cursor.lastrowid

async def get_stats():
    """Получение статистики"""
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute("SELECT COUNT(*) FROM messages")
        total = (await cursor.fetchone())[0]

        cursor = await db.execute(
            """SELECT content_type, COUNT(*) as count
               FROM messages GROUP BY content_type"""
        )
        type_counts = {row['content_type']: row['count'] for row in await cursor.fetchall()}

        cursor = await db.execute(
            """SELECT COUNT(DISTINCT sender_id) FROM messages"""
        )
        unique = (await cursor.fetchone())[0]

        return {
            'total': total,
            'text': type_counts.get('text', 0),
            'photo': type_counts.get('photo', 0),
            'video': type_counts.get('video', 0),
            'voice': type_counts.get('voice', 0),
            'sticker': type_counts.get('sticker', 0),
            'unique_senders': unique
        }

async def get_all_messages(limit: int = 50):
    """Получение всех сообщений"""
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT id, content_type, text, created_at
               FROM messages ORDER BY created_at DESC LIMIT ?""",
            (limit,)
        )
        rows = await cursor.fetchall()
        return [
            {
                'id': row['id'],
                'type': row['content_type'],
                'text': row['text'],
                'date': row['created_at']
            }
            for row in rows
        ]

async def block_user(user_id: int):
    """Блокировка пользователя"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """INSERT OR IGNORE INTO blocked_users (user_id) VALUES (?)""",
            (user_id,)
        )
        await db.commit()

async def is_blocked(user_id: int) -> bool:
    """Проверка блокировки"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """SELECT 1 FROM blocked_users WHERE user_id = ?""",
            (user_id,)
        )
        return await cursor.fetchone() is not None
