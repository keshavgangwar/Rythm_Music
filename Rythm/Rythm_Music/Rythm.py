import dearpygui.dearpygui as dpg
import ntpath
import json
from mutagen.mp3 import MP3
from tkinter import Tk, filedialog
import threading
import pygame
import time
import random
import os
import atexit

# Initialize Dear PyGui context and Pygame mixer
dpg.create_context()
dpg.create_viewport(title="Rythm Music", large_icon="icon.ico", small_icon="icon.ico")
pygame.mixer.init()

# Global variables
global state
state = None
global no
no = 0
_DEFAULT_MUSIC_VOLUME = 0.5
pygame.mixer.music.set_volume(_DEFAULT_MUSIC_VOLUME)

# Function to update volume based on slider input
def update_volume(sender, app_data):
    pygame.mixer.music.set_volume(app_data / 100.0)

# Load existing songs from JSON database
def load_database():
    songs = json.load(open("data/songs.json", "r+"))["songs"]
    for filename in songs:
        dpg.add_button(label=f"{ntpath.basename(filename)}", callback=play, width=-1,
                       height=25, user_data=filename.replace("\\", "/"), parent="list")
        dpg.add_spacer(height=2, parent="list")

# Update JSON database with new song
def update_database(filename: str):
    data = json.load(open("data/songs.json", "r+"))
    if filename not in data["songs"]:
        data["songs"] += [filename]
    json.dump(data, open("data/songs.json", "r+"), indent=4)

# Update slider position during playback
def update_slider():
    global state
    while pygame.mixer.music.get_busy() or state != 'paused':
        dpg.configure_item(item="pos", default_value=pygame.mixer.music.get_pos() / 1000)
        time.sleep(0.7)
    state = None
    dpg.configure_item("cstate", default_value=f"State: None")
    dpg.configure_item("csong", default_value="Now Playing : ")
    dpg.configure_item("play", label="Play")
    dpg.configure_item(item="pos", max_value=100)
    dpg.configure_item(item="pos", default_value=0)

# Play selected song
def play(sender, app_data, user_data):
    global state, no
    if user_data:
        no = user_data
        pygame.mixer.music.load(user_data)
        audio = MP3(user_data)
        dpg.configure_item(item="pos", max_value=audio.info.length)
        pygame.mixer.music.play()
        thread = threading.Thread(target=update_slider, daemon=False)
        thread.start()
        if pygame.mixer.music.get_busy():
            dpg.configure_item("play", label="Pause")
            state = "playing"
            dpg.configure_item("cstate", default_value=f"State: Playing")
            dpg.configure_item("csong", default_value=f"Now Playing : {ntpath.basename(user_data)}")

# Toggle play/pause functionality
def play_pause():
    global state, no
    if state == "playing":
        state = "paused"
        pygame.mixer.music.pause()
        dpg.configure_item("play", label="Play")
        dpg.configure_item("cstate", default_value=f"State: Paused")
    elif state == "paused":
        state = "playing"
        pygame.mixer.music.unpause()
        dpg.configure_item("play", label="Pause")
        dpg.configure_item("cstate", default_value=f"State: Playing")
    else:
        songs = json.load(open("data/songs.json", "r"))["songs"]
        if songs:
            song = random.choice(songs)
            no = song
            pygame.mixer.music.load(song)
            pygame.mixer.music.play()
            thread = threading.Thread(target=update_slider, daemon=False)
            thread.start()
            dpg.configure_item("play", label="Pause")
            if pygame.mixer.music.get_busy():
                audio = MP3(song)
                dpg.configure_item(item="pos", max_value=audio.info.length)
                state = "playing"
                dpg.configure_item("csong", default_value=f"Now Playing : {ntpath.basename(song)}")
                dpg.configure_item("cstate", default_value=f"State: Playing")

# Play previous song
def pre():
    global state, no
    songs = json.load(open('data/songs.json', 'r'))["songs"]
    try:
        n = songs.index(no)
        if n == 0:
            n = len(songs)
        play(sender=None, app_data=None, user_data=songs[n - 1])
    except:
        pass

