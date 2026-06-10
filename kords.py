import pyautogui
import keyboard

print("Наведи мышь на ЛЕВЫЙ ВЕРХНИЙ УГОЛ первой цены и нажми F2")
keyboard.wait('f2')
x1, y1 = pyautogui.position()
print(f"Левая верхняя точка: X={x1}, Y={y1}")

print("Наведи мышь на ПРАВЫЙ НИЖНИЙ УГОЛ последней цены и нажми F2")
keyboard.wait('f2')
x2, y2 = pyautogui.position()
print(f"Правая нижняя точка: X={x2}, Y={y2}")

print(f"\nГотовые координаты:")
print(f"PRICE_AREA_X = {x1}")
print(f"PRICE_AREA_Y = {y1}")
print(f"PRICE_AREA_W = {x2 - x1}")
print(f"PRICE_AREA_H = {y2 - y1}")
