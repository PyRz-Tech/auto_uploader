import os
import time
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
import logging
from src.drive_utils import (
    upload_file,
    delete_file_from_drive,
    get_or_create_drive_folder
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
logger = logging.getLogger(__name__)

class Watcher(FileSystemEventHandler):
    """
    A file system watcher that monitors a folder and syncs changes with Google Drive.

    This class extends FileSystemEventHandler to monitor a specified local folder for
    file creation, modification, deletion, and movement events. It interacts with
    Google Drive using the provided service to upload, update, or delete files. The
    watcher maintains a mapping of local files to Google Drive file IDs and retrieves
    or creates a Google Drive folder ID for synchronization.

    Attributes:
        service (googleapiclient.discovery.Resource): Google Drive API service instance.
        watch_folder (str): Path to the local folder to monitor.
        base_dir (str): Base directory for storing configuration files (defaults to BASE_DIR).
        mapping_path (str): Path to the JSON file storing file-to-ID mappings.
        folder_id_file (str): Path to the text file storing the Google Drive folder ID.
        folder_id (str or None): The Google Drive folder ID, initialized via get_or_create_folder_id.
    """

    def __init__(self, service, watch_folder, base_dir: str | None = None):
        """
        Initialize the Watcher instance.

        Args:
            service (googleapiclient.discovery.Resource): Google Drive API service instance.
            watch_folder (str): Path to the local folder to monitor for changes.
            base_dir (str, optional): Base directory for configuration files. Defaults to BASE_DIR.

        Notes:
            - Initializes paths for the file mapping JSON and folder ID text file.
            - The folder_id attribute is set to None until get_or_create_folder_id is called.
        """
        self.service = service
        self.watch_folder = watch_folder
        self.base_dir = base_dir or BASE_DIR
        self.mapping_path = os.path.join(self.base_dir, "file_map.json")
        self.folder_id_file = os.path.join(self.base_dir, "folder_id.txt")
        self.folder_id = None

    def get_or_create_folder_id(self):
        """
        Retrieve or create a Google Drive folder ID and store it locally.

        Attempts to read an existing folder ID from a text file. If the file does not
        exist or reading fails, it retrieves or creates a folder ID using the Google Drive
        API and saves it to the file.

        Returns:
            str or None: The Google Drive folder ID if successful, otherwise None.

        Notes:
            - The folder ID is saved to a file named 'folder_id.txt' in the base directory.
            - Errors during file reading or writing are logged, but the function continues
              to attempt folder creation if reading fails.
            - The folder_id attribute is updated if a valid ID is retrieved or created.
        """
        if os.path.exists(self.folder_id_file):
            try:
                with open(self.folder_id_file, "r", encoding="utf-8") as f:
                    folder_id = f.read().strip()
                    if folder_id:
                        self.folder_id = folder_id
                        return folder_id
            except Exception as e:
                logger.error(f"Failed to read folder ID: {e}")

        folder_id = get_or_create_drive_folder(self.service, os.path.basename(self.watch_folder))
        if folder_id:
            try:
                os.makedirs(self.base_dir, exist_ok=True)
                with open(self.folder_id_file, "w", encoding="utf-8") as f:
                    f.write(folder_id)
                self.folder_id = folder_id
            except Exception as e:
                logger.error(f"Failed to save folder ID: {e}")
        return folder_id

    def on_modified(self, event):
        """
        Handle file modification events.

        Triggers an upload to Google Drive for modified files, ignoring directories
        and hidden files (those starting with a dot).

        Args:
            event (watchdog.events.FileSystemEvent): The file system event object.

        Notes:
            - Only non-directory files are processed.
            - Hidden files (starting with '.') are ignored.
            - Calls upload_file to handle the upload or update to Google Drive.
        """
        if event.is_directory:
            return
        if os.path.basename(event.src_path).startswith('.'):
            return
        upload_file(self.service, self.folder_id, self.mapping_path, event.src_path)

    def on_created(self, event):
        """
        Handle file creation events.

        Triggers an upload to Google Drive for newly created files, ignoring directories
        and hidden files (those starting with a dot).

        Args:
            event (watchdog.events.FileSystemEvent): The file system event object.

        Notes:
            - Only non-directory files are processed.
            - Hidden files (starting with '.') are ignored.
            - Calls upload_file to handle the upload to Google Drive.
        """
        if event.is_directory:
            return
        if os.path.basename(event.src_path).startswith('.'):
            return
        upload_file(self.service, self.folder_id, self.mapping_path, event.src_path)

    def on_deleted(self, event):
        """
        Handle file deletion events.

        Triggers deletion from Google Drive for deleted files, ignoring directories
        and hidden files (those starting with a dot).

        Args:
            event (watchdog.events.FileSystemEvent): The file system event object.

        Notes:
            - Only non-directory files are processed.
            - Hidden files (starting with '.') are ignored.
            - Calls delete_file_from_drive to remove the file from Google Drive.
        """
        if event.is_directory:
            return
        if os.path.basename(event.src_path).startswith('.'):
            return
        delete_file_from_drive(self.service, self.mapping_path, os.path.basename(event.src_path))

    def on_moved(self, event):
        """
        Handle file move events.

        Triggers deletion from Google Drive if the file is moved to a trash directory,
        ignoring directories and non-trash destinations.

        Args:
            event (watchdog.events.FileSystemEvent): The file system event object containing
                src_path and dest_path.

        Notes:
            - Only non-directory files are processed.
            - Files moved to paths containing '/.local/share/Trash' or '/Trash' are deleted
              from Google Drive.
            - Calls delete_file_from_drive for trash destinations.
        """
        if event.is_directory:
            return
        if "/.local/share/Trash" in getattr(event, "dest_path", "") or "/Trash" in getattr(event, "dest_path", ""):
            delete_file_from_drive(self.service, self.mapping_path, os.path.basename(event.src_path))

    def run(self):
        """
        Start the file system observer to monitor the watch folder.

        Initializes the folder ID if not already set, creates an Observer, schedules
        it to monitor the watch folder recursively, and starts the observer. Runs until
        interrupted by a KeyboardInterrupt, then stops and joins the observer.

        Returns:
            None: The function does not return a value. It runs the observer until interrupted.

        Notes:
            - Logs when the observer starts and stops.
            - Uses a 1-second sleep loop to keep the observer running.
            - Ensures the folder ID is initialized before starting the observer.
        """
        if not self.folder_id:
            self.get_or_create_folder_id()
        observer = Observer()
        observer.schedule(self, self.watch_folder, recursive=True)
        observer.start()
        logger.info("Observer started. Watching for file changes...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            logger.info("Observer stopped by user.")
        observer.join()