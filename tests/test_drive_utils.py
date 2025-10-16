import unittest
from unittest.mock import patch, MagicMock, mock_open
from types import SimpleNamespace
from googleapiclient.errors import HttpError
from src.drive_utils import (
    upload_file,
    get_drive_service,
    get_or_create_drive_folder,
    get_file_id,
    delete_file_from_drive
)


class TestUploadFile(unittest.TestCase):
    """
    Unit tests for the upload_file function in the src.drive_utils module.

    This test suite verifies the behavior of the upload_file function, which uploads or
    updates files to Google Drive. The tests cover scenarios including no internet connection,
    uploading a new file, updating an existing file, and handling upload errors, using
    mocking to simulate Google Drive API interactions, file operations, and network checks.
    """

    @patch("src.drive_utils.logger")
    @patch("src.drive_utils.is_internet_connected", return_value=False)
    def test_no_internet_connection(self, mock_net, mock_logger):
        """
        Test that upload_file aborts when there is no internet connection.

        Mocks the is_internet_connected function to simulate no internet connection,
        ensuring the function logs an error and does not attempt to upload.

        Args:
            mock_net (MagicMock): Mock for is_internet_connected function.
            mock_logger (MagicMock): Mock for the logger object.

        Asserts:
            - An error is logged indicating no internet connection.
        """
        upload_file(MagicMock(), "folder123", "mapping.json", "file.txt")
        mock_logger.error.assert_called_once_with("Cannot upload 'file.txt' — no internet connection.")

    @patch("src.drive_utils.logger")
    @patch("src.drive_utils.save_file_mapping")
    @patch("src.drive_utils.get_file_id", return_value=None)
    @patch("src.drive_utils.is_internet_connected", return_value=True)
    @patch("src.drive_utils.MediaFileUpload")
    def test_upload_new_file(self, mock_media, mock_net, mock_get_id, mock_save_map, mock_logger):
        """
        Test that upload_file uploads a new file to Google Drive.

        Mocks Google Drive API, file ID retrieval, and file mapping to simulate uploading
        a new file, ensuring the file is created and its ID is saved.

        Args:
            mock_media (MagicMock): Mock for MediaFileUpload class.
            mock_net (MagicMock): Mock for is_internet_connected function.
            mock_get_id (MagicMock): Mock for get_file_id function.
            mock_save_map (MagicMock): Mock for save_file_mapping function.
            mock_logger (MagicMock): Mock for the logger object.

        Asserts:
            - The Google Drive API create method is called once.
            - The file mapping is saved with the new file ID.
            - An info log confirms the file upload.
        """
        mock_service = MagicMock()
        mock_files = mock_service.files.return_value
        mock_create = mock_files.create.return_value
        mock_create.execute.return_value = {"id": "new_file_id"}

        upload_file(mock_service, "folder123", "mapping.json", "file.txt")

        mock_files.create.assert_called_once()
        mock_save_map.assert_called_once_with("mapping.json", "file.txt", "new_file_id")
        mock_logger.info.assert_any_call("[UPLOADED] 'file.txt' successfully uploaded to Drive.")

    @patch("src.drive_utils.logger")
    @patch("src.drive_utils.get_file_id", return_value="existing123")
    @patch("src.drive_utils.is_internet_connected", return_value=True)
    @patch("src.drive_utils.MediaFileUpload")
    def test_update_existing_file(self, mock_media, mock_net, mock_get_id, mock_logger):
        """
        Test that upload_file updates an existing file on Google Drive.

        Mocks Google Drive API and file ID retrieval to simulate updating an existing
        file, ensuring the update method is called and no new mapping is created.

        Args:
            mock_media (MagicMock): Mock for MediaFileUpload class.
            mock_net (MagicMock): Mock for is_internet_connected function.
            mock_get_id (MagicMock): Mock for get_file_id function.
            mock_logger (MagicMock): Mock for the logger object.

        Asserts:
            - The Google Drive API update method is called with the existing file ID.
            - An info log confirms the file update.
        """
        mock_service = MagicMock()
        mock_files = mock_service.files.return_value
        mock_update = mock_files.update.return_value
        mock_update.execute.return_value = None

        upload_file(mock_service, "folder123", "mapping.json", "file.txt")

        mock_files.update.assert_called_once_with(
            fileId="existing123", media_body=mock_media.return_value
        )
        mock_logger.info.assert_any_call("[UPDATED] 'file.txt' successfully updated on Drive.")

    @patch("src.drive_utils.logger")
    @patch("src.drive_utils.save_file_mapping")
    @patch("src.drive_utils.get_file_id", return_value=None)
    @patch("src.drive_utils.is_internet_connected", return_value=True)
    @patch("src.drive_utils.MediaFileUpload")
    def test_upload_raises_exception(self, mock_media, mock_net, mock_get_id, mock_save_map, mock_logger):
        """
        Test that upload_file handles exceptions during upload.

        Mocks Google Drive API to simulate an error during file creation, ensuring the
        error is logged and the function handles the failure gracefully.

        Args:
            mock_media (MagicMock): Mock for MediaFileUpload class.
            mock_net (MagicMock): Mock for is_internet_connected function.
            mock_get_id (MagicMock): Mock for get_file_id function.
            mock_save_map (MagicMock): Mock for save_file_mapping function.
            mock_logger (MagicMock): Mock for the logger object.

        Asserts:
            - An error log is generated for the upload failure.
        """
        mock_service = MagicMock()
        mock_files = mock_service.files.return_value
        mock_files.create.side_effect = Exception("upload error")

        upload_file(mock_service, "folder123", "mapping.json", "file.txt")

        mock_logger.error.assert_any_call("Error during upload: upload error")


