import unittest
from unittest.mock import patch, MagicMock
from src.main import main


class TestMainFunction(unittest.TestCase):
    """
    Unit tests for the main function in the src.main module.

    This test suite verifies the behavior of the main function, which serves as the entry
    point for the Google Drive AutoUploader. The tests cover scenarios including successful
    initialization and execution of the file watcher, as well as failure to initialize the
    Google Drive service, using mocking to simulate directory creation, Google Drive API
    service initialization, and watcher operations.
    """

    @patch("src.main.logger")
    @patch("src.drive_utils.get_drive_service")
    @patch("src.watcher.Watcher")
    def test_main_successful_run(self, mock_watcher, mock_get_service, mock_logger):
        """
        Test that the main function initializes and runs successfully.

        Mocks directory creation, Google Drive service initialization, and the Watcher
        class to simulate a successful run of the main function, ensuring all components
        are called correctly and no errors are logged.

        Args:
            mock_makedirs (MagicMock): Mock for os.makedirs function.
            mock_watcher (MagicMock): Mock for the Watcher class.
            mock_get_service (MagicMock): Mock for get_drive_service function.
            mock_logger (MagicMock): Mock for the logger object.

        Asserts:
            - The watch folder is created (or checked for existence).
            - The Google Drive service is initialized with the correct credentials and token paths.
            - The Watcher is instantiated and run.
            - No error logs are generated.
        """
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service
        mock_watcher_instance = MagicMock()
        mock_watcher.return_value = mock_watcher_instance

        main("cred.json", "watched_folder")

        mock_get_service.assert_called_once_with("cred.json", "token.json")
        mock_watcher.assert_called_once_with(mock_service, "watched_folder")
        mock_watcher_instance.run.assert_called_once()
        mock_logger.error.assert_not_called()

    @patch("src.main.logger")
    @patch("src.drive_utils.get_drive_service", return_value=None)
    def test_main_service_initialization_failure(self, mock_get_service, mock_logger):
        """
        Test that the main function handles failure to initialize the Google Drive service.

        Mocks directory creation and Google Drive service initialization to simulate a
        failure in service initialization, ensuring the function logs an error and exits
        gracefully.

        Args:
            mock_makedirs (MagicMock): Mock for os.makedirs function.
            mock_get_service (MagicMock): Mock for get_drive_service function.
            mock_logger (MagicMock): Mock for the logger object.

        Asserts:
            - The watch folder is created (or checked for existence).
            - The Google Drive service initialization is attempted.
            - An error log is generated indicating the failure.
        """
        main("cred.json", "watched_folder")

        mock_get_service.assert_called_once_with("cred.json", "token.json")
        mock_logger.error.assert_any_call("Google Drive service could not be initialized.")


if __name__ == "__main__":
    unittest.main()