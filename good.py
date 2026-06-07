import ssl
ssl._create_default_https_context = ssl._create_unverified_context

import mss
import easyocr
import ctypes
import time
import random
import cv2
import numpy as np
import re
from PIL import Image
import keyboard
import traceback
from threading import Thread
import os
import sys
import torch
import pyautogui

pyautogui.FAILSAFE = False

WORKING = True

ITEMS_FILE = "items_save.txt"
RESTART_SIGNAL_FILE = "restart_signal.txt"

PRICE_AREA_X = 1251
PRICE_AREA_Y = 390
PRICE_AREA_W = 57
PRICE_AREA_H = 376

# Параметры сайдбара
SCROLLBAR_X = 1394
SCROLLBAR_Y = 347
SCROLL_STEP = 80  # шаг прокрутки в пикселях

print(f"Область цен: X={PRICE_AREA_X}, Y={PRICE_AREA_Y}, W={PRICE_AREA_W}, H={PRICE_AREA_H}")

print("Загрузка EasyOCR...")
print(f"CUDA: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")

reader = easyocr.Reader(['en'], gpu=True, model_storage_directory='easyocr_models')
print("OCR готов!")

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_KEYUP = 0x0100
BACKSPACE_VIRTUAL_CODE = 0x08
window_handle = ctypes.windll.user32.FindWindowW(None, 'STALCRAFT')

templates = {}
template_files = {
    'auction': 'blueprints/auctionRecognition.png',
    'buyout': 'blueprints/buyoutRecognition.png',
    'search': 'blueprints/searchRecognition.png',
    'buy': 'blueprints/buyRecognition.png',
}
for name, path in template_files.items():
    templates[name] = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if templates[name] is None:
        print(f"Ошибка: шаблон {path} не загружен")

sct = mss.mss()
monitor = sct.monitors[1]

def send_restart_signal():
    with open(RESTART_SIGNAL_FILE, "w") as f:
        f.write("restart")
    print("📡 Сигнал перезапуска")
    time.sleep(0.5)
    sys.exit(0)

def save_items(items):
    with open(ITEMS_FILE, "w", encoding="utf-8") as f:
        for name, price in items:
            f.write(f"{name}|{price}\n")
    print(f"💾 Сохранено: {len(items)}")

