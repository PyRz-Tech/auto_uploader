import os
import logging

logger = logging.getLogger(__name__)

def main(credentials_path, watch_folder):
    """
    Initialize and run the Google Drive AutoUploader.

    Creates the specified watch folder if it does not exist, initializes a Google
    Drive API service using the provided credentials, and starts a Watcher instance
    to monitor the folder for file changes. If the Google Drive service cannot be
    initialized, an error is logged, and the function exits.

    Args:
        credentials_path (str): Path to the Google credentials JSON file.
        watch_folder (str): Path to the local folder to monitor for file changes.

    Returns:
        None: The function does not return a value. It initializes the watcher and
        runs it until interrupted.

    Notes:
        - The token file for Google Drive API credentials is stored in the same
          directory as the credentials file, named 'token.json'.
        - If the watch folder does not exist, it is created automatically.
        - If the Google Drive service initialization fails, the function logs an
          error and returns early.
    """
    from src.watcher import Watcher
    from src.drive_utils import get_drive_service
    token_path = os.path.join(os.path.dirname(credentials_path), "token.json")
    service = get_drive_service(credentials_path, token_path)
    if not service:
        logger.error("Google Drive service could not be initialized.")
        return
    watcher = Watcher(service, watch_folder)
    watcher.run()