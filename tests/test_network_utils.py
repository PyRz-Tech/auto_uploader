import unittest
from unittest.mock import patch, MagicMock
import socket

from src.network_utils import is_internet_connected


class TestInternetConnection(unittest.TestCase):
    """
    Unit tests for the is_internet_connected function in the src.network_utils module.

    This test suite verifies the behavior of the is_internet_connected function, which
    checks for an active internet connection by attempting to connect to a public DNS
    server (8.8.8.8:53). The tests cover scenarios including a successful connection and
    a failed connection, using mocking to simulate socket operations.
    """

    @patch("src.network_utils.socket.create_connection")
    def test_internet_connected(self, mock_create_connection):
        """
        Test that is_internet_connected returns True when a connection is successful.

        Mocks the socket.create_connection function to simulate a successful connection
        to the public DNS server, ensuring the function returns True and logs the
        appropriate messages.

        Args:
            mock_create_connection (MagicMock): Mock for socket.create_connection function.

        Asserts:
            - The function returns True.
            - The socket.create_connection is called with the correct parameters (Google's
              public DNS server 8.8.8.8, port 53, and a 3-second timeout).
        """
        mock_create_connection.return_value = MagicMock()
        
        result = is_internet_connected()
        self.assertTrue(result)
        mock_create_connection.assert_called_once_with(("8.8.8.8", 53), timeout=3)

    @patch("src.network_utils.socket.create_connection")
    def test_internet_not_connected(self, mock_create_connection):
        """
        Test that is_internet_connected returns False when a connection fails.

        Mocks the socket.create_connection function to simulate a failed connection
        by raising an OSError, ensuring the function returns False and logs the
        appropriate messages.

        Args:
            mock_create_connection (MagicMock): Mock for socket.create_connection function.

        Asserts:
            - The function returns False.
            - The socket.create_connection is called with the correct parameters (Google's
              public DNS server 8.8.8.8, port 53, and a 3-second timeout).
        """
        mock_create_connection.side_effect = OSError("No connection")
        
        result = is_internet_connected()
        self.assertFalse(result)
        mock_create_connection.assert_called_once_with(("8.8.8.8", 53), timeout=3)


if __name__ == "__main__":
    unittest.main()