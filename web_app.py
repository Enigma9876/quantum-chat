from flask import Flask, render_template_string, request, redirect, url_for, session
from flask_socketio import SocketIO, join_room, leave_room, send, emit
import threading
import random
import string
import webbrowser
import subprocess
import os
import time

# Initialize Flask and SocketIO
app = Flask(__name__) #creating instance of flask app
app.config['SECRET_KEY'] = 'insightful_secret_key'
socketio = SocketIO(app)

# Store active rooms and chat history in memory
# Structure: { 'CODE': {'users': [], 'messages': []} }
active_rooms = {}

# --- HELPER FUNCTIONS ---
def generate_room_code():
    """Generate a unique 4-character code for rooms."""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        if code not in active_rooms:
            return code
def set_port_visibility(port, visible):
    code_space = os.getenv("CODE_SPACE_NAME")
    if not code_space:
        return # Not running in CodeSpaces, skip
    command = ["gh", "codespace", "ports", "visibility", f"{port}:{visible}", "--codespace", code_space]
    subprocess.run(command, check=True)


# --- UI TEMPLATE FOR WEB APP ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Insightful Encryptions</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        /* THEME VARIABLES */
        :root {
            --steam-dark: #171a21;
            --steam-header: #1b2838;
            --steam-text: #c7d5e0;
            --steam-blue: #66c0f4;
            --steam-green-top: #a4d007;
            --steam-green-bot: #536904;
            --steam-button-gray: #212c3d;
            --font-stack: "Motiva Sans", "Helvetica Neue", Helvetica, Arial, sans-serif;
        }

        body {
            background-color: var(--steam-dark);
            color: var(--steam-text);
            font-family: var(--font-stack);
            margin: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            height: 100vh;
            overflow: hidden;
            
            /* BACKGROUND PATTERN */
            background-image: 
                linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px),
                radial-gradient(circle at 50% 50%, rgba(27, 40, 56, 0.8) 0%, rgba(23, 26, 33, 1) 100%);
            background-size: 40px 40px, 40px 40px, 100% 100%;
            background-position: center center;
            background-repeat: repeat, repeat, no-repeat; 
        }

        .header {
            width: 100%;
            background: linear-gradient(to bottom, #1b2838 0%, #171a21 100%);
            padding: 20px;
            box-shadow: 0 10px 20px rgba(0,0,0,0.4);
            display: flex;
            justify-content: center;
            border-bottom: 1px solid #2a3f5a;
        }

        h1 {
            margin: 0;
            font-size: 32px;
            text-transform: uppercase;
            letter-spacing: 4px;
            color: #fff;
            font-weight: 300;
            text-shadow: 0 0 15px rgba(102, 192, 244, 0.3);
        }

        .container {
            width: 90%;
            max-width: 900px;
            background: rgba(23, 26, 33, 0.9);
            padding: 40px;
            border-radius: 8px;
            backdrop-filter: blur(10px);
            box-shadow: 0 0 30px rgba(0,0,0,0.5);
            border: 1px solid rgba(255,255,255,0.05);
            margin-top: 40px;
            height: 70vh; /* Fixed height for chat layout */
            display: flex;
            flex-direction: column;
        }

        /* BUTTON STYLES */
        .btn {
            display: flex;
            align-items: center;
            width: 100%;
            padding: 20px;
            margin: 15px 0;
            background: linear-gradient(to right, var(--steam-button-gray) 0%, #2a3f5a 100%);
            color: #fff;
            font-size: 18px;
            text-decoration: none;
            text-transform: uppercase;
            border: none;
            border-radius: 2px;
            cursor: pointer;
            transition: all 0.2s;
            box-shadow: 0 4px 10px rgba(0,0,0,0.3);
        }

        .btn:hover {
            background: linear-gradient(to right, #47bfff 0%, #1a44c2 100%);
            transform: translateX(5px);
        }

        /* HOST BUTTON (Green Play Style) */
        .btn-host {
            background: linear-gradient(to bottom, var(--steam-green-top) 5%, var(--steam-green-bot) 100%);
            justify-content: center;
            font-size: 24px;
            font-weight: bold;
            padding: 25px;
            text-align: center;
        }
        .btn-host:hover {
            background: linear-gradient(to bottom, #b6d634 5%, #536904 100%);
            transform: scale(1.02);
        }

        /* JOIN SECTION LAYOUT */
        .join-row {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }

        .input-code {
            flex: 1;
            padding: 20px;
            background: #000;
            border: 1px solid #444;
            color: var(--steam-blue);
            font-family: monospace;
            font-size: 24px;
            text-transform: uppercase;
            text-align: center;
            letter-spacing: 5px;
        }
        
        .input-code:focus { outline: 1px solid var(--steam-blue); }

        .btn-join {
            width: auto;
            padding: 0 40px;
            margin: 0;
            background: #2a3f5a;
            font-weight: bold;
        }

        /* CHAT ROOM STYLES */
        .chat-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #444;
            padding-bottom: 15px;
            margin-bottom: 15px;
        }

        .chat-log {
            flex: 1;
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid #333;
            padding: 20px;
            overflow-y: auto;
            margin-bottom: 20px;
            font-family: monospace;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .message { padding: 5px 10px; border-radius: 4px; }
        .msg-system { color: #ffd700; font-style: italic; }
        .msg-user { color: #fff; }
        .msg-self { color: var(--steam-blue); text-align: right; }
        
        .chat-controls {
            display: flex;
            gap: 10px;
        }

        .chat-input {
            flex: 1;
            padding: 15px;
            background: #101216;
            border: 1px solid #333;
            color: white;
            font-size: 16px;
        }
    </style>
</head>
<body>

    <div class="header">
        <h1>Insightful Encryptions</h1>
    </div>

    <div class="container">
        {% if page == 'home' %}
            <div style="color:#8f98a0; margin-bottom: 20px;">SELECT MODULE</div>
            <a href="/classroom" class="btn">Classroom Interface</a>
            <a href="/lab" class="btn">The Lab</a>
            <a href="/local" class="btn">Local Connection</a>

        {% elif page == 'local' %}
            <div style="text-align: center; margin-bottom: 30px;">
                <h2 style="color:white;">Local Connection</h2>
                <p style="color:#8f98a0;">Host a secure room or join an existing one.</p>
            </div>
            
            <form action="/host" method="post">
                <button type="submit" class="btn btn-host">HOST NEW SERVER</button>
            </form>

            <div style="text-align: center; color: #8f98a0; margin: 20px 0;">— OR JOIN EXISTING —</div>

            <form action="/join" method="post" class="join-row">
                <input type="text" name="room_code" class="input-code" placeholder="ENTER CODE" maxlength="4" required>
                <button type="submit" class="btn btn-join">JOIN</button>
            </form>

            <a href="/" style="color:#66c0f4; text-decoration:none; display:block; text-align:center; margin-top:30px;">Back to Menu</a>

        {% elif page == 'chat' %}
            <div class="chat-header">
                <h2 style="margin:0; color:#fff;">ROOM: <span style="color:var(--steam-green-top); font-family:monospace;">{{ room_code }}</span></h2>
                <a href="/leave" style="color:#ff4444; text-decoration:none; border:1px solid #ff4444; padding:5px 15px; border-radius:4px;">DISCONNECT</a>
            </div>

            <div id="chat-box" class="chat-log">
                <div class="message msg-system">[SYSTEM] Encrypted connection established.</div>
            </div>

            <div class="chat-controls">
                <input type="text" id="msg-input" class="chat-input" placeholder="Type an encrypted message..." autofocus>
                <button onclick="sendMessage()" class="btn" style="width:auto; margin:0; padding:0 30px;">SEND</button>
            </div>

            <script>
                const socket = io();
                const room = "{{ room_code }}";
                const chatBox = document.getElementById('chat-box');
                const input = document.getElementById('msg-input');

                // Join the room immediately
                socket.emit('join', {room: room});

                // Listen for incoming messages
                socket.on('message', function(data) {
                    const div = document.createElement('div');
                    div.className = 'message ' + (data.type || 'msg-user');
                    div.textContent = data.msg;
                    chatBox.appendChild(div);
                    chatBox.scrollTop = chatBox.scrollHeight;
                });

                function sendMessage() {
                    if (input.value.trim() !== "") {
                        socket.send({msg: input.value, room: room});
                        input.value = '';
                    }
                }

                // Send on Enter key
                input.addEventListener("keypress", function(event) {
                    if (event.key === "Enter") sendMessage();
                });
            </script>
        {% endif %}
    </div>

</body>
</html>
"""

# --- FLASK ROUTES ---

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, page='home')

@app.route('/classroom')
def classroom():
    return render_template_string(HTML_TEMPLATE, page='home') # Placeholder

@app.route('/lab')
def lab():
    return render_template_string(HTML_TEMPLATE, page='home') # Placeholder

@app.route('/local')
def local():
    return render_template_string(HTML_TEMPLATE, page='local')

@app.route('/host', methods=['POST'])
def host_server():
    code = generate_room_code()
    active_rooms[code] = {'users': 0}
    session['room'] = code
    return render_template_string(HTML_TEMPLATE, page='chat', room_code=code)

@app.route('/join', methods=['POST'])
def join_server():
    code = request.form.get('room_code').upper()
    if code in active_rooms:
        session['room'] = code
        return render_template_string(HTML_TEMPLATE, page='chat', room_code=code)
    else:
        # Simple error handling: go back to local page
        return redirect(url_for('local'))

@app.route('/leave')
def leave_server():
    session.pop('room', None)
    return redirect(url_for('local'))

# --- SOCKET EVENTS (The "Server" Logic) ---

@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)
    send({'msg': f'[SYSTEM] A new user has joined Room {room}.', 'type': 'msg-system'}, to=room)

@socketio.on('message')
def handle_message(data):
    room = data['room']
    msg = data['msg']
    # Broadcast message to everyone in the room
    send({'msg': f'User: {msg}', 'type': 'msg-user'}, to=room)

@socketio.on('disconnect')
def on_disconnect():
    print("User disconnected")

# --- RUNNER ---
if __name__ == '__main__':
    # Auto-open browser the first time the server starts
    threading.Timer(1.25, lambda: webbrowser.open("http://127.0.0.1:5000")).start() # change to only do this once in future
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)