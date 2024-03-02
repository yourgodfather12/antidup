import PySimpleGUI as sg
import hashlib
import os
import concurrent.futures
from difflib import SequenceMatcher
from datetime import datetime
import shutil

def file_hash(file_path, block_size=65536, algorithm='sha256'):
    """Calculate the hash value of a file."""
    hash_func = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for block in iter(lambda: f.read(block_size), b''):
            hash_func.update(block)
    return hash_func.hexdigest()

def find_duplicates(folder_path, algorithm, progress_callback, window):
    """Find duplicate files in the specified folder."""
    hashes = {}
    total_files = sum(len(files) for _, _, files in os.walk(folder_path))
    progress_counter = 0

    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = []
        for root, _, filenames in os.walk(folder_path):
            for filename in filenames:
                filepath = os.path.join(root, filename)
                future = executor.submit(process_file, filepath, algorithm)
                futures.append(future)

        for future in concurrent.futures.as_completed(futures):
            try:
                file_hash_value, filepath = future.result()
                if file_hash_value in hashes:
                    hashes[file_hash_value].append(filepath)
                else:
                    hashes[file_hash_value] = [filepath]

                progress_counter += 1
                progress_callback(progress_counter, total_files, filepath, window)
            except Exception as e:
                log_error(e)

    return hashes

def process_file(filepath, algorithm):
    """Process a single file, calculating its hash value."""
    try:
        file_hash_value = file_hash(filepath, algorithm=algorithm)
        return file_hash_value, filepath
    except Exception as e:
        raise e

def update_progress_bar(progress_counter, total_files, filepath, window):
    """Update the progress bar and status text."""
    try:
        progress_percentage = int(progress_counter / total_files * 100)
        window["-PROGRESS-"].update_bar(progress_counter, total_files)
        window["-STATUS-"].update(f"Scanning: {filepath} ({progress_percentage}% complete)")
    except Exception as e:
        log_error(e)

def log_error(error):
    """Log errors to a text file."""
    with open("error_log.txt", "a") as f:
        f.write(f"{datetime.now()} - {error}\n")

def compare_files(file1, file2):
    """Compare two files and calculate their similarity ratio."""
    with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
        content1 = f1.read()
        content2 = f2.read()
        similarity_ratio = SequenceMatcher(None, content1, content2).ratio()
    return similarity_ratio

def delete_duplicates(duplicates):
    """Delete duplicate files."""
    for files in duplicates.values():
        if len(files) > 1:
            # Keep the first file and delete the rest
            for filepath in files[1:]:
                try:
                    os.remove(filepath)
                    sg.Print(f"Deleted: {filepath}")
                except Exception as e:
                    log_error(e)
                    sg.Print(f"Failed to delete: {filepath}")

def move_duplicates(duplicates, dest_folder):
    """Move duplicate files to a specified destination folder."""
    for files in duplicates.values():
        if len(files) > 1:
            for filepath in files[1:]:
                try:
                    shutil.move(filepath, dest_folder)
                    sg.Print(f"Moved: {filepath} to {dest_folder}")
                except Exception as e:
                    log_error(e)
                    sg.Print(f"Failed to move: {filepath}")

def main():
    sg.theme("DarkGrey13")

    layout = [
        [sg.Text("Select a folder to scan for duplicates")],
        [sg.Input(key="-FOLDER-"), sg.FolderBrowse()],
        [sg.Text("Hashing Algorithm:"), sg.InputText(default_text="sha256", key="-ALGORITHM-")],
        [sg.Button("Scan"), sg.Button("Cancel")],
        [sg.ProgressBar(100, orientation="h", size=(30, 20), key="-PROGRESS-")],
        [sg.Text("", size=(40, 1), key="-STATUS-")],
        [sg.Multiline(size=(60, 10), key="-FILE-CONTENT-")],
        [sg.Button("Save Duplicates", key="-SAVE-")],
        [sg.Button("Delete Duplicates", key="-DELETE-")],
        [sg.Button("Move Duplicates", key="-MOVE-"), sg.InputText(key="-DEST-FOLDER-", size=(40, 1)), sg.FolderBrowse(target="-DEST-FOLDER-")]
    ]

    window = sg.Window("Duplicate Files Finder", layout)

    while True:
        event, values = window.read()

        if event == sg.WINDOW_CLOSED or event == "Cancel":
            break
        elif event == "Scan":
            folder_path = values["-FOLDER-"]
            algorithm = values["-ALGORITHM-"]
            if folder_path:
                window["-STATUS-"].update("Scanning...")
                window["-FILE-CONTENT-"].update("")
                progress_bar = window["-PROGRESS-"]
                progress_bar.update_bar(0, 1)
                duplicates = find_duplicates(folder_path, algorithm=algorithm, progress_callback=update_progress_bar, window=window)
                sg.Print("Scan Complete")
            else:
                sg.popup("Please select a folder.")

        elif event == "-SAVE-":
            filename = sg.popup_get_file("Save Duplicates List As:", save_as=True, default_extension=".txt")
            if filename:
                with open(filename, "w") as f:
                    f.write("Duplicates found:\n")
                    for files in duplicates.values():
                        if len(files) > 1:
                            f.write("\n".join(files))
                            f.write("\n\n")
                sg.popup("Duplicates list saved successfully!")

        elif event == "-DELETE-":
            delete_duplicates(duplicates)

        elif event == "-MOVE-":
            dest_folder = values["-DEST-FOLDER-"]
            move_duplicates(duplicates, dest_folder)

    window.close()

if __name__ == "__main__":
    main()
