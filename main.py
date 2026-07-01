import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import Response, FileResponse
from pydantic import BaseModel
from typing import List
from services.image_gen import generate_receipt_image

app = FastAPI(title="The Petty Receipt API")

current_dir = os.path.dirname(os.path.abspath(__file__))

# Находим точный путь к файлу index.html
INDEX_HTML_PATH = os.path.join(current_dir, "index.html")

class ReceiptItem(BaseModel):
    name: str
    cost: int

class ReceiptRequest(BaseModel):
    items: List[ReceiptItem]
    roast_text: str

# 1. Главная страница сайта — теперь отдаем файл напрямую!
@app.get("/")
async def read_root():
    # Проверяем, существует ли файл, чтобы выдать красивую ошибку, если ты забыл его создать
    if not os.path.exists(INDEX_HTML_PATH):
        raise HTTPException(status_code=404, detail=f"index.html not found at {INDEX_HTML_PATH}")
    return FileResponse(INDEX_HTML_PATH)

# 2. Эндпоинт генерации чека
@app.post("/generate")
async def generate_receipt(payload: ReceiptRequest, request: Request):
    try:
        ip_address = request.client.host if request.client else "127.0.0.1"
        
        context = {
            "items": [{"name": item.name, "cost": item.cost} for item in payload.items],
            "roast_text": payload.roast_text,
            "ip_address": ip_address
        }
        
        img_bytes = generate_receipt_image(context)
        return Response(content=img_bytes, media_type="image/png")
        
    except Exception as e:
        print(f"Error during generation: {e}")
        raise HTTPException(status_code=500, detail="Terminal malfunction. Could not print receipt.")