# Play next song
def next():
    global state, no
    try:
        songs = json.load(open('data/songs.json', 'r'))["songs"]
        n = songs.index(no)
        if n == len(songs) - 1:
            n = -1
        play(sender=None, app_data=None, user_data=songs[n + 1])
    except:
        pass

# Stop playback
def stop():
    global state
    pygame.mixer.music.stop()
    state = None

# Add single file to database
def add_files():
    data = json.load(open("data/songs.json", "r"))
    root = Tk()
    root.withdraw()
    filename = filedialog.askopenfilename(filetypes=[("Music Files", ("*.mp3", "*.wav", "*.ogg"))])
    root.quit()
    if filename.endswith(".mp3" or ".wav" or ".ogg"):
        if filename not in data["songs"]:
            update_database(filename)
            dpg.add_button(label=f"{ntpath.basename(filename)}", callback=play, width=-1, height=25, user_data=filename.replace("\\", "/"), parent="list")
            dpg.add_spacer(height=2, parent="list")

# Add entire folder to database
def add_folder():
    data = json.load(open("data/songs.json", "r"))
    root = Tk()
    root.withdraw()
    folder = filedialog.askdirectory()
    root.quit()
    for filename in os.listdir(folder):
        if filename.endswith(".mp3" or ".wav" or ".ogg"):
            if filename not in data["songs"]:
                update_database(os.path.join(folder, filename).replace("\\", "/"))
                dpg.add_button(label=f"{ntpath.basename(filename)}", callback=play, width=-1, height=25, user_data=os.path.join(folder, filename).replace("\\", "/"), parent="list")
                dpg.add_spacer(height=2, parent="list")

# Search for songs in database
def search(sender, app_data, user_data):
    songs = json.load(open("data/songs.json", "r"))["songs"]
    dpg.delete_item("list", children_only=True)
    for index, song in enumerate(songs):
        if app_data in song.lower():
            dpg.add_button(label=f"{ntpath.basename(song)}", callback=play, width=-1, height=25, user_data=song, parent="list")
            dpg.add_spacer(height=2, parent="list")

# Remove all songs from database
def removeall():
    songs = json.load(open("data/songs.json", "r"))
    songs["songs"].clear()
    json.dump(songs, open("data/songs.json", "w"), indent=4)
    dpg.delete_item("list", children_only=True)
    load_database()

# Shuffle songs in database
def shuffle():
    songs = json.load(open("data/songs.json", "r"))["songs"]
    if songs:
        random.shuffle(songs)
        dpg.delete_item("list", children_only=True)
        for filename in songs:
            dpg.add_button(label=f"{ntpath.basename(filename)}", callback=play, width=-1,
                           height=25, user_data=filename.replace("\\", "/"), parent="list")
            dpg.add_spacer(height=2, parent="list")

# Dear PyGui theme and UI setup
with dpg.theme(tag="base"):
    with dpg.theme_component():
        dpg.add_theme_color(dpg.mvThemeCol_Button, (130, 142, 250))
        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (137, 142, 255, 95))
        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (137, 142, 255))
        dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 3)
        dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 4)
        dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 4, 4)
        dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 4, 4)
        dpg.add_theme_style(dpg.mvStyleVar_WindowTitleAlign, 0.50, 0.50)
        dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 0)
        dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 10, 14)
        dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (25, 25, 25))
        dpg.add_theme_color(dpg.mvThemeCol_Border, (0, 0, 0, 0))
        dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg, (0, 0, 0, 0))
        dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (130, 142, 250))
        dpg.add_theme_color(dpg.mvThemeCol_CheckMark, (221, 166, 185))
        dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (172, 174, 197))

