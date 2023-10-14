from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
import uvicorn
import utils.postgres as postgres
import os
import utils.values as values

app = FastAPI()
engine = postgres.init_db()

upload_dir = os.getenv('UPLOAD_DIR')
plot_dir = os.getenv('PLOT_DIR')
server_host = os.getenv('SERVER_HOST')
port_string = os.getenv('SERVER_PORT')
port_string.lstrip('0')
if port_string == "":
    server_port = 0
else: 
    server_port = int(port_string)

os.makedirs(upload_dir, exist_ok=True)
os.makedirs(plot_dir, exist_ok=True)


def is_excel_file(filename: str) -> bool:
    """
    Проверяет, является ли представленный файл файлом Excel на основе расширения файла.
    
    Аргументы:
    - filename: Имя файла.

    Возвращаемая переменная:

    - bool: True, если файл Excel, в противном случае False.
    """
    allowed_extensions = {".xls", ".xlsx", ".xlsm"}
    return any(filename.lower().endswith(ext) for ext in allowed_extensions)

def generate_unique_filename(file_extension, original_filename):
    """
    Генерирует уникальное имя файла на основе расширения и оригинального имени файла.

   Аргументы:
    - file_extension: Расширение файла.
    - original_filename: Оригинальное имя файла.
    
    Возвращаемая переменная:
    - string: Уникальное имя файла.
    """
    original_filename_without_extension = os.path.splitext(original_filename)[0]
    unique_filename = f"{values.timestamp}_{values.random_chars}_{original_filename_without_extension}.{file_extension}"
    return unique_filename

@app.post("/v1/upload")
async def upload_file(file: UploadFile):
    """
    Endpoint для загрузки файла Excel, проверки его формата, генерации уникального имени и загрузки данных в БД.

    Аргументы:
   -  file: Загружаемый файл.

    Возвращает: 
    
    Сообщение об успешной загрузке и обработке или сообщение об ошибке.
    """
    if not is_excel_file(file.filename):
        return {"error": "Неверный формат файла. Пожалуйста, загрузите файл Excel."}

    file_extension = file.filename.split(".")[-1]
    original_filename = file.filename
    unique_filename = generate_unique_filename(file_extension, original_filename)
    file_path = os.path.join(upload_dir, unique_filename)

    with open(file_path, "wb") as f:
        f.write(file.file.read())
    exceptions = postgres.process_excel(file_path, engine)
    if exceptions == []:
        return {"message": f"Файл Excel '{file.filename}' успешно загружен и обработан."}
    else: 
        return {"error": exceptions}

@app.get("/v1/generate_image")
async def generate_image():
    """
    Генерирует изображение на основе данных из БД Postgres и возвращает его в виде файла.

    Возвращает: 
     
    Изображение с графиком по данным из БД в формате .PNG или сообщение об ошибке.
    """

    try:
        df = postgres.db_to_df(engine)
        if df is None:
            raise HTTPException(status_code=500, detail="Произошла ошибка при получении данных из базы данных.")

        plot_filename = postgres.plot_data(df, plot_dir)
        if not plot_filename:
            raise HTTPException(status_code=500, detail="Произошла ошибка при построении графика данных.")

        if not os.path.exists(plot_filename):
            raise HTTPException(status_code=404, detail="Файл с графиком не найден.")

        return FileResponse(plot_filename, media_type='image/png')

    except HTTPException as e:
       return {"message": e}

if __name__ == "__main__":
    uvicorn.run(app, host=server_host, port=server_port)
