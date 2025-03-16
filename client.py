import tkinter as tk
import threading
import json
import pygame
import os
import socket
from security import Security
from notification_manager import NotificationManager
from concurrent.futures import ThreadPoolExecutor
from tkinter import ttk, filedialog, messagebox
from config import Config


class ChatClient:
    def __init__(self):
        self.config = Config()
        self.security = Security(self.config.ENCRYPTION_KEY)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.notification_manager = NotificationManager(self.config.NOTIFICATION_SOUND)
        self.thread_pool = ThreadPoolExecutor(max_workers=10)
        self.is_connected = False

        self.setup_gui()
            
    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("LU-Connect")
        
        # Login frame
        self.login_frame = ttk.Frame(self.root, padding="10")
        self.login_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Label(self.login_frame, text="Username:").grid(row=0, column=0)
        self.username_var = tk.StringVar()
        ttk.Entry(self.login_frame, textvariable=self.username_var).grid(row=0, column=1)
        
        ttk.Label(self.login_frame, text="Password:").grid(row=1, column=0)
        self.password_var = tk.StringVar()
        ttk.Entry(self.login_frame, textvariable=self.password_var, show="*").grid(row=1, column=1)
        
        ttk.Button(self.login_frame, text="Login", command=self.login).grid(row=2, column=0, columnspan=2)
        ttk.Button(self.login_frame, text="Register", command=self.register).grid(row=3, column=0, columnspan=2)
        
        # Chat frame
        self.chat_frame = ttk.Frame(self.root, padding="10")
        
        self.messages_text = tk.Text(self.chat_frame, height=20, width=50)
        self.messages_text.grid(row=0, column=0, columnspan=2)
        
        self.message_var = tk.StringVar()
        ttk.Entry(self.chat_frame, textvariable=self.message_var).grid(row=1, column=0)
        
        ttk.Button(self.chat_frame, text="Send", command=self.send_message).grid(row=1, column=1)
        ttk.Button(self.chat_frame, text="Send File", command=self.send_file).grid(row=2, column=0)
        
        self.notification_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.chat_frame, text="Notifications", variable=self.notification_var).grid(row=2, column=1)

    def register(self):
        username = self.username_var.get()
        password = self.password_var.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Username and password are required")
            return
        
        try:
            # Establish a connection to the server
            self.socket.connect((self.config.HOST, self.config.PORT))
            
            # Send registration request to the server
            self.socket.send(self.security.encrypt_data(json.dumps({
                "type": "register",
                "username": username,
                "password": password
            })))
            
            # Handle response
            response = json.loads(self.security.decrypt_data(
                self.socket.recv(self.config.BUFFER_SIZE)))
            
            if response['status'] == 'registration_success':
                messagebox.showinfo("Success", "Registration successful! Please log in.")
            else:
                messagebox.showerror("Error", response.get('message', 'Registration failed'))
            
            # Close the connection after registration
            self.socket.close()
            # Create a new socket for future connections
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        except Exception as e:
            messagebox.showerror("Error", f"Registration failed: {e}")
            #! Excpetioon handling
            # Create a new socket in case of failure
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    def login(self):
        try:
            # Create a new socket connection for each login attempt
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.config.HOST, self.config.PORT))
            
            print("Connected to the server")
            
            # Send authentication
            auth_data = {
                "type": "login",
                "username": self.username_var.get(),
                "password": self.password_var.get()
            }
            self.socket.send(self.security.encrypt_data(json.dumps(auth_data)))
            
            print("Sent login request")
            
            # Handle response
            response = json.loads(self.security.decrypt_data(
                self.socket.recv(self.config.BUFFER_SIZE)))
            
            print(f"Received login response: {response}")
            
            if response['status'] == 'connected':
                self.is_connected = True
                self.login_frame.grid_remove()
                self.chat_frame.grid(row=0, column=0)

                #! Multi-threading
                # Use the thread pool to handle receiving messages
                self.receiver_future = self.thread_pool.submit(self.receive_messages)

            elif response['status'] == 'waiting':
                messagebox.showinfo(
                    "Waiting",
                    f"Server is full. You are position {response['position']} "
                    f"in queue. Estimated wait: {response['estimated_wait']} minutes")
            else:
                #! Error handling
                messagebox.showerror("Error", "Authentication failed")
                
        except Exception as e:
            print(f"Error during login: {e}")
            messagebox.showerror("Error", f"Connection failed: {e}")
            # Create a new socket in case of failure
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def send_message(self):
        message = self.message_var.get()
        if message and self.is_connected:
            data = {
                "type": "message",
                "content": message
            }
            self.socket.send(self.security.encrypt_data(json.dumps(data)))
            self.message_var.set("")
    
    def send_file(self):
        if not self.is_connected:
            messagebox.showerror("Error", "Not connected to server")
            return
            
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("Word Documents", "*.docx"),
                ("PDF Files", "*.pdf"),
                ("JPEG Images", "*.jpeg")
            ]
        )
        
        if file_path:
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            data = {
                "type": "file",
                "filename": os.path.basename(file_path),
                "content": file_data.hex()
            }
            self.socket.send(self.security.encrypt_data(json.dumps(data)))
    
    def receive_messages(self):
        print("Started receiving messages")
        
        while self.is_connected:
            try:
                encrypted_data = self.socket.recv(self.config.BUFFER_SIZE)
                if not encrypted_data:
                    self.is_connected = False
                    break
                
                data = json.loads(self.security.decrypt_data(encrypted_data))
                
                print(f"Received message: {data}")
                self.root.after(0, self.update_messages_text, data)
                
            except ConnectionAbortedError:
                print("Connection aborted")
                self.is_connected = False
                break
            except Exception as e:
                print(f"Error receiving message: {e}")
                self.is_connected = False
                break
        
        print("Stopped receiving messages")
        self.socket.close()
        #! Exception handling
        # Don't quit the root directly from a non-main thread
        self.root.after(0, self.handle_disconnection)
    
    def update_messages_text(self, data):
        if data['type'] == 'message':
            self.messages_text.insert(tk.END,
                f"[{data['timestamp']}] {data['sender']}: {data['content']}\n")
            if self.notification_var.get():
                self.notification_manager.play_notification(
                    json.dumps({"notifications": self.notification_var.get()}))
    
    def handle_disconnection(self):
        # Handle disconnection in the main thread
        if self.is_connected == False:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            messagebox.showinfo("Disconnected", "You have been disconnected from the server")
            self.chat_frame.grid_remove()
            self.login_frame.grid(row=0, column=0)
        
    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()

    def on_close(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.is_connected = False
            # Only attempt to send disconnect if connected
            try:
                if self.socket.fileno() != -1:  # Check if socket is still valid
                    # Send a disconnect message to the server
                    disconnect_message = {
                        "type": "disconnect"
                    }
                    self.socket.send(self.security.encrypt_data(json.dumps(disconnect_message)))
                    # Close the socket connection
                    self.socket.close()
            except:
                pass
            # Shutdown thread pool
            self.thread_pool.shutdown(wait=False)
            # Destroy the GUI window and exit the program
            self.root.destroy()
if __name__ == "__main__":
    client = ChatClient()
    client.run()