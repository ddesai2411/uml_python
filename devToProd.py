import shutil
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime

def select_directory(title):
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    root.title(title)  # Set the title of the window

    directory = filedialog.askdirectory(title=title)

    return directory

def show_warning(message):
    return messagebox.askyesno("Warning", message)

def show_message(message):
    messagebox.showinfo("Message", message)

def ignore_pyc_files(directory, files):
    return {file for file in files if file.endswith(".ipynb")}

# Get new codebase folder and destination directory
newCodeSource = select_directory("Select the new codebase folder of New Version")
prodDir = select_directory("Select the directory where Production code is/Needs to be deployed")

# Backup path with timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
new_codebase_path = os.path.join(prodDir, os.path.basename(newCodeSource))
backup_folder_name = os.path.basename(new_codebase_path) + "_" + timestamp
backup_path = os.path.join(prodDir, 'BAK', backup_folder_name)


# Display a warning and get user confirmation
confirmation = show_warning("You are Copying the Codebase to Production Environment!!! \n Are you sure you want to proceed?")

if confirmation:
    try:
        if os.path.exists(new_codebase_path):
            # Create backup directory if it doesn't exist
            if not os.path.exists(backup_path):
                os.makedirs(backup_path)
            # Move the new codebase folder to the backup location
            shutil.move(new_codebase_path, backup_path)
            print(f"Backup of the previous version created at {backup_path}.")
            # Move the new codebase folder to the destination directory
            # shutil.copytree(newCodeSource, new_codebase_path)
            shutil.copytree(newCodeSource, new_codebase_path, ignore=ignore_pyc_files)
            print(f"New Version of the Codebase successfully deployed to {prodDir}.")

        else:
            # Move the new codebase folder to the destination directory
            # shutil.move(newCodeSource, new_codebase_path)
            shutil.copytree(newCodeSource, new_codebase_path, ignore=ignore_pyc_files)
            print(f'New Code Deployed to {prodDir}.')


    except Exception as e:
        print(f"An error occurred: {e}")
else:
    show_message("Deployment Terminated.")