import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import Response, FileResponse
from pydantic import BaseModel
from typing import List
from services.image_gen import generate_receipt_image

app = FastAPI(title="The Petty Receipt API")

# --- АВТОМАТИЧЕСКИЙ НЕУБИВАЕМЫЙ ПОИСК ФАЙЛА INDEX.HTML ---
def find_index_html():
    # Начинаем поиск с самого корня проекта на сервере Render
    root_dir = "/opt/render/project/src"
    
    # Если вдруг папка другая, берем текущую директорию кода
    if not os.path.exists(root_dir):
        root_dir = os.path.dirname(os.path.abspath(__file__))
        
    # Сканируем абсолютно все папки в проекте в поисках index.html
    for root, dirs, files in os.walk(root_dir):
        if "index.html" in files:
            found_path = os.path.join(root, "index.html")
            print(f"--- УРА! Файл index.html найден по пути: {found_path} ---")
            return found_path
    return None

INDEX_HTML_PATH = find_index_html()
# --------------------------------------------------------

class ReceiptItem(BaseModel):
    name: str
    cost: int

class ReceiptRequest(BaseModel):
    items: List[ReceiptItem]
    roast_text: str

# 1. Главная страница сайта
@app.get("/")
async def read_root():
    # Если поисковик не нашел файл во время старта
    if not INDEX_HTML_PATH:
        raise HTTPException(
            status_code=404, 
            detail="index.html absolute panic! The file is literally missing from the GitHub repository."
        )
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
