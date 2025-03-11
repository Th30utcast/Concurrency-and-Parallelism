import hashlib
from cryptography.fernet import Fernet

class Security:
    def __init__(self, encryption_key):
        self.cipher_suite = Fernet(encryption_key)
    
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def encrypt_data(self, data):
        return self.cipher_suite.encrypt(data.encode())
    
    def decrypt_data(self, encrypted_data):
        return self.cipher_suite.decrypt(encrypted_data).decode()