with dpg.theme(tag="slider_thin"):
    with dpg.theme_component():
        dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (130, 142, 250, 99))
        dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (130, 142, 250, 99))
        dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, (255, 255, 255))
        dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, (255, 255, 255))
        dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (130, 142, 250, 99))
        dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 3)
        dpg.add_theme_style(dpg.mvStyleVar_GrabMinSize, 30)

with dpg.theme(tag="slider"):
    with dpg.theme_component():
        dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (130, 142, 250, 99))
        dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (130, 142, 250, 99))
        dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, (255, 255, 255))
        dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, (255, 255, 255))
        dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (130, 142, 250, 99))
        dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 3)
        dpg.add_theme_style(dpg.mvStyleVar_GrabMinSize, 30)

with dpg.theme(tag="songs"):
    with dpg.theme_component():
        dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 2)
        dpg.add_theme_color(dpg.mvThemeCol_Button, (89, 89, 144, 40))
        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (0, 0, 0, 0))

with dpg.font_registry():
    monobold = dpg.add_font("fonts/MonoLisa-Bold.ttf", 12)
    head = dpg.add_font("fonts/MonoLisa-Bold.ttf", 15)

# Main window and UI layout
with dpg.window(tag="main", label="Rythm Music Player"):
    with dpg.child_window(autosize_x=True, height=45, no_scrollbar=True):
        dpg.add_text(f"Now Playing : ", tag="csong")
    dpg.add_spacer(height=2)

    with dpg.group(horizontal=True):
        with dpg.child_window(width=200, tag="sidebar"):
            dpg.add_spacer(height=5)
            dpg.add_separator()
            dpg.add_spacer(height=5)
            dpg.add_button(label="Add File", width=-1, height=28, callback=add_files)
            dpg.add_button(label="Add Folder", width=-1, height=28, callback=add_folder)
            dpg.add_button(label="Remove All Songs", width=-1, height=28, callback=removeall)
            dpg.add_button(label="Shuffle", width=-1, height=28, callback=shuffle)
            dpg.add_spacer(height=5)
            dpg.add_separator()
            dpg.add_spacer(height=5)
            dpg.add_text(f"State: {state}", tag="cstate")
            dpg.add_spacer(height=5)
            dpg.add_separator()

        with dpg.child_window(autosize_x=True, border=False):
            with dpg.child_window(autosize_x=True, height=80, no_scrollbar=True):
                with dpg.group(horizontal=True):
                    with dpg.group(horizontal=True):
                        dpg.add_button(label="Play", width=65, height=30, tag="play", callback=play_pause)
                        dpg.add_button(label="Pre", width=65, height=30, show=True, tag="pre", callback=pre)
                        dpg.add_button(label="Next", tag="next", show=True, callback=next, width=65, height=30)
                        dpg.add_button(label="Stop", callback=stop, width=65, height=30)
                    dpg.add_slider_float(tag="volume", width=120, height=15, pos=(10, 59), format="%.0f%%", default_value=_DEFAULT_MUSIC_VOLUME * 100, callback=update_volume)
                    dpg.add_slider_float(tag="pos", width=-1, pos=(140, 59), format="", max_value=100)

            with dpg.child_window(autosize_x=True, delay_search=True):
                with dpg.group(horizontal=True, tag="query"):
                    dpg.add_input_text(hint="Search for a song", width=-1, callback=search)
                dpg.add_spacer(height=5)
                with dpg.child_window(autosize_x=True, delay_search=True, tag="list"):
                    load_database()

# Theme and font bindings
dpg.bind_item_theme("volume", "slider_thin")
dpg.bind_item_theme("pos", "slider")
dpg.bind_item_theme("list", "songs")
dpg.bind_theme("base")
dpg.bind_font(monobold)

# Function to safely exit the application
def safe_exit():
    pygame.mixer.music.stop()
    pygame.quit()

# Register safe exit function
atexit.register(safe_exit)

# Setup Dear PyGui and display viewport
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_primary_window("main", True)
dpg.maximize_viewport()

# Start Dear PyGui event loop
dpg.start_dearpygui()
dpg.destroy_context()