class TestGetOrCreateDriveFolder(unittest.TestCase):
    """
    Unit tests for the get_or_create_drive_folder function in the src.drive_utils module.

    This test suite verifies the behavior of the get_or_create_drive_folder function,
    which retrieves or creates a folder in Google Drive. The tests cover scenarios including
    finding an existing folder, creating a new folder, and handling errors during folder
    listing or creation, using mocking to simulate Google Drive API interactions.
    """

    @patch("src.drive_utils.get_drive_service")
    def test_existing_folder_found(self, mock_get_service):
        """
        Test that get_or_create_drive_folder returns an existing folder's ID.

        Mocks the Google Drive API to simulate finding an existing folder, ensuring the
        correct folder ID is returned and no folder creation is attempted.

        Args:
            mock_get_service (MagicMock): Mock for get_drive_service function.

        Asserts:
            - The correct folder ID is returned.
            - The list method is called once.
            - The create method is not called.
        """
        mock_service = MagicMock()
        mock_files = MagicMock()
        mock_list = MagicMock()
        mock_get_service.return_value = mock_service
        mock_service.files.return_value = mock_files
        mock_files.list.return_value = mock_list
        mock_list.execute.return_value = {
            "files": [{"id": "folder123", "name": "MyFolder"}]
        }

        folder_id = get_or_create_drive_folder(mock_service, "MyFolder")

        self.assertEqual(folder_id, "folder123")
        mock_service.files().list.assert_called_once()
        mock_service.files().create.assert_not_called()

    @patch("src.drive_utils.get_drive_service")
    def test_create_folder_when_not_exists(self, mock_get_service):
        """
        Test that get_or_create_drive_folder creates a new folder when none exists.

        Mocks the Google Drive API to simulate an empty folder list, ensuring a new
        folder is created and its ID is returned.

        Args:
            mock_get_service (MagicMock): Mock for get_drive_service function.

        Asserts:
            - The new folder ID is returned.
            - The list method is called once.
            - The create method is called once.
        """
        mock_service = MagicMock()
        mock_files = MagicMock()
        mock_list = MagicMock()
        mock_get_service.return_value = mock_service
        mock_service.files.return_value = mock_files
        mock_files.list.return_value = mock_list
        mock_list.execute.return_value = {'files': []}

        mock_service.files.return_value = mock_files
        mock_files.create.return_value = mock_files
        mock_files.execute.return_value = {'id': 'NewFolderId'}

        folder_id = get_or_create_drive_folder(mock_service, 'NewFolder')

        self.assertEqual(folder_id, "NewFolderId")
        mock_files.list.assert_called_once()
        mock_files.create.assert_called_once()

    def test_service_error_handling(self):
        """
        Test that get_or_create_drive_folder handles service errors during folder listing.

        Mocks the Google Drive API to simulate an error during folder listing, ensuring
        the function returns None.

        Asserts:
            - None is returned when an error occurs.
        """
        mock_service = MagicMock()
        mock_service.files.return_value.list.return_value.execute.side_effect = Exception("service error")

        folder_id = get_or_create_drive_folder(mock_service, "New Folder")

        self.assertIsNone(folder_id)

    @patch("src.drive_utils.get_drive_service")
    def test_list_files_error_handling(self, mock_get_service):
        """
        Test that get_or_create_drive_folder handles errors during folder listing.

        Mocks the Google Drive API to simulate a failure in listing folders, ensuring
        the function returns None.

        Args:
            mock_get_service (MagicMock): Mock for get_drive_service function.

        Asserts:
            - None is returned when listing folders fails.
        """
        mock_service = MagicMock()
        mock_files = MagicMock()
        mock_get_service.return_value = mock_service
        mock_service.files.return_value = mock_files
        mock_files.list.side_effect = Exception("Faild to list folders")

        folder_id = get_or_create_drive_folder(mock_service, "New Folder")

        self.assertIsNone(folder_id)

    @patch("src.drive_utils.get_drive_service")
    def test_create_folder_error_handling(self, mock_get_service):
        """
        Test that get_or_create_drive_folder handles errors during folder creation.

        Mocks the Google Drive API to simulate an empty folder list followed by a failure
        in folder creation, ensuring the function returns None.

        Args:
            mock_get_service (MagicMock): Mock for get_drive_service function.

        Asserts:
            - None is returned when folder creation fails.
        """
        mock_service = MagicMock()
        mock_files = MagicMock()
        mock_list = MagicMock()
        mock_get_service.return_value = mock_service
        mock_service.files.return_value = mock_files
        mock_files.list.return_value = mock_list
        mock_list.execute.return_value = {'files': []}

        mock_service.files.return_value = mock_files
        mock_files.create.return_value = mock_files
        mock_files.execute.side_effect = Exception("create error")

        folder_id = get_or_create_drive_folder(mock_service, 'New Folder')

        self.assertIsNone(folder_id)


