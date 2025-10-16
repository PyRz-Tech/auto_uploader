import unittest
from unittest.mock import patch, mock_open
import json
from src.file_utils import save_file_mapping
from src.file_utils import remove_file_mapping


class TestSaveFileMapping(unittest.TestCase):
    """
    Unit tests for the save_file_mapping function in the src.file_utils module.

    This test suite verifies the behavior of the save_file_mapping function, which saves
    or updates a file-to-ID mapping in a JSON file. The tests cover scenarios including
    creating a new mapping file, updating an existing mapping, handling corrupted JSON,
    and handling write errors, using mocking to simulate file operations and JSON handling.
    """

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists", return_value=False)
    @patch("src.file_utils.logger")
    def test_create_new_mapping_file(self, mock_logger, mock_path_exists, mock_file):
        """
        Test that save_file_mapping creates a new mapping file.

        Mocks file operations to simulate the absence of a mapping file, ensuring the
        function creates a new file and saves the mapping.

        Args:
            mock_logger (MagicMock): Mock for the logger object.
            mock_path_exists (MagicMock): Mock for os.path.exists function.
            mock_file (MagicMock): Mock for the built-in open function.

        Asserts:
            - The file is opened in write mode.
            - The write method is called.
            - An info log confirms the mapping is saved.
        """
        save_file_mapping("dummy_path.json", "file.txt", "123")
        mock_file.assert_called_with("dummy_path.json", "w")
        handle = mock_file()
        handle.write.assert_called()
        mock_logger.info.assert_called_with("Mapping saved for 'file.txt' (ID: 123)")

    @patch("builtins.open", new_callable=mock_open, read_data='{"old_file.txt": "999"}')
    @patch("os.path.exists", return_value=True)
    @patch("json.dump")
    @patch("src.file_utils.logger")
    def test_update_existing_mapping(self, mock_logger, mock_json_dump, mock_path_exists, mock_file):
        """
        Test that save_file_mapping updates an existing mapping file.

        Mocks file operations to simulate an existing mapping file, ensuring the function
        updates the file with the new mapping while preserving existing entries.

        Args:
            mock_logger (MagicMock): Mock for the logger object.
            mock_json_dump (MagicMock): Mock for json.dump function.
            mock_path_exists (MagicMock): Mock for os.path.exists function.
            mock_file (MagicMock): Mock for the built-in open function.

        Asserts:
            - The updated mapping includes both old and new entries.
            - An info log confirms the mapping is saved.
        """
        save_file_mapping("dummy_path.json", "file.txt", "123")
        expected = {"old_file.txt": "999", "file.txt": "123"}
        mock_json_dump.assert_called_with(expected, mock_file())
        mock_logger.info.assert_called_with("Mapping saved for 'file.txt' (ID: 123)")

    @patch("builtins.open", new_callable=mock_open, read_data='invalid_json')
    @patch("os.path.exists", return_value=True)
    @patch("json.dump")
    @patch("src.file_utils.logger")
    def test_corrupted_json_recreates_file(self, mock_logger, mock_json_dump, mock_path_exists, mock_file):
        """
        Test that save_file_mapping recreates the file when JSON is corrupted.

        Mocks file operations to simulate a corrupted JSON file, ensuring the function
        logs a warning, recreates the file, and saves the new mapping.

        Args:
            mock_logger (MagicMock): Mock for the logger object.
            mock_json_dump (MagicMock): Mock for json.dump function.
            mock_path_exists (MagicMock): Mock for os.path.exists function.
            mock_file (MagicMock): Mock for the built-in open function.

        Asserts:
            - A warning log is generated for corrupted JSON.
            - The json.dump function is called to save the new mapping.
        """
        save_file_mapping("dummy_path.json", "file.txt", "123")
        mock_logger.warning.assert_called_with("Corrupted JSON in dummy_path.json. Recreating file.")
        mock_json_dump.assert_called()

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists", return_value=False)
    @patch("json.dump", side_effect=Exception("Write error"))
    @patch("src.file_utils.logger")
    def test_write_error_logged(self, mock_logger, mock_json_dump, mock_path_exists, mock_file):
        """
        Test that save_file_mapping handles write errors.

        Mocks file operations and json.dump to simulate a write error, ensuring the
        function logs an error and continues gracefully.

        Args:
            mock_logger (MagicMock): Mock for the logger object.
            mock_json_dump (MagicMock): Mock for json.dump function.
            mock_path_exists (MagicMock): Mock for os.path.exists function.
            mock_file (MagicMock): Mock for the built-in open function.

        Asserts:
            - An error log is generated for the write failure.
        """
        save_file_mapping("dummy_path.json", "file.txt", "123")
        mock_logger.error.assert_called_with("Failed to write mapping file: Write error")


