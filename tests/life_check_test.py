import cv2
import mss
import numpy as np
life_check_template = cv2.imread('blueprints/life_check_area.png', cv2.IMREAD_GRAYSCALE)

LIFE_CHECK_AREA_X = 507
LIFE_CHECK_AREA_Y = 238
LIFE_CHECK_AREA_W = 96
LIFE_CHECK_AREA_H = 36

def is_life_check_area_visible():
    """Надёжная и быстрая проверка (2-3 мс)"""
    with mss.mss() as sct:
        monitor = {"top": LIFE_CHECK_AREA_Y, "left": LIFE_CHECK_AREA_X,
                   "width": LIFE_CHECK_AREA_W, "height": LIFE_CHECK_AREA_H}
        screenshot = sct.grab(monitor)
        screenshot_gray = cv2.cvtColor(np.array(screenshot), cv2.COLOR_BGR2GRAY)
    
    result = cv2.matchTemplate(screenshot_gray, life_check_template, cv2.TM_SQDIFF_NORMED)
    min_val, _, _, _ = cv2.minMaxLoc(result)
    return min_val < 0.1

for i in range(50):
    if is_life_check_area_visible():
        print("Аукцион открыт")
    else:
        print("Аукцион закрыт")
    time.sleep(2)
