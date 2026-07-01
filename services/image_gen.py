import os
from PIL import Image, ImageDraw, ImageFont
import io
import datetime
import random

def draw_barcode(draw, x_start, y_start, height=40):
    random.seed(42) 
    current_x = x_start
    for _ in range(25):
        line_width = random.choice([2, 3, 5])
        space_width = random.choice([2, 4, 6])
        draw.rectangle([current_x, y_start, current_x + line_width, y_start + height], fill="black")
        current_x += line_width + space_width

def wrap_text(text, max_chars=32):
    """Разбивает текст на строки по максимальному количеству символов"""
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        if len(" ".join(current_line + [word])) <= max_chars:
            current_line.append(word)
        else:
            lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))
    return lines

def generate_receipt_image(context):
    width = 400
    items = context.get('items', [])
    roast_text = context.get('roast_text', '')
    
    # Разбиваем вердикт на строки, чтобы он не уезжал за края
    roast_lines = wrap_text(roast_text, max_chars=34)
    
    # Динамически рассчитываем высоту с учетом количества товаров и строк вердикта
    height = 420 + (len(items) * 32) + (len(roast_lines) * 22)
    
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    # --- ЖЕЛЕЗОБЕТОННОЕ ПОДКЛЮЧЕНИЕ ШРИФТОВ ---
    # Находим папку, где лежит этот файл (services/)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Собираем пути к файлам шрифтов в этой же папке
    font_path_regular = os.path.join(current_dir, "cour.ttf")
    font_path_bold = os.path.join(current_dir, "courbd.ttf")
    
    try:
        # Явно указываем кодировку UTF-8 и базовый движок компоновки для Linux
        font = ImageFont.truetype(font_path_regular, 16, encoding="utf-8", layout_engine=ImageFont.Layout.BASIC)
        font_bold = ImageFont.truetype(font_path_bold, 22, encoding="utf-8", layout_engine=ImageFont.Layout.BASIC)
        font_small = ImageFont.truetype(font_path_regular, 12, encoding="utf-8", layout_engine=ImageFont.Layout.BASIC)
        print("--- ШРИФТЫ УСПЕШНО ЗАГРУЖЕНЫ С ПОДДЕРЖКОЙ ЮНИКОДА ---")
    except Exception as e:
        # Если что-то пойдет не так, мы увидим точную причину в логах Render
        print(f"!!! ОШИБКА ЗАГРУЗКИ ШРИФТОВ: {e} !!!")
        font = ImageFont.load_default()
        font_bold = font
        font_small = font

    y = 30
    
    # Шапка
    draw.text((width/2, y), "THE PETTY RECEIPT", fill="black", font=font_bold, anchor="mt")
    y += 30
    draw.text((width/2, y), "ОТДЕЛ АУДИТА ЖИЗНЕННЫХ ПРИОРИТЕТОВ", fill="black", font=font_small, anchor="mt")
    y += 40

    # Инфо
    draw.text((20, y), f"ДАТА: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}", fill="black", font=font)
    y += 25
    draw.text((20, y), f"ТЕРМИНАЛ: {context['ip_address']}", fill="black", font=font)
    y += 30

    def draw_dashed_line(y_pos):
        for i in range(20, width - 20, 15):
            draw.line((i, y_pos, i + 8, y_pos), fill="black", width=2)
            
    draw_dashed_line(y)
    y += 20

    # Таблица
    draw.text((20, y), "НАИМЕНОВАНИЕ", fill="black", font=font)
    draw.text((width - 20, y), "ИТОГО", fill="black", font=font, anchor="rt")
    y += 25
    draw_dashed_line(y)
    y += 20

    # Вывод позиций
    total_damage = 0
    for item in items:
        name = item['name'] if len(item['name']) < 28 else item['name'][:25] + "..."
        draw.text((20, y), name, fill="black", font=font)
        draw.text((width - 20, y), f"{item['cost']} РУБ", fill="black", font=font, anchor="rt")
        total_damage += item['cost']
        y += 32

    draw_dashed_line(y)
    y += 20

    # Итоговый счет
    draw.text((20, y), "ИТОГО УЩЕРБ:", fill="black", font=font_bold)
    draw.text((width - 20, y), f"{total_damage} РУБ", fill="black", font=font_bold, anchor="rt")
    y += 50

    # Вердикт
    draw.text((width/2, y), "--- ВЕРДИКТ ---", fill="black", font=font, anchor="mt")
    y += 30
    
    # Отрисовка перенесенного по строкам вердикта
    for line in roast_lines:
        draw.text((width/2, y), line, fill="black", font=font, anchor="mt")
        y += 22
    y += 25

    # Штрихкод
    draw_barcode(draw, x_start=70, y_start=y, height=50)
    y += 60
    
    draw.text((width/2, y), "0 123456 789012", fill="black", font=font_small, anchor="mt")
    y += 30

    draw.text((width/2, y), "*** СПАСИБО ЗА ЧЕСТНОСТЬ ***", fill="black", font=font_small, anchor="mt")

    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()
