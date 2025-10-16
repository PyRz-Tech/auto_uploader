"""
Main entry point for the Google Drive AutoUploader application.

This script sets up logging, loads configuration settings, and initiates the main
file-watching and synchronization process with Google Drive. It uses the load_config
function to retrieve credentials and folder settings, then passes them to the main
function to start the application. Error handling is implemented to log specific
issues during configuration loading.
"""
import sys
import os
import logging
from src.config_loader import load_config
from src.main import main

logger = logging.getLogger(__name__)
"""
Logger instance for the current module.

Used to log errors and other information during configuration loading and application
execution. The logger is configured with the module's name to provide context for log
messages.
"""

def validate_paths(credentials, folder):
    """Validate both credentials file and watch folder at the same time."""
    errors = []
    if not os.path.isfile(credentials):
        errors.append(f"Credentials file '{credentials}' does not exist.")
    if not os.path.isdir(folder):
        errors.append(f"Watch folder '{folder}' does not exist or is not writable.")
    if errors:
        for e in errors:
            logger.error(e)
        sys.exit(1)
    logger.info("All paths are valid.")


def get_config():
    """
    Load and return the application configuration.

    Retrieves configuration settings using the load_config function, which reads from
    a configuration file. Handles specific exceptions by logging appropriate error
    messages and re-raising the exceptions to halt execution.

    Returns:
        dict: Configuration dictionary containing 'credentials' and 'local_folder' keys.

    Raises:
        FileNotFoundError: If the configuration file cannot be found.
        KeyError: If required configuration keys ('credentials' or 'local_folder') are missing.
        Exception: For other unexpected errors during configuration loading.
    """
    try:
        return load_config()
    except FileNotFoundError as e:
        logger.error(f"Config file not found: {e}")
        raise
    except KeyError as e:
        logger.error(f"Missing config key: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error loading config: {e}")
        raise

def start_app(credentials, folder):
    """
    Start the Google Drive AutoUploader application with the provided configuration.

    Initiates the main function with the specified credentials and folder path to begin
    monitoring and synchronizing files with Google Drive.

    Args:
        credentials (str): Path to the Google Drive API credentials file.
        folder (str): Path to the local folder to be monitored.
    """
    validate_paths(credentials, folder)
    main(credentials, folder)

def run():
    """
    Run the Google Drive AutoUploader application.

    Loads the configuration using get_config and passes the credentials and local folder
    paths to start_app to initialize the file watcher and start synchronization with
    Google Drive.

    Raises:
        FileNotFoundError: If the configuration file cannot be found.
        KeyError: If required configuration keys are missing.
        Exception: For other unexpected errors during configuration loading or execution.
    """
    config = get_config()
    print(f"credentials: {config["credentials"]}, local_folder: {config["local_folder"]}" )
    start_app(config["credentials"], config["local_folder"])
