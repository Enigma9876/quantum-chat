# 💬 TCP Chat Messaging App for GitHub Codespaces

A Python TCP client-server chat application that demonstrates real-time messaging between multiple devices.
w
## Setup

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies (if any)
pip install -r requirements.txt
```

## Running the Chat App

### Terminal 1 - Start the Server
```bash
python server.py
```
Expected output:
```
[HH:MM:SS] 🚀 Chat Server Started
[HH:MM:SS] 📍 Listening on 0.0.0.0:8080
[HH:MM:SS] ⏳ Waiting for clients to connect...
```

### Terminal 2 - Run First Client

uvicorn main:app --reload --host 0.0.0.0 --port 8000
```bash
python client.py
```
Expected output:
```
[HH:MM:SS] 🔄 Connecting to localhost:8080...
[HH:MM:SS] ✅ Connected! Type messages and press Enter. Type 'quit' to exit.
You: 
```

### Terminal 3+ - Run More Clients (Optional)
```bash
python client.py
```

Now type messages in any client terminal and they will be broadcast to all other connected clients!

---

## 🔌 Understanding the TCP Connection Process

### What is TCP?
**TCP (Transmission Control Protocol)** is a connection-oriented protocol that ensures reliable, ordered message delivery. Think of it like making a phone call:
- You dial (connect)
- You talk (send/receive)
- You hang up (disconnect)

### The TCP 3-Way Handshake

When a client connects to the server, here's what happens:

```
CLIENT                                    SERVER
  |                                         |
  |-------- 1️⃣ SYN (I want to connect) ----->|
  |                                         |
  |<------ 2️⃣ SYN-ACK (I accept) ----------|
  |                                         |
  |-------- 3️⃣ ACK (Connection established) -->|
  |                                         |
  |========== CONNECTION OPEN ============|
  |                                         |
  |  Can now send/receive data bidirectionally
  |                                         |
```

**Step-by-step:**
1. **SYN**: Client sends "I want to connect"
2. **SYN-ACK**: Server replies "I accept, let's talk"
3. **ACK**: Client confirms "Great, I'm ready"

After this handshake, both sides can send and receive data.

---

## 📤 Message Flow in This Chat App

```
┌─────────────────────────────────────────────────────────────┐
│                        CHAT NETWORK                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CLIENT A              SERVER              CLIENT B       │
│  (User_5000)      (Listening on 8080)      (User_5001)    │
│     │                    │                      │         │
│     │ ─────TCP Connect────> (Connection 1)     │         │
│     │ <──Connected ACK──                        │         │
│     │                                                       │
│     │                    │ <──TCP Connect──── (Connection 2)
│     │                    | ──Connected ACK──> │         │
│     │                                          │         │
│     │ "Hello from A"                           │         │
│     ├──────────────────────────────>│          │         │
│     │                      │         │          │         │
│     │                      └─────────broadcast──────────>│
│     │                               │          │         │
│     │                               │    "User_5000: Hello from A"
│     │ <──────────broadcast─────────┤          │         │
│     │ "User_5001: Hi A"            │          │         │
│     │                               │          │         │
│     │                        "Hi A" │          │         │
│     │                               └──────────────────>│
│     │                                          │         │
│
```

### How a Message Gets Delivered

1. **Client A** types "Hello from A" and presses Enter
2. **Client A socket** sends the message to the Server
3. **Server receives** the message on Connection 1
4. **Server broadcasts** to all OTHER clients (Client B, Client C, etc.)
5. **Each Client receives** the message and displays it
6. **Next message from any client** goes through the same process

---

## 🔄 The Event Loop

### Server Side
```
while True:
    client_socket, address = server.accept()  # Wait for new connection
    │
    └─> Spawn new thread for each client
        │
        └─> Handle that client's messages:
            while True:
                message = client_socket.recv(1024)  # Wait for message
                broadcast(message)  # Send to all others
