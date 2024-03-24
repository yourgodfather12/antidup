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

    def calculate_image_hash(self, file_path):
        """Calculate the perceptual hash value of an image."""
        try:
            hash_value = imagehash.average_hash(Image.open(file_path))
            return str(hash_value)
        except Exception as e:
            raise e

    def find_duplicates(self, folder_path):
        """Find duplicate images in the specified folder."""
        self.hashes = {}
        self.total_files = sum(len(files) for _, _, files in os.walk(folder_path))
        self.progress_counter = 0
        self.folder_path = folder_path

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []
            for root, _, filenames in os.walk(folder_path):
                for filename in filenames:
                    filepath = os.path.join(root, filename)
                    future = executor.submit(self.process_image, filepath)
                    futures.append(future)

            for future in concurrent.futures.as_completed(futures):
                try:
                    image_hash_value, filepath = future.result()
                    if image_hash_value in self.hashes:
                        self.hashes[image_hash_value].append(filepath)
                    else:
                        self.hashes[image_hash_value] = [filepath]

                    self.progress_counter += 1
                    self.update_progress_bar()
                except Exception as e:
                    self.log_error(e)

    def process_image(self, filepath):
        """Process a single image, calculating its hash value."""
        try:
            image_hash_value = self.calculate_image_hash(filepath)
            return image_hash_value, filepath
        except Exception as e:
            raise e

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
            image1 = Image.open(image1_path)
            image2 = Image.open(image2_path)
            hash1 = imagehash.average_hash(image1)
            hash2 = imagehash.average_hash(image2)
            similarity = hash1 - hash2
            return similarity
        except Exception as e:
            self.log_error(e)
            return 0  # Return 0 similarity in case of errors

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
        folder_path = values["-FOLDER-"]
        if folder_path:
            self.window["-STATUS-"].update("Scanning...")
            self.window["-FILE-CONTENT-"].update("")
            progress_bar = self.window["-PROGRESS-"]
            progress_bar.update_bar(0, 1)
            threading.Thread(target=self.find_duplicates, args=(folder_path,)).start()
        else:
            sg.popup("Please select a folder.")

    def handle_save(self, values):
        """Handle the save button click event."""
        filename = sg.popup_get_file("Save Duplicates List As:", save_as=True, default_extension=".txt")
        self.save_duplicates_list(filename)

    def handle_delete(self):
        """Handle the delete button click event."""
        self.delete_duplicates()

    def handle_move(self, values):
        """Handle the move button click event."""
        dest_folder = values["-DEST-FOLDER-"]
        self.move_duplicates(dest_folder)

    def build_gui(self):
        """Build the PySimpleGUI-based GUI."""
        sg.theme("DarkGrey13")

        layout = [
            [sg.Text("Select a folder to scan for images")],
            [sg.Input(key="-FOLDER-"), sg.FolderBrowse()],
            [sg.Button("Scan"), sg.Button("Cancel")],
            [sg.ProgressBar(100, orientation="h", size=(30, 20), key="-PROGRESS-")],
            [sg.Text("", size=(40, 1), key="-STATUS-")],
            [sg.Multiline(size=(60, 10), key="-FILE-CONTENT-")],
            [sg.Button("Save Duplicates", key="-SAVE-")],
            [sg.Button("Delete Duplicates", key="-DELETE-")],
            [sg.Button("Move Duplicates", key="-MOVE-"), sg.InputText(key="-DEST-FOLDER-", size=(40, 1)), sg.FolderBrowse(target="-DEST-FOLDER-")]
        ]

        window = sg.Window("Duplicate Images Finder", layout)
        self.window = window
        self.progress_bar = window["-PROGRESS-"]

        while True:
            event, values = window.read()

            if event == sg.WINDOW_CLOSED or event == "Cancel":
                break
            elif event == "Scan":
                self.handle_scan(values)
            elif event == "-SAVE-":
                self.handle_save(values)
            elif event == "-DELETE-":
                self.handle_delete()
            elif event == "-MOVE-":
                self.handle_move(values)

        window.close()

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
