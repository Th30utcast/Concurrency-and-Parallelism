import os
from cryptography.fernet import Fernet

class Config:
    HOST = 'localhost'
    PORT = 5555
    MAX_CONNECTIONS = 3
    ALLOWED_FILE_TYPES = ('.docx', '.pdf', '.jpeg')
    BUFFER_SIZE = 65536
    DB_PATH = 'lu_connect.db'
    NOTIFICATION_SOUND = 'notification.wav'
    
    # Generate encryption key if it doesn't exist
    KEY_FILE = 'encryption.key'
    if not os.path.exists(KEY_FILE):
        with open(KEY_FILE, 'wb') as key_file:
            key_file.write(Fernet.generate_key())
    
    with open(KEY_FILE, 'rb') as key_file:
        ENCRYPTION_KEY = key_file.read()