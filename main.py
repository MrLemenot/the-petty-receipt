import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import Response, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional
from services.image_gen import generate_receipt_image

app = FastAPI(title="The Petty Receipt API")

# Настройка путей для фронтенда (templates и static)
current_dir = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(current_dir, "templates"))

# Если у тебя есть папка static для CSS/JS, раскомментируй строку ниже:
# app.mount("/static", StaticFiles(directory=os.path.join(current_dir, "static")), name="static")

# Структура данных, которую мы ждем от фронтенда (входные данные квиза)
class ReceiptItem(BaseModel):
    name: str
    cost: int

class ReceiptRequest(BaseModel):
    items: List[ReceiptItem]
    roast_text: str

# 1. Главная страница сайта
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    # Рендерит наш index.html из папки templates
    return templates.TemplateResponse("index.html", {"request": request})

# 2. Эндпоинт генерации чека
@app.post("/generate")
async def generate_receipt(payload: ReceiptRequest, request: Request):
    try:
        # Автоматически определяем IP-адрес терминала (пользователя)
        ip_address = request.client.host if request.client else "127.0.0.1"
        
        # Собираем контекст для передачи в image_gen.py
        context = {
            "items": [{"name": item.name, "cost": item.cost} for item in payload.items],
            "roast_text": payload.roast_text,
            "ip_address": ip_address
        }
        
        # Генерируем бинарные данные картинки PNG
        img_bytes = generate_receipt_image(context)
        
        # Возвращаем картинку в браузер с правильным медиа-типом
        return Response(content=img_bytes, media_type="image/png")
        
    except Exception as e:
        print(f"Error during generation: {e}")
        raise HTTPException(status_code=500, detail="Terminal malfunction. Could not print receipt.")

# Запуск локально для тестов: uvicorn main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
