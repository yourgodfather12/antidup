import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import hashlib
import shutil
import mimetypes
import csv
from datetime import datetime
import concurrent.futures

import progress


def display_status(param, color):
    pass


def save_settings(filename):
    settings = {
        "starting_path": starting_path_var.get(),
        "duplicates_folder": duplicates_folder_var.get(),
        "min_size": min_size_var.get(),
        "max_size": max_size_var.get(),
        "delete_duplicates": delete_duplicates_var.get(),
        "file_types": file_types_var.get(),
        "exclude_file_types": exclude_file_types_var.get()
    }
    with open(filename, "w") as f:
        json.dump(settings, f)
    display_status("Settings saved successfully.", color="green")

def load_settings(filename):
    try:
        with open(filename, "r") as f:
            settings = json.load(f)
            starting_path_var.set(settings.get("starting_path", ""))
            duplicates_folder_var.set(settings.get("duplicates_folder", ""))
            min_size_var.set(settings.get("min_size", "0"))
            max_size_var.set(settings.get("max_size", "10240"))
            delete_duplicates_var.set(settings.get("delete_duplicates", False))
            file_types_var.set(settings.get("file_types", ""))
            exclude_file_types_var.set(settings.get("exclude_file_types", ""))
        display_status("Settings loaded successfully.", color="green")
    except Exception as e:
        display_status(f"Error loading settings: {e}", color="red")

def show_about():
    messagebox.showinfo("About", "Duplicate File Finder\nVersion 2.0\n\n© 2024 Your Company\nAll rights reserved.")

def browse_folder(entry_var):
    folder_path = filedialog.askdirectory()
    if folder_path:
        entry_var.set(folder_path)

def display_progress_details(current_file, total_duplicates):
    progress_details_label.config(text=f"Processing: {current_file} | Duplicates Found: {total_duplicates}")

def process_files_with_details(starting_path, duplicates_folder, min_size, max_size, delete_duplicates, file_types, exclude_file_types):
    try:
        progress_details_label.config(text="")
        hashes = {}
        total_duplicates = 0
        duplicate_files = []
        for root, dirs, files in os.walk(starting_path):
            for filename in files:
                file_path = os.path.join(root, filename)
                file_size = os.path.getsize(file_path)
                if min_size <= file_size <= max_size:
                    try:
                        file_type, _ = mimetypes.guess_type(file_path)
                        if file_type and (not file_types or any(ft.strip().lower() in file_type.lower() for ft in file_types.split(','))) and \
                                (not exclude_file_types or all(eft.strip().lower() not in file_type.lower() for eft in exclude_file_types.split(','))):
                            with open(file_path, "rb") as f:
                                file_hash = hashlib.sha256(f.read()).hexdigest()
                            if file_hash in hashes:
                                total_duplicates += 1
                                if delete_duplicates:
                                    os.remove(file_path)
                                else:
                                    duplicate_name = get_unique_filename(file_path, duplicates_folder)
                                    shutil.move(file_path, duplicate_name)
                                    duplicate_files.append((filename, file_size, root, duplicate_name))
                            else:
                                hashes[file_hash] = file_path
                    except Exception as e:
                        display_status(f"Error processing file: {e}", color="red")
                progress_var.set(progress)
                display_progress_details(file_path, total_duplicates)
        generate_report(duplicate_files)
        display_status("Done!", color="green")
    except Exception as e:
        display_status(f"Error processing files: {e}", color="red")

def get_unique_filename(file_path, duplicates_folder):
    base_name, ext = os.path.splitext(file_path)
    count = 1
    while True:
        new_name = f"{base_name}_{count}{ext}"
        if not os.path.exists(os.path.join(duplicates_folder, new_name)):
            return os.path.join(duplicates_folder, new_name)
        count += 1

def generate_report(duplicate_files):
    report_filename = "duplicate_report.csv"
    try:
        with open(report_filename, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Filename", "Size (bytes)", "Original Path", "Duplicate Path"])
            for filename, size, root, duplicate_name in duplicate_files:
                writer.writerow([filename, size, root, duplicate_name])
        display_status(f"Report saved as '{report_filename}'", color="green")
    except Exception as e:
        display_status(f"Error generating report: {e}", color="red")

def start_processing_with_details():
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.submit(process_files_with_details, starting_path_var.get(), duplicates_folder_var.get(), int(min_size_var.get()) * 1024, int(max_size_var.get()) * 1024, delete_duplicates_var.get(), file_types_var.get(), exclude_file_types_var.get())

root = tk.Tk()
root.title("Duplicate File Finder")
root.geometry("600x400")

main_frame = ttk.Frame(root)
main_frame.pack(expand=True, fill="both", padx=20, pady=20)

starting_path_label = ttk.Label(main_frame, text="Starting Path:")
starting_path_label.grid(row=0, column=0, sticky="w", pady=5)
starting_path_var = tk.StringVar()
starting_path_entry = ttk.Entry(main_frame, textvariable=starting_path_var, width=50)
starting_path_entry.grid(row=0, column=1, sticky="ew", pady=5)
ttk.Button(main_frame, text="Browse", command=lambda: browse_folder(starting_path_var)).grid(row=0, column=2, pady=5)

duplicates_folder_label = ttk.Label(main_frame, text="Duplicates Folder:")
duplicates_folder_label.grid(row=1, column=0, sticky="w", pady=5)
duplicates_folder_var = tk.StringVar()
duplicates_folder_entry = ttk.Entry(main_frame, textvariable=duplicates_folder_var, width=50)
duplicates_folder_entry.grid(row=1, column=1, sticky="ew", pady=5)
ttk.Button(main_frame, text="Browse", command=lambda: browse_folder(duplicates_folder_var)).grid(row=1, column=2, pady=5)

min_size_label = ttk.Label(main_frame, text="Minimum File Size (KB):")
min_size_label.grid(row=2, column=0, sticky="w", pady=5)
min_size_var = tk.StringVar(value="0")
min_size_entry = ttk.Entry(main_frame, textvariable=min_size_var, width=10)
min_size_entry.grid(row=2, column=1, sticky="w", pady=5)

max_size_label = ttk.Label(main_frame, text="Maximum File Size (KB):")
max_size_label.grid(row=2, column=2, sticky="w", pady=5)
max_size_var = tk.StringVar(value="10240")
max_size_entry = ttk.Entry(main_frame, textvariable=max_size_var, width=10)
max_size_entry.grid(row=2, column=3, sticky="w", pady=5)

file_types_label = ttk.Label(main_frame, text="Include File Types (comma-separated):")
file_types_label.grid(row=3, column=0, sticky="w", pady=5)
file_types_var = tk.StringVar()
file_types_entry = ttk.Entry(main_frame, textvariable=file_types_var, width=50)
file_types_entry.grid(row=3, column=1, columnspan=3, sticky="ew", pady=5)

exclude_file_types_label = ttk.Label(main_frame, text="Exclude File Types (comma-separated):")
exclude_file_types_label.grid(row=4, column=0, sticky="w", pady=5)
exclude_file_types_var = tk.StringVar()
exclude_file_types_entry = ttk.Entry(main_frame, textvariable=exclude_file_types_var, width=50)
exclude_file_types_entry.grid(row=4, column=1, columnspan=3, sticky="ew", pady=5)

delete_duplicates_var = tk.BooleanVar(value=False)
delete_duplicates_check = ttk.Checkbutton(main_frame, text="Delete Duplicates", variable=delete_duplicates_var)
delete_duplicates_check.grid(row=5, column=0, columnspan=4, pady=5)

process_button = ttk.Button(main_frame, text="Process Files", command=start_processing_with_details)
process_button.grid(row=6, column=0, columnspan=4, pady=10)

progress_var = tk.IntVar()
progress_bar = ttk.Progressbar(main_frame, variable=progress_var, maximum=100)
progress_bar.grid(row=7, column=0, columnspan=4, pady=5, sticky="ew")

progress_details_label = ttk.Label(main_frame, text="")
progress_details_label.grid(row=8, column=0, columnspan=4, pady=5)

status_label = ttk.Label(main_frame, text="")
status_label.grid(row=9, column=0, columnspan=4, pady=5)

menu_bar = tk.Menu(root)
root.config(menu=menu_bar)

file_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Save Settings", command=lambda: save_settings("settings.json"))
file_menu.add_command(label="Load Settings", command=lambda: load_settings("settings.json"))
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root.quit)

help_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Help", menu=help_menu)
help_menu.add_command(label="About", command=show_about)

load_settings("settings.json")

root.mainloop()