class TestRemoveFileMapping(unittest.TestCase):
    """
    Unit tests for the remove_file_mapping function in the src.file_utils module.

    This test suite verifies the behavior of the remove_file_mapping function, which
    removes a file-to-ID mapping from a JSON file. The tests cover scenarios including
    a non-existent mapping file, errors reading the file, removing an existing mapping,
    errors writing the updated mapping, and attempting to remove a non-existent mapping,
    using mocking to simulate file operations and JSON handling.
    """

    @patch("os.path.exists", return_value=False)
    @patch("src.file_utils.logger")
    def test_mapping_file_not_exists(self, mock_logger, mock_exists):
        """
        Test that remove_file_mapping handles a non-existent mapping file.

        Mocks os.path.exists to simulate a missing mapping file, ensuring a warning is
        logged and the function exits gracefully.

        Args:
            mock_logger (MagicMock): Mock for the logger object.
            mock_exists (MagicMock): Mock for os.path.exists function.

        Asserts:
            - A warning log is generated indicating the file does not exist.
        """
        remove_file_mapping("dummy.json", "file.txt")
        mock_logger.warning.assert_called_with("dummy.json does not exist.")

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists", return_value=True)
    @patch("json.load", side_effect=Exception("Read error"))
    @patch("src.file_utils.logger")
    def test_error_reading_mapping_file(self, mock_logger, mock_json_load, mock_exists, mock_file):
        """
        Test that remove_file_mapping handles errors reading the mapping file.

        Mocks file operations and json.load to simulate a read error, ensuring an error
        is logged and the function exits gracefully.

        Args:
            mock_logger (MagicMock): Mock for the logger object.
            mock_json_load (MagicMock): Mock for json.load function.
            mock_exists (MagicMock): Mock for os.path.exists function.
            mock_file (MagicMock): Mock for the built-in open function.

        Asserts:
            - An error log is generated for the read failure.
        """
        remove_file_mapping("dummy.json", "file.txt")
        mock_logger.error.assert_called_with("Error reading mapping file: Read error")

    @patch("builtins.open", new_callable=mock_open, read_data='{"file.txt": "123", "other.txt": "999"}')
    @patch("os.path.exists", return_value=True)
    @patch("src.file_utils.logger")
    def test_remove_existing_file_mapping(self, mock_logger, mock_exists, mock_file):
        """
        Test that remove_file_mapping removes an existing file mapping.

        Mocks file operations to simulate a valid JSON mapping file, ensuring the
        specified file is removed from the mapping and the updated mapping is saved.

        Args:
            mock_logger (MagicMock): Mock for the logger object.
            mock_exists (MagicMock): Mock for os.path.exists function.
            mock_file (MagicMock): Mock for the built-in open function.

        Asserts:
            - The specified file is removed from the mapping.
            - Other mappings remain intact.
            - An info log confirms the mapping removal.
        """
        remove_file_mapping("dummy.json", "file.txt")

        handle = mock_file()
        written = "".join(call.args[0] for call in handle.write.call_args_list)
        written_data = json.loads(written)

        self.assertNotIn("file.txt", written_data)
        self.assertIn("other.txt", written_data)
        mock_logger.info.assert_called_with("Removed file mapping for 'file.txt'")

    @patch("builtins.open", new_callable=mock_open, read_data='{"file.txt": "123"}')
    @patch("os.path.exists", return_value=True)
    @patch("json.dump", side_effect=Exception("Write error"))
    @patch("src.file_utils.logger")
    def test_error_writing_mapping_file(self, mock_logger, mock_json_dump, mock_exists, mock_file):
        """
        Test that remove_file_mapping handles errors writing the mapping file.

        Mocks file operations and json.dump to simulate a write error, ensuring an
        error is logged and the function handles the failure gracefully.

        Args:
            mock_logger (MagicMock): Mock for the logger object.
            mock_json_dump (MagicMock): Mock for json.dump function.
            mock_exists (MagicMock): Mock for os.path.exists function.
            mock_file (MagicMock): Mock for the built-in open function.

        Asserts:
            - An error log is generated for the write failure.
        """
        remove_file_mapping("dummy.json", "file.txt")
        mock_logger.error.assert_called_with("Error writing mapping file: Write error")

    @patch("builtins.open", new_callable=mock_open, read_data='{"other.txt": "999"}')
    @patch("os.path.exists", return_value=True)
    @patch("src.file_utils.logger")
    def test_file_not_in_mapping(self, mock_logger, mock_exists, mock_file):
        """
        Test that remove_file_mapping handles a non-existent file in the mapping.

        Mocks file operations to simulate a valid JSON file without the specified file,
        ensuring a warning is logged and the function exits gracefully.

        Args:
            mock_logger (MagicMock): Mock for the logger object.
            mock_exists (MagicMock): Mock for os.path.exists function.
            mock_file (MagicMock): Mock for the built-in open function.

        Asserts:
            - A warning log is generated indicating the file is not in the mapping.
        """
        remove_file_mapping("dummy.json", "file.txt")
        mock_logger.warning.assert_called_with("'file.txt' not found in file mapping.")


if __name__ == "__main__":
    unittest.main()