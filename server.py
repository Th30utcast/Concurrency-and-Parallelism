import socket
import threading
import json
import sqlite3
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from config import Config  # Import Config class
from database import Database
from security import Security
from connection_manager import ConnectionManager
from file_handler import FileHandler

class ChatServer:
    def __init__(self):
        self.config = Config()
        self.db = Database(self.config.DB_PATH)
        self.security = Security(self.config.ENCRYPTION_KEY)
        self.connection_manager = ConnectionManager(self.config.MAX_CONNECTIONS)
        self.file_handler = FileHandler(self.config.ALLOWED_FILE_TYPES)
        self.thread_pool = ThreadPoolExecutor(max_workers=20)  # Create thread pool
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Add this line to reuse address
        self.server_socket.bind((self.config.HOST, self.config.PORT))
        self.server_socket.listen(5)
        self.active_user_ids = {}  # To track user_id to client_socket mapping
        print(f"Server started on {self.config.HOST}:{self.config.PORT}")
    
    def start(self):
        try:
            while True:
                client_socket, client_address = self.server_socket.accept()
                print(f"New connection request from {client_address}")
                #! Multi-threading 
                # Submit the client handling task to the thread pool
                self.thread_pool.submit(self.handle_client, client_socket, client_address)
        except KeyboardInterrupt:
            print("Server shutting down...")
        finally:
            self.server_socket.close()
            self.thread_pool.shutdown(wait=True)
                
    def handle_client(self, client_socket, client_address):
        user_id = None
        try:
            # Receive initial data
            encrypted_data = client_socket.recv(self.config.BUFFER_SIZE)
            if not encrypted_data:
                print(f"No data received from {client_address}")
                return
            data = json.loads(self.security.decrypt_data(encrypted_data))
            print(f"Received data from {client_address}: {data}")
            if data['type'] == 'register':
                
                #! Handle registration
                self.handle_registration(client_socket, data)
                return  # End processing after registration
            elif data['type'] == 'login':
                
                #! Handle login
                user_id = self.authenticate_user(data['username'], data['password'])
                if not user_id:
                    print(f"Authentication failed for {client_address}")
                    client_socket.send(self.security.encrypt_data(
                        json.dumps({"status": "auth_failed"})))
                    return
                print(f"Authentication successful for {client_address}")
                
                #! Semaphore, Acquire a connection slot
                if not self.connection_manager.acquire_connection():
                    
                    #! Add client to waiting queue
                    position, wait_time = self.connection_manager.add_to_waiting_queue(client_socket, client_address)
                    client_socket.send(self.security.encrypt_data(
                        json.dumps({
                            "status": "waiting",
                            "position": position,
                            "estimated_wait": wait_time
                        })
                    ))
                    return
                # Set up client session
                self.connection_manager.active_connections[user_id] = client_socket
                self.active_user_ids[client_socket] = user_id  # Track socket to user_id mapping
                client_socket.send(self.security.encrypt_data(
                    json.dumps({"status": "connected"})))
                print(f"Client {client_address} connected successfully")
                # Main message loop
                while True:
                    encrypted_data = client_socket.recv(self.config.BUFFER_SIZE)
                    if not encrypted_data:
                        break
                    data = json.loads(self.security.decrypt_data(encrypted_data))
                    print(f"Received message from {client_address}: {data}")
                    if data['type'] == 'message':
                        self.handle_message(user_id, data['content'])
                    elif data['type'] == 'file':
                        self.handle_file_transfer(user_id, data)
                    elif data['type'] == 'disconnect':
                        break
        except Exception as e:
            print(f"Error handling client {client_address}: {e}")
        finally:
            # ! Semaphore, Release the connection slot
            if user_id is not None:
                self.connection_manager.release_connection(user_id)
                if user_id in self.connection_manager.active_connections:
                    del self.connection_manager.active_connections[user_id]
            # Remove from active_user_ids mapping
            if client_socket in self.active_user_ids:
                del self.active_user_ids[client_socket]
            client_socket.close()
        
    def handle_registration(self, client_socket, data):
        username = data['username']
        password = data['password']
        try:
            with sqlite3.connect(self.config.DB_PATH) as conn:
                c = conn.cursor()
                c.execute('''
                    INSERT INTO users (username, password_hash)
                    VALUES (?, ?)
                ''', (username, self.security.hash_password(password)))
                conn.commit()
            # Send success response to the client
            client_socket.send(self.security.encrypt_data(json.dumps({
                "status": "registration_success"
            })))
        except sqlite3.IntegrityError:
            # Send failure response to the client if username already exists
            client_socket.send(self.security.encrypt_data(json.dumps({
                "status": "registration_failed",
                "message": "Username already exists"
            })))
        except Exception as e:
            # Send failure response to the client for any other exception
            client_socket.send(self.security.encrypt_data(json.dumps({
                "status": "registration_failed",
                "message": str(e)
            })))
            
    def authenticate_user(self, username, password):
        print(f"Authenticating user: {username}")
        with sqlite3.connect(self.config.DB_PATH) as conn:
            c = conn.cursor()
            # retrieve user_id and password_hash from the database
            c.execute('SELECT user_id, password_hash FROM users WHERE username = ?', (username,))
            result = c.fetchone()
            if result:
                print(f"User found: {result}")
                if self.security.hash_password(password) == result[1]:
                    print(f"Authentication successful for user: {username}")
                    return result[0]
                else:
                    print(f"Authentication failed for user: {username}")
            else:
                print(f"User not found: {username}")
            return None

    def handle_message(self, user_id, content):
        try:
            # Save message to the database
            with sqlite3.connect(self.config.DB_PATH) as conn:
                c = conn.cursor()
                c.execute('''
                    INSERT INTO messages (sender_id, content, timestamp)
                    VALUES (?, ?, ?)
                ''', (user_id, content, datetime.now()))
                conn.commit()
            # Broadcast the message to all connected clients
            message_data = {
                "type": "message",
                "sender": self.db.get_username(user_id),
                "content": content,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            # Make a copy of the active_connections dictionary to avoid modification during iteration
            active_connections = dict(self.connection_manager.active_connections)
            for client_id, client_socket in active_connections.items():
                try:
                    client_socket.send(self.security.encrypt_data(json.dumps(message_data)))
                except Exception as e:
                    print(f"Error sending message to client {client_id}: {e}")
                    # Remove the client from active connections
                    if client_id in self.connection_manager.active_connections:
                        del self.connection_manager.active_connections[client_id]
                    #! Semaphore released when client disconnects
                    self.connection_manager.release_connection(client_id)
        except Exception as e:
            print(f"Error handling message: {e}")

    # Attempt number 7
    # I don't believ this works. i giv up
    def handle_file_transfer(self, user_id, data):
        try:
            file_data = bytes.fromhex(data['content'])
            file_path = self.file_handler.save_file(file_data, data['filename'])
            # Save file metadata to the database
            with sqlite3.connect(self.config.DB_PATH) as conn:
                c = conn.cursor()
                c.execute('''
                    INSERT INTO messages (sender_id, content, timestamp, is_file, file_path)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, data['filename'], datetime.now(), True, file_path))
                conn.commit()
            # Notify all clients about the file
            # discconecting the client , idk why... maybe bcz file too big
            file_message = {
                "type": "message",
                "sender": self.db.get_username(user_id),
                "content": f"Shared a file: {data['filename']}",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            # Make a copy of the active_connections dictionary to avoid modification during iteration
            # nope this is not working
            active_connections = dict(self.connection_manager.active_connections)
            for client_id, client_socket in active_connections.items():
                try:
                    client_socket.send(self.security.encrypt_data(json.dumps(file_message)))
                except:
                    # Remove the client from active connections
                    if client_id in self.connection_manager.active_connections:
                        del self.connection_manager.active_connections[client_id]
                    #! Semaphore released when client disconnects
                    self.connection_manager.release_connection(client_id)
        except Exception as e:
            print(f"Error handling file transfer: {e}")

if __name__ == "__main__":
    server = ChatServer()
    server.start()