import subprocess
import time
import os
import sys
import ctypes

RESTART_SIGNAL_FILE = "restart_signal.txt"

def restore_game():
    """Разворачивает окно игры"""
    try:
        hwnd = ctypes.windll.user32.FindWindowW(None, 'STALCRAFT')
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            ctypes.windll.user32.SetForegroundWindow(hwnd)
            time.sleep(0.5)
            return True
    except:
        pass
    return False

def minimize_game():
    """Сворачивает окно игры"""
    try:
        hwnd = ctypes.windll.user32.FindWindowW(None, 'STALCRAFT')
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 6)  # SW_MINIMIZE
            time.sleep(0.5)
            return True
    except:
        pass
    return False

def run_bot():
    """Запускает бота"""
    print("🚀 Запуск бота...")
    
    # Перед запуском разворачиваем игру
    restore_game()
    
    process = subprocess.Popen(
        [sys.executable, "main.py"],
        stdout=None,
        stderr=None,
        text=False
    )
    
    while True:
        if os.path.exists(RESTART_SIGNAL_FILE):
            os.remove(RESTART_SIGNAL_FILE)
            print("🔄 Получен сигнал перезапуска!")
            process.terminate()
            time.sleep(1)
            
            # Сворачиваем игру перед перезапуском
            print("📦 Сворачиваю игру...")
            minimize_game()
            time.sleep(1)
            
            return False
        
        if process.poll() is not None:
            break
        
        time.sleep(0.5)
    
    return True

def main():
    print("=" * 50)
    print("🛡️ НАДЗИРАТЕЛЬ БОТА")
    print("=" * 50)
    print("Надзиратель запущен. Бот будет перезапускаться при проблемах")
    print("Нажми Ctrl+C в этом окне для остановки")
    print("=" * 50)
    
    if os.path.exists(RESTART_SIGNAL_FILE):
        os.remove(RESTART_SIGNAL_FILE)
    
    restart_count = 0
    
    while True:
        try:
            print(f"\n📌 Запуск бота (перезапуск #{restart_count})")
            
            success = run_bot()
            
            if not success:
                restart_count += 1
                print(f"🔄 Перезапускаю бота... (всего: {restart_count})")
                time.sleep(2)
                continue
            
            print("✅ Бот завершил работу нормально")
            break
            
        except KeyboardInterrupt:
            print("\n🛑 Надзиратель остановлен")
            break
        except Exception as e:
            print(f"❌ Ошибка надзирателя: {e}")
            time.sleep(3)

if __name__ == "__main__":
    main()
