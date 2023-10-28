import asyncpg
from dotenv import load_dotenv
import os

load_dotenv()

class Database:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not isinstance(cls._instance, cls):
            cls._instance = super(Database, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        self.db_params = {
            'host': os.getenv('DATABASE_HOST'),
            'port': os.getenv('DATABASE_PORT'),
            'database': os.getenv('DATABASE_NAME'),
            'user': os.getenv('DATABASE_USER'),
            'password': os.getenv('DATABASE_PASSWORD')
        }
        self.pool = None

    async def create_pool(self):
        if self.pool is None:
            self.pool = await asyncpg.create_pool(**self.db_params)
        return self.pool

    async def set_db_tables(self):
        pool= await self.create_pool()
        create_query = os.getenv('CREATE_QUERY')
        if not (create_query and os.path.exists(create_query)):
                raise FileNotFoundError(f"The SQL-query file does not exist or is not specified.")
        async with pool.acquire() as connection:
            try:
                with open(create_query, 'r') as file:
                    create_query_text = file.read()
            except IOError as e:
                raise FileNotFoundError(f"Error when reading DDL-file at '{create_query}': {e}")

            try:
                await connection.execute(create_query_text)
            except asyncpg.exceptions.PostgresError as e:
                raise RuntimeError(f"Error executing SQL command in '{create_query}': {e}")


    async def add_rows(self, df, table: str, matching_key=None, col_name=None):
        pool = await self.create_pool()
        exceptions = []
        try:
             async with pool.acquire() as connection:
                for _, row in df.iterrows():
                    try: 
                        await connection.copy_records_to_table(table, records=[row.tolist()],columns=list(df.columns))
                    except Exception as e:
                                exceptions.append(e)
        except Exception as e:
                    exceptions.append(e)
                    return exceptions # implement try catch for the caller function

        if exceptions:
            return exceptions
        else:
            return None

    async def simple_select_query(self, table):
        pool= await self.create_pool()
        query = f"SELECT * FROM \"{table}\""
        try:
            async with pool.acquire() as connection:
                async with connection.transaction():
                    stmt = await connection.prepare(query)
                    columns = [a.name for a in stmt.get_attributes()]
                    data = await stmt.fetch()
                    return data, columns, None
        except Exception as e:
           return [], [], e

    async def check_connection(self):
        pool = await self.create_pool()
        if pool:
            try:
                async with pool.acquire() as connection:
                    await connection.fetchval('SELECT 1')
                    return 
            except Exception as e:
                raise(f"An error occurred while checking the connection: {e}")

    async def init(self):
        await self.create_pool() #Пул получит синглтон, его методы в этой функции не нужны
        await self.check_connection()
        create_query = os.getenv('CREATE_QUERY')
        if not (create_query and os.path.exists(create_query)):
            raise FileNotFoundError(f"The SQL-query file does not exist or is not specified.")
        err = await self.set_db_tables()
        if err:
            raise err
            
db = Database()
