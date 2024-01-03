import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import os
import zipfile
import requests
import modio
import json
import wget

game_path_final = ""

def clear_window(window):
    for widget in window.winfo_children():
        widget.destroy()

def download_and_extract(destination_folder, tkwin):
    # Download the zip file
    tkwin.destroy()

    response = requests.get("https://github.com/LavaGang/MelonLoader/releases/download/v0.6.1/MelonLoader.x64.zip", stream=True)
    if response.status_code == 200:
        # Get the total size of the file
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024  # 1 KB chunk size

        # Save the zip file
        zip_file_path = os.path.join(destination_folder, "MelonLoader.x64.zip")
        with open(zip_file_path, "wb") as zip_file:
            # Create a Tkinter window for the progress bar
            progress_window = tk.Tk()
            progress_window.title("Download Progress")
            progress_window.geometry('400x300')
            
            pb = ttk.Progressbar(progress_window, orient='horizontal', mode='determinate', length=280)
            pb.pack(pady=20)
            # Update the progress bar in the Tkinter window
            for data in response.iter_content(chunk_size=block_size):
                zip_file.write(data)
                downloaded_size = os.path.getsize(zip_file_path)
                percent_complete = (downloaded_size / total_size) * 100
                pb['value'] = int(round(percent_complete))
                progress_window.update()
                progress_window.update_idletasks()                

            progress_window.destroy()  # Close the progress window

        print("\nDownload complete.")
        # Extract the contents
        with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
            zip_ref.extractall(destination_folder)
        
        # Clean up: Remove the downloaded zip file
        os.remove(zip_file_path)
        
        print("Extraction complete.")
        open_mod_window()
    else:
        print(f"Failed to download the file. Status code: {response.status_code}")
        exit()


def get_game_folder():
    executable_name = "GodsOfGravity.exe"  # Replace with the actual executable name
    file_path = filedialog.askopenfilename(initialdir="/", title="Select Game Executable", filetypes=[("Executable files", "*.exe")])

    if file_path:
        # Check if the selected file has the desired executable name
        if os.path.basename(file_path) == executable_name:
            game_folder = os.path.dirname(file_path)
            game_folder_var.set(game_folder)
            print(f"Game folder: {game_folder}")
            path_window.destroy()  # Close the path window
            global game_path_final
            game_path_final = game_folder
            if os.path.exists(game_folder + r'\\MelonLoader'):
                print("Melon is already installed!")
                open_mod_window()
            else:
                print("Installing melon")
                window = tk.Tk()
                window.title("Install MelonLoader")
                window.geometry("400x300")
                label = tk.Label(window, text="Do you want to install MelonLoader?\n(Required for installing mods)")
                label.pack(pady=20)
                yes_button = tk.Button(window, text="Yes", command=lambda: download_and_extract(game_folder, window))
                no_button = tk.Button(window, text="No", command=lambda: exit())
                yes_button.pack(pady=5)
                no_button.pack(pady=5)
                window.mainloop()

        else:
            print(f"Selected file does not match the expected executable name: {executable_name}")

# Create dictionaries for quick lookup (global scope)
id_to_name = {}
name_to_id = {}

def open_mod_window():
    # Use the game_folder as needed, for example, to fetch mods
    # Use the game_folder as needed, for example, to fetch mods
    filters = modio.Filter()
    filters.like(name="[MelonLoader]*")
    mods_list = game.get_mods(filters=filters).results

    # Check the structure of the Mod object
    # Assuming that 'id' and 'name' are attributes of the Mod object
    mod_list = [{'id': mod.id, 'name': mod.name} for mod in mods_list]

    # Update global dictionaries
    global id_to_name, name_to_id
    id_to_name = {mod['id']: mod['name'] for mod in mod_list}
    name_to_id = {mod['name']: mod['id'] for mod in mod_list}

    # Create the mod window
    create_mod_window(mod_list)

# Function to create the mod window
def create_mod_window(mods):
    window = tk.Tk()
    window.title("Download Mods")
    window.geometry("400x300")
    top_text = tk.Label(window, text="Download some mods!")
    top_text.pack(padx=10, pady=15)
    for mod in mods:
        mod_name = str(mod["name"])
        mod_name.replace('[MelonLoader] ', '')
        print(mod_name)
        mod_button = tk.Button(window, text=mod_name, command=lambda name=mod['name']: on_name_click(name, window))
        mod_button.pack(pady=10, padx=5)  # Add vertical padding between buttons

    window.mainloop()

def on_name_click(mod_name, window):
    clear_window(window)
    mod_id = name_to_id.get(mod_name, "Not found")
    print(f"Mod ID clicked for {mod_name}: {mod_id}")
    r = requests.get(f'https://g-5003.modapi.io/v1/games/5003/mods/{mod_id}/files', params={'api_key' : game_key}, headers = {'Accept' : 'application/json'})
    #print(json.dumps(r.json(), indent=4))
    r = r.json()
    binary_url = r['data'][0]['download']['binary_url']
    print(binary_url)
    print(game_path_final)
    def download_mod(url, mod_path, window):
        clear_window(window)
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            total_size = int(response.headers.get('content-length', 0))
            pb = ttk.Progressbar(window, orient='horizontal', mode='determinate', length=280)
            pb.pack(pady=20)
            pb['value'] = 0
            with open(mod_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=128):
                    file.write(chunk)
                    download_size = os.path.getsize(mod_path)
                    percent_complete = (download_size / total_size) * 100
                    pb['value'] = int(round(percent_complete))
                    window.update()
                    window.update_idletasks()
        popup = tk.Toplevel(window)
        popup.title("Complete")

        label = tk.Label(popup, text="Install Complete!")
        label.pack(padx=20, pady=20)
        def close_press():
            window.destroy()

        close_button = tk.Button(popup, text="Close", command=lambda: close_press())
        close_button.pack(pady=10)
        popup.mainloop()
                
        with zipfile.ZipFile(mod_path, "r") as zip_ref:
            zip_ref.extractall(os.path.join(game_path_final))
        os.remove(mod_path)
        open_mod_window()

    def back_but():
        window.destroy()
        open_mod_window()

    download_button = tk.Button(window, text="Download", command=lambda: download_mod(binary_url, os.path.join(game_path_final + f"\\Mods\\{mod_name}.zip"), window))
    back_button = tk.Button(window, text="Back", command=lambda: back_but())
    download_button.pack(padx=5, pady=5)
    back_button.pack(padx=5, pady=5)


game_key = 'INSERT GAME KEY HERE '

client = modio.Client(api_key=game_key)
game = client.get_game(5003)

# Create the main window to get the game path
path_window = tk.Tk()
path_window.geometry("400x300")
path_window.title("Game Path Window")

game_folder_var = tk.StringVar()

label = tk.Label(path_window, text="Select the game executable:")
label.pack(pady=20)

browse_button = tk.Button(path_window, text="Browse", command=get_game_folder)
browse_button.pack(pady=10)

path_window.mainloop()
