"""
Unit tests for the Google Drive AutoUploader application runner.

This module contains test cases for the app_runner module, focusing on validating
path checks, configuration loading, and application startup. It uses unittest and
mock to simulate file system operations and configuration loading, ensuring the
application behaves correctly under various conditions.
"""
import os
import unittest
from unittest import mock
from src import app_runner


class TestRunModule(unittest.TestCase):
    """
    Test suite for the app_runner module.

    Tests the functionality of path validation, configuration loading, and application
    startup in the Google Drive AutoUploader application.
    """

    @mock.patch("os.path.isfile")
    @mock.patch("os.path.isdir")
    def test_validate_paths_all_valid(self, mock_isdir, mock_isfile):
        """
        Test validate_paths when both credentials file and watch folder are valid.

        Mocks os.path.isfile and os.path.isdir to return True, simulating valid paths.
        Verifies that validate_paths executes without raising an exception.

        Args:
            mock_isdir (MagicMock): Mock for os.path.isdir.
            mock_isfile (MagicMock): Mock for os.path.isfile.
        """
        mock_isfile.return_value = True
        mock_isdir.return_value = True
        app_runner.validate_paths("fake_credentials.json", "/fake/watch_folder")

    @mock.patch("os.path.isfile")
    @mock.patch("os.path.isdir")
    def test_validate_paths_missing_credentials(self, mock_isdir, mock_isfile):
        """
        Test validate_paths when the credentials file is missing.

        Mocks os.path.isfile to return False and os.path.isdir to return True, simulating
        a missing credentials file. Verifies that a SystemExit is raised.

        Args:
            mock_isdir (MagicMock): Mock for os.path.isdir.
            mock_isfile (MagicMock): Mock for os.path.isfile.
        """
        mock_isfile.return_value = False
        mock_isdir.return_value = True
        with self.assertRaises(SystemExit):
            app_runner.validate_paths("fake_credentials.json", "/fake/watch_folder")

    @mock.patch("os.path.isfile")
    @mock.patch("os.path.isdir")
    def test_validate_paths_missing_folder(self, mock_isdir, mock_isfile):
        """
        Test validate_paths when the watch folder is missing.

        Mocks os.path.isfile to return True and os.path.isdir to return False, simulating
        a missing watch folder. Verifies that a SystemExit is raised.

        Args:
            mock_isdir (MagicMock): Mock for os.path.isdir.
            mock_isfile (MagicMock): Mock for os.path.isfile.
        """
        mock_isfile.return_value = True
        mock_isdir.return_value = False
        with self.assertRaises(SystemExit):
            app_runner.validate_paths("fake_credentials.json", "/fake/watch_folder")

    @mock.patch("os.path.isfile")
    @mock.patch("os.path.isdir")
    def test_validate_paths_both_missing(self, mock_isdir, mock_isfile):
        """
        Test validate_paths when both credentials file and watch folder are missing.

        Mocks os.path.isfile and os.path.isdir to return False, simulating both paths
        being invalid. Verifies that a SystemExit is raised.

        Args:
            mock_isdir (MagicMock): Mock for os.path.isdir.
            mock_isfile (MagicMock): Mock for os.path.isfile.
        """
        mock_isfile.return_value = False
        mock_isdir.return_value = False
        with self.assertRaises(SystemExit):
            app_runner.validate_paths("fake_credentials.json", "/fake/watch_folder")

    @mock.patch("src.app_runner.main")
    @mock.patch("os.path.isfile")
    @mock.patch("os.path.isdir")
    def test_start_app_calls_main(self, mock_isdir, mock_isfile, mock_main):
        """
        Test start_app to ensure it calls the main function with correct arguments.

        Mocks os.path.isfile and os.path.isdir to return True, and mocks the main function
        to verify it is called with the provided credentials and folder paths.

        Args:
            mock_isdir (MagicMock): Mock for os.path.isdir.
            mock_isfile (MagicMock): Mock for os.path.isfile.
            mock_main (MagicMock): Mock for app_runner.main.
        """
        mock_isfile.return_value = True
        mock_isdir.return_value = True
        app_runner.start_app("fake_credentials.json", "/fake/watch_folder")
        mock_main.assert_called_once_with("fake_credentials.json", "/fake/watch_folder")

    @mock.patch("src.app_runner.load_config")
    @mock.patch("src.app_runner.logger")
    def test_load_config_file_not_found(self, mock_logger, mock_load_config):
        """
        Test get_config when the configuration file is not found.

        Mocks load_config to raise a FileNotFoundError and verifies that the error is
        logged and re-raised.

        Args:
            mock_logger (MagicMock): Mock for app_runner.logger.
            mock_load_config (MagicMock): Mock for app_runner.load_config.
        """
        mock_load_config.side_effect = FileNotFoundError("file missing")
        with self.assertRaises(FileNotFoundError):
            app_runner.get_config()
        mock_logger.error.assert_called_with("Config file not found: file missing")

    @mock.patch("src.app_runner.load_config")
    @mock.patch("src.app_runner.logger")
    def test_load_config_missing_key(self, mock_logger, mock_load_config):
        """
        Test get_config when a required configuration key is missing.

        Mocks load_config to raise a KeyError and verifies that the error is logged
        and re-raised.

        Args:
            mock_logger (MagicMock): Mock for app_runner.logger.
            mock_load_config (MagicMock): Mock for app_runner.load_config.
        """
        mock_load_config.side_effect = KeyError("missing key")
        with self.assertRaises(KeyError):
            app_runner.get_config()
        mock_logger.error.assert_called_with("Missing config key: 'missing key'")

    @mock.patch("src.app_runner.load_config")
    @mock.patch("src.app_runner.logger")
    def test_load_config_unexpected_exception(self, mock_logger, mock_load_config):
        """
        Test get_config when an unexpected error occurs during configuration loading.

        Mocks load_config to raise a RuntimeError and verifies that the error is logged
        and re-raised.

        Args:
            mock_logger (MagicMock): Mock for app_runner.logger.
            mock_load_config (MagicMock): Mock for app_runner.load_config.
        """
        mock_load_config.side_effect = RuntimeError("unexpected error")
        with self.assertRaises(RuntimeError):
            app_runner.get_config()
        mock_logger.error.assert_called_with("Unexpected error loading config: unexpected error")

    @mock.patch("src.app_runner.main")
    @mock.patch("src.app_runner.validate_paths")
    @mock.patch("src.app_runner.load_config")
    def test_run_calls_get_config_and_start_app(self, mock_get_config, mock_start_app, mock_main):
        """
        Test run to ensure it calls get_config and start_app with correct arguments.

        Mocks load_config to return a valid configuration, and verifies that get_config
        and start_app are called with the expected credentials and folder paths.

        Args:
            mock_get_config (MagicMock): Mock for app_runner.load_config.
            mock_start_app (MagicMock): Mock for app_runner.start_app.
            mock_main (MagicMock): Mock for app_runner.main.
        """
        mock_get_config.return_value = {
            "credentials": "/fake/credentials.json",
            "local_folder": "/fake/watch_folder"
        }
        app_runner.run()
        mock_get_config.assert_called_once()
        mock_start_app.assert_called_once_with("/fake/credentials.json", "/fake/watch_folder")

if __name__ == "__main__":
    unittest.main()