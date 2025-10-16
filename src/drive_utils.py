import json
import os
import pickle
import logging
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from src.file_utils import save_file_mapping, get_file_id, remove_file_mapping
from src.network_utils import is_internet_connected

logger = logging.getLogger(__name__)


def get_drive_service(credentials_path, token_path):
    """
    Initialize and return a Google Drive API service instance.

    Loads or refreshes Google API credentials from a token file or initiates an
    authentication flow if no valid credentials are found. The credentials are saved
    to the token file after authentication or refresh. If successful, a Google Drive
    API service instance is created and returned.

    Args:
        credentials_path (str): Path to the Google credentials JSON file.
        token_path (str): Path to the token file for storing/retrieving credentials.

    Returns:
        googleapiclient.discovery.Resource or None: A Google Drive API service instance
        if successful, otherwise None if authentication or service creation fails.

    Notes:
        - If a valid token exists, it is loaded from the token_path.
        - If the token is expired but has a refresh token, it is refreshed.
        - If no valid token exists, a new authentication flow is initiated.
        - Errors during authentication or service creation are logged, and None is returned.
    """
    creds = None
    if os.path.exists(token_path):
        with open(token_path, "rb") as token:
            creds = pickle.load(token)
            logger.info("Loaded existing token credentials.")

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing expired credentials...")
            creds.refresh(Request())
        else:
            try:
                logger.info("No valid credentials found. Starting Google authentication flow...")
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, ['https://www.googleapis.com/auth/drive.file'])
                creds = flow.run_local_server(port=0)
                logger.info("User successfully authenticated with Google.")
            except Exception as e:
                logger.error("Authentication failed or user denied access.")
                logger.error(f"Error details: {e}")
                return None

        with open(token_path, "wb") as token:
            pickle.dump(creds, token)
            logger.info("New token saved.")

    try:
        service = build("drive", "v3", credentials=creds)
        logger.info("Google Drive service successfully created.")
        return service
    except Exception as e:
        logger.error(f"Failed to create Google Drive service: {e}")
        return None


def get_or_create_drive_folder(service, folder_name):
    """
    Retrieve or create a folder in Google Drive and return its ID.

    Searches for an existing folder with the specified name in Google Drive. If found,
    returns its ID. If not found, creates a new folder and returns its ID.

    Args:
        service (googleapiclient.discovery.Resource): Google Drive API service instance.
        folder_name (str): Name of the folder to retrieve or create.

    Returns:
        str or None: The ID of the existing or newly created folder, or None if an error occurs.

    Notes:
        - The search query excludes trashed folders and only matches exact folder names.
        - Errors during folder listing or creation are logged, and None is returned.
    """
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    try:
        results = service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get("files", [])
    except Exception as e:
        logger.error(f"Failed to list folders: {e}")
        return None

    if files:
        folder_id = files[0]["id"]
        logger.info(f"Found existing folder '{folder_name}' (ID: {folder_id})")
        return folder_id

    try:
        folder = service.files().create(
            body={"name": folder_name, "mimeType": "application/vnd.google-apps.folder"},
            fields="id"
        ).execute()
        folder_id = folder.get("id")
        logger.info(f"Created new folder '{folder_name}' (ID: {folder_id})")
        return folder_id
    except Exception as e:
        logger.error(f"Failed to create folder '{folder_name}': {e}")
        return None


def upload_file(service, folder_id, mapping_path, file_path):
    """
    Upload or update a file to Google Drive.

    Checks for an internet connection before proceeding. If the file exists in the
    mapping, it updates the existing file on Google Drive. Otherwise, it uploads a new
    file to the specified folder and saves its ID to the mapping file.

    Args:
        service (googleapiclient.discovery.Resource): Google Drive API service instance.
        folder_id (str): ID of the Google Drive folder to upload the file to.
        mapping_path (str): Path to the JSON file storing file-to-ID mappings.
        file_path (str): Path to the local file to upload.

    Returns:
        None: The function does not return a value. It logs the outcome of the operation.

    Notes:
        - Uses resumable uploads for reliability.
        - If no internet connection is available, the function logs an error and returns early.
        - Errors during upload or update are logged.
    """
    if not is_internet_connected():
        logger.error(f"Cannot upload '{file_path}' — no internet connection.")
        return

    file_name = os.path.basename(file_path)
    media = MediaFileUpload(file_path, resumable=True)
    existing_file_id = get_file_id(mapping_path, file_name)

    try:
        if existing_file_id:
            service.files().update(fileId=existing_file_id, media_body=media).execute()
            logger.info(f"[UPDATED] '{file_name}' successfully updated on Drive.")
        else:
            file = service.files().create(
                body={"name": file_name, "parents": [folder_id]},
                media_body=media,
                fields="id"
            ).execute()
            save_file_mapping(mapping_path, file_name, file.get("id"))
            logger.info(f"[UPLOADED] '{file_name}' successfully uploaded to Drive.")
    except Exception as e:
        logger.error(f"Error during upload: {e}")


def delete_file_from_drive(service, mapping_path, file_name):
    """
    Delete a file from Google Drive and remove its mapping.

    Retrieves the file ID from the mapping file and deletes the file from Google Drive.
    If successful, removes the file's mapping from the mapping file.

    Args:
        service (googleapiclient.discovery.Resource): Google Drive API service instance.
        mapping_path (str): Path to the JSON file storing file-to-ID mappings.
        file_name (str): Name of the file to delete.

    Returns:
        None: The function does not return a value. It logs the outcome of the operation.

    Raises:
        HttpError: If an HTTP error occurs during the Google Drive API call.
        Exception: For any other unexpected errors during the deletion process.

    Notes:
        - If the file ID is not found in the mapping, a warning is logged and the function returns early.
        - Errors during deletion are logged, including specific handling for HttpError.
    """
    file_id = get_file_id(mapping_path, file_name)
    if not file_id:
        logger.warning(f"'{file_name}' not found in Drive mapping.")
        return

    try:
        logger.info(f"Deleting '{file_name}' (ID: {file_id}) from Drive...")
        service.files().delete(fileId=file_id).execute()
        remove_file_mapping(mapping_path, file_name)
        logger.info(f"'{file_name}' deleted from Drive.")
    except HttpError as e:
        logger.error(f"HTTP error deleting '{file_name}': {e}")
    except Exception as e:
        logger.error(f"Unexpected error deleting '{file_name}': {e}")