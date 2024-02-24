import os
import hashlib
import shutil
import concurrent.futures
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

class AdvancedDuplicateFileFinder:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Duplicate File Finder")
        self.root.geometry("800x500")
        self.root.configure(bg="#333333")

        self.main_frame = ttk.Frame(root, style="Dark.TFrame")
        self.main_frame.pack(expand=True, fill="both", padx=20, pady=20)

        ttk.Label(self.main_frame, text="Starting Path:", style="Dark.TLabel").grid(row=0, column=0, sticky="w", pady=5)
        self.starting_path_var = tk.StringVar()
        ttk.Entry(self.main_frame, textvariable=self.starting_path_var, width=50).grid(row=0, column=1, columnspan=2, sticky="ew", pady=5)
        ttk.Button(self.main_frame, text="Browse", command=self.browse_folder).grid(row=0, column=3, pady=5)

        ttk.Label(self.main_frame, text="Duplicates Folder:", style="Dark.TLabel").grid(row=1, column=0, sticky="w", pady=5)
        self.duplicates_folder_var = tk.StringVar()
        ttk.Entry(self.main_frame, textvariable=self.duplicates_folder_var, width=50).grid(row=1, column=1, columnspan=2, sticky="ew", pady=5)
        ttk.Button(self.main_frame, text="Browse", command=self.browse_duplicates_folder).grid(row=1, column=3, pady=5)

        self.delete_duplicates_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self.main_frame, text="Delete Duplicates", variable=self.delete_duplicates_var, style="Dark.TCheckbutton").grid(row=2, column=0, columnspan=4, pady=5)

        self.process_button = ttk.Button(self.main_frame, text="Start Scan", command=self.start_processing, style="Dark.TButton")
        self.process_button.grid(row=3, column=0, columnspan=4, pady=10)

        self.progress_var = tk.DoubleVar()
        ttk.Label(self.main_frame, text="Progress:", style="Dark.TLabel").grid(row=4, column=0, sticky="w", pady=5)
        self.progress_bar = ttk.Progressbar(self.main_frame, variable=self.progress_var, maximum=100, length=600, mode="determinate")
        self.progress_bar.grid(row=4, column=1, columnspan=3, sticky="ew", pady=5)

        self.results_listbox = tk.Listbox(self.main_frame, selectmode="extended", width=80, height=15)
        self.results_listbox.grid(row=5, column=0, columnspan=4, pady=10, padx=5, sticky="ew")
        self.results_listbox.bind("<Double-Button-1>", self.open_file)

        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(self.root, textvariable=self.status_var, anchor="w", style="Dark.TLabel")
        self.status_label.pack(side="bottom", fill="x")

        self.main_frame.bind("<Configure>", self.scale_text)

    def browse_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.starting_path_var.set(folder_path)

    def browse_duplicates_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.duplicates_folder_var.set(folder_path)

    def process_files(self, starting_path, duplicates_folder, delete_duplicates):
        try:
            files = []
            for root, dirs, filenames in os.walk(starting_path):
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    files.append(file_path)
            total_files = len(files)
            if total_files == 0:
                self.display_error("No files found in the specified directory.")
                return
            print("Total files:", total_files)  # Debug print
            duplicates_found = 0
            batch_size = 10  # Adjust the batch size as needed
            processed_files = 0
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = {executor.submit(self.process_file, file_path, duplicates_folder, delete_duplicates): file_path for file_path in files}
                for future in concurrent.futures.as_completed(futures):
                    duplicates_found += future.result()
                    processed_files += 1
                    if processed_files % batch_size == 0:
                        self.root.after(0, self.update_progress, duplicates_found, total_files)
            self.update_progress(duplicates_found, total_files)  # Update progress for remaining files
        except Exception as e:
            self.display_error(f"Error processing files: {e}")

    def process_file(self, file_path, duplicates_folder, delete_duplicates):
        try:
            with open(file_path, "rb") as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            if delete_duplicates:
                if os.path.exists(duplicates_folder):
                    os.remove(file_path)
            else:
                if not os.path.exists(duplicates_folder):
                    os.makedirs(duplicates_folder)
                shutil.move(file_path, os.path.join(duplicates_folder, os.path.basename(file_path)))
            self.results_listbox.insert(tk.END, file_path)  # Add file to results list
            return 1
        except Exception as e:
            return 0

    def start_processing(self):
        starting_path = self.starting_path_var.get()
        duplicates_folder = self.duplicates_folder_var.get()
        delete_duplicates = self.delete_duplicates_var.get()

        if not starting_path:
            self.display_error("Please select a starting path.")
            return
        if not os.path.exists(starting_path):
            self.display_error("Starting path does not exist.")
            return
        if delete_duplicates and not duplicates_folder:
            self.display_error("Please select a folder for duplicates.")
            return

        self.progress_var.set(0)
        self.update_status("Scanning...")
        concurrent.futures.ThreadPoolExecutor().submit(self.process_files, starting_path, duplicates_folder, delete_duplicates)

    def update_status(self, message):
        self.status_var.set(message)

    def update_progress(self, duplicates_found, total_files):
        if total_files > 0:
            progress_percentage = (duplicates_found / total_files) * 100
            self.progress_var.set(progress_percentage)
            self.update_status(f"Scanning completed. Duplicates Found: {duplicates_found}")
        else:
            self.display_error("Total files count is zero.")

    def display_error(self, message):
        messagebox.showerror("Error", message)

    def scale_text(self, event):
        self.status_label.config(wraplength=self.root.winfo_width()-20)

    def open_file(self, event):
        selected_indices = self.results_listbox.curselection()
        for index in selected_indices:
            file_path = self.results_listbox.get(index)
            os.startfile(file_path)  # Open selected file(s)

if __name__ == "__main__":
    root = tk.Tk()
    root.style = ttk.Style()
    root.style.theme_use("clam")
    root.style.configure("Dark.TFrame", background="#333333")
    root.style.configure("Dark.TLabel", background="#333333", foreground="white")
    root.style.configure("Dark.TEntry", background="#555555", foreground="white")
    root.style.map("Dark.TEntry", fieldbackground=[("readonly", "#555555"), ("focus", "#555555")])
    root.style.configure("Dark.TButton", background="#555555", foreground="white", font=("Helvetica", 10, "bold"))
    root.style.map("Dark.TButton", background=[("active", "#777777")])
    root.style.configure("Dark.TCheckbutton", background="#333333", foreground="white", font=("Helvetica", 10))
    app = AdvancedDuplicateFileFinder(root)
    root.mainloop()