class TestGetDriveService(unittest.TestCase):
    """
    Unit tests for the get_drive_service function in the src.drive_utils module.

    This test suite verifies the behavior of the get_drive_service function, which
    initializes a Google Drive API service. The tests cover scenarios including using
    an existing valid token, refreshing an expired token, initiating a new authentication
    flow, and handling authentication or service build failures, using mocking to simulate
    file operations and Google API interactions.
    """

    @patch("src.drive_utils.build")
    @patch("src.drive_utils.pickle.load")
    @patch("src.drive_utils.os.path.exists", return_value=True)
    @patch("builtins.open", new_callable=mock_open)
    def test_valid_token_exists(self, mock_file, mock_exists, mock_pickle, mock_build):
        """
        Test that get_drive_service uses an existing valid token.

        Mocks file operations and Google API to simulate loading a valid token,
        ensuring the service is built without initiating an authentication flow.

        Args:
            mock_file (MagicMock): Mock for the built-in open function.
            mock_exists (MagicMock): Mock for os.path.exists function.
            mock_pickle (MagicMock): Mock for pickle.load function.
            mock_build (MagicMock): Mock for build function.

        Asserts:
            - The service is returned successfully.
            - The build method is called once.
        """
        creds = MagicMock(valid=True)
        mock_pickle.return_value = creds
        mock_build.return_value = "fake_service"

        service = get_drive_service("cred.json", "token.pickle")

        self.assertEqual(service, "fake_service")
        mock_build.assert_called_once()

    @patch("src.drive_utils.build")
    @patch("src.drive_utils.pickle.dump")
    @patch("src.drive_utils.pickle.load")
    @patch("src.drive_utils.os.path.exists", return_value=True)
    @patch("builtins.open", new_callable=mock_open)
    def test_token_expired_and_refresh(self, mock_file, mock_exists, mock_pickle_load, mock_pickle_dump, mock_build):
        """
        Test that get_drive_service refreshes an expired token.

        Mocks file operations and Google API to simulate an expired token with a refresh
        token, ensuring the token is refreshed and the service is built.

        Args:
            mock_file (MagicMock): Mock for the built-in open function.
            mock_exists (MagicMock): Mock for os.path.exists function.
            mock_pickle_load (MagicMock): Mock for pickle.load function.
            mock_pickle_dump (MagicMock): Mock for pickle.dump function.
            mock_build (MagicMock): Mock for build function.

        Asserts:
            - The token is refreshed.
            - The refreshed token is saved.
            - The service is returned successfully.
        """
        creds = MagicMock(valid=False, expired=True, refresh_token=True)
        mock_pickle_load.return_value = creds
        mock_build.return_value = "fake_service"

        service = get_drive_service("cred.json", "token.pickle")

        creds.refresh.assert_called_once()
        mock_pickle_dump.assert_called_once()
        self.assertEqual(service, "fake_service")

    @patch("src.drive_utils.build")
    @patch("src.drive_utils.pickle.dump")
    @patch("src.drive_utils.os.path.exists", return_value=False)
    @patch("src.drive_utils.InstalledAppFlow.from_client_secrets_file")
    @patch("builtins.open", new_callable=mock_open)
    def test_no_token_auth_flow(self, mock_file, mock_flow, mock_exists, mock_pickle_dump, mock_build):
        """
        Test that get_drive_service initiates a new authentication flow when no token exists.

        Mocks file operations and Google API to simulate the absence of a token file,
        ensuring an authentication flow is initiated and a new token is saved.

        Args:
            mock_file (MagicMock): Mock for the built-in open function.
            mock_flow (MagicMock): Mock for InstalledAppFlow.from_client_secrets_file.
            mock_exists (MagicMock): Mock for os.path.exists function.
            mock_pickle_dump (MagicMock): Mock for pickle.dump function.
            mock_build (MagicMock): Mock for build function.

        Asserts:
            - The authentication flow is initiated.
            - The new token is saved.
            - The service is returned successfully.
        """
        mock_flow_instance = MagicMock()
        mock_flow.return_value = mock_flow_instance
        mock_flow_instance.run_local_server.return_value = MagicMock(valid=True)
        mock_build.return_value = "fake_service"

        service = get_drive_service("cred.json", "token.pickle")

        mock_flow.assert_called_once_with("cred.json", ['https://www.googleapis.com/auth/drive.file'])
        mock_flow_instance.run_local_server.assert_called_once()
        mock_pickle_dump.assert_called_once()
        self.assertEqual(service, "fake_service")

    @patch("src.drive_utils.InstalledAppFlow.from_client_secrets_file", side_effect=Exception("Auth failed"))
    @patch("src.drive_utils.os.path.exists", return_value=False)
    def test_authentication_failure(self, mock_exists, mock_flow):
        """
        Test that get_drive_service handles authentication failures.

        Mocks the authentication flow to simulate a failure, ensuring the function
        returns None.

        Args:
            mock_exists (MagicMock): Mock for os.path.exists function.
            mock_flow (MagicMock): Mock for InstalledAppFlow.from_client_secrets_file.

        Asserts:
            - None is returned when authentication fails.
        """
        result = get_drive_service("cred.json", "token.pickle")
        self.assertIsNone(result)

    @patch("src.drive_utils.build", side_effect=Exception("Build failed"))
    @patch("src.drive_utils.pickle.load", return_value=MagicMock(valid=True))
    @patch("src.drive_utils.os.path.exists", return_value=True)
    @patch("builtins.open", new_callable=mock_open)
    def test_service_build_failure(self, mock_file, mock_exists, mock_pickle, mock_build):
        """
        Test that get_drive_service handles service build failures.

        Mocks file operations and Google API to simulate a failure during service
        building, ensuring the function returns None.

        Args:
            mock_file (MagicMock): Mock for the built-in open function.
            mock_exists (MagicMock): Mock for os.path.exists function.
            mock_pickle (MagicMock): Mock for pickle.load function.
            mock_build (MagicMock): Mock for build湘

        Asserts:
            - None is returned when service building fails.
        """
        result = get_drive_service("cred.json", "token.pickle")
        self.assertIsNone(result)