```

### Client Side
```
Main Thread:                    Receive Thread:
│                               │
├─ Prompt user for input       ├─ Listen for server messages
│                               │
├─ User types message          ├─ When message arrives:
│                               │   Print it
└─ Send to server              │   Prompt for more input
   (and repeat)                │   (and repeat)
                               └─ Runs simultaneously!
```

The **two threads** allow the client to send and receive messages at the same time—just like texting!

---

## 💾 Key Data Structures

### Server's Client Dictionary
```python
clients = {
    socket_obj_1: {'name': 'User_5000', 'address': ('127.0.0.1', 5000)},
    socket_obj_2: {'name': 'User_5001', 'address': ('127.0.0.1', 5001)},
}
```
The server keeps track of all connected clients so it can broadcast messages.

---

## 🌐 Using GitHub Codespaces to Connect External Devices

### Step 1: Run the Server
```bash
python server.py
```

### Step 2: Make Port Public
1. Open the **Ports** panel in VS Code (bottom panel or `Ctrl+Shift+P` → "Ports: Focus")
2. Right-click port **8080** → **"Make Public"** (set Visibility to "Public")
3. Note the **Forwarded Address** (e.g., `https://zany-space-inv...-8080.app.github.dev`)

### Step 3: Connect from External Device
On another machine, run:
```bash
# Replace with your Codespace's actual URL (remove the "https://" part)
python client.py zany-space-inv...-8080.app.github.dev
```

**⚠️ Note:** GitHub Codespaces currently requires port forwarding through HTTPS/WSS. For HTTP/WebSocket, the local `localhost:8080` works perfectly for testing.

---

## 🛑 Shutting Down

### Stop all clients
- Type `quit` and press Enter in each client terminal, or
- Press `Ctrl+C`

### Stop the server
- Press `Ctrl+C` in the server terminal, or
- Run: `pkill -f "python server.py"`

---

## 📊 Example Session

**Server Output:**
```
[14:23:45] 🚀 Chat Server Started
[14:23:45] 📍 Listening on 0.0.0.0:8080
[14:23:45] ⏳ Waiting for clients to connect...
[14:23:50] ✅ User_5000 connected from ('127.0.0.1', 5000)
[14:23:50] [SYSTEM] User_5000 joined the chat!
[14:23:55] ✅ User_5001 connected from ('127.0.0.1', 5001)
[14:23:55] [SYSTEM] User_5001 joined the chat!
[14:24:00] 📨 User_5000: Hello everyone!
[14:24:05] 📨 User_5001: Hi there!
[14:24:10] 📊 Active users: User_5000, User_5001
```

**Client A Output:**
```
[14:23:50] 🔄 Connecting to localhost:8080...
[14:23:50] ✅ Connected! Type messages and press Enter. Type 'quit' to exit.
You: Hello everyone!

📨 User_5001: Hi there!
You: 
```

**Client B Output:**
```
[14:23:55] 🔄 Connecting to localhost:8080...
[14:23:55] ✅ Connected! Type messages and press Enter. Type 'quit' to exit.
You: 
📨 [SYSTEM] User_5000 joined the chat!

📨 User_5000: Hello everyone!
You: Hi there!
```

---

## 🎯 Key Concepts Demonstrated

- **TCP Sockets**: Reliable, ordered communication
- **Multithreading**: Handling multiple clients simultaneously
- **Broadcasting**: Sending one message to many recipients
- **Synchronization**: Using locks to protect shared data (`clients` dictionary)
- **Event-Driven**: Responding to client connections and messages
- **Networking**: Ports, addresses, and protocols

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Connection refused" | Make sure `server.py` is running in another terminal |
| Port already in use | Run `pkill -f "python server.py"` or wait a few seconds after killing |
| Messages not appearing | Check that both clients are connected (watch the server output) |
| Can't connect from external device | Make sure port 8080 is Public in the Ports panel and use the correct URL |
