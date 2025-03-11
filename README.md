# Concurrency and Parallelism

## Project Overview
This project is an implementation of a concurrent and parallel chat system with secure communication, database management, and real-time message handling. The system consists of a **server** and **client** application, ensuring scalability and efficient handling of multiple connections.

## Features
- **Multi-threaded Server:** Utilizes `ThreadPoolExecutor` for managing client connections.
- **Secure Communication:** Implements encryption and hashing for authentication.
- **Database Integration:** Uses SQLite for storing user credentials and messages.
- **Real-time Notifications:** Includes a notification manager for client-side alerts.
- **File Transfer Support:** Allows users to send files with type restrictions.
- **Queue Management:** Manages connections when the server is at full capacity.

## Repository Structure
```
/Concurrency-and-Parallelism
│── server.py              # Main server script handling client connections
│── client.py              # GUI-based client application
│── config.py              # Configuration settings and encryption key management
│── database.py            # Handles SQLite database interactions
│── security.py            # Provides encryption and hashing utilities
│── connection_manager.py  # Manages client connections and queues
│── file_handler.py        # Handles file storage and validation
│── notification_manager.py# Plays notification sounds for messages
│── README.md              # This documentation file
```

## Installation and Setup
### Prerequisites
- Python 3.x
- Required dependencies (Install using `pip install -r requirements.txt`)

### Running the Server
1. Ensure that all dependencies are installed.
2. Run the following command to start the server:
   ```bash
   python server.py
   ```

### Running the Client
1. Ensure that the server is running.
2. Run the client application:
   ```bash
   python client.py
   ```

## Usage
1. **Register** a new user via the client application.
2. **Login** with registered credentials.
3. **Send messages** in real-time.
4. **Transfer files** between users.
5. **Receive notifications** for new messages.

## Contributions
Feel free to fork this repository and submit pull requests for improvements.

## License
This project is licensed under the MIT License.

