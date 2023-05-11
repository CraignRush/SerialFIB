# Imports
import logging, sys
from src.FLM.utils.config import LOGGER_NAME_CLIENT, LOGGER_NAME_SERVER, LOGGING_LEVEL
# Configure logger
logger_client = logging.getLogger(LOGGER_NAME_CLIENT)    # Modul name
logger_client.setLevel(LOGGING_LEVEL)        # Log level
log_format = logging.Formatter( '%(asctime)s %(levelname)s:\t%(name)s:%(funcName)s()\t%(message)s')  # Log Format
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(log_format)
logger_client.addHandler(stream_handler)
file_handler = logging.FileHandler(filename='./client.log')
file_handler.setFormatter(log_format)
logger_client.addHandler(file_handler)
logger_client.propagate = False

# Configure logger
logger_server= logging.getLogger(LOGGER_NAME_SERVER)    # Modul name
logger_server.setLevel(LOGGING_LEVEL)        # Log level
log_format = logging.Formatter( '%(asctime)s %(levelname)s:\t%(name)s: %(funcName)s()\t%(message)s')  # Log Format
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(log_format)
logger_server.addHandler(stream_handler)
file_handler = logging.FileHandler(filename='./server.log')
file_handler.setFormatter(log_format)
logger_server.addHandler(file_handler)
logger_server.propagate = False