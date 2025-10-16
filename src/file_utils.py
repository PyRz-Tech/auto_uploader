import os
import json
import logging

logger = logging.getLogger(__name__)


def save_file_mapping(mapping_path, file_name, file_id):
    """
    Save or update a file-to-ID mapping in a JSON file.

    Loads an existing JSON mapping file, updates it with the specified file name and
    Google Drive file ID, and saves it back to the file. If the mapping file does not
    exist, a new one is created. If the JSON is corrupted, the file is recreated.

    Args:
        mapping_path (str): Path to the JSON file storing file-to-ID mappings.
        file_name (str): Name of the file to map.
        file_id (str): Google Drive file ID to associate with the file name.

    Returns:
        None: The function does not return a value. It logs the outcome of the operation.

    Notes:
        - If the mapping file exists but contains invalid JSON, a warning is logged,
          and the file is recreated with the new mapping.
        - Errors during file writing are logged, but no exceptions are raised.
    """
    mapping = {}
    if os.path.exists(mapping_path):
        try:
            with open(mapping_path, "r") as f:
                mapping = json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"Corrupted JSON in {mapping_path}. Recreating file.")
            mapping = {}

    mapping[file_name] = file_id
    try:
        with open(mapping_path, "w") as f:
            json.dump(mapping, f)
        logger.info(f"Mapping saved for '{file_name}' (ID: {file_id})")
    except Exception as e:
        logger.error(f"Failed to write mapping file: {e}")


def get_file_id(mapping_path, file_name):
    """
    Retrieve the Google Drive file ID for a given file name from a JSON mapping file.

    Checks if the mapping file exists and attempts to load it to find the file ID
    associated with the specified file name.

    Args:
        mapping_path (str): Path to the JSON file storing file-to-ID mappings.
        file_name (str): Name of the file to look up.

    Returns:
        str or None: The Google Drive file ID if found, otherwise None.

    Notes:
        - If the mapping file does not exist, a warning is logged, and None is returned.
        - If an error occurs while reading the file (e.g., corrupted JSON), an error is
          logged, and None is returned.
    """
    if not os.path.exists(mapping_path):
        logger.warning(f"{mapping_path} does not exist.")
        return None
    try:
        with open(mapping_path, "r") as f:
            mapping = json.load(f)
        return mapping.get(file_name)
    except Exception as e:
        logger.error(f"Error reading file mapping: {e}")
        return None


def remove_file_mapping(mapping_path, file_name):
    """
    Remove a file-to-ID mapping from a JSON mapping file.

    Loads the JSON mapping file, removes the specified file's mapping if it exists,
    and saves the updated mapping back to the file.

    Args:
        mapping_path (str): Path to the JSON file storing file-to-ID mappings.
        file_name (str): Name of the file whose mapping should be removed.

    Returns:
        None: The function does not return a value. It logs the outcome of the operation.

    Notes:
        - If the mapping file does not exist, a warning is logged, and the function returns early.
        - If the file name is not found in the mapping, a warning is logged.
        - Errors during reading or writing the mapping file are logged, but no exceptions are raised.
    """
    if not os.path.exists(mapping_path):
        logger.warning(f"{mapping_path} does not exist.")
        return
    try:
        with open(mapping_path, "r") as f:
            mapping = json.load(f)
    except Exception as e:
        logger.error(f"Error reading mapping file: {e}")
        return

    if file_name in mapping:
        del mapping[file_name]
        try:
            with open(mapping_path, "w") as f:
                json.dump(mapping, f)
            logger.info(f"Removed file mapping for '{file_name}'")
        except Exception as e:
            logger.error(f"Error writing mapping file: {e}")
    else:
        logger.warning(f"'{file_name}' not found in file mapping.")