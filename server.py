import socket
import threading
import time
from datetime import datetime

# Dictionary to store connected clients: {client_socket: client_info}
clients = {}
clients_lock = threading.Lock()

def log(message):
    """Print timestamped log messages."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

def broadcast(message, sender_socket=None):
    """Send a message to all connected clients except the sender."""
    with clients_lock: 
        for client_socket in list(clients.keys()):
            if client_socket != sender_socket:
                try:
                    client_socket.send(message.encode('utf-8'))
                except Exception as e:
                    log(f"Failed to send message to {clients[client_socket]['name']}: {e}")

def handle_client(client_socket, address):
    """Handle a single client connection."""
    client_name = f"User_{address[1]}"
    
    with clients_lock:
        clients[client_socket] = {
            'name': client_name,
            'address': address,
            'connected_at': datetime.now()
        }
    
    log(f"✅ {client_name} connected from {address}")
    broadcast(f"[SYSTEM] {client_name} joined the chat!")
    
    try:
        while True:
            # Receive message from client
            message = client_socket.recv(1024).decode('utf-8').strip()
            
            if not message:
                break
            
            # Log the message
            log(f"📨 {client_name}: {message}")
            
            # Broadcast to all other clients
            broadcast(f"{client_name}: {message}", client_socket)
            
    except ConnectionResetError:
        log(f"⚠️  {client_name} disconnected abruptly")
    except Exception as e:
        log(f"❌ Error with {client_name}: {e}")
    
    finally:
        # Remove client from connected list
        with clients_lock:
            if client_socket in clients:
                del clients[client_socket]
        
        client_socket.close()
        log(f"❌ {client_name} disconnected")
        broadcast(f"[SYSTEM] {client_name} left the chat!")

def show_status():
    """Periodically show active connections."""
    while True:
        time.sleep(30)
        with clients_lock:
            if clients:
                log(f"📊 Active users: {', '.join([c['name'] for c in clients.values()])}")

def start_server(host='0.0.0.0', port=8080):
    """Start the TCP chat server."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(5)
    
    log(f"🚀 Chat Server Started")
    log(f"📍 Listening on {host}:{port}")
    log(f"⏳ Waiting for clients to connect...")
    
    # Start status thread
    status_thread = threading.Thread(target=show_status, daemon=True)
    status_thread.start()
    
    try:
        while True:
            client_socket, address = server.accept()
            # Handle each client in a separate thread
            thread = threading.Thread(target=handle_client, args=(client_socket, address))
            thread.daemon = True
            thread.start()
    except KeyboardInterrupt:
        log("\n🛑 Server shutting down...")
    finally:
        server.close()

if __name__ == "__main__":
    start_server()
