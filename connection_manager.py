import threading
import queue
import time

class ConnectionManager:
    def __init__(self, max_connections):
        self.semaphore = threading.Semaphore(max_connections)
        self.waiting_queue = queue.PriorityQueue()
        self.active_connections = {}
        self.lock = threading.Lock()
        
    def add_to_waiting_queue(self, client_socket, client_address):
        position = self.waiting_queue.qsize() + 1
        estimated_wait = position * 10  # Estimate 10 minutes per connection
        self.waiting_queue.put((time.time(), (client_socket, client_address)))
        return position, estimated_wait
    
    def acquire_connection(self):
        return self.semaphore.acquire(blocking=False)  # Changed to non-blocking
    
    def release_connection(self, client_id):
        with self.lock:
            if client_id in self.active_connections:
                del self.active_connections[client_id]
                self.semaphore.release()
                
                # Process the next client in the waiting queue if any
                if not self.waiting_queue.empty():
                    try:
                        _, (waiting_socket, waiting_address) = self.waiting_queue.get_nowait()
                        waiting_socket.send(b'{"status": "your_turn"}')  # Simplified; in practice, encrypt this
                    except Exception as e:
                        print(f"Error processing waiting queue: {e}")