import tkinter as tk
from tkinter import filedialog
import os
import zipfile
import requests
import modio
from customtkinter import *
from lxml.html import fromstring, etree
from lxml import html
from PIL import Image
import io
import sys

game_path_final = ""

def on_closing(window):
    window.destroy()
    print("closing")
    sys.exit()

#wipes the window clean
def clear_window(window):
    for widget in window.winfo_children():
        widget.destroy()

#downloads and extracts MelonLoader into the game(if not already installed)
def download_and_extract(destination_folder, tkwin):
    tkwin.after(100, tkwin.destroy)

    response = requests.get("https://github.com/LavaGang/MelonLoader/releases/download/v0.6.1/MelonLoader.x64.zip", stream=True)
    if response.status_code == 200:
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024  

        zip_file_path = os.path.join(destination_folder, "MelonLoader.x64.zip")
        with open(zip_file_path, "wb") as zip_file:
            progress_window = CTk()
            progress_window.protocol("WM_DELETE_WINDOW", lambda: on_closing(progress_window))
            progress_window.title("Download Progress")
            progress_window.geometry('400x300')
            progress_window.resizable(False, False)
            
            pb = CTkProgressBar(progress_window, mode='determinate', orientation="horizontal")
            pb.pack(pady=20)
            for data in response.iter_content(chunk_size=block_size):
                zip_file.write(data)
                downloaded_size = os.path.getsize(zip_file_path)
                percent_complete = (downloaded_size / total_size)
                pb.set(percent_complete)
                progress_window.update()
                progress_window.update_idletasks()
            progress_window.after(100, progress_window.destroy())

        with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
            zip_ref.extractall(destination_folder)
        
        os.remove(zip_file_path)
        
        open_mod_window()
    else:
        print(f"Failed to download the file. Status code: {response.status_code}")
        exit()

#Creates a prompt for the GoG exe location
def get_game_folder():
    executable_name = "GodsOfGravity.exe"
    file_path = filedialog.askopenfilename(initialdir="/", title="Select Game Executable", filetypes=[("Executable files", "*.exe")])

    if file_path:
        if os.path.basename(file_path) == executable_name:
            game_folder = os.path.dirname(file_path)
            path_window.destroy()
            global game_path_final
            game_path_final = game_folder
            if os.path.exists(game_folder + r'\\MelonLoader'):
                open_mod_window()
            else:
                window = CTk()
                window.protocol("WM_DELETE_WINDOW", lambda: on_closing(window))
                window.title("Install MelonLoader")
                window.geometry("800x600")
                window.resizable(False, False)
                label = CTkLabel(window, text="Do you want to install MelonLoader?\n(Required for installing mods)")
                label.pack(pady=2, anchor="center")
                yes_button = CTkButton(window, text="Yes", command=lambda: download_and_extract(game_folder, window))
                no_button = CTkButton(window, text="No", command=lambda: exit())
                yes_button.pack(pady=5, anchor="center")
                no_button.pack(pady=5, anchor="center")
                window.mainloop()

        else:
            print(f"Selected file does not match the expected executable name: {executable_name}")

id_to_name = {}
name_to_id = {}

#A bit misleading, it gets all the mods that have the "MelonLoader Mod" and passes them to create_mod_menu
def open_mod_window():
    filters = modio.Filter().values_in(tags=["MelonLoader Mod"])
    mods_list = game.get_mods(filters=filters).results

    mod_list = [{'id': mod.id, 'name': mod.name} for mod in mods_list]

    global id_to_name, name_to_id
    id_to_name = {mod['id']: mod['name'] for mod in mod_list}
    name_to_id = {mod['name']: mod['id'] for mod in mod_list}

    create_mod_window(mod_list)

#Takes the mod list and creates a button out of each
def create_mod_window(mods):
    window = CTk()
    window.protocol("WM_DELETE_WINDOW", lambda: on_closing(window))
    window.title("Download Mods")
    window.geometry("800x600")
    window.resizable(False, False)
    scroll_frame = CTkScrollableFrame(window, label_text="Download some mods!", width=800, height=800)
    scroll_frame.pack(pady=5, padx=5)
    for mod in mods:
        mod_name = str(mod["name"])
        mod_button = CTkButton(scroll_frame, text=mod_name, command=lambda name=mod['name']: on_name_click(name, window))
        mod_button.pack(pady=5, padx=5)
    for x in range(20):
        CTkButton(scroll_frame, text=f"Dummy Mod {x + 1}").pack(pady=5, padx=5)
    window.mainloop()

