import asyncio
import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set.")


async def init_pool() -> asyncpg.Pool:
    return await asyncpg.create_pool(
        dsn=DATABASE_URL,
        min_size=2,
        max_size=10,
        timeout=30.0,
    )


async def create_user_with_first_post(
    conn: asyncpg.Connection,
    username: str,
    email: str,
    post_title: str,
    post_content: str,
) -> int:
    async with conn.transaction():
        user_query = """
        INSERT INTO users (username, email)
        VALUES ($1, $2)
        RETURNING id;
        """
        user_id = await conn.fetchval(user_query, username, email)

        post_query = """
        INSERT INTO posts (user_id, title, content)
        VALUES ($1, $2, $3)
        RETURNING id;
        """
        await conn.fetchval(post_query, user_id, post_title, post_content)

        return user_id


async def get_user_posts(
    conn: asyncpg.Connection, user_id: int
) -> list[asyncpg.Record]:
    query = """
    SELECT p.id, p.title, p.content, p.published_at, u.username
    FROM posts p
    JOIN users u ON u.id = p.user_id
    WHERE u.id = $1;
    """
    return await conn.fetch(query, user_id)


async def main():
    pool = await init_pool()
    try:
        async with pool.acquire() as conn:
            user_id = await create_user_with_first_post(
                conn,
                username="diana",
                email="diana@example.com",
                post_title="Python ve asyncpg",
                post_content="Transaction yönetimi ve bağlantı havuzu kullanımı.",
            )
            print(f"Kullanıcı ve yazı başarıyla oluşturuldu. User ID: {user_id}")

            posts = await get_user_posts(conn, user_id)
            for post in posts:
                print(f"Yazı: {post['title']} | Yazar: {post['username']}")

    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(main())
