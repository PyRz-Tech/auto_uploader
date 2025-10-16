import json
import os
import argparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_config():
    """
    Load and update configuration for the Google Drive AutoUploader.

    This function initializes an ArgumentParser to handle command-line arguments for
    specifying the path to Google credentials and the local folder to sync. It attempts
    to load existing configuration from a 'config.json' file in the base directory.
    If the file exists, it updates the default configuration with the loaded values.
    Command-line arguments override the loaded configuration if provided. If required
    configuration values are missing, it prompts the user for input. The updated
    configuration is then saved to the 'config.json' file.

    Returns:
        dict: A dictionary containing the configuration with keys:
            - 'credentials': Path to the Google credentials JSON file.
            - 'local_folder': Path to the local folder to sync with Google Drive.

    Notes:
        - The configuration is saved to 'config.json' in the base directory after updates.
        - If the 'config.json' file is corrupted or cannot be read, the function proceeds
          with default values and user input.
        - User input is prompted only if the required configuration values are not provided
          via command-line arguments or the config file.
    """
    parser = argparse.ArgumentParser(description="Google Drive AutoUploader")
    parser.add_argument("--credentials", help="Path to Google credentials.json", required=False)
    parser.add_argument("--watch_folder", help="Local folder to sync", required=False)
    args = parser.parse_args()

    config_path = os.path.join(BASE_DIR, "config.json")
    config = {"credentials": "", "local_folder": ""}

    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            try:
                config.update(json.load(f))
            except Exception:
                pass

    if args.credentials:
        config["credentials"] = args.credentials
    if args.watch_folder:
        config["local_folder"] = args.watch_folder

    if not config["credentials"]:
        config["credentials"] = input("Enter path to Google credentials.json: ").strip()
    if not config["local_folder"]:
        config["local_folder"] = input("Enter folder path to sync: ").strip()

    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    return config