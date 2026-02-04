import socket
import threading
import sys
from datetime import datetime

def log(message):
    """Print timestamped log messages."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

def receive_messages(client_socket):
    """Receive messages from server in a separate thread."""
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                break
            print(f"\n📨 {message}")
            print("You: ", end="", flush=True)
        except:
            break

def connect_to_server(host='localhost', port=8080):
    """Connect to chat server and send/receive messages."""
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        log(f"🔄 Connecting to {host}:{port}...")
        client.connect((host, port))
        log(f"✅ Connected! Type messages and press Enter. Type 'quit' to exit.")
        
        # Start receive thread
        receive_thread = threading.Thread(target=receive_messages, args=(client,), daemon=True)
        receive_thread.start()
        
        # Send messages from user input
        while True:
            try:
                message = input("You: ").strip()
                if message.lower() == 'quit':
                    log("👋 Disconnecting...")
                    break
                if message:
                    client.send(message.encode('utf-8'))
            except KeyboardInterrupt:
                log("\n👋 Disconnecting...")
                break
        
        client.close()
        log("❌ Disconnected from server")
        
    except ConnectionRefusedError:
        log(f"❌ Could not connect to {host}:{port}")
        log("   Make sure the server is running: python server.py")
    except Exception as e:
        log(f"❌ Error: {e}")

if __name__ == "__main__":
    # Optional: pass host as command line argument
    host = sys.argv[1] if len(sys.argv) > 1 else 'localhost'
    connect_to_server(host=host)
