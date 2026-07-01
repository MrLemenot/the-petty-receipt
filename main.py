from fastapi import FastAPI
from fastapi.responses import StreamingResponse, HTMLResponse
from pydantic import BaseModel
from typing import List
import io
import os
from PIL import Image, ImageDraw, ImageFont

app = FastAPI()

class ReceiptItem(BaseModel):
    name: str
    cost: str

class ReceiptRequest(BaseModel):
    title: str
    subtitle: str
    date_str: str
    items: List[ReceiptItem]
    total_str: str
    verdict: str
    footer_1: str
    footer_2: str

@app.get("/", response_class=HTMLResponse)
async def get_index():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    elif os.path.exists("static/index.html"):
        with open("static/index.html", "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Файл index.html не найден рядом с main.py</h1>"

@app.post("/api/generate")
async def generate_receipt(payload: ReceiptRequest):
    line_height = 26
    padding_x = 40
    padding_y = 35
    
    # 1. Сначала просто считаем, какая высота нам НАДОБИТСЯ
    dynamic_lines_count = len(payload.items) + 16
    estimated_height = (dynamic_lines_count * line_height) + (padding_y * 2)
    
    # 2. Создаем ОДИН финальный холст сразу нужного размера с белым фоном
    img_width = 460
    image = Image.new("RGB", (img_width, estimated_height), "white")
    draw = ImageDraw.Draw(image)
    
    font = None
    possible_fonts = ["cour.ttf", "courier.ttf", "arial.ttf", "calibri.ttf"]
    for f_name in possible_fonts:
        try:
            font = ImageFont.truetype(f_name, 16)
            break
        except IOError:
            continue
    if font is None:
        font = ImageFont.load_default()

    y = padding_y
    
    def draw_center(text, current_y, fill_color="black"):
        try:
            w = draw.textlength(text, font=font)
        except AttributeError:
            w = len(text) * 8
        x = (img_width - w) // 2
        draw.text((x, current_y), text, fill=fill_color, font=font)
        return w

    # --- Отрисовка контента ---
    # Шапка
    draw_center(payload.title, y)
    y += line_height
    draw_center(payload.subtitle, y)
    y += line_height * 1.5
    
    draw_center(payload.date_str, y)
    y += line_height
    draw_center("= = = = = = = = = = = = = = = = =", y)
    y += line_height * 1.2
    
    # Позиции
    for item in payload.items:
        name_str = item.name[:22]
        cost_str = item.cost
        spaces_needed = 34 - len(name_str) - len(cost_str)
        line_str = name_str + ("." * max(1, spaces_needed)) + cost_str
        draw_center(line_str, y)
        y += line_height
        
    y += line_height * 0.3
    draw_center("= = = = = = = = = = = = = = = = =", y)
    y += line_height * 1.2
    
    # Итого
    total_text = f"  {payload.total_str}  "
    try:
        tw = draw.textlength(total_text, font=font)
    except AttributeError:
        tw = len(total_text) * 8
        
    tx = (img_width - tw) // 2
    draw.rectangle([tx, y - 4, tx + tw, y + line_height + 2], outline="black", width=2)
    draw_center(total_text, y)
    y += line_height * 2.0
    
    # Вердикт
    verdict_text = f"  {payload.verdict}  "
    try:
        vw = draw.textlength(verdict_text, font=font)
    except AttributeError:
        vw = len(verdict_text) * 8
    vx = (img_width - vw) // 2
    
    draw.rectangle([vx, y - 4, vx + vw, y + line_height + 4], fill="black")
    draw_center(verdict_text, y, fill_color="white")
    y += line_height * 2.2
    
    # Подвал
    draw_center(payload.footer_1, y)
    y += line_height
    draw_center(payload.footer_2, y)
    y += line_height * 1.8
    
    # Штрихкод
    barcode_height = 35
    widths = [3, 5, 2, 4, 2, 6, 3, 2, 5, 3, 2, 4, 3, 6, 2, 3, 5, 2, 4, 2, 5, 3]
    gap = 2
    
    total_barcode_width = sum(widths) + (gap * (len(widths) - 1))
    barcode_x = (img_width - total_barcode_width) // 2
    barcode_y = y
    
    current_bx = barcode_x
    for i, w in enumerate(widths):
        if i % 2 == 0:
            draw.rectangle([current_bx, barcode_y, current_bx + w, barcode_y + barcode_height], fill="black")
        current_bx += w + gap
        
    y += barcode_height + 5
    draw_center("No. 0001923847 2026", y)
    
    # Теперь мы знаем точный конец контента
    final_height = y + line_height + 25
    
    # Обрезаем картинку строго по нижней границе, если остался лишний хвост
    final_image = image.crop((0, 0, img_width, final_height))
    final_draw = ImageDraw.Draw(final_image)
    
    # Рисуем красивую рамку — она 100% закроется внизу!
    final_draw.rectangle([15, 15, img_width - 15, final_height - 15], outline="black", width=2)

    img_byte_arr = io.BytesIO()
    final_image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    return StreamingResponse(img_byte_arr, media_type="image/png")