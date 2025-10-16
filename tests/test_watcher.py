import os
import unittest
from unittest.mock import patch, Mock, mock_open
import tempfile
from src.watcher import Watcher


class TestWatcher(unittest.TestCase):
    """
    Unit tests for the Watcher class in the src.watcher module.

    This test suite verifies the behavior of the Watcher class, which monitors a local
    directory for file changes and synchronizes them with Google Drive. The tests cover
    scenarios including folder ID management, file creation, modification, deletion,
    movement, and observer lifecycle, using mocking to simulate file operations, Google
    Drive API interactions, and observer behavior, along with a temporary directory for
    testing.
    """

    def setUp(self):
        """
        Set up a temporary directory and mock service for each test.

        Creates a temporary directory for testing file operations and initializes a mock
        Google Drive service.

        Attributes:
            temp_dir (TemporaryDirectory): Temporary directory for testing.
            watch_folder (str): Path to the temporary directory.
            service_mock (Mock): Mock for the Google Drive service.
        """
        self.temp_dir = tempfile.TemporaryDirectory()
        self.watch_folder = self.temp_dir.name
        self.service_mock = Mock()

    def tearDown(self):
        """
        Clean up the temporary directory after each test.

        Ensures the temporary directory is removed to prevent side effects between tests.
        """
        self.temp_dir.cleanup()

    @patch("src.watcher.open", new_callable=lambda: mock_open(read_data="existing_id"))
    @patch("src.watcher.os.path.exists", return_value=True)
    def test_get_or_create_folder_id_reads_existing(self, mock_exists, mock_open_fn):
        """
        Test that get_or_create_folder_id reads an existing folder ID from file.

        Mocks file operations to simulate an existing folder ID file, ensuring the ID
        is read correctly and returned.

        Args:
            mock_exists (Mock): Mock for os.path.exists function.
            mock_open_fn (Mock): Mock for the built-in open function.

        Asserts:
            - The correct folder ID is returned.
            - The folder ID file is opened in read mode with UTF-8 encoding.
        """
        w = Watcher(service=self.service_mock, watch_folder=self.watch_folder, base_dir=self.watch_folder)
        folder_id = w.get_or_create_folder_id()
        self.assertEqual(folder_id, "existing_id")
        mock_open_fn.assert_called_with(w.folder_id_file, "r", encoding="utf-8")

    @patch("builtins.open", side_effect=Exception("read fail"))
    @patch("src.watcher.logger")
    @patch("src.watcher.get_or_create_drive_folder", return_value="new_id")
    @patch("src.watcher.os.path.exists", return_value=True)
    def test_get_or_create_folder_id_read_exception(self, mock_exists, mock_get_folder, mock_logger, mock_file):
        """
        Test that get_or_create_folder_id handles read exceptions.

        Mocks file operations and get_or_create_drive_folder to simulate a failure when
        reading the folder ID file, ensuring the function falls back to creating a new
        folder ID and logs an error.

        Args:
            mock_exists (Mock): Mock for os.path.exists function.
            mock_get_folder (Mock): Mock for get_or_create_drive_folder function.
            mock_logger (Mock): Mock for the logger object.
            mock_file (Mock): Mock for the built-in open function.

        Asserts:
            - The new folder ID is returned.
            - An error is logged for the read failure.
        """
        watcher = Watcher(service=self.service_mock, watch_folder=self.watch_folder)
        folder_id = watcher.get_or_create_folder_id()
        self.assertEqual(folder_id, "new_id")
        mock_logger.error.assert_called()

    @patch("builtins.open", side_effect=Exception("disk full"))
    @patch("src.watcher.logger")
    @patch("src.watcher.get_or_create_drive_folder", return_value="folder999")
    @patch("src.watcher.os.path.exists", return_value=False)
    def test_get_or_create_folder_id_save_exception(self, mock_exists, mock_get_folder, mock_logger, mock_file):
        """
        Test that get_or_create_folder_id handles save exceptions.

        Mocks file operations and get_or_create_drive_folder to simulate a failure when
        saving the folder ID, ensuring the function returns the new folder ID and logs
        an error.

        Args:
            mock_exists (Mock): Mock for os.path.exists function.
            mock_get_folder (Mock): Mock for get_or_create_drive_folder function.
            mock_logger (Mock): Mock for the logger object.
            mock_file (Mock): Mock for the built-in open function.

        Asserts:
            - The new folder ID is returned.
            - An error is logged for the save failure.
        """
        watcher = Watcher(service=self.service_mock, watch_folder=self.watch_folder)
        folder_id = watcher.get_or_create_folder_id()
        self.assertEqual(folder_id, "folder999")
        mock_logger.error.assert_called()

    @patch("src.watcher.upload_file")
    @patch("src.watcher.get_or_create_drive_folder", return_value="folder123")
    def test_on_created_triggers_upload(self, mock_get_folder, mock_upload):
        """
        Test that on_created triggers file upload for non-directory files.

        Mocks get_or_create_drive_folder and upload_file to simulate a file creation
        event, ensuring the upload function is called.

        Args:
            mock_get_folder (Mock): Mock for get_or_create_drive_folder function.
            mock_upload (Mock): Mock for upload_file function.

        Asserts:
            - The upload_file function is called once.
        """
        watcher = Watcher(service=self.service_mock, watch_folder=self.watch_folder)
        event = Mock(is_directory=False, src_path="/path/to/file.txt")
        watcher.on_created(event)
        mock_upload.assert_called_once()

    @patch("src.watcher.upload_file")
    @patch("src.watcher.get_or_create_drive_folder", return_value="folder123")
    def test_on_modified_triggers_upload(self, mock_get_folder, mock_upload):
        """
        Test that on_modified triggers file upload for non-directory files.

        Mocks get_or_create_drive_folder and upload_file to simulate a file modification
        event, ensuring the upload function is called.

        Args:
            mock_get_folder (Mock): Mock for get_or_create_drive_folder function.
            mock_upload (Mock): Mock for upload_file function.

        Asserts:
            - The upload_file function is called once.
        """
        watcher = Watcher(service=self.service_mock, watch_folder=self.watch_folder)
        event = Mock(is_directory=False, src_path="/path/to/file.txt")
        watcher.on_modified(event)
        mock_upload.assert_called_once()

    @patch("src.watcher.upload_file")
    def test_on_modified_ignores_hidden_files_and_dirs(self, mock_upload):
        """
        Test that on_modified ignores hidden files and directories.

        Simulates hidden file and directory modification events, ensuring the upload
        function is not called.

        Args:
            mock_upload (Mock): Mock for upload_file function.

        Asserts:
            - The upload_file function is not called for hidden files or directories.
        """
        watcher = Watcher(service=self.service_mock, watch_folder=self.watch_folder)
        hidden_event = Mock(is_directory=False, src_path="/path/to/.hidden.txt")
        dir_event = Mock(is_directory=True, src_path="/path/to/dir")
        watcher.on_modified(hidden_event)
        watcher.on_modified(dir_event)
        mock_upload.assert_not_called()

    @patch("src.watcher.delete_file_from_drive")
    def test_on_deleted_triggers_delete(self, mock_delete):
        """
        Test that on_deleted triggers file deletion for non-directory files.

        Mocks delete_file_from_drive to simulate a file deletion event, ensuring the
        delete function is called.

        Args:
            mock_delete (Mock): Mock for delete_file_from_drive function.

        Asserts:
            - The delete_file_from_drive function is called once.
        """
        watcher = Watcher(service=self.service_mock, watch_folder=self.watch_folder)
        event = Mock(is_directory=False, src_path="/path/to/file.txt")
        watcher.on_deleted(event)
        mock_delete.assert_called_once()

    @patch("src.watcher.delete_file_from_drive")
    def test_on_deleted_ignores_hidden_and_dirs(self, mock_delete):
        """
        Test that on_deleted ignores hidden files and directories.

        Simulates hidden file and directory deletion events, ensuring the delete
        function is not called.

        Args:
            mock_delete (Mock): Mock for delete_file_from_drive function.

        Asserts:
            - The delete_file_from_drive function is not called for hidden files or directories.
        """
        watcher = Watcher(service=self.service_mock, watch_folder=self.watch_folder)
        hidden_event = Mock(is_directory=False, src_path="/path/to/.hidden.txt")
        dir_event = Mock(is_directory=True, src_path="/path/to/dir")
        watcher.on_deleted(hidden_event)
        watcher.on_deleted(dir_event)
        mock_delete.assert_not_called()

    @patch("src.watcher.delete_file_from_drive")
    def test_on_moved_triggers_delete_when_to_trash(self, mock_delete):
        """
        Test that on_moved triggers deletion when a file is moved to the trash.

        Mocks delete_file_from_drive to simulate a file being moved to the trash,
        ensuring the delete function is called.

        Args:
            mock_delete (Mock): Mock for delete_file_from_drive function.

        Asserts:
            - The delete_file_from_drive function is called once for trash movement.
        """
        watcher = Watcher(service=self.service_mock, watch_folder=self.watch_folder)
        event = Mock(is_directory=False, src_path="/path/to/file.txt",
                     dest_path="/.local/share/Trash/file.txt")
        watcher.on_moved(event)
        mock_delete.assert_called_once()

    @patch("src.watcher.delete_file_from_drive")
    def test_on_moved_ignores_non_trash(self, mock_delete):
        """
        Test that on_moved ignores file movements not to the trash.

        Simulates a file movement to a non-trash location, ensuring the delete function
        is not called.

        Args:
            mock_delete (Mock): Mock for delete_file_from_drive function.

        Asserts:
            - The delete_file_from_drive function is not called for non-trash movements.
        """
        watcher = Watcher(service=self.service_mock, watch_folder=self.watch_folder)
        event = Mock(is_directory=False, src_path="/path/to/file.txt",
                     dest_path="/other/path/file.txt")
        watcher.on_moved(event)
        mock_delete.assert_not_called()

    @patch("builtins.open", new_callable=Mock)
    @patch("os.path.exists", return_value=False)
    @patch("src.watcher.get_or_create_drive_folder", return_value="dummy_folder_id")
    @patch("src.watcher.logger")
    @patch("time.sleep", side_effect=KeyboardInterrupt)
    @patch("src.watcher.Observer")
    def test_run_starts_and_stops(self, mock_observer, mock_sleep, mock_logger, mock_get_folder, mock_exists, mock_open):
        """
        Test that the run method starts and stops the observer correctly.

        Mocks file operations, get_or_create_drive_folder, and the Observer class to
        simulate the lifecycle of the watcher, ensuring it starts, schedules, and stops
        correctly on KeyboardInterrupt.

        Args:
            mock_observer (Mock): Mock for the Observer class.
            mock_sleep (Mock): Mock for time.sleep function.
            mock_logger (Mock): Mock for the logger object.
            mock_get_folder (Mock): Mock for get_or_create_drive_folder function.
            mock_exists (Mock): Mock for os.path.exists function.
            mock_open (Mock): Mock for the built-in open function.

        Asserts:
            - The observer is created and scheduled.
            - The observer starts and stops correctly.
            - An info log confirms the observer has started.
        """
        mock_instance = Mock()
        mock_observer.return_value = mock_instance

        watcher = Watcher(service=Mock(), watch_folder="/some/folder")
        watcher.run()

        mock_observer.assert_called_once()
        mock_instance.schedule.assert_called_once()
        mock_instance.start.assert_called_once()
        mock_instance.stop.assert_called_once()
        mock_instance.join.assert_called_once()
        mock_logger.info.assert_any_call("Observer started. Watching for file changes...")

    @patch("src.watcher.get_or_create_drive_folder", return_value="drive_folder_123")
    @patch("src.watcher.os.makedirs")
    @patch("builtins.open", new_callable=mock_open)
    def test_folder_id_written_and_set(self, mock_file, mock_makedirs, mock_get_folder):
        """
        Test that get_or_create_folder_id writes and sets the folder ID correctly.

        Mocks file operations, directory creation, and get_or_create_drive_folder to
        simulate creating a new folder ID, ensuring it is written to a file and set in
        the watcher instance.

        Args:
            mock_file (Mock): Mock for the built-in open function.
            mock_makedirs (Mock): Mock for os.makedirs function.
            mock_get_folder (Mock): Mock for get_or_create_drive_folder function.

        Asserts:
            - The get_or_create_drive_folder function is called with the correct arguments.
            - The base directory is created (or checked for existence).
            - The folder ID is written to the file.
            - The folder ID is set in the watcher instance and returned.
        """
        watcher = Watcher(service=Mock(), watch_folder="/some/folder")
        
        watcher.folder_id = None

        folder_id = watcher.get_or_create_folder_id()

        mock_get_folder.assert_called_once_with(watcher.service, "folder")

        mock_makedirs.assert_called_once_with(watcher.base_dir, exist_ok=True)

        mock_file.assert_any_call(watcher.folder_id_file, "w", encoding="utf-8")
        mock_file().write.assert_called_once_with("drive_folder_123")

        self.assertEqual(watcher.folder_id, "drive_folder_123")

        self.assertEqual(folder_id, "drive_folder_123")

    @patch("src.watcher.upload_file")
    @patch("src.watcher.get_or_create_drive_folder", return_value="dummy_folder_id")
    def test_on_created_ignores_directories(self, mock_get_folder, mock_upload):
        """
        Test that on_created ignores directory creation events.

        Mocks get_or_create_drive_folder and upload_file to simulate a directory creation
        event, ensuring the upload function is not called.

        Args:
            mock_get_folder (Mock): Mock for get_or_create_drive_folder function.
            mock_upload (Mock): Mock for upload_file function.

        Asserts:
            - The upload_file function is not called for directories.
        """
        watcher = Watcher(service=Mock(), watch_folder="/some/folder")

        dir_event = Mock(is_directory=True, src_path="/some/folder/subdir")
        watcher.on_created(dir_event)

        mock_upload.assert_not_called()

    @patch("src.watcher.upload_file")
    @patch("src.watcher.get_or_create_drive_folder", return_value="dummy_folder_id")
    def test_on_created_ignores_hidden_files(self, mock_get_folder, mock_upload):
        """
        Test that on_created ignores hidden file creation events.

        Mocks get_or_create_drive_folder and upload_file to simulate a hidden file
        creation event, ensuring the upload function is not called.

        Args:
            mock_get_folder (Mock): Mock for get_or_create_drive_folder function.
            mock_upload (Mock): Mock for upload_file function.

        Asserts:
            - The upload_file function is not called for hidden files.
        """
        watcher = Watcher(service=Mock(), watch_folder="/some/folder")

        hidden_file_event = Mock(is_directory=False, src_path="/some/folder/.hidden_file.txt")
        watcher.on_created(hidden_file_event)

        mock_upload.assert_not_called()

    @patch("src.watcher.upload_file")
    @patch("src.watcher.get_or_create_drive_folder", return_value="dummy_folder_id")
    def test_on_moved_ignores_directories(self, mock_get_folder, mock_upload):
        """
        Test that on_moved ignores directory movement events.

        Mocks get_or_create_drive_folder and upload_file to simulate a directory movement
        event, ensuring the upload function is not called.

        Args:
            mock_get_folder (Mock): Mock for get_or_create_drive_folder function.
            mock_upload (Mock): Mock for upload_file function.

        Asserts:
            - The upload_file function is not called for directories.
        """
        watcher = Watcher(service=Mock(), watch_folder="/some/folder")

        dir_event = Mock(is_directory=True, src_path="/some/folder/subdir")
        watcher.on_moved(dir_event)

        mock_upload.assert_not_called()


if __name__ == "__main__":
    unittest.main()