class TestGetFileId(unittest.TestCase):
    """
    Unit tests for the get_file_id function in the src.drive_utils module.

    This test suite verifies the behavior of the get_file_id function, which retrieves
    a Google Drive file ID from a JSON mapping file. The tests cover scenarios including
    a non-existent mapping file, valid JSON with a file ID, invalid JSON, reading errors,
    and missing keys in the JSON, using mocking to simulate file operations.
    """

    @patch("os.path.exists", return_value=False)
    def test_file_not_exists(self, mock_path_exists):
        """
        Test that get_file_id returns None when the mapping file does not exist.

        Mocks os.path.exists to simulate a missing mapping file, ensuring None is returned.

        Args:
            mock_path_exists (MagicMock): Mock for os.path.exists function.

        Asserts:
            - None is returned when the mapping file does not exist.
        """
        result = get_file_id("mapping.json", "file.txt")
        self.assertIsNone(result)

    @patch("builtins.open", new_callable=mock_open, read_data='{"file.txt": "123"}')
    @patch("os.path.exists", return_value=True)
    def test_file_exists_and_valid_json(self, mock_path_exists, mock_file):
        """
        Test that get_file_id returns the file ID when the mapping file contains valid JSON.

        Mocks file operations to simulate a valid JSON mapping file, ensuring the correct
        file ID is returned.

        Args:
            mock_path_exists (MagicMock): Mock for os.path.exists function.
            mock_file (MagicMock): Mock for the built-in open function.

        Asserts:
            - The correct file ID is returned.
        """
        result = get_file_id("mapping.json", "file.txt")
        self.assertEqual(result, '123')

    @patch("builtins.open", new_callable=mock_open, read_data='invlid_json')
    @patch("os.path.exists", return_value=True)
    def test_invalid_json(self, mock_path_exists, mock_file):
        """
        Test that get_file_id handles invalid JSON in the mapping file.

        Mocks file operations to simulate a corrupted JSON file, ensuring None is returned.

        Args:
            mock_path_exists (MagicMock): Mock for os.path.exists function.
            mock_file (MagicMock): Mock for the built-in open function.

        Asserts:
            - None is returned when the JSON is invalid.
        """
        result = get_file_id("mapping.json", "file.txt")
        self.assertIsNone(result)

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists", return_value=True)
    @patch("json.load", side_effect=Exception("Something went wrong"))
    def test_read_file_error(self, mock_json_load, mock_path_exists, mock_file):
        """
        Test that get_file_id handles errors during file reading.

        Mocks file operations and json.load to simulate an error during reading,
        ensuring None is returned.

        Args:
            mock_json_load (MagicMock): Mock for json.load function.
            mock_path_exists (MagicMock): Mock for os.path.exists function.
            mock_file (MagicMock): Mock for the built-in open function.

        Asserts:
            - None is returned when a reading error occurs.
        """
        result = get_file_id("mapping.json", "file.txt")
        self.assertIsNone(result)

    @patch("builtins.open", new_callable=mock_open, read_data='{"file.txt": "123"}')
    @patch("os.path.exists", return_value=True)
    def test_key_not_in_json(self, mock_path_exists, mock_file):
        """
        Test that get_file_id returns None when the file is not in the mapping.

        Mocks file operations to simulate a valid JSON file without the requested file,
        ensuring None is returned.

        Args:
            mock_path_exists (MagicMock): Mock for os.path.exists function.
            mock_file (MagicMock): Mock for the built-in open function.

        Asserts:
            - None is returned when the file name is not in the mapping.
        """
        result = get_file_id("mapping.json", "non_exists.txt")
        self.assertIsNone(result)


class TestDeleteFileFromDrive(unittest.TestCase):
    """
    Unit tests for the delete_file_from_drive function in the src.drive_utils module.

    This test suite verifies the behavior of the delete_file_from_drive function, which
    deletes a file from Google Drive and removes its mapping. The tests cover scenarios
    including successful deletion, file not found in mapping, HTTP errors, and unexpected
    exceptions, using mocking to simulate Google Drive API interactions and file operations.
    """

    @patch("src.drive_utils.remove_file_mapping")
    @patch("src.drive_utils.get_file_id")
    def test_file_found_and_deleted(self, mock_get_file_id, mock_remove_file_mapping):
        """
        Test that delete_file_from_drive deletes a file and removes its mapping.

        Mocks get_file_id and Google Drive API to simulate a successful file deletion,
        ensuring the file is deleted and its mapping is removed.

        Args:
            mock_get_file_id (MagicMock): Mock for get_file_id function.
            mock_remove_file_mapping (MagicMock): Mock for remove_file_mapping function.

        Asserts:
            - Appropriate info logs are generated for deletion.
            - The file mapping is removed.
        """
        mock_get_file_id.return_value = "fake_file_id"
        
        mock_service = MagicMock()
        mock_service.files.return_value.delete.return_value.execute.return_value = None
        
        with self.assertLogs(level='INFO') as log:
            delete_file_from_drive(mock_service, "mapping.json", "test_file.txt")
        
        self.assertIn("Deleting 'test_file.txt' (ID: fake_file_id) from Drive...", log.output[0])
        self.assertIn("'test_file.txt' deleted from Drive.", log.output[1])
        
        mock_remove_file_mapping.assert_called_once_with("mapping.json", "test_file.txt")

    @patch("src.drive_utils.get_file_id")
    def test_file_not_found(self, mock_get_file_id):
        """
        Test that delete_file_from_drive handles a missing file in the mapping.

        Mocks get_file_id to simulate a missing file ID, ensuring a warning is logged
        and no deletion is attempted.

        Args:
            mock_get_file_id (MagicMock): Mock for get_file_id function.

        Asserts:
            - A warning log is generated indicating the file is not in the mapping.
        """
        mock_get_file_id.return_value = None
        
        mock_service = MagicMock()
        
        with self.assertLogs(level='WARNING') as log:
            delete_file_from_drive(mock_service, "mapping.json", "missing_file.txt")
        
        self.assertIn("'missing_file.txt' not found in Drive mapping.", log.output[0])

    @patch("src.drive_utils.remove_file_mapping")
    @patch("src.drive_utils.get_file_id", return_value="fake_file_id")
    def test_http_error(self, mock_get_file_id, mock_remove_file_mapping):
        """
        Test that delete_file_from_drive handles HTTP errors during deletion.

        Mocks Google Drive API to simulate an HTTP error, ensuring an error is logged
        and the file mapping is not removed.

        Args:
            mock_get_file_id (MagicMock): Mock for get_file_id function.
            mock_remove_file_mapping (MagicMock): Mock for remove_file_mapping function.

        Asserts:
            - An HTTP error log is generated.
            - The file mapping is not removed.
        """
        mock_service = MagicMock()
        fake_resp = SimpleNamespace(status=500, reason="Server Error")
        mock_service.files.return_value.delete.return_value.execute.side_effect = HttpError(resp=fake_resp, content=b"error")
        
        with self.assertLogs(level='ERROR') as log:
            delete_file_from_drive(mock_service, "mapping.json", "test_file.txt")
        
        self.assertTrue(any("HTTP error deleting 'test_file.txt'" in msg for msg in log.output))
        mock_remove_file_mapping.assert_not_called()

    @patch("src.drive_utils.logger")
    @patch("src.drive_utils.remove_file_mapping")
    @patch("src.drive_utils.get_file_id", return_value="12345")
    def test_delete_file_from_drive_unexpected_exception(self, mock_get_id, mock_remove, mock_logger):
        """
        Test that delete_file_from_drive handles unexpected exceptions during deletion.

        Mocks Google Drive API to simulate an unexpected error, ensuring an error is
        logged and the file mapping is not removed.

        Args:
            mock_get_id (MagicMock): Mock for get_file_id function.
            mock_remove (MagicMock): Mock for remove_file_mapping function.
            mock_logger (MagicMock): Mock for the logger object.

        Asserts:
            - An error log is generated for the unexpected exception.
            - The file mapping is not removed.
            - get_file_id is called once.
        """
        mock_service = MagicMock()
        mock_service.files.return_value.delete.return_value.execute.side_effect = Exception("Network down")

        delete_file_from_drive(mock_service, "dummy.json", "file.txt")

        mock_logger.error.assert_called_with("Unexpected error deleting 'file.txt': Network down")
        mock_remove.assert_not_called()
        mock_get_id.assert_called_once_with("dummy.json", "file.txt")


if __name__ == "__main__":
    unittest.main()