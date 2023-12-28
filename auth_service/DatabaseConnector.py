import aiomysql
import asyncio


async def connect_to_db(max_retries=3, delay=2):
    retry_count = 0
    last_exception = None

    while retry_count < max_retries:
        try:
            conn = await aiomysql.connect(
                host="university.mysql.database.azure.com",
                user="mediaEngine",
                password="DisSys2023",
                db='mediaservice',
                charset='utf8mb4')
            return conn
        except Exception as e:  # Consider catching a broader range of exceptions
            last_exception = e
            retry_count += 1
            print(f"Failed to connect to DB: {e}, retrying ({retry_count}/{max_retries})...")
            await asyncio.sleep(delay)

    raise Exception(f"Failed to connect to the database after several attempts: {last_exception}")


async def get_user_salt(username):
    conn = await connect_to_db()  # Await the connection

    try:
        async with conn.cursor() as cursor:  # Use async context manager for cursor
            await cursor.execute("SELECT salt FROM users WHERE username = %s", (username,))
            salt = await cursor.fetchone()
        return salt

    finally:
        conn.close()  # This is fine as conn.close() is synchronous in aiomysql


async def validate_user(username, password):
    conn = await connect_to_db()  # Establish a new connection

    try:
        async with conn.cursor() as cursor:
            cursor.execute("SELECT username FROM users WHERE username = %s AND password = %s", (username, password))
            user = await cursor.fetchone()
        return user
    finally:
        conn.close()


async def create_user(username, password, salt, email):
    # Establish a new connection
    conn = await connect_to_db()

    try:
        # Use async context manager for cursor
        async with conn.cursor() as cursor:
            # Execute the INSERT query
            await cursor.execute("INSERT INTO users (username, password, salt, email) VALUES (%s, %s, %s, %s)",
                                 (username, password, salt, email))

        # Commit the transaction
        await conn.commit()

        # Check if the user was created
        user = await get_user(username)

        if user is None:
            return False

        return True

    finally:
        # Close the connection
        conn.close()


async def get_user(username):
    conn = await connect_to_db()

    try:
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT username FROM users WHERE username = %s", (username,))
            user = await cursor.fetchone()
        return user
    finally:
        conn.close()

async def get_user_email(email):
    conn = await connect_to_db()

    try:
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT email FROM users WHERE email = %s", (email,))
            user = await cursor.fetchone()
        return user
    finally:
        conn.close()