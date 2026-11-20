
import aiosqlite

DB_NAME = "usersData.db"


async def setup_database() -> None:
    """
    تهيئة قاعدة البيانات وإنشاء جميع الجداول (users, supporters, active_users).
    يتم أيضاً مسح جدول active_users عند البدء لفك تعليق أي مستخدم.
    """

    create_users_table = """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            lang TEXT DEFAULT 'ar',
            count INTEGER DEFAULT 0
        )
    """

    create_supporters_table = """
        CREATE TABLE IF NOT EXISTS supporters (
            user_id INTEGER PRIMARY KEY
        )
    """

    create_active_table = """
        CREATE TABLE IF NOT EXISTS active_users (
            user_id INTEGER PRIMARY KEY
        )
    """

    async with aiosqlite.connect(DB_NAME) as conn:
        await conn.execute(create_users_table)
        await conn.execute(create_supporters_table)
        await conn.execute(create_active_table)

        await conn.execute("DELETE FROM active_users")
        await conn.commit()


async def user_exists(user_id: int) -> bool:
    """التحقق من وجود المستخدم في قاعدة البيانات"""
    async with aiosqlite.connect(DB_NAME) as conn:
        cursor = await conn.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
        return await cursor.fetchone() is not None


async def get_user_lang(user_id: int) -> str:
    """جلب لغة المستخدم"""
    async with aiosqlite.connect(DB_NAME) as conn:
        cursor = await conn.execute(
            "SELECT lang FROM users WHERE user_id = ?", (user_id,)
        )
        result = await cursor.fetchone()
        return result[0] if result else "ar"


async def set_language(user_id: int, new_lang: str) -> None:
    """تغيير لغة المستخدم"""

    query = """
        INSERT INTO users (user_id, lang, count) VALUES (?, ?, 0)
        ON CONFLICT(user_id) DO UPDATE SET lang = excluded.lang
    """
    async with aiosqlite.connect(DB_NAME) as conn:
        await conn.execute(query, (user_id, new_lang))
        await conn.commit()


async def get_user_count(user_id: int) -> int:
    """ عداد استخدام المستخدم"""
    async with aiosqlite.connect(DB_NAME) as conn:
        cursor = await conn.execute(
            "SELECT count FROM users WHERE user_id = ?", (user_id,)
        )
        result = await cursor.fetchone()
        return result[0] if result else 0


async def increment_usage(user_id: int) -> None:
    """زيادة عداد الاستخدام بمقدار واحد (ينشئ المستخدم إن لم يوجد)"""
    query = """
        INSERT INTO users (user_id, lang, count) VALUES (?, 'ar', 1)
        ON CONFLICT(user_id) DO UPDATE SET count = count + 1
    """
    async with aiosqlite.connect(DB_NAME) as conn:
        await conn.execute(query, (user_id,))
        await conn.commit()


async def decrement_usage(user_id: int) -> None:
    """إنقاص عداد الاستخدام بمقدار واحد (للمستخدمين الموجودين)"""
    query = """
        UPDATE users 
        SET count = count - 1 
        WHERE user_id = ?
    """
    async with aiosqlite.connect(DB_NAME) as conn:
        await conn.execute(query, (user_id,))
        await conn.commit()


async def add_new_user(user_id: int, lang: str = "ar") -> None:
    """إضافة مستخدم جديد فقط إذا لم يكن موجوداً"""
    async with aiosqlite.connect(DB_NAME) as conn:
        await conn.execute(
            "INSERT OR IGNORE INTO users (user_id, lang, count) VALUES (?, ?, 0)",
            (user_id, lang),
        )
        await conn.commit()


async def get_all_users() -> int:
    """العدد الكلي للمستخدمين"""
    try:
        async with aiosqlite.connect(DB_NAME) as conn:
            cursor = await conn.execute("SELECT COUNT(*) FROM users")
            result = await cursor.fetchone()
        return result[0] if result else 0
    except aiosqlite.Error as e:
        print(f"Database error: {e}")
        return 0


async def get_language_stats() -> tuple[int, int]:
    """إحصائيات اللغات.
    Returns: (عدد_العربية, عدد_الإنجليزية)
    """
    try:
        async with aiosqlite.connect(DB_NAME) as conn:
            query = """
                SELECT 
                    SUM(CASE WHEN lang = 'ar' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN lang = 'en' THEN 1 ELSE 0 END)
                FROM users
            """
            cursor = await conn.execute(query)
            result = await cursor.fetchone()

        ar_count = result[0] if result and result[0] else 0
        en_count = result[1] if result and result[1] else 0

        return ar_count, en_count
    except aiosqlite.Error as e:
        print(f"Database error: {e}")
        return 0, 0


async def get_sum_of_counts() -> int:
    """مجموع الاستخدامات الكلي لجميع المستخدمين"""
    try:
        async with aiosqlite.connect(DB_NAME) as conn:
            cursor = await conn.execute("SELECT SUM(count) FROM users")
            result = await cursor.fetchone()
            return result[0] if result and result[0] else 0
    except aiosqlite.Error as e:
        print(f"Database error: {e}")
        return 0


async def get_top_10_users() -> list[tuple[int, int]]:
    """قائمة التوب 10 مستخدمين"""
    try:
        async with aiosqlite.connect(DB_NAME) as conn:
            cursor = await conn.execute(
                "SELECT user_id, count FROM users ORDER BY count DESC LIMIT 10"
            )
            return await cursor.fetchall()
    except aiosqlite.Error as e:
        print(f"Database error: {e}")
        return []


# ===================== إدارة قائمة الداعمين ===================== #


async def add_supporter(user_id: int) -> None:
    """إضافة داعم جديد (تجاهل الأمر إذا كان موجوداً مسبقاً)"""
    async with aiosqlite.connect(DB_NAME) as conn:
        await conn.execute(
            "INSERT OR IGNORE INTO supporters (user_id) VALUES (?)", (user_id,)
        )
        await conn.commit()


async def remove_supporter(user_id: int) -> None:
    """حذف داعم من القائمة"""
    async with aiosqlite.connect(DB_NAME) as conn:
        await conn.execute("DELETE FROM supporters WHERE user_id = ?", (user_id,))
        await conn.commit()


async def get_all_supporters() -> list[int]:
    """قائمة بكل الآيديات للداعمين"""
    async with aiosqlite.connect(DB_NAME) as conn:
        cursor = await conn.execute("SELECT user_id FROM supporters")
        rows = await cursor.fetchall()
        return [row[0] for row in rows]


async def is_supporter(user_id: int) -> bool:
    """التحقق هل المستخدم في قائمة الداعمين أم لا"""
    async with aiosqlite.connect(DB_NAME) as conn:
        cursor = await conn.execute(
            "SELECT 1 FROM supporters WHERE user_id = ?", (user_id,)
        )
        return await cursor.fetchone() is not None


# ================= قائمة المستخدمين النشطين (المشغولين) ================= #


async def is_user_busy(user_id: int) -> bool:
    """التحقق هل المستخدم مشغول حالياً"""
    async with aiosqlite.connect(DB_NAME) as conn:
        cursor = await conn.execute(
            "SELECT 1 FROM active_users WHERE user_id = ?", (user_id,)
        )
        return await cursor.fetchone() is not None


async def set_user_busy(user_id: int) -> None:
    """إضافه لقائمة النشطين"""
    async with aiosqlite.connect(DB_NAME) as conn:
        await conn.execute(
            "INSERT OR IGNORE INTO active_users (user_id) VALUES (?)", (user_id,)
        )
        await conn.commit()


async def set_user_free(user_id: int) -> None:
    """حذف من قائمة النشطين"""
    async with aiosqlite.connect(DB_NAME) as conn:
        await conn.execute("DELETE FROM active_users WHERE user_id = ?", (user_id,))
        await conn.commit()
