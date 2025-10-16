import socket
import logging

logger = logging.getLogger(__name__)

def is_internet_connected():
    """
    Check if an internet connection is available.

    Attempts to establish a socket connection to a public DNS server (8.8.8.8:53)
    with a timeout of 3 seconds to determine if an internet connection is active.

    Returns:
        bool: True if the connection is successful, False otherwise.

    Notes:
        - Uses Google's public DNS server (8.8.8.8, port 53) as the target for the connection check.
        - Logs an info message when checking connectivity and upon successful connection.
        - Logs a warning if the connection attempt fails due to an OSError.
    """
    try:
        logger.info("Checking internet connectivity...")
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        logger.info("Internet connection detected.")
        return True
    except OSError:
        logger.warning("No internet connection detected.")
        return False