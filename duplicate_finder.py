import PySimpleGUI as sg
import os
import concurrent.futures
from PIL import Image
import imagehash
import shutil
import threading
from datetime import datetime

class DuplicateFinder:
    def __init__(self):
        self.hashes = {}
        self.duplicates = {}
        self.progress_counter = 0
        self.total_files = 0
        self.folder_path = ""
        self.threshold = 10  # Adjust threshold as needed
        self.progress_bar = None
        self.window = None
        self.scanning = False
        self.scan_thread = None

    def calculate_image_hash(self, file_path):
        """Calculate the perceptual hash value of an image."""
        try:
            with Image.open(file_path) as img:
                hash_value = imagehash.average_hash(img)
            return str(hash_value)
        except Exception as e:
            self.log_error(e)
            return None

    def find_duplicates(self, folder_path):
        """Find duplicate images in the specified folder."""
        self.hashes = {}
        self.total_files = sum(len(files) for _, _, files in os.walk(folder_path))
        self.progress_counter = 0
        self.folder_path = folder_path
        self.scanning = True

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(self.process_image, os.path.join(root, filename))
                for root, _, filenames in os.walk(folder_path)
                for filename in filenames
            ]

            for future in concurrent.futures.as_completed(futures):
                if not self.scanning:
                    break
                try:
                    result = future.result()
                    if result:
                        image_hash_value, filepath = result
                        if image_hash_value in self.hashes:
                            self.hashes[image_hash_value].append(filepath)
                        else:
                            self.hashes[image_hash_value] = [filepath]

                        self.progress_counter += 1
                        self.update_progress_bar()
                except Exception as e:
                    self.log_error(e)

        self.find_similar_images()

    def process_image(self, filepath):
        """Process a single image, calculating its hash value."""
        image_hash_value = self.calculate_image_hash(filepath)
        if image_hash_value:
            return image_hash_value, filepath
        return None

    def update_progress_bar(self):
        """Update the progress bar and status text."""
        try:
            progress_percentage = int(self.progress_counter / self.total_files * 100)
            self.progress_bar.update_bar(self.progress_counter, self.total_files)
            self.window["-STATUS-"].update(f"Scanning: {self.folder_path} ({progress_percentage}% complete)")
        except Exception as e:
            self.log_error(e)

    def log_error(self, error):
        """Log errors to a text file."""
        with open("error_log.txt", "a") as f:
            f.write(f"{datetime.now()} - {error}\n")

    def compare_images(self, image1_path, image2_path):
        """Compare two images and determine their similarity."""
        try:
            with Image.open(image1_path) as img1, Image.open(image2_path) as img2:
                hash1 = imagehash.average_hash(img1)
                hash2 = imagehash.average_hash(img2)
                similarity = hash1 - hash2
            return similarity
        except Exception as e:
            self.log_error(e)
            return float('inf')  # Return max similarity in case of errors

    def find_similar_images(self):
        """Find similar images based on perceptual hashing and image content."""
        self.duplicates = {}
        for hash_value, filepaths in self.hashes.items():
            if len(filepaths) > 1:
                for i, filepath1 in enumerate(filepaths):
                    for filepath2 in filepaths[i+1:]:
                        similarity = self.compare_images(filepath1, filepath2)
                        if similarity <= self.threshold:
                            if hash_value in self.duplicates:
                                self.duplicates[hash_value].append((filepath1, filepath2))
                            else:
                                self.duplicates[hash_value] = [(filepath1, filepath2)]

        self.display_duplicates()

    def delete_duplicates(self):
        """Delete duplicate images."""
        for files_list in self.duplicates.values():
            for filepath1, filepath2 in files_list:
                try:
                    os.remove(filepath2)  # Delete the second file
                    sg.Print(f"Deleted: {filepath2}")
                except Exception as e:
                    self.log_error(e)
                    sg.Print(f"Failed to delete: {filepath2}")

    def move_duplicates(self, dest_folder):
        """Move duplicate images to a specified destination folder."""
        for files_list in self.duplicates.values():
            for filepath1, filepath2 in files_list:
                try:
                    shutil.move(filepath2, dest_folder)
                    sg.Print(f"Moved: {filepath2} to {dest_folder}")
                except Exception as e:
                    self.log_error(e)
                    sg.Print(f"Failed to move: {filepath2}")

    def handle_scan(self, values):
        """Handle the scan button click event."""
        if self.scanning:
            sg.popup("Scan is already in progress!")
            return

        folder_path = values["-FOLDER-"]
        if folder_path:
            self.window["-STATUS-"].update("Scanning...")
            self.window["-FILE-CONTENT-"].update("")
            self.progress_bar.update_bar(0, 1)
            self.scan_thread = threading.Thread(target=self.find_duplicates, args=(folder_path,))
            self.scan_thread.start()
        else:
            sg.popup("Please select a folder.")

    def handle_save(self, values):
        """Handle the save button click event."""
        filename = sg.popup_get_file("Save Duplicates List As:", save_as=True, default_extension=".txt")
        if filename:
            self.save_duplicates_list(filename)

    def handle_delete(self):
        """Handle the delete button click event."""
        self.delete_duplicates()

    def handle_move(self, values):
        """Handle the move button click event."""
        dest_folder = values["-DEST-FOLDER-"]
        if dest_folder:
            self.move_duplicates(dest_folder)
        else:
            sg.popup("Please select a destination folder.")

    def handle_pause(self):
        """Handle the pause button click event."""
        if self.scanning:
            self.scanning = False
            self.window["-STATUS-"].update("Scan paused.")

    def handle_resume(self, values):
        """Handle the resume button click event."""
        if not self.scanning and self.scan_thread and self.scan_thread.is_alive():
            self.scanning = True
            self.window["-STATUS-"].update("Resuming scan...")
            self.scan_thread = threading.Thread(target=self.find_duplicates, args=(self.folder_path,))
            self.scan_thread.start()

    def display_duplicates(self):
        """Display the list of duplicate files in the GUI."""
        duplicates_text = ""
        for files_list in self.duplicates.values():
            for filepath1, filepath2 in files_list:
                duplicates_text += f"{filepath1}\n{filepath2}\n\n"
        self.window["-FILE-CONTENT-"].update(duplicates_text)

    def build_gui(self):
        """Build the PySimpleGUI-based GUI."""
        sg.theme("DarkGrey13")

        layout = [
            [sg.Text("Select a folder to scan for images")],
            [sg.Input(key="-FOLDER-"), sg.FolderBrowse()],
            [sg.Button("Scan"), sg.Button("Pause"), sg.Button("Resume"), sg.Button("Cancel")],
            [sg.ProgressBar(100, orientation="h", size=(30, 20), key="-PROGRESS-")],
            [sg.Text("", size=(40, 1), key="-STATUS-")],
            [sg.Multiline(size=(60, 10), key="-FILE-CONTENT-")],
            [sg.Button("Save Duplicates", key="-SAVE-")],
            [sg.Button("Delete Duplicates", key="-DELETE-")],
            [sg.Button("Move Duplicates"), sg.InputText(key="-DEST-FOLDER-", size=(40, 1)), sg.FolderBrowse(target="-DEST-FOLDER-")]
        ]

        self.window = sg.Window("Duplicate Images Finder", layout)
        self.progress_bar = self.window["-PROGRESS-"]

        while True:
            event, values = self.window.read()

            if event == sg.WINDOW_CLOSED or event == "Cancel":
                if self.scanning:
                    self.scanning = False
                    self.scan_thread.join()
                break
            elif event == "Scan":
                self.handle_scan(values)
            elif event == "Pause":
                self.handle_pause()
            elif event == "Resume":
                self.handle_resume(values)
            elif event == "-SAVE-":
                self.handle_save(values)
            elif event == "-DELETE-":
                self.handle_delete()
            elif event == "-MOVE-":
                self.handle_move(values)

        self.window.close()

    def save_duplicates_list(self, filename):
        """Save the list of duplicate images to a text file."""
        if filename:
            with open(filename, "w") as f:
                f.write("Duplicate Images List:\n\n")
                for files_list in self.duplicates.values():
                    for filepath1, filepath2 in files_list:
                        f.write(f"{filepath1}\n{filepath2}\n\n")
            sg.popup("Duplicates list saved successfully!")

if __name__ == "__main__":
    finder = DuplicateFinder()
    finder.build_gui()
