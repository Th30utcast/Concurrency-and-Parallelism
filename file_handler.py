import os
import uuid

class FileHandler:
    def __init__(self, allowed_types):
        self.allowed_types = allowed_types
        self.upload_dir = 'uploads'
        os.makedirs(self.upload_dir, exist_ok=True)
    
    def is_allowed_file(self, filename):
        return os.path.splitext(filename)[1].lower() in self.allowed_types
    
    def save_file(self, file_data, filename):
        if not self.is_allowed_file(filename):
            raise ValueError("File type not allowed")
        
        safe_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(self.upload_dir, safe_filename)
        
        with open(file_path, 'wb') as f:
            f.write(file_data)
        return file_path