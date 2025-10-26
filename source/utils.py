import os
import shutil

def cleanup_files(temp_file_path: str, temp_dir_path: str):
    """
    Safely removes the generated file and directory.
    This function will run in the background.
    """
    print(f"🧹 Background task: Cleaning up {temp_file_path} and {temp_dir_path}...")
    try:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            print(f"Removed file: {temp_file_path}")
        if os.path.exists(temp_dir_path):
            shutil.rmtree(temp_dir_path) # Use shutil.rmtree to delete a directory and its contents
            print(f"Removed directory: {temp_dir_path}")
        print("✨ Cleanup complete.")
    except Exception as e:
        print(f"Error during cleanup: {e}")