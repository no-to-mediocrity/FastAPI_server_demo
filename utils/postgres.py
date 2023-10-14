import pandas as pd
from sqlalchemy import create_engine, text, MetaData, Table
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
import os
import matplotlib.pyplot as plt
import utils.values as values

load_dotenv()

# Параметры подключения к базе данных из .env файла
db_params = {
    'host': os.getenv('DATABASE_HOST'),
    'port': os.getenv('DATABASE_PORT'),
    'database': os.getenv('DATABASE_NAME'),
    'user': os.getenv('DATABASE_USER'),
    'password': os.getenv('DATABASE_PASSWORD')
}

def create_postgresql_engine():
    """
    Создает и возвращает движок SQLAlchemy для подключения к базе данных PostgreSQL.

    Возвращаемая переменная:
    sqlalchemy.engine.base.Connection: объект движка SQLAlchemy.
    """
    engine = create_engine(f'postgresql+psycopg2://{db_params["user"]}:{db_params["password"]}@{db_params["host"]}:{db_params["port"]}/{db_params["database"]}')
    return engine

def create_table(engine, create_query):
    """
    Создаёт таблицу в базе данных, используя предоставленный SQLAlchemy-движок.

    Аргументы:
        - engine (sqlalchemy.engine.base.Connection): SQLAlchemy-движок для подключения к базе данных.
        - create_query (str): Путь к файлу SQL DDL для создания таблицы.
    """
    try:
        with engine.connect() as conn:
            with open(create_query, 'r') as file:
                create_query_text = file.read()
                conn.execute(text(create_query_text))
                conn.commit()
    except IOError as e:
        print(f"Error when reading DDL-file: {e}")
        exit()

def provide_id_to_data(excel_data, projects_table, engine):
    """
    Присваивает идентификаторы проектам в Excel-данных, соответствующим записям в таблице проектов.

    Аргументы:
        - excel_data (pandas.DataFrame): DataFrame с данными из Excel.
        - projects_table (str): Имя таблицы проектов в базе данных.
        - engine (sqlalchemy.engine.base.Connection): SQLAlchemy-движок для подключения к базе данных.

    Возвращаемая переменная:
    pandas.DataFrame: DataFrame с данными, в которых идентификаторы проектов заменены на соответствующие записи из таблицы проектов.
    """
    read_query = f"SELECT * FROM \"{projects_table}\""
    project_names = pd.read_sql(text(read_query), engine)
    merged_df = pd.merge(project_names, excel_data, on='name', how='left')
    merged_df = merged_df.drop(columns=['name'])
    merged_df = merged_df.rename(columns={'id': 'project_id'})
    return merged_df

def process_excel(path, engine):
    """
    Обрабатывает данные из Excel-файла и загружает их в базу данных.

    Аргументы:
        - path (str): Путь к Excel-файлу с данными.
        - engine (sqlalchemy.engine.base.Connection): SQLAlchemy-движок для подключения к базе данных.

    Возвращаемая переменная:
    list: Список исключений, которые могли возникнуть в процессе обработки и загрузки данных.
    """
    exceptions = []
    df = pd.read_excel(path)
    unique_names = df['name'].unique()
    projects_table = "projects" 
    unique_names_df = pd.DataFrame({'name': unique_names})
    try:
        unique_names_df.to_sql(projects_table, engine, index=False, if_exists='append')
    except SQLAlchemyError as e:
        parts = str(e).split('\n\n')
        trimmed_message = parts[0]
        exceptions.append(trimmed_message) 
    merged_df = provide_id_to_data(df, projects_table, engine)
    data_table = "project_data"
    try:
        merged_df.to_sql(data_table, engine, index=False, if_exists='append')
    except SQLAlchemyError as e:
        parts = str(e).split('\n\n')
        trimmed_message = parts[0]
        exceptions.append(trimmed_message)
    return exceptions

def db_to_df(engine):
    """
    Извлекает данные из базы данных и преобразует их в DataFrame.

    Аргументы:
        - engine (sqlalchemy.engine.base.Connection): SQLAlchemy-движок для подключения к базе данных.

    Возвращаемая переменная:
    pandas.DataFrame: DataFrame, содержащий объединенные данные из таблиц проектов и данных о проектах.
    """
    metadata = MetaData()
    metadata.reflect(bind=engine)
    table_names = metadata.tables.keys()
    
    tables_data = {}

    if "project_data" not in table_names and "projects" not in table_names:
        return None

    for table_name in table_names:
        table = Table(table_name, metadata, autoload=True, autoload_with=engine)
        sql_query = table.select()
        df = pd.read_sql(sql_query, engine)
        if df.empty: 
             return None
        tables_data[table_name] = df

    merged_df = pd.merge(tables_data["projects"], tables_data["project_data"], left_on='id', right_on='project_id')
    merged_df = merged_df.drop(columns=['id'])
    
    return merged_df

def plot_data(df, path):
    """
    Создает график на основе данных из DataFrame и сохраняет его как изображение.

    Аргументы:
        - df (pandas.DataFrame): DataFrame с данными для построения графика.
        - path (str): Путь для сохранения изображения графика.

    Возвращаемая переменная:
    str: Путь к сохраненному изображению графика.
    """
    plt.figure(figsize=(10, 6))
    for name, group in df.groupby('name'):
        plt.plot(group['year'], group['cost'], marker='o', label=name)
    plt.title('Затраты vs. Год')
    plt.xlabel('Год')
    plt.ylabel('Затраты')
    plt.legend(title='Имя')
    plt.grid(True)
    unique_filename = f"{values.timestamp}_{values.random_chars}_plot.png"
    plt.savefig(path + "/" + unique_filename)
    plt.close()
    return path + "/" + unique_filename

def init_db():
    """
    Инициализирует базу данных, создавая необходимые таблицы.

    Возвращаемая переменная:
    sqlalchemy.engine.base.Connection: SQLAlchemy-движок для подключения к базе данных.
    """
    create_query = os.getenv('CREATE_QUERY')
    if not (create_query and os.path.exists(create_query)):
        print(f"The SQL-query file does not exist or is not specified.")
        exit()
    engine = create_postgresql_engine()
    create_table(engine, create_query)
    print("\033[32mINFO\033[0m:     The Postgres database has been initialized.")
    return engine 