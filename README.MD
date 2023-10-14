
# FastAPI server demo


Это FastAPI приложение предоставляет возможность загрузки файлов Excel, проверки их формата, а затем загрузки данных из этих файлов в базу данных Postgres. Также приложение предоставляет возможность генерации графиков на основе данных из базы данных и возвращения их в виде файлов PNG.

 

## Установка

Для установки и запуска приложения выполните следующие шаги:

  
1. Склонируйте репозиторий:

 
```bash

git clone https://github.com/no-to-mediocrity/FastAPI_server_demo
```

Перейдите в директорию проекта:

```bash

cd ./FastAPI_server_demo
```

При необходимости создайте виртуальное окружение и активируйте его 

```bash
python3 -m venv .venv && source ./.venv/bin/activate
```

Установите необходимые зависимости:

```bash

pip3 install -r requirements
```

Укажите конфигурацию в файле .env. Необходимо установить следующие переменные окружения:

- DATABASE_NAME = название БД PostgreSQL 
- DATABASE_USER = пользователь БД PostgreSQL  
-   DATABASE_PASSWORD = пароль БД PostgreSQL   
-   DATABASE_HOST = хост БД PostgreSQL 
-   DATABASE_PORT = порт БД PostgreSQL 
- CREATE_QUERY = расположение файла с DDL базы данных
-   UPLOAD_DIR = расположение папки, где будут храниться загруженные Excel-файлы
-   PLOT_DIR = расположение папки, где будут храниться сгенерированные графики  
-   SERVER_HOST =  хост запускаемого сервера
-   SERVER_PORT = порт запускаемого сервера

Запустите приложение:

```bash

python3 server.py
```

## Использование

Приложение предоставляет два эндпоинта:

  ### /v1/upload - загрузка файлов Excel
  
Метод: POST

Описание: Этот эндпоинт позволяет загрузить файл Excel, проверить его формат, сгенерировать уникальное имя файла и загрузить данные из файла в базу данных Postgres.

 
Пример запроса:

  
```curl
curl --location 'http://localhost:8000/v1/upload/' \
--form 'file=@"/Users/user/python/src/FastAPI_server/example.xlsx"'
```

### /v1/generate_image - генерация изображения с графиком


Метод: GET

Описание: Этот эндпоинт использует данные из базы данных Postgres для генерации графика и возвращает его в формате PNG.

 
Пример запроса:
```curl
 curl --location --request GET 'http://localhost:8000/v1/generate_image/' \
--form 'file=@"/Users/user/python/src/FastAPI_server/example.xlsx"'
  ```

Возвращается изображение с графиком в формате PNG.

 