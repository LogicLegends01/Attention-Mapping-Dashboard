import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from pynput import keyboard, mouse
import pygetwindow as gw
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import seaborn as sns
import numpy as np
from plyer import notification as ns

# Data Storage

keyboard_events = 0
mouse_events = 0
last_activity = time.time()

attention_levels = []
window_switches = []
current_window = ""

running = False
tracking_thread_started = False

# time tracking
window_time_data = {}          
window_enter_time = None     

# distraction tracking
last_distraction_window = ""
distraction_keywords = [
    "instagram",
    "youtube",
    "whatsapp",
    "twitter",
    "x"
]


# Keyboard Listener


def on_key_press(key):
    global keyboard_events, last_activity
    keyboard_events += 1
    last_activity = time.time()

keyboard_listener = keyboard.Listener(on_press=on_key_press)
keyboard_listener.start()

# Mouse Listener

def on_move(x, y):
    global mouse_events, last_activity
    mouse_events += 1
    last_activity = time.time()

mouse_listener = mouse.Listener(on_move=on_move)
mouse_listener.start()

# Window Tracking

def get_active_window():
    try:
        window = gw.getActiveWindow()
        if window and window.title:
            return window.title
    except:
        pass
    return "Unknown Window"

# Distraction Detection

def is_distracting_window(window_title):
    title = window_title.lower()

    if "twitter" in title:
        return True

    x_patterns = [" x ", " on x", "x.com"]
    if any(p in title for p in x_patterns):
        return True

    for keyword in ["instagram", "youtube", "whatsapp"]:
        if keyword in title:
            return True

    return False


def show_distraction_notification(window_title):
    def popup():
        ns.notify(
            title="Attention Tracker",
            message="Attention Shift Detected"
        )
        
    root.after(0, popup)

# Time Formatting

def format_seconds(seconds):
    seconds = int(seconds)
    hrs = seconds // 3600
    mins = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hrs:02d}:{mins:02d}:{secs:02d}"

# Time Spent UI Update

def update_time_spent_box():
    time_box.delete(0, tk.END)

    sorted_data = sorted(window_time_data.items(), key=lambda x: x[1], reverse=True)

    for window_name, seconds in sorted_data:
        time_box.insert(tk.END, f"{window_name}  -->  {format_seconds(seconds)}")

# Heatmap Update

def update_heatmap():
    if len(attention_levels) == 0:
        return

    data = np.array(attention_levels).reshape(1, -1)

    fig.clear()
    ax = fig.add_subplot(111)

    sns.heatmap(
        data,
        cmap="YlOrRd",
        cbar=True,
        xticklabels=False,
        yticklabels=["Attention"],
        ax=ax
    )

    ax.set_title("Attention Heatmap")
    canvas.draw()

# Attention Analyzer

def analyze_attention():
    global keyboard_events, mouse_events
    global attention_levels, current_window, window_enter_time
    global last_distraction_window, running

    current_window = get_active_window()
    window_enter_time = time.time()
    

    while running:
        time.sleep(10)

        if not running:
            break 

       
        activity_score = keyboard_events + mouse_events
        idle = time.time() - last_activity

        if idle > 5:
            level = 0
        elif activity_score < 5:
            level = 1
        elif activity_score < 15:
            level = 2
        else:
            level = 3 

        attention_levels.append(level)

        keyboard_events = 0
        mouse_events = 0

        
        new_window = get_active_window()
        now = time.time()

        if new_window != current_window:
            if current_window:
                spent = now - window_enter_time
                window_time_data[current_window] = window_time_data.get(current_window, 0) + spent

            switch_text = f"{time.strftime('%H:%M:%S')} : {current_window}  -->  {new_window}"
            window_switches.append(switch_text)
            root.after(0, lambda text=switch_text: window_box.insert(tk.END, text))

            current_window = new_window
            window_enter_time = now

            if is_distracting_window(new_window):
                if last_distraction_window != new_window:
                    last_distraction_window = new_window
                    show_distraction_notification(new_window)
            else:
                last_distraction_window = ""

        else:
            
            if current_window:
                window_time_data[current_window] = window_time_data.get(current_window, 0) + 10

        root.after(0, update_time_spent_box)
        root.after(0, update_heatmap)

# Start / Stop

def start_tracking():
    global running, tracking_thread_started, current_window, window_enter_time

    if running:
        return

    running = True
    status_label.config(text="Status: Running")

    current_window = get_active_window()
    window_enter_time = time.time()

    thread = threading.Thread(target=analyze_attention, daemon=True)
    thread.start()
    tracking_thread_started = True

def stop_tracking():
    global running, current_window, window_enter_time

    if not running:
        return 

    running = False

    if current_window and window_enter_time:
        spent = time.time() - window_enter_time
        window_time_data[current_window] = window_time_data.get(current_window, 0) + spent
        update_time_spent_box()

    status_label.config(text="Status: Stopped")

# UI Setup

root = tk.Tk()
root.title("Attention Mapping Dashboard")
root.geometry("1000x750")

# Buttons
btn_frame = tk.Frame(root)
btn_frame.pack(pady=10)

start_btn = tk.Button(btn_frame, text="Start Tracking", command=start_tracking)
start_btn.pack(side=tk.LEFT, padx=10)

stop_btn = tk.Button(btn_frame, text="Stop Tracking", command=stop_tracking)
stop_btn.pack(side=tk.LEFT, padx=10)

# Heatmap Figure
fig, ax = plt.subplots(figsize=(8, 2))
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(pady=10)

# Window Switches
switch_label = tk.Label(root, text="Window Switches")
switch_label.pack()

window_box = tk.Listbox(root, height=10, width=120)
window_box.pack(pady=5)

# Time Spent
time_label = tk.Label(root, text="Time Spent on Different Tabs / Windows")
time_label.pack()

time_box = tk.Listbox(root, height=12, width=120)
time_box.pack(pady=5)

# Status
status_label = tk.Label(root, text="Status: Idle")
status_label.pack(pady=10)

root.mainloop()