import os
import hjson

# Function to get list of files in a folder
def get_files_in_folder_without_extension(folder_path):
    return [os.path.splitext(file)[0] for file in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, file))]

# Function to compare files in folder with a given list
def compare_files(folder_files, file_list):
    existing_files = [file for file in folder_files if file in file_list]
    new_files = [file for file in folder_files if file not in file_list]
    return existing_files, new_files

# Function to load the approved_symbols_long from the HJSON file
def load_approved_symbols_from_hjson(hjson_file_path):
    with open(hjson_file_path, 'r') as f:
        hjson_data = hjson.load(f)
    return hjson_data.get('approved_symbols_long', [])

# Example usage:
folder_path = '/Users/att/passivbot_configs/clock'  # Change to your folder path
hjson_file_path = '/Users/att/passivbot_configs/config_live_clock.hjson'  # Change to your HJSON file path

# Get the list of approved symbols from the HJSON file
file_list = load_approved_symbols_from_hjson(hjson_file_path)

# Get files in folder
folder_files = get_files_in_folder_without_extension(folder_path)

# Compare the files
existing_files, new_files = compare_files(folder_files, file_list)

# Display the result
print("Existing files:", existing_files)
print("New files that are not in the list:", new_files)