def load_items():
    items = []
    if os.path.exists(ITEMS_FILE):
        with open(ITEMS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("|")
                if len(parts) == 2:
                    items.append([parts[0], int(parts[1])])
        print(f"📂 Загружено: {len(items)}")
    return items

def quick_click():
    pyautogui.click()
    time.sleep(0.001)

def imageRecognitionFast(template, screenshot_gray):
    result = cv2.matchTemplate(screenshot_gray, template, cv2.TM_SQDIFF_NORMED)
    mn, _, mnLoc, _ = cv2.minMaxLoc(result)
    return mnLoc

def get_screenshot():
    screenshot = sct.grab(monitor)
    screenshot_rgb = np.array(screenshot)
    screenshot_gray = cv2.cvtColor(screenshot_rgb, cv2.COLOR_BGR2GRAY)
    return screenshot_rgb, screenshot_gray

def initAuction():
    screen_x = pyautogui.size().width // 2
    screen_y = pyautogui.size().height // 2
    pyautogui.click(screen_x, screen_y)
    time.sleep(0.2)
    
    pyautogui.press('esc')
    time.sleep(0.3)
    pyautogui.press('esc')
    time.sleep(0.3)
    
    for _ in range(3):
        pyautogui.press('P')
        time.sleep(0.2)
    
    for attempt in range(5):
        _, screenshot_gray = get_screenshot()
        aucX, aucY = imageRecognitionFast(templates['auction'], screenshot_gray)
        if aucX != 0 and aucY != 0:
            pyautogui.moveTo(random.randint(aucX+30, aucX+50), random.randint(aucY+3, aucY+10), 0.01)
            quick_click()
            print("  ✅ Аукцион открыт")
            break
        time.sleep(0.5)

def sort_by_price():
    _, screenshot_gray = get_screenshot()
    X, Y = imageRecognitionFast(templates['buyout'], screenshot_gray)
    if X == 0 and Y == 0:
        return False
    click_x = random.randint(X+5, X+50)
    click_y = random.randint(Y+3, Y+15)
    pyautogui.moveTo(click_x, click_y, 0.01)
    quick_click()
    time.sleep(0.1)
    quick_click()
    print("  📊 Сортировка")
    time.sleep(0.3)
    return True

def searchClick():
    _, screenshot_gray = get_screenshot()
    X, Y = imageRecognitionFast(templates['search'], screenshot_gray)
    if X == 0 and Y == 0:
        return False
    x = random.randint(X+3, X+40)
    y = random.randint(Y+4, Y+13)
    pyautogui.moveTo(x, y, 0.01)
    quick_click()
    return True

def refresh_auction():
    """Только нажимает кнопку Поиск, без скролла"""
    searchClick()
    time.sleep(0.1)

def refresh_and_scroll_to_position(steps):
    """
    Нажимает Поиск и СРАЗУ скроллит на нужную позицию.
    Возвращает актуальный Y сайдбара.
    """
    searchClick()
    time.sleep(0.3)  # Ждём загрузки после поиска
    
    if steps > 0:
        print(f"  ⚡ Быстрый скролл на {steps} шагов...")
        current_y = scroll_sidebar_down(steps, SCROLLBAR_Y)
    else:
        current_y = SCROLLBAR_Y
    
    return current_y

def scroll_sidebar_down(steps=1, current_scroll_y=None):
    """
    Прокрутка сайдбара вниз на указанное количество шагов.
    Делает ОДНО движение на (SCROLL_STEP * steps) пикселей.
    Возвращает новую позицию Y сайдбара.
    """
    if current_scroll_y is None:
        current_scroll_y = SCROLLBAR_Y
    
    if steps <= 0:
        return current_scroll_y
    
    start_x = SCROLLBAR_X
    target_y = current_scroll_y + (SCROLL_STEP * steps)  # ОДНО движение на полную дистанцию
    
    print(f"  ↕️ Скролл сайдбара: {current_scroll_y} -> {target_y} ({steps} шагов за раз)")
    
    # Захватываем сайдбар
    pyautogui.moveTo(start_x, current_scroll_y, duration=0.01)
    pyautogui.mouseDown(button='left')
    time.sleep(0.05)
    
    # Тянем ОДНИМ движением на полную дистанцию
    pyautogui.moveTo(start_x, target_y, duration=0.15)
    time.sleep(0.05)
    pyautogui.mouseUp(button='left')
    time.sleep(0.3)
    
    return target_y

def find_first_price(img_rgb):
    price_area = img_rgb[PRICE_AREA_Y:PRICE_AREA_Y+PRICE_AREA_H, 
                         PRICE_AREA_X:PRICE_AREA_X+PRICE_AREA_W]
    results = reader.readtext(price_area, detail=1, paragraph=False, allowlist='0123456789')
    
    if not results:
        return "empty"
    
    for (bbox, text, confidence) in results:
        digits = re.sub(r'[^0-9]', '', text)
        if not digits:
            continue
        
        price = int(digits)
        if price < 1000 and len(text) > len(digits) + 1:
            price = price * 1000
        
        if price == 999999:
            print(f"    ⚠️ Мусорная цена: {price}")
            continue
        
        x1, y1 = bbox[0]
        x2, y2 = bbox[2]
        center_x = PRICE_AREA_X + (x1 + x2) // 2
        center_y = PRICE_AREA_Y + (y1 + y2) // 2
        print(f"    🔍 Цена: '{text}' -> {price}")
        return price, center_x, center_y
    
    print(f"    ⚠️ Все цены мусорные (999999)")
    return "garbage"

def buy_full_process(click_x, click_y):
    pyautogui.moveTo(click_x, click_y, 0.01)
    quick_click()
    print("  💰 Клик по цене")
    time.sleep(0.2)
    _, gray = get_screenshot()
    X, Y = imageRecognitionFast(templates['buy'], gray)
    if X == 0 and Y == 0:
        print("  ❌ Кнопка 'Купить' не найдена")
        return False
    buy_x = random.randint(X+5, X+60)
    buy_y = random.randint(Y+5, Y+20)
    pyautogui.moveTo(buy_x, buy_y, 0.01)
    quick_click()
    print("  🛒 Купить")
    time.sleep(0.1)
    pyautogui.press('esc')
    print("  🔚 ESC")
    time.sleep(0.1)
    return True

def exit_check():
    global WORKING
    while WORKING:
        if keyboard.is_pressed("f1"):
            WORKING = False
            break
        time.sleep(0.01)

def search_and_buy(name, limit):
    """
    Первичный поиск предмета.
    Возвращает (успех, кол-во шагов до первой цены)
    """
    print(f"\n🔍 ИЩУ: {name}")
    _, gray = get_screenshot()
    X, Y = imageRecognitionFast(templates['search'], gray)
    if X == 0 and Y == 0:
        print("  ❌ Кнопка поиска не найдена")
        main()
        return False, 0
    
    # Ввод названия
    x = random.randint(X-17, X-11)
    y = random.randint(Y+2, Y+13)
    pyautogui.moveTo(x, y, 0.01)
    quick_click()
    time.sleep(0.05)
    
    for _ in range(random.randint(40, 55)):
        ctypes.windll.user32.SendMessageW(window_handle, WM_KEYUP, BACKSPACE_VIRTUAL_CODE, 0)
        time.sleep(0.001)
    for ch in name:
        ctypes.windll.user32.SendMessageW(window_handle, 0x0102, ord(ch), 0)
        time.sleep(0.001)
    
    searchClick()
    time.sleep(0.15)
    sort_by_price()
    
    # Первый анализ ДО скролла (начальная позиция)
    rgb, _ = get_screenshot()
    result = find_first_price(rgb)
    
    steps_scrolled = 0
    current_scroll_y = SCROLLBAR_Y
    empty_count = 0
    
    while WORKING:
        # Если нашли нормальную цену
        if result not in ["empty", "garbage", None]:
            price, click_x, click_y = result
            print(f"  📋 Цена: {price} (лимит {limit})")
            print(f"  📌 Найдено через {steps_scrolled} шагов скролла")
            
            if price <= limit:
                print(f"  ✅ ПОДХОДИТ! Покупаю...")
                buy_full_process(click_x, click_y)
                print(f"🎉 КУПИЛ {name} за {price}!")
                return True, steps_scrolled
            else:
                print(f"  ❌ Цена {price} > {limit}")
                # ПЕРВЫЙ РАЗ: если нашли на нулевом шаге — скроллим дальше для первичного поиска
                if steps_scrolled == 0:
                    print(f"  📭 Цена не подходит, скроллю дальше...")
                    current_scroll_y = scroll_sidebar_down(1, current_scroll_y)
                    steps_scrolled += 1
                else:
                    # Уже нашли позицию, но цена не подходит — обновляем и возвращаемся
                    print(f"  🔄 Обновляю позицию...")
                    current_scroll_y = refresh_and_scroll_to_position(steps_scrolled)
        
        # Пусто или мусор
        elif result == "empty" or result == "garbage":
            empty_count += 1
            reason = "пусто" if result == "empty" else "мусор"
            print(f"  📭 Область цен: {reason} ({empty_count}/6), скроллю сайдбар...")
            current_scroll_y = scroll_sidebar_down(1, current_scroll_y)
            steps_scrolled += 1
            if empty_count >= 6:
                print(f"  🔄 6 раз нет цен! ПЕРЕЗАПУСК...")
                main()
                return False, 0
        
        # Ошибка распознавания
        elif result is None:
            print("  ⚠️ Ошибка распознавания, обновляю...")
            current_scroll_y = refresh_and_scroll_to_position(steps_scrolled)
            empty_count = 0
        
        # Анализируем снова
        rgb, _ = get_screenshot()
        result = find_first_price(rgb)
        time.sleep(0.1)

def main():
    global WORKING
    print("=" * 50)
    print("⚡ БОТ STALCRAFT ⚡")
    print("=" * 50)
    print("F1 - СТОП")
    
    items = load_items()
    if not items:
        cnt = int(input('Сколько предметов: '))
        for i in range(cnt):
            name = input(f'Предмет {i+1}: ')
            price = int(input(f'Лимит для "{name}": '))
            items.append([name, price])
        save_items(items)
    
    print("\nСТАРТ через 3 сек...")
    time.sleep(3)
    
    initAuction()
    
    t = Thread(target=exit_check, daemon=True)
    t.start()
    
    # Словарь для хранения оптимальных позиций скролла
    optimal_scroll = {}
    
    print("\n" + "=" * 50)
    print("ПЕРВИЧНЫЙ ПОИСК")
    print("=" * 50)
    for name, limit in items:
        if not WORKING:
            break
        while WORKING:
            success, steps = search_and_buy(name, limit)
            if success:
                print(f"\n✅ {name} КУПЛЕН!")
                optimal_scroll[name] = steps
                print(f"📌 Оптимальный скролл для '{name}': {steps} шагов\n")
                break
            else:
                print(f"\n🔄 ПЕРЕЗАПУСК ДЛЯ: {name}\n")
                time.sleep(1)
    
    print("\n" + "=" * 50)
    print("БЕСКОНЕЧНЫЙ ЦИКЛ")
    print("=" * 50)
    print(f"📌 Оптимальные позиции: {optimal_scroll}")
    
    while WORKING:
        for name, limit in items:
            if not WORKING:
                break
            
            saved_steps = optimal_scroll.get(name, 0)
            print(f"\n🔄 {name} (оптимальный скролл: {saved_steps} шагов)")
            
            # 1. Нажимаем поиск и СРАЗУ скроллим на сохранённую позицию ОДНИМ движением
            current_scroll_y = refresh_and_scroll_to_position(saved_steps)
            steps_scrolled = saved_steps
            empty_count = 0
            
            # 2. ТЕПЕРЬ делаем первый анализ
            rgb, _ = get_screenshot()
            result = find_first_price(rgb)
            
            while WORKING:
                # Нормальная цена
                if result not in ["empty", "garbage", None]:
                    price, click_x, click_y = result
                    print(f"  📋 Цена: {price} (лимит {limit})")
                    
                    if price <= limit:
                        print(f"  ✅ ПОДХОДИТ! Покупаю...")
                        buy_full_process(click_x, click_y)
                        print(f"🎉 КУПИЛ {name} за {price}!")
                        
                        # После покупки: поиск + скролл на позицию ОДНИМ движением
                        current_scroll_y = refresh_and_scroll_to_position(saved_steps)
                        steps_scrolled = saved_steps
                    else:
                        print(f"  ❌ Цена {price} > {limit}, обновляю позицию...")
                        current_scroll_y = refresh_and_scroll_to_position(saved_steps)
                        steps_scrolled = saved_steps
                
                # Пусто или мусор
                elif result == "empty" or result == "garbage":
                    empty_count += 1
                    reason = "пусто" if result == "empty" else "мусор"
                    print(f"  📭 Область цен: {reason} ({empty_count}/6), скроллю сайдбар...")
                    current_scroll_y = scroll_sidebar_down(1, current_scroll_y)
                    steps_scrolled += 1
                    if empty_count >= 6:
                        print(f"  🔄 6 раз нет цен! ПЕРЕЗАПУСК...")
                        main()
                        return
                
                # Ошибка распознавания
                elif result is None:
                    print("  ⚠️ Ошибка распознавания, обновляю...")
                    current_scroll_y = refresh_and_scroll_to_position(saved_steps)
                    steps_scrolled = saved_steps
                    empty_count = 0
                
                # Следующий анализ
                rgb, _ = get_screenshot()
                result = find_first_price(rgb)
                time.sleep(0.1)
        time.sleep(0.05)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nСтоп")
    except Exception as e:
        print(f"Ошибка: {e}")
        traceback.print_exc()
