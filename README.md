This Python script helps users identify and manage duplicate files within a specified folder. It calculates the hash value of each file to compare them efficiently and provides options to either delete or move duplicate files.

Features
Scan a folder for duplicate files.
Choose the hashing algorithm for file comparison.
Save a list of duplicate files to a text file.
Delete duplicate files directly from the folder.
Move duplicate files to a specified destination folder.
Usage
Run the script.
Select the folder you want to scan for duplicates.
Choose a hashing algorithm (default is sha256).
Click "Scan" to start the process.
After the scan completes, you can choose to save, delete, or move duplicate files.
Requirements
Python 3.x
PySimpleGUI (install via pip install PySimpleGUI)
difflib (comes pre-installed with Python)
How It Works
The script calculates the hash value of each file using the specified algorithm.
It compares the hash values to identify duplicate files.
Users can choose to delete or move the duplicate files as per their preference.
Author
This script was created by [Your Name].

License
This project is licensed under the [license name] License - see the LICENSE.md file for details.

Feel free to customize any sections according to your preferences and requirements!
