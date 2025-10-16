import unittest
from unittest.mock import patch, mock_open
import os
import json
from src import config_loader


class TestConfigLoader(unittest.TestCase):
    """
    Unit tests for the load_config function in the src.config_loader module.

    This test suite verifies the behavior of the load_config function, which loads
    and updates configuration settings for the Google Drive AutoUploader. The tests
    cover scenarios including loading an existing configuration file with command-line
    arguments, handling invalid JSON with user input, and creating a new configuration
    file when none exists, using mocking to simulate file operations, command-line
    arguments, and user input.
    """

    @patch(
        "src.config_loader.open",
        new_callable=mock_open,
        read_data='{"credentials": "old.json", "local_folder": "old_folder"}'
    )
    @patch(
        "src.config_loader.os.path.exists",
        return_value=True
    )
    @patch(
        "src.config_loader.argparse.ArgumentParser.parse_args",
        return_value=type("Args", (), {"credentials": "new.json", "watch_folder": "new_folder"})()
    )
    def test_load_config_with_existing_file_and_args(self, mock_args, mock_exists, mock_file):
        """
        Test that load_config updates configuration with command-line arguments.

        Mocks file operations, os.path.exists, and command-line arguments to simulate
        loading an existing configuration file and overriding it with new values from
        command-line arguments. Verifies that the updated configuration is saved.

        Args:
            mock_args (MagicMock): Mock for argparse.ArgumentParser.parse_args.
            mock_exists (MagicMock): Mock for os.path.exists function.
            mock_file (MagicMock): Mock for the built-in open function.

        Asserts:
            - The returned configuration contains the values from command-line arguments.
            - The configuration file is opened in write mode to save the updated values.
            - The written configuration matches the command-line arguments.
        """
        result = config_loader.load_config()

        self.assertEqual(result["credentials"], "new.json")
        self.assertEqual(result["local_folder"], "new_folder")

        mock_file.assert_any_call(os.path.join(config_loader.BASE_DIR, "config.json"), "w")
        handle = mock_file()
        written_content = "".join(call[0][0] for call in handle.write.call_args_list)
        written_data = json.loads(written_content)
        self.assertEqual(written_data["credentials"], "new.json")
        self.assertEqual(written_data["local_folder"], "new_folder")

    @patch("builtins.input", side_effect=["input_cred.json", "input_folder"])
    @patch("src.config_loader.open", new_callable=mock_open, read_data='invalid data')
    @patch("os.path.exists", return_value=True)
    @patch("argparse.ArgumentParser.parse_args", return_value=type("Args", (), {"credentials": "", "watch_folder": ""})())
    def test_load_config_with_invalid_json_and_input(self, mock_args, mock_exists, mock_file, mock_input):
        """
        Test that load_config handles invalid JSON by using user input.

        Mocks file operations, os.path.exists, command-line arguments, and user input
        to simulate a corrupted JSON configuration file, ensuring the function falls
        back to user input and saves the new configuration.

        Args:
            mock_args (MagicMock): Mock for argparse.ArgumentParser.parse_args.
            mock_exists (MagicMock): Mock for os.path.exists function.
            mock_file (MagicMock): Mock for the built-in open function.
            mock_input (MagicMock): Mock for the built-in input function.

        Asserts:
            - The returned configuration contains values from user input.
            - The configuration file is opened in write mode to save the new values.
        """
        result = config_loader.load_config()

        self.assertEqual(result["credentials"], "input_cred.json")
        self.assertEqual(result["local_folder"], "input_folder")

        mock_file.assert_any_call(os.path.join(config_loader.BASE_DIR, "config.json"), "w")

    @patch("builtins.input", side_effect=["cred.json", "folder"])
    @patch("os.path.exists", return_value=False)
    @patch("builtins.open", new_callable=mock_open)
    @patch("argparse.ArgumentParser.parse_args", return_value=type("Args", (), {"credentials": "", "watch_folder": ""})())
    def test_load_config_creates_new_file(self, mock_args, mock_open_file, mock_exists, mock_input):
        """
        Test that load_config creates a new configuration file with user input.

        Mocks file operations, os.path.exists, command-line arguments, and user input
        to simulate the absence of a configuration file, ensuring the function prompts
        for user input and creates a new file with the provided values.

        Args:
            mock_args (MagicMock): Mock for argparse.ArgumentParser.parse_args.
            mock_open_file (MagicMock): Mock for the built-in open function.
            mock_exists (MagicMock): Mock for os.path.exists function.
            mock_input (MagicMock): Mock for the built-in input function.

        Asserts:
            - The returned configuration contains values from user input.
            - The configuration file is opened in write mode to create a new file.
        """
        result = config_loader.load_config()

        self.assertEqual(result["credentials"], "cred.json")
        self.assertEqual(result["local_folder"], "folder")
        mock_open_file.assert_called_with(os.path.join(config_loader.BASE_DIR, "config.json"), "w")


if __name__ == "__main__":
    unittest.main()