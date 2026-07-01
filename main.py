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
    # Кликаем по центру экрана для фокуса
    screen_x = pyautogui.size().width // 2
    screen_y = pyautogui.size().height // 2
    pyautogui.click(screen_x, screen_y)
    time.sleep(0.2)
    
    # Двойное нажатие ESC
    pyautogui.press('esc')
    time.sleep(0.3)
    pyautogui.press('esc')
    time.sleep(0.3)
    
    # Открываем аукцион (английская P)
    for _ in range(3):
        pyautogui.press('P')
        time.sleep(0.2)
    
    # Ждём появления кнопки аукциона и кликаем
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
    searchClick()
    time.sleep(0.1)

def scroll_down_multi(amount=4):
    cx = pyautogui.size().width // 2
    cy = pyautogui.size().height // 2
    pyautogui.moveTo(cx, cy, duration=0)
    for _ in range(amount):
        pyautogui.scroll(-3)
        time.sleep(0.02)
    time.sleep(0.1)

def find_first_price(img_rgb):
    price_area = img_rgb[PRICE_AREA_Y:PRICE_AREA_Y+PRICE_AREA_H, 
                         PRICE_AREA_X:PRICE_AREA_X+PRICE_AREA_W]
    results = reader.readtext(price_area, detail=1, paragraph=False, allowlist='0123456789')
    if not results:
        return "empty"
    for (bbox, text, confidence) in results:
        digits = re.sub(r'[^0-9]', '', text)
        if digits:
            price = int(digits)
            if price < 1000 and len(text) > len(digits) + 1:
                price = price * 1000
            x1, y1 = bbox[0]
            x2, y2 = bbox[2]
            center_x = PRICE_AREA_X + (x1 + x2) // 2
            center_y = PRICE_AREA_Y + (y1 + y2) // 2
            print(f"    🔍 Цена: '{text}' -> {price}")
            return price, center_x, center_y
    return None

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
    searchClick()
    print("  🔄 Обновление")
    return True

def exit_check():
    global WORKING
    while WORKING:
        if keyboard.is_pressed("f1"):
            WORKING = False
            break
        time.sleep(0.01)

def search_and_buy(name, limit):
    print(f"\n🔍 ИЩУ: {name}")
    _, gray = get_screenshot()
    X, Y = imageRecognitionFast(templates['search'], gray)
    if X == 0 and Y == 0:
        print("  ❌ Кнопка поиска не найдена")
        send_restart_signal()
        return False
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
    empty_count = 0
    while WORKING:
        rgb, _ = get_screenshot()
        result = find_first_price(rgb)
        if result == "empty":
            empty_count += 1
            print(f"  📭 Нет цен ({empty_count}/6), скроллю...")
            scroll_down_multi(4)
            if empty_count >= 6:
                print(f"  🔄 6 раз нет цен! РЕСТАРТ")
                send_restart_signal()
                return False
            continue
        empty_count = 0
        if result is None:
            print("  ⚠️ Ошибка, обновляю...")
            refresh_auction()
            time.sleep(0.1)
            continue
        price, click_x, click_y = result
        print(f"  📋 Цена: {price} (лимит {limit})")
        if price <= limit:
            print(f"  ✅ ПОДХОДИТ! Покупаю...")
            buy_full_process(click_x, click_y)
            print(f"🎉 КУПИЛ {name} за {price}!")
            return True
        else:
            print(f"  ❌ Цена {price} > {limit}, ищу...")
            refresh_auction()
            time.sleep(0.1)
            continue

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
    
    # ОТКРЫВАЕМ АУКЦИОН (С ФОКУСИРОВКОЙ ОКНА)
    initAuction()
    
    t = Thread(target=exit_check, daemon=True)
    t.start()
    
    print("\n" + "=" * 50)
    print("ПЕРВИЧНЫЙ ПОИСК")
    print("=" * 50)
    for name, limit in items:
        if not WORKING:
            break
        while WORKING:
            success = search_and_buy(name, limit)
            if success:
                print(f"\n✅ {name} КУПЛЕН!\n")
                break
            else:
                print(f"\n🔄 ПЕРЕЗАПУСК ДЛЯ: {name}\n")
                time.sleep(1)
    
    print("\n" + "=" * 50)
    print("БЕСКОНЕЧНЫЙ ЦИКЛ")
    print("=" * 50)
    while WORKING:
        for name, limit in items:
            if not WORKING:
                break
            print(f"\n🔄 {name}")
            refresh_auction()
            time.sleep(0.1)
            empty_count = 0
            while WORKING:
                rgb, _ = get_screenshot()
                result = find_first_price(rgb)
                if result == "empty":
                    empty_count += 1
                    print(f"  📭 Нет цен ({empty_count}/6), скроллю...")
                    scroll_down_multi(4)
                    if empty_count >= 6:
                        print(f"  🔄 6 раз нет цен! РЕСТАРТ")
                        send_restart_signal()
                    continue
                empty_count = 0
                if result is None:
                    print("  ⚠️ Ошибка, обновляю...")
                    refresh_auction()
                    time.sleep(0.1)
                    continue
                price, click_x, click_y = result
                print(f"  📋 Цена: {price} (лимит {limit})")
                if price <= limit:
                    print(f"  ✅ ПОДХОДИТ! Покупаю...")
                    buy_full_process(click_x, click_y)
                    print(f"🎉 КУПИЛ {name} за {price}!")
                else:
                    print(f"  ❌ Цена {price} > {limit}, обновляю...")
                    refresh_auction()
                    time.sleep(0.1)
                    continue
        time.sleep(0.05)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nСтоп")
    except Exception as e:
        print(f"Ошибка: {e}")
        traceback.print_exc()
#я гей