#Handles mod installing
def on_name_click(mod_name, window):
    clear_window(window)
    mod_id = name_to_id.get(mod_name, "Not found")
    r = requests.get(f'https://g-5003.modapi.io/v1/games/5003/mods/{mod_id}/files', params={'api_key' : game_key}, headers = {'Accept' : 'application/json'})
    r = r.json()
    binary_url = r['data'][0]['download']['binary_url']
    def download_mod(url, mod_path, window):
        clear_window(window)
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            total_size = int(response.headers.get('content-length', 0))
            pb = CTkProgressBar(window, mode='determinate')
            pb.pack(pady=10)
            pb.set(0)
            folders = ["Mods", "Plugins", "UserLibs", "UserData"]
            for folder in folders:
                if not os.path.exists(os.path.join(game_path_final, folder)):
                    os.makedirs(os.path.join(game_path_final, folder))
            with open(mod_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=128):
                    file.write(chunk)
                    download_size = os.path.getsize(mod_path)
                    percent_complete = (download_size / total_size)
                    pb.set(percent_complete)
                    window.update()
                    window.update_idletasks()
            pb.set(1)
        popup = CTkToplevel(window)
        window.withdraw()
        popup.title("Complete")

        label = CTkLabel(popup, text="Install Complete!")
        label.pack(padx=20, pady=20, anchor="center")
        def close_press():
            window.destroy()

        close_button = CTkButton(popup, text="Close", command=lambda: close_press())
        close_button.pack(pady=10, padx=10, anchor="center")
        popup.mainloop()
                
        with zipfile.ZipFile(mod_path, "r") as zip_ref:
            zip_ref.extractall(os.path.join(game_path_final))
        os.remove(mod_path)
        open_mod_window()

    def back_butto():
        window.destroy()
        open_mod_window()
    mod = game.get_mod(mod_id)
    mod_desc = mod.description
    scroll_frame = CTkScrollableFrame(window, width=800, height=600)
    scroll_frame.pack(pady=5, padx=5, anchor="ne")
    mod_desc = fromstring(mod_desc).text_content()
    logo =  mod.logo.small
    response = requests.get(logo)
    response.raise_for_status()
    logo = io.BytesIO(response.content)
    logo_image = CTkImage(dark_image=Image.open(logo), light_image=Image.open(logo), size=(320, 180))
    CTkLabel(scroll_frame, text="", image=logo_image).pack(pady=20)
    desc = CTkLabel(scroll_frame, text=mod_desc, wraplength=550)
    desc.pack(pady=20)
    for i in mod.media.images:
        root = html.fromstring(str(i))
        dl_link = root.get("original")
        new_image = requests.get(dl_link)
        new_image.raise_for_status()
        root = io.BytesIO(new_image.content)
        final_image = CTkImage(dark_image=Image.open(root), light_image=Image.open(root), size=(320, 180))
        img_label = CTkLabel(scroll_frame, text="", image=final_image)
        img_label.pack(pady=5)
    download_button = CTkButton(scroll_frame, text="Download", command=lambda: download_mod(binary_url, os.path.join(game_path_final + f"/Mods/{mod_name}.zip"), window))
    back_button = CTkButton(window, text="Back", command=lambda: back_butto())
    download_button.pack()
    back_button.place(relx=0.01, rely=0.01, anchor="nw")
    window.mainloop()


game_key = 'PUT API KEY HERE'

client = modio.Client(api_key=game_key)
game = client.get_game(5003)

set_appearance_mode("dark")

path_window = CTk()
path_window.protocol("WM_DELETE_WINDOW", lambda: on_closing(path_window))
path_window.geometry("400x300")
path_window.resizable(False, False)
path_window.title("Game Path Window")

label = CTkLabel(path_window, text="Select the game executable:")
label.pack(pady=1)

browse_button = CTkButton(path_window, text="Browse", command=get_game_folder)
browse_button.pack(pady=5)

path_window.mainloop()
