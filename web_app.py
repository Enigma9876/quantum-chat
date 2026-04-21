from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from flask_socketio import SocketIO, join_room, leave_room, send, emit
import threading
import random
import string
import webbrowser
import uuid 

from crypto import manager

# Initialize Flask and SocketIO
app = Flask(__name__) 
app.config['SECRET_KEY'] = 'insightful_secret_key' 
socketio = SocketIO(app) 

# Encryption related
encryption_manager = manager.CryptoManager()

# Store active rooms and chat history in memory
active_rooms = {}
active_usernames = []

# --- HELPER FUNCTIONS ---
def generate_room_code():
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        if code not in active_rooms:
            return code


# --- UI TEMPLATE FOR WEB APP ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Insightful Encryptions</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script type="module" src="https://cdn.jsdelivr.net/npm/emoji-picker-element@1/index.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;600&family=Inter:wght@300;400;600;800&display=swap" rel="stylesheet">
    <style>
        /* MODERN CYBER/GLASSMORPHISM THEME */
        :root {
            --bg-dark: #0f172a;
            --bg-panel: rgba(30, 41, 59, 0.7);
            --text-main: #e2e8f0;
            --text-muted: #94a3b8;
            --accent-blue: #3b82f6;
            --accent-blue-hover: #60a5fa;
            --accent-green: #10b981;
            --accent-purple: #8b5cf6;
            --danger: #ef4444;
            --border-light: rgba(255, 255, 255, 0.1);
            --font-main: 'Inter', sans-serif;
            --font-mono: 'Fira Code', monospace;
        }

        body {
            background-color: var(--bg-dark);
            color: var(--text-main);
            font-family: var(--font-main);
            margin: 0; display: flex; flex-direction: column; align-items: center;
            height: 100vh; overflow: hidden;
            background-image: 
                radial-gradient(circle at 15% 50%, rgba(59, 130, 246, 0.15), transparent 25%),
                radial-gradient(circle at 85% 30%, rgba(139, 92, 246, 0.15), transparent 25%);
            background-attachment: fixed;
        }

        /* Custom Scrollbar */
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.2); border-radius: 10px; }
        ::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.3); }

        .header { width: 100%; background: rgba(15, 23, 42, 0.8); padding: 20px 15px; backdrop-filter: blur(12px); display: flex; justify-content: center; border-bottom: 1px solid var(--border-light); z-index: 10; }
        h1 { margin: 0; font-size: 26px; text-transform: uppercase; letter-spacing: 5px; color: #fff; font-weight: 800; background: linear-gradient(to right, #60a5fa, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }

        .container { width: 95%; max-width: 1400px; background: var(--bg-panel); padding: 25px; border-radius: 16px; backdrop-filter: blur(16px); box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5); border: 1px solid var(--border-light); margin-top: 3vh; height: 82vh; display: flex; flex-direction: column; }

        .btn { display: flex; align-items: center; justify-content: center; width: 100%; padding: 18px; margin: 15px 0; background: linear-gradient(135deg, var(--accent-blue) 0%, #2563eb 100%); color: #fff; font-size: 16px; text-decoration: none; text-transform: uppercase; border: none; border-radius: 8px; cursor: pointer; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3); font-family: var(--font-main); font-weight: 600; letter-spacing: 1px;}
        .btn:hover { background: linear-gradient(135deg, #60a5fa 0%, var(--accent-blue) 100%); transform: translateY(-2px); box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4); }
        .btn-host { background: linear-gradient(135deg, var(--accent-green) 0%, #059669 100%); font-size: 20px; box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3); }
        .btn-host:hover { background: linear-gradient(135deg, #34d399 0%, var(--accent-green) 100%); box-shadow: 0 8px 25px rgba(16, 185, 129, 0.4); }
        .btn-join { width: auto; padding: 0 40px; margin: 0; background: #334155; box-shadow: none;}
        .btn-join:hover { background: #475569; }

        .input-username { width: 100%; padding: 18px 20px; background: rgba(0,0,0,0.2); border: 1px solid var(--border-light); color: #fff; font-size: 18px; border-radius: 8px; box-sizing: border-box; text-align: center; margin-bottom: 30px; transition: all 0.3s; font-family: var(--font-main); }
        .input-username:focus { outline: none; border-color: var(--accent-blue); box-shadow: 0 0 15px rgba(59, 130, 246, 0.2); background: rgba(0,0,0,0.4); }
        .join-row { display: flex; gap: 12px; }
        .input-code { flex: 1; padding: 15px; background: rgba(0,0,0,0.3); border: 1px solid var(--border-light); color: var(--accent-blue); font-family: var(--font-mono); font-size: 24px; text-transform: uppercase; text-align: center; letter-spacing: 8px; border-radius: 8px; box-sizing: border-box; transition: all 0.3s; }
        .input-code:focus { outline: none; border-color: var(--accent-purple); box-shadow: 0 0 15px rgba(139, 92, 246, 0.2); }

        .chat-layout { display: flex; width: 100%; height: 100%; gap: 25px; }
        .chat-column { flex: 2; display: flex; flex-direction: column; }
        .encryption-panel { flex: 3.5; background: rgba(15, 23, 42, 0.6); border: 1px solid var(--border-light); border-radius: 12px; display: flex; flex-direction: column; overflow: hidden; box-shadow: inset 0 0 20px rgba(0,0,0,0.2); }
        
        .panel-section { padding: 25px; display: flex; flex-direction: column; }
        .panel-top { height: 28%; flex: none; overflow-y: auto;} 
        .panel-bottom { height: 72%; flex: none; display: flex; flex-direction: column; padding-bottom: 0; overflow: hidden;} 
        
        .panel-divider { height: 1px; background: linear-gradient(to right, transparent, var(--border-light), transparent); width: 100%; flex-shrink: 0; }
        .panel-header { color: var(--accent-purple); font-weight: 800; font-size: 16px; text-transform: uppercase; letter-spacing: 2px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 12px; margin-bottom: 15px; flex-shrink: 0; }
        
        .chat-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-light); padding-bottom: 15px; margin-bottom: 15px; }
        .chat-log { flex: 1; background: rgba(0, 0, 0, 0.2); border: 1px solid var(--border-light); border-radius: 12px; padding: 20px; overflow-y: auto; margin-bottom: 20px; font-family: var(--font-mono); display: flex; flex-direction: column; gap: 12px; }

        .message-row { display: flex; flex-direction: column; margin-bottom: 4px; }
        .msg-content-wrapper { display: flex; align-items: flex-start; justify-content: space-between; padding: 10px 14px; border-radius: 8px; transition: all 0.2s; box-sizing: border-box; border: 1px solid transparent; background: rgba(255,255,255,0.03); }
        .msg-text-area { flex: 1; line-height: 1.5; font-size: 14px; word-break: break-all;}
        .msg-system { color: var(--accent-purple); font-style: italic; background: transparent; border: none; padding: 5px 10px;}
        .msg-user { color: #f8fafc; cursor: pointer; }
        .msg-content-wrapper.selected { background-color: rgba(59, 130, 246, 0.1); border: 1px solid var(--accent-blue); transform: scale(1.01); box-shadow: 0 4px 12px rgba(0,0,0,0.2); }

        .msg-actions { display: flex; align-items: center; justify-content: flex-end; gap: 8px; width: 60px; min-width: 60px; opacity: 0; transition: opacity 0.2s; }
        .msg-content-wrapper:hover { background-color: rgba(255, 255, 255, 0.08); }
        .msg-content-wrapper:hover .msg-actions { opacity: 1; }

        .action-btn { background: none; border: none; cursor: pointer; color: var(--text-muted); opacity: 0.7; padding: 4px; display: flex; align-items: center; justify-content: center; transition: all 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275); }
        .action-btn:hover { opacity: 1; color: #fff; transform: scale(1.2); }
        .btn-trash:hover { color: var(--danger); }
        .btn-emoji:hover { color: #fbbf24; }

        .emoji-picker-container { position: absolute; z-index: 1000; display: none; box-shadow: 0 15px 35px rgba(0,0,0,0.6); border-radius: 12px; border: 1px solid var(--border-light); background: var(--bg-dark); overflow: hidden; }
        .reactions-row { display: flex; gap: 6px; flex-wrap: wrap; padding-left: 10px; margin-top: 6px; }
        .reaction-badge { background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 4px 8px; font-size: 13px; cursor: pointer; color: var(--text-muted); display: flex; align-items: center; gap: 5px; user-select: none; transition: all 0.2s; font-family: var(--font-main); }
        .reaction-badge:hover { background: rgba(255, 255, 255, 0.1); color: #fff; }
        .reaction-badge.active { background: rgba(59, 130, 246, 0.2); border-color: var(--accent-blue); color: #fff; }

        .chat-controls { display: flex; gap: 12px; }
        .chat-input { flex: 1; padding: 15px; background: rgba(0,0,0,0.3); border: 1px solid var(--border-light); color: white; font-size: 15px; border-radius: 8px; font-family: var(--font-main); transition: all 0.3s;}
        .chat-input:focus { outline: none; border-color: var(--accent-blue); box-shadow: 0 0 10px rgba(59, 130, 246, 0.2); }

        #encryption-selector { padding: 15px; background: rgba(0,0,0,0.3); border: 1px solid var(--border-light); color: white; font-size: 15px; font-family: var(--font-main); border-radius: 8px; cursor: pointer; outline: none; transition: all 0.3s;}
        #encryption-selector:focus { border-color: var(--accent-blue); }
        #encryption-selector option { background: var(--bg-dark); color: white; }

        input[type=range] { -webkit-appearance: none; width: 100%; background: transparent; }
        input[type=range]::-webkit-slider-thumb { -webkit-appearance: none; height: 20px; width: 20px; border-radius: 50%; background: var(--accent-blue); cursor: pointer; margin-top: -8px; box-shadow: 0 0 10px rgba(59, 130, 246, 0.5); transition: transform 0.1s;}
        input[type=range]::-webkit-slider-thumb:hover { transform: scale(1.2); }
        input[type=range]::-webkit-slider-runnable-track { width: 100%; height: 4px; cursor: pointer; background: rgba(255,255,255,0.1); border-radius: 2px; }
        input[type=range]:focus { outline: none; }

        /* TABS STYLING */
        .tabs-container { display: flex; flex-direction: column; height: 100%; overflow: hidden;}
        .tabs-header { display: flex; border-bottom: 1px solid rgba(255,255,255,0.05); flex-shrink: 0; margin-bottom: 10px;}
        .tab-btn { flex: 1; background: none; border: none; color: var(--text-muted); padding: 14px 10px; cursor: pointer; transition: all 0.3s; font-weight: 600; text-transform: uppercase; font-size: 13px; letter-spacing: 1px; border-bottom: 2px solid transparent; font-family: var(--font-main); }
        .tab-btn:hover { color: #fff; background: rgba(255,255,255,0.03); }
        .tab-btn.active { color: var(--accent-blue); border-bottom-color: var(--accent-blue); background: linear-gradient(to top, rgba(59, 130, 246, 0.1), transparent); }
        
        .tab-content { display: none; flex: 1; overflow-y: auto; padding: 5px 0 40px 0; color: var(--text-muted); line-height: 1.6; font-size: 14px; min-height: 0;}
        .tab-content.active { display: flex; flex-direction: column; }
        
        /* INNER SIDEBAR STYLING FOR DECRYPTION TOOLS */
        .side-btn { background: none; border: none; color: var(--text-muted); padding: 14px 12px; cursor: pointer; transition: all 0.2s; font-weight: 600; font-size: 12px; text-transform: uppercase; text-align: left; border-left: 3px solid transparent; width: 100%; border-bottom: 1px solid rgba(255,255,255,0.02); font-family: var(--font-main); }
        .side-btn:hover { color: #fff; background: rgba(255,255,255,0.03); padding-left: 16px;}
        .side-btn.active { color: var(--accent-blue); border-left-color: var(--accent-blue); background: linear-gradient(to right, rgba(59, 130, 246, 0.1), transparent); padding-left: 16px;}
        .tool-pane { display: none; height: 100%; flex-direction: column;}
        .tool-pane.active { display: flex; animation: fadeIn 0.4s ease; }
        
        /* SOLVER OUTPUTS */
        .brute-force-output { background: rgba(0,0,0,0.3); border: 1px solid var(--border-light); border-radius: 8px; padding: 20px; margin-top: 15px; font-family: var(--font-mono); font-size: 15px; color: var(--accent-green); letter-spacing: 1px; min-height: 80px; word-break: break-all; box-shadow: inset 0 0 15px rgba(0,0,0,0.5);}
        .solution-box { background: rgba(0,0,0,0.2); border: 1px solid var(--border-light); border-radius: 8px; padding: 18px; margin-bottom: 15px;}
        .sol-title { color: var(--text-muted); font-size: 11px; font-weight: 800; letter-spacing: 1.5px; margin-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 6px;}
        .math-row { font-family: var(--font-mono); color: #fff; margin: 8px 0; display: flex; align-items: center; gap: 12px; font-size: 14px;}
        .math-arrow { color: var(--accent-purple); font-weight: bold;}

        @keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
    </style>
</head>
<body>

    <div class="header">
        <h1>Insightful Encryptions</h1>
    </div>

    <div class="container">
        {% if page == 'home' %}
            <div style="color:var(--text-muted); margin-bottom: 25px; font-weight: 600; letter-spacing: 2px;">SELECT MODULE</div>
            <a href="/classroom" class="btn">Classroom Interface</a>
            <a href="/lab" class="btn">The Lab</a>
            <a href="/local" class="btn">Local Connection</a>

        {% elif page == 'local' %}
            <div style="text-align: center; margin-bottom: 40px;">
                <h2 style="color:white; margin-bottom: 8px; font-size: 28px;">Local Connection</h2>
                <p style="color:var(--text-muted); margin-top: 0; font-size: 16px;">Configure your session to begin.</p>
            </div>

            <form method="post" id="local-connection-form" style="width: 100%; max-width: 450px; margin: 0 auto;">
                <div style="text-align: center; color:var(--text-muted); font-size: 12px; font-weight: 800; margin-bottom: 10px; letter-spacing: 1.5px;">1. SET YOUR ALIAS</div>
                <input type="text" id="username_input" name="username" class="input-username" placeholder="Enter Username" maxlength="12" required>
                <div id="username_warning" style="color: var(--danger); font-size: 14px; margin-top: -20px; margin-bottom: 20px; height: 16px; text-align: center;"></div>

                <div style="text-align: center; color:var(--text-muted); font-size: 12px; font-weight: 800; margin-bottom: 10px; letter-spacing: 1.5px;">2. CHOOSE ACTION</div>
                <button type="submit" formaction="/host" id="btn-host" class="btn btn-host" style="width: 100%; margin-top: 0;">HOST NEW SERVER</button>

                <div style="text-align: center; color: var(--text-muted); margin: 30px 0; font-weight: 800; font-size: 14px; letter-spacing: 3px; opacity: 0.5;">— OR JOIN EXISTING —</div>
                <div class="join-row"> 
                    <input type="text" name="room_code" id="room_code_box" class="input-code" placeholder="CODE" maxlength="4">
                    <button type="submit" formaction="/join" id="btn-join" class="btn btn-join">JOIN</button>
                </div>
            </form>
 
            <script>
                const usernameInput = document.getElementById('username_input');
                const warningDiv = document.getElementById('username_warning');
                const hostButton = document.getElementById('btn-host');
                const joinButton = document.getElementById('btn-join');

                usernameInput.addEventListener('input', function() {
                    fetch('/api/usernames')
                        .then(response => response.json())
                        .then(takenUsernames => {
                    if(takenUsernames.includes(usernameInput.value))  { 
                        warningDiv.textContent = "Username already in use.";
                        hostButton.disabled = true; joinButton.disabled = true;
                        usernameInput.style.borderColor = "var(--danger)";
                    } else {
                        warningDiv.textContent = "";
                        usernameInput.style.borderColor = "var(--border-light)";
                        hostButton.disabled = false; joinButton.disabled = false;
                    } 
                    });
                });
                
                document.getElementById('btn-host').addEventListener('click', () => document.getElementById('room_code_box').required = false);
                document.getElementById('btn-join').addEventListener('click', () => document.getElementById('room_code_box').required = true);
            </script>
            <a href="/" style="color:var(--accent-blue); text-decoration:none; display:block; text-align:center; margin-top:40px; font-weight:600;">Back to Menu</a>
 
        {% elif page == 'chat' %}
            
            <div class="chat-layout">
                <div class="chat-column">
                    <div class="chat-header">
                        <h2 style="margin:0; color:#fff; font-size: 20px;">ROOM: <span style="color:var(--accent-green); font-family:var(--font-mono); font-size: 24px;">{{ room_code }}</span></h2>
                        <a href="/leave" style="color:var(--danger); text-decoration:none; border:1px solid var(--danger); padding:8px 16px; border-radius:6px; font-weight:600; font-size: 14px; transition: all 0.2s;" onmouseover="this.style.background='var(--danger)'; this.style.color='#fff';" onmouseout="this.style.background='transparent'; this.style.color='var(--danger)';">DISCONNECT</a>
                    </div>

                    <div id="chat-box" class="chat-log"></div>

                    <div class="chat-controls">
                        <input type="text" id="msg-input" class="chat-input" placeholder="Type an encrypted message..." autofocus>
                        <select id="encryption-selector">
                            <option value="none">None</option> 
                            <option value="caesar">Caesar Cipher</option> 
                            <option value="hill">Hill</option>
                            <option value="aes">AES</option>
                            <option value="vigenere">Vignere</option>
                            <option value="quantum">BB84</option>
                        </select>
                        <button onclick="sendMessage()" class="btn" style="width:auto; margin:0; padding:0 35px;">SEND</button>
                    </div>
                </div>

                <div class="encryption-panel">
                    <div class="panel-section panel-top">
                        <div class="panel-header">Encryption - <span id="current-cipher" style="color: #fff;">None</span></div>
                        
                        <div id="caesar-controls" style="display: none; margin-top: 5px;">
                            <label for="caesar-slider" style="color: var(--text-muted); font-size: 12px; font-weight: 800; letter-spacing: 1px;">
                                SHIFT VALUE: <span id="shift-display" style="color: var(--accent-blue); font-size: 16px;">1</span>
                            </label>
                            <input type="range" id="caesar-slider" min="1" max="25" value="1" style="margin: 15px 0 20px 0;">
                            
                            <div style="background: rgba(0,0,0,0.3); padding: 12px; border-radius: 8px; border: 1px solid var(--border-light); text-align: center;">
                                <div style="color: var(--text-muted); font-size: 10px; margin-bottom: 8px; font-weight: 800; letter-spacing: 1px;">EXAMPLE SHIFT</div>
                                <div style="font-family: var(--font-mono); font-size: 15px; color: #fff; letter-spacing: 4px;">A B C D E</div>
                                <div id="example-shift" style="font-family: var(--font-mono); font-size: 15px; color: var(--accent-green); letter-spacing: 4px; margin-top: 4px;">B C D E F</div>
                            </div>
                        </div>

                        <div id="hill-controls" style="display: none; margin-top: 15px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                                <label style="color: var(--text-muted); font-size: 12px; font-weight: 800; letter-spacing: 1px;">KEY MATRIX:</label>
                                <select id="hill-size" style="background: rgba(0,0,0,0.3); border: 1px solid var(--border-light); color: var(--accent-blue); padding: 6px; border-radius: 6px; outline: none; cursor: pointer; font-family: var(--font-main);">
                                    <option value="2">2x2 Matrix</option>
                                    <option value="3">3x3 Matrix</option>
                                    <option value="4">4x4 Matrix</option>
                                </select>
                            </div>
                            <div id="hill-matrix-container" style="display: grid; gap: 8px; grid-template-columns: repeat(2, 1fr); background: rgba(0,0,0,0.2); padding: 15px; border-radius: 8px; border: 1px solid var(--border-light);">
                                </div>
                        </div>

                        <div id="text-key-controls" style="display: none; margin-top: 15px;">
                            <label style="color: var(--text-muted); font-size: 12px; font-weight: 800; letter-spacing: 1px;">ENCRYPTION KEY / KEYWORD:</label>
                            <input type="text" id="text-key-input" class="chat-input" value="SECRET" style="width: 100%; padding: 12px; margin-top: 10px; font-family: var(--font-mono); box-sizing: border-box; text-align: center; text-transform: uppercase;">
                        </div>
                    </div>
                    
                    <div class="panel-divider"></div>
                    
                    <div class="panel-section panel-bottom">
                        <div class="panel-header" style="flex-shrink: 0; color: var(--accent-blue);">Selected Message</div>
                        
                        <div id="selection-placeholder" style="color: var(--text-muted); font-style: italic; text-align: center; margin-top: 30px; font-size: 15px;">
                            Click a message in the chat to view details.
                        </div>

                        <div id="selection-details" class="tabs-container" style="display: none;">
                            
                            <div style="background: rgba(0,0,0,0.3); padding: 15px; border-radius: 8px; border: 1px solid var(--border-light); margin-bottom: 15px; flex-shrink: 0;">
                                <div style="color: var(--text-muted); font-size: 10px; margin-bottom: 8px; font-weight: 800; letter-spacing: 1px;">PAYLOAD</div>
                                <div id="sel-payload" style="color: #fff; font-family: var(--font-mono); word-wrap: break-word; font-size: 15px;"></div>
                            </div>

                            <div class="tabs-header" style="flex-shrink: 0;">
                                <button class="tab-btn active" onclick="switchTab('decryption')">Decryption</button>
                                <button class="tab-btn" onclick="switchTab('solution')">Solution</button>
                                <button class="tab-btn" onclick="switchTab('history')">History</button>
                            </div>

                            <div id="tab-decryption" class="tab-content active">
                                <div id="tool-container-none" style="display:block; text-align: center; color: var(--text-muted); font-style: italic; padding-top: 20px;">
                                    No decryption tools needed for plaintext.
                                </div>

                                <div id="tool-container-active" style="display:none; height: 100%; min-height: 0;">
                                    <div style="display: flex; height: 100%; gap: 15px;">
                                        
                                        <div style="width: 180px; flex-shrink: 0; display: flex; flex-direction: column; border-right: 1px solid var(--border-light); padding-right: 15px; overflow-y: auto;">
                                            <button class="side-btn active" onclick="switchTool(this, 'tool-shift')">Linear Shift Analysis</button>
                                            <button class="side-btn" onclick="switchTool(this, 'tool-matrix')">Matrix Factorization</button>
                                            <button class="side-btn" onclick="switchTool(this, 'tool-kasiski')">Statistical Attack</button>
                                        </div>
                                        
                                        <div style="flex: 1; overflow-y: auto; padding-right: 10px; padding-bottom: 40px;">
                                            
                                            <div id="tool-shift" class="tool-pane active">
                                                <h3 style="color: #fff; margin: 0 0 12px 0; font-size: 18px; font-weight: 600;">Linear Shift Analysis</h3>
                                                <p style="margin-top: 0; color: var(--text-muted);">This method systematically tests all 25 possible alphabetical shifts against the encrypted message. By sliding through every potential reverse shift and displaying the result, you can visually scan to identify the step that produces readable English.</p>
                                                
                                                <div style="margin-top: 20px;">
                                                    <label for="analyzer-slider" style="color: var(--text-muted); font-size: 12px; font-weight: 800; letter-spacing: 1px; display:block;">
                                                        TEST REVERSE SHIFT: <span id="analyzer-display" style="color: var(--accent-blue); font-size: 16px;">1</span>
                                                    </label>
                                                    <input type="range" id="analyzer-slider" min="1" max="25" value="1" style="margin: 15px 0;">
                                                    <div id="analyzer-output" class="brute-force-output"></div>
                                                </div>
                                            </div>

                                            <div id="tool-matrix" class="tool-pane">
                                                <h3 style="color: #fff; margin: 0 0 12px 0; font-size: 18px; font-weight: 600;">Matrix Factorization</h3>
                                                <p style="margin-top: 0; color: var(--text-muted);">Step through the linear algebra required to crack a Hill Cipher modulo 26.</p>
                                                
                                                <div id="matrix-step-container" class="brute-force-output" style="display:none; text-align: left; font-size: 14px; line-height: 1.6;">
                                                    </div>
                                                
                                                <div style="margin-top: 20px; display: flex; gap: 10px;">
                                                    <button id="btn-matrix-start" class="btn" style="padding: 12px; font-size: 14px;" onclick="startHillSolver()">INITIALIZE CRACKER</button>
                                                    <button id="btn-matrix-next" class="btn" style="padding: 12px; font-size: 14px; display:none; background: linear-gradient(135deg, var(--accent-purple) 0%, #6d28d9 100%);" onclick="nextHillStep()">NEXT STEP ↳</button>
                                                </div>
                                            </div>

                                            <div id="tool-kasiski" class="tool-pane">
                                                <h3 style="color: #fff; margin: 0 0 12px 0; font-size: 18px; font-weight: 600;">Statistical Keyword Attack</h3>
                                                <p style="margin-top: 0; color: var(--text-muted);">Step through a Kasiski Examination and Frequency Analysis to break a Vigenère cipher.</p>
                                                
                                                <div id="vig-step-container" class="brute-force-output" style="display:none; text-align: left; font-size: 14px; line-height: 1.6;">
                                                    </div>
                                                
                                                <div style="margin-top: 20px; display: flex; gap: 10px;">
                                                    <button id="btn-vig-start" class="btn" style="padding: 12px; font-size: 14px;" onclick="startVigenereSolver()">INITIATE STATISTICAL ATTACK</button>
                                                    <button id="btn-vig-next" class="btn" style="padding: 12px; font-size: 14px; display:none; background: linear-gradient(135deg, var(--accent-purple) 0%, #6d28d9 100%);" onclick="nextVigenereStep()">NEXT STEP ↳</button>
                                                </div>
                                            </div>

                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div id="tab-solution" class="tab-content">
                                <div id="sol-none" style="display:block; text-align: center; color: var(--text-muted); font-style: italic; padding-top: 20px;">
                                    Message was sent without encryption.
                                </div>
                                <div id="sol-dynamic" style="display:none;">
                                    
                                    <div class="solution-box">
                                        <div class="sol-title">1. ENCRYPTION PROCESS</div>
                                        <div class="math-row">
                                            <span style="color:var(--text-muted);">Plaintext:</span> <span id="dyn-plain-1" style="color:var(--accent-blue);"></span>
                                        </div>
                                        <div class="math-row" style="color:var(--accent-green); font-size: 13px;">
                                            <span class="math-arrow">↳</span> <span id="dyn-enc-op"></span>
                                        </div>
                                        <div class="math-row">
                                            <span style="color:var(--text-muted);">Ciphertext:</span> <span id="dyn-cipher-1" style="color:#fff;"></span>
                                        </div>
                                    </div>

                                    <div class="solution-box" style="border-color: var(--accent-purple); background: rgba(139, 92, 246, 0.05);">
                                        <div class="sol-title" style="color: var(--accent-purple); border-bottom-color: rgba(139, 92, 246, 0.2);">2. RECOMMENDED TOOL</div>
                                        <div id="dyn-tool" style="color: #fff; font-size: 14px; margin-top: 8px; line-height: 1.5;"></div>
                                    </div>

                                    <div class="solution-box">
                                        <div class="sol-title">3. DECRYPTION SOLUTION</div>
                                        <div class="math-row">
                                            <span style="color:var(--text-muted);">Ciphertext:</span> <span id="dyn-cipher-2" style="color:#fff;"></span>
                                        </div>
                                        <div class="math-row" style="color:var(--accent-green); font-size: 13px;">
                                            <span class="math-arrow">↳</span> <span id="dyn-dec-op"></span>
                                        </div>
                                        <div class="math-row">
                                            <span style="color:var(--text-muted);">Plaintext:</span> <span id="dyn-plain-2" style="color:var(--accent-blue);"></span>
                                        </div>
                                    </div>

                                </div>
                            </div>

                            <div id="tab-history" class="tab-content">
                                <div id="hist-none" style="display:block; text-align: center; color: var(--text-muted); font-style: italic; padding-top: 20px;">
                                    No cipher history to display.
                                </div>
                                <div id="hist-caesar" class="history-block" style="display:none;">
                                    <h3 style="color: #fff; margin: 0 0 10px 0; font-size: 18px; font-weight: 600;">History of the Caesar Cipher</h3>
                                    <p style="margin-top: 0;">The Caesar cipher is named after Julius Caesar, who, according to Suetonius, used it with a shift of three (A becoming D when encrypting, and D becoming A when decrypting) to protect messages of military significance. While Caesar's cipher is the first recorded use of this scheme, other substitution ciphers are known to have been used earlier.</p>
                                    <p>Today, the Caesar cipher is completely unsuitable for secure communication due to its microscopic key space, but it is often incorporated as a part of more complex schemes, such as the Vigenère cipher.</p>
                                </div>
                                <div id="hist-hill" class="history-block" style="display:none;">
                                    <h3 style="color: #fff; margin: 0 0 10px 0; font-size: 18px; font-weight: 600;">History of the Hill Cipher</h3>
                                    <p style="margin-top: 0;">Invented by Lester S. Hill in 1929, the Hill cipher was the first polygraphic cipher in which it was practical (though barely) to operate on more than three symbols at once. It is based on linear algebra, specifically matrix multiplication modulo 26.</p>
                                    <p>While the Hill cipher is vulnerable to a known-plaintext attack because it is completely linear, its introduction of mathematical matrices into cryptology was revolutionary and paved the way for modern block ciphers like AES.</p>
                                </div>
                                <div id="hist-aes" class="history-block" style="display:none;">
                                    <h3 style="color: #fff; margin: 0 0 10px 0; font-size: 18px; font-weight: 600;">History of AES (Advanced Encryption Standard)</h3>
                                    <p style="margin-top: 0;">AES was established by the U.S. National Institute of Standards and Technology (NIST) in 2001. After a multi-year competition, the Rijndael cipher, developed by two Belgian cryptographers (Joan Daemen and Vincent Rijmen), was selected as the standard.</p>
                                    <p>AES is a symmetric key algorithm, meaning the same key is used for both encrypting and decrypting the data. It is currently the global standard for secure data and is used everywhere from secure web browsing to classified government communications.</p>
                                </div>
                                <div id="hist-vigenere" class="history-block" style="display:none;">
                                    <h3 style="color: #fff; margin: 0 0 10px 0; font-size: 18px; font-weight: 600;">History of the Vigenère Cipher</h3>
                                    <p style="margin-top: 0;">First described by Giovan Battista Bellaso in 1553, the cipher is easy to understand and implement, but it resisted all attempts to break it for three centuries, earning it the description <i>le chiffre indéchiffrable</i> (the indecipherable cipher).</p>
                                    <p>It works by using a series of interwoven Caesar ciphers based on the letters of a keyword. It was finally broken in 1863 by Friedrich Kasiski, who published a general method for deciphering it.</p>
                                </div>
                                <div id="hist-quantum" class="history-block" style="display:none;">
                                    <h3 style="color: #fff; margin: 0 0 10px 0; font-size: 18px; font-weight: 600;">History of BB84 (Quantum Cryptography)</h3>
                                    <p style="margin-top: 0;">BB84 is a quantum key distribution scheme developed by Charles Bennett and Gilles Brassard in 1984. It is the first quantum cryptography protocol.</p>
                                    <p>Rather than relying on mathematical complexity (like AES), BB84 relies on the fundamental laws of quantum mechanics. If a hacker attempts to intercept the quantum key, the act of measuring the photons fundamentally changes their state, immediately alerting the sender and receiver to the breach.</p>
                                </div>
                            </div>
                            
                        </div>
                    </div>
                </div>
            </div>

            <script>
                const socket = io();
                const room = "{{ room_code }}";
                const myUsername = "{{ current_user }}"; 
                
                const chatBox = document.getElementById('chat-box');
                const input = document.getElementById('msg-input');
                const selection_box = document.getElementById('encryption-selector');
                const cipher_text = document.getElementById('current-cipher');
                
                const caesarControls = document.getElementById('caesar-controls');
                const caesarSlider = document.getElementById('caesar-slider');
                const shiftDisplay = document.getElementById('shift-display');
                const exampleShift = document.getElementById('example-shift');
                
                const hillControls = document.getElementById('hill-controls');
                const hillSizeSelect = document.getElementById('hill-size');
                const hillMatrixContainer = document.getElementById('hill-matrix-container');
                
                const textKeyControls = document.getElementById('text-key-controls');
                const textKeyInput = document.getElementById('text-key-input');

                let selectedMessageId = null;
                let activeMessageIdForEmoji = null;
                let activePayloadForTools = ""; 
                let activeOriginalMsg = "";
                let activeCipherKey = null;
                let activeCipherType = null;

                // Function to visually generate the matrix grid
                function renderHillMatrix(size) {
                    hillMatrixContainer.style.gridTemplateColumns = `repeat(${size}, 1fr)`;
                    hillMatrixContainer.innerHTML = '';
                    
                    // Default matrix values to [[3,3], [2,5]] if 2x2, otherwise Identity matrix
                    const default2x2 = [3, 3, 2, 5];
                    let count = 0;

                    for (let i = 0; i < size; i++) {
                        for (let j = 0; j < size; j++) {
                            const gridInput = document.createElement('input');
                            gridInput.type = 'number';
                            gridInput.className = 'chat-input hill-cell';
                            gridInput.style.padding = '10px 5px';
                            gridInput.style.textAlign = 'center';
                            gridInput.style.fontFamily = 'var(--font-mono)';
                            gridInput.style.fontSize = '16px';
                            
                            if (size === 2) {
                                gridInput.value = default2x2[count] || 0;
                            } else {
                                gridInput.value = (i === j) ? 1 : 0; // Identity matrix
                            }
                            
                            hillMatrixContainer.appendChild(gridInput);
                            count++;
                        }
                    }
                }

                // Listen for size changes
                hillSizeSelect.addEventListener('change', (e) => renderHillMatrix(parseInt(e.target.value)));

                // Initialize default 2x2 matrix
                renderHillMatrix(2);

                // Configure Global Emoji Picker
                const pickerContainer = document.createElement('div');
                pickerContainer.className = 'emoji-picker-container';
                const emojiPicker = document.createElement('emoji-picker');
                pickerContainer.appendChild(emojiPicker);
                document.body.appendChild(pickerContainer);

                customElements.whenDefined('emoji-picker').then(() => {
                    const checkShadow = setInterval(() => {
                        if (emojiPicker.shadowRoot) {
                            clearInterval(checkShadow);
                            const style = document.createElement('style');
                            style.textContent = `
                                :host {
                                    --background: var(--bg-dark);
                                    --border-color: rgba(255,255,255,0.1);
                                    --input-border-color: rgba(255,255,255,0.2);
                                    --input-font-color: #fff;
                                    --indicator-color: #3b82f6;
                                    --button-hover-background: rgba(59, 130, 246, 0.15);
                                    --search-background: rgba(0,0,0,0.3);
                                    --category-font-color: #94a3b8;
                                }
                                .nav { display: none !important; }
                                .preview { display: none !important; }
                                input.search { border-radius: 6px !important; }
                            `;
                            emojiPicker.shadowRoot.appendChild(style);
                        }
                    }, 50);
                });

                emojiPicker.addEventListener('emoji-click', event => {
                    if (activeMessageIdForEmoji) {
                        socket.emit('react_message', { room: room, id: activeMessageIdForEmoji, emoji: event.detail.unicode });
                        pickerContainer.style.display = 'none';
                    }
                });

                document.addEventListener('click', event => {
                    if (!pickerContainer.contains(event.target) && !event.target.closest('.btn-emoji')) {
                        pickerContainer.style.display = 'none';
                    }
                });

                socket.emit('join', {room: room});

                function appendMessageToDOM(data) {
                    const row = document.createElement('div');
                    row.className = 'message-row';
                    if (data.id) row.id = 'msg-row-' + data.id;

                    const contentWrapper = document.createElement('div');
                    contentWrapper.className = 'msg-content-wrapper ' + (data.type || 'msg-user');
                    if (data.id) contentWrapper.id = 'msg-content-' + data.id;

                    const textArea = document.createElement('div');
                    textArea.className = 'msg-text-area';

                    if (data.type === 'msg-system') {
                        textArea.textContent = data.msg;
                        contentWrapper.appendChild(textArea);
                    } else {
                        textArea.innerHTML = `<span style="color:var(--accent-blue); font-weight:600;">${data.username}</span><span style="color:var(--text-muted);">:</span> ${data.msg}`;
                        
                        // Pass original payload and active keys for the tools
                        contentWrapper.onclick = () => selectMessage(data.id, data.username, data.msg, data.original_msg, data.cipher || 'none', data.key || 0);

                        const actionContainer = document.createElement('div');
                        actionContainer.className = 'msg-actions';

                        const emojiBtn = document.createElement('button');
                        emojiBtn.className = 'action-btn btn-emoji';
                        emojiBtn.innerHTML = `<svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none"><circle cx="12" cy="12" r="10"></circle><path d="M8 14s1.5 2 4 2 4-2 4-2"></path><line x1="9" y1="9" x2="9.01" y2="9"></line><line x1="15" y1="9" x2="15.01" y2="9"></line></svg>`;
                        emojiBtn.onclick = (e) => {
                            e.stopPropagation(); 
                            activeMessageIdForEmoji = data.id;
                            const rect = emojiBtn.getBoundingClientRect();
                            pickerContainer.style.display = 'block';
                            pickerContainer.style.top = (rect.bottom + window.scrollY + 5) + 'px';
                            pickerContainer.style.left = (rect.left + window.scrollX - 250) + 'px'; 
                        };
                        actionContainer.appendChild(emojiBtn);

                        if (data.username === myUsername) {
                            const delBtn = document.createElement('button');
                            delBtn.className = 'action-btn btn-trash';
                            delBtn.innerHTML = `<svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>`; 
                            delBtn.onclick = (e) => {
                                e.stopPropagation(); 
                                socket.emit('delete_message', { room: room, id: data.id });
                            };
                            actionContainer.appendChild(delBtn);
                        }
                        
                        contentWrapper.appendChild(textArea);
                        contentWrapper.appendChild(actionContainer);
                    }

                    row.appendChild(contentWrapper);
                    const reactionsRow = document.createElement('div');
                    reactionsRow.className = 'reactions-row';
                    if (data.id) reactionsRow.id = 'reactions-' + data.id;
                    row.appendChild(reactionsRow);

                    chatBox.appendChild(row);
                    chatBox.scrollTop = chatBox.scrollHeight;

                    if (data.reactions) renderReactions(data.id, data.reactions);
                }

                function renderReactions(msgId, reactionsMap) {
                    const row = document.getElementById('reactions-' + msgId);
                    if (!row) return;
                    row.innerHTML = ''; 
                    for (const [emoji, users] of Object.entries(reactionsMap)) {
                        if (users.length > 0) {
                            const badge = document.createElement('div');
                            badge.className = 'reaction-badge';
                            if (users.includes(myUsername)) badge.classList.add('active');
                            badge.textContent = `${emoji} ${users.length}`;
                            badge.onclick = () => socket.emit('react_message', { room: room, id: msgId, emoji: emoji });
                            row.appendChild(badge);
                        }
                    }
                }

                socket.on('chat_history', messages => messages.forEach(msg => appendMessageToDOM(msg)));
                socket.on('message', data => appendMessageToDOM(data));
                socket.on('reactions_updated', data => renderReactions(data.id, data.reactions));
                socket.on('message_deleted', data => {
                    const msgElement = document.getElementById('msg-row-' + data.id);
                    if (msgElement) msgElement.remove();
                    if (selectedMessageId === data.id) clearSelection();
                });

                function sendMessage() {
                    if (input.value.trim() !== "") {
                        
                        // Parse the correct key format based on selection
                        let encVal = 0;
                        if (selection_box.value === 'caesar') {
                            encVal = parseInt(caesarSlider.value) || 0;
                        } else if (selection_box.value === 'hill') {
                            const size = parseInt(hillSizeSelect.value);
                            const cells = document.querySelectorAll('.hill-cell');
                            let matrix = [];
                            let cellIndex = 0;
                            
                            for (let i = 0; i < size; i++) {
                                let row = [];
                                for (let j = 0; j < size; j++) {
                                    row.push(parseInt(cells[cellIndex].value) || 0);
                                    cellIndex++;
                                }
                                matrix.push(row);
                            }
                            encVal = matrix;
                        } else if (['aes', 'vigenere', 'quantum'].includes(selection_box.value)) {
                            encVal = textKeyInput.value;
                        }

                        socket.send({
                            msg: input.value, 
                            room: room, 
                            encryption: selection_box.value,
                            'encryption-value': encVal
                        });
                        input.value = '';
                    }
                }
                input.addEventListener("keypress", event => { if (event.key === "Enter") sendMessage(); });

                // --- OUTER TAB SWITCHER ---
                function switchTab(tabId) {
                    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
                    event.target.classList.add('active');
                    document.querySelectorAll('.tab-content').forEach(pane => pane.classList.remove('active'));
                    document.getElementById('tab-' + tabId).classList.add('active');
                }

                // --- INNER TOOL SWITCHER ---
                function switchTool(btnElement, targetPaneId) {
                    document.querySelectorAll('.side-btn').forEach(btn => btn.classList.remove('active'));
                    btnElement.classList.add('active');
                    document.querySelectorAll('.tool-pane').forEach(pane => pane.classList.remove('active'));
                    document.getElementById(targetPaneId).classList.add('active');
                }

                function selectMessage(id, username, msgText, originalMsg, cipherType, cipherKey) {
                    if (selectedMessageId) {
                        let prevMsg = document.getElementById('msg-content-' + selectedMessageId);
                        if(prevMsg) prevMsg.classList.remove('selected');
                    }
                    selectedMessageId = id;
                    let currentMsg = document.getElementById('msg-content-' + id);
                    if(currentMsg) currentMsg.classList.add('selected');

                    activePayloadForTools = msgText;
                    activeOriginalMsg = originalMsg || msgText;
                    activeCipherKey = cipherKey;
                    activeCipherType = cipherType;

                    document.getElementById('selection-placeholder').style.display = 'none';
                    document.getElementById('selection-details').style.display = 'flex';
                    document.getElementById('sel-payload').textContent = msgText;

                    document.getElementById('tool-container-none').style.display = 'none';
                    document.getElementById('tool-container-active').style.display = 'none';
                    document.getElementById('sol-none').style.display = 'none';
                    document.getElementById('sol-dynamic').style.display = 'none';
                    document.getElementById('hist-none').style.display = 'none';
                    
                    document.querySelectorAll('.history-block').forEach(el => el.style.display = 'none');

                    // Reset Matrix UI
                    document.getElementById('btn-matrix-start').style.display = 'flex';
                    document.getElementById('btn-matrix-start').textContent = 'INITIALIZE CRACKER';
                    document.getElementById('btn-matrix-next').style.display = 'none';
                    document.getElementById('matrix-step-container').style.display = 'none';
                    
                    // Reset Vigenere UI
                    document.getElementById('btn-vig-start').style.display = 'flex';
                    document.getElementById('btn-vig-start').textContent = 'INITIATE STATISTICAL ATTACK';
                    document.getElementById('btn-vig-next').style.display = 'none';
                    document.getElementById('vig-step-container').style.display = 'none';

                    if (cipherType !== 'system') {
                        document.getElementById('tool-container-active').style.display = 'block';
                        document.getElementById('sol-dynamic').style.display = 'block';

                        document.getElementById('dyn-plain-1').textContent = originalMsg || msgText;
                        document.getElementById('dyn-cipher-1').textContent = msgText;
                        document.getElementById('dyn-cipher-2').textContent = msgText;
                        document.getElementById('dyn-plain-2').textContent = originalMsg || msgText;

                        if (cipherType === 'caesar') {
                            document.getElementById('hist-caesar').style.display = 'block';
                            const shiftVal = parseInt(cipherKey) || 0;
                            document.getElementById('dyn-enc-op').textContent = `Applied Caesar Shift: +${shiftVal}`;
                            document.getElementById('dyn-tool').innerHTML = `To solve this without knowing the key, use the <strong>Linear Shift Analysis</strong> tool to systematically check all 25 possible shifts until readable English appears.`;
                            document.getElementById('dyn-dec-op').textContent = `Reverse Caesar Shift: -${shiftVal}`;

                        } else if (cipherType === 'none') {
                            document.getElementById('hist-none').style.display = 'block';
                            document.getElementById('dyn-enc-op').textContent = `No Encryption Applied`;
                            document.getElementById('dyn-tool').innerHTML = `This message is in plaintext. You can still explore the tools on the left to see how they affect unencrypted data.`;
                            document.getElementById('dyn-dec-op').textContent = `Message Unaltered`;

                        } else if (cipherType === 'hill') {
                            document.getElementById('hist-hill').style.display = 'block';
                            document.getElementById('dyn-enc-op').textContent = `Applied Hill Matrix Transformation`;
                            document.getElementById('dyn-tool').innerHTML = `To solve this, use the <strong>Matrix Factorization</strong> tool to calculate the exact Multiplicative Modulo 26 Inverse.`;
                            document.getElementById('dyn-dec-op').textContent = `Applied Inverse Matrix Transformation`;

                        } else if (cipherType === 'aes') {
                            document.getElementById('hist-aes').style.display = 'block';
                            document.getElementById('dyn-enc-op').textContent = `Applied Advanced Encryption Standard (AES)`;
                            document.getElementById('dyn-tool').innerHTML = `Modern AES cannot be broken by traditional mathematical tools. A dictionary attack or side-channel attack is required.`;
                            document.getElementById('dyn-dec-op').textContent = `Applied AES Decryption Algorithm`;

                        } else if (cipherType === 'vigenere') {
                            document.getElementById('hist-vigenere').style.display = 'block';
                            document.getElementById('dyn-enc-op').textContent = `Applied Vigenère Polyalphabetic Cipher`;
                            document.getElementById('dyn-tool').innerHTML = `To solve this, use the <strong>Statistical Attack</strong> tool to run an interactive Kasiski examination and isolate the repeating shifts.`;
                            document.getElementById('dyn-dec-op').textContent = `Applied Vigenère Decryption Shift`;

                        } else if (cipherType === 'quantum') {
                            document.getElementById('hist-quantum').style.display = 'block';
                            document.getElementById('dyn-enc-op').textContent = `Applied BB84 Quantum Key Protocol`;
                            document.getElementById('dyn-tool').innerHTML = `Quantum keys are theoretically unconditionally secure. Without the precise photon polarization states, brute force is impossible.`;
                            document.getElementById('dyn-dec-op').textContent = `Verified Quantum Key State`;
                        }

                        // Reset visual outputs for tools
                        document.getElementById('analyzer-slider').value = 1;
                        document.getElementById('analyzer-display').textContent = 1;
                        runCaesarBruteForceSlider(1);

                    } else {
                        // System messages hide all tools
                        document.getElementById('tool-container-none').style.display = 'block';
                        document.getElementById('sol-none').style.display = 'block';
                        document.getElementById('hist-none').style.display = 'block';
                    }
                }

                function clearSelection() {
                    selectedMessageId = null;
                    document.getElementById('selection-placeholder').style.display = 'block';
                    document.getElementById('selection-details').style.display = 'none';
                }

                // --- CAESAR DECIPHER TOOL ---
                function performCaesarShift(text, amount) {
                    return text.split('').map(char => {
                        const code = char.charCodeAt(0);
                        if (code >= 65 && code <= 90) {
                            return String.fromCharCode(((code - 65 - amount + 260) % 26) + 65);
                        } else if (code >= 97 && code <= 122) {
                            return String.fromCharCode(((code - 97 - amount + 260) % 26) + 97);
                        }
                        return char; 
                    }).join('');
                }

                function runCaesarBruteForceSlider(shiftValue) {
                    if (!activePayloadForTools) return;
                    const outputDiv = document.getElementById('analyzer-output');
                    const decrypted = performCaesarShift(activePayloadForTools, shiftValue);
                    outputDiv.textContent = decrypted;
                }

                const analyzerSlider = document.getElementById('analyzer-slider');
                analyzerSlider.addEventListener('input', function() {
                    document.getElementById('analyzer-display').textContent = this.value;
                    runCaesarBruteForceSlider(parseInt(this.value));
                });

                // --- INTERACTIVE MATRIX FACTORIZATION ALGORITHM ---
                let hillStep = 0;
                let hillState = {};

                function startHillSolver() {
                    const container = document.getElementById('matrix-step-container');
                    
                    if (activeCipherType !== 'hill' || !activeCipherKey || activeCipherKey.length !== 2) {
                        container.style.display = 'block';
                        container.innerHTML = `<span style="color:var(--danger)">ERROR: This tool requires an active 2x2 Hill Cipher message selected.</span>`;
                        return;
                    }
                    
                    // Initialize state
                    hillStep = 1;
                    hillState = {
                        a: activeCipherKey[0][0], b: activeCipherKey[0][1],
                        c: activeCipherKey[1][0], d: activeCipherKey[1][1],
                        det: 0, detInv: 0
                    };
                    
                    // UI Updates
                    document.getElementById('btn-matrix-start').style.display = 'none';
                    document.getElementById('btn-matrix-next').style.display = 'flex';
                    container.style.display = 'block';
                    
                    container.innerHTML = `
                        <div style="color:var(--accent-blue); font-weight:800; margin-bottom: 10px; letter-spacing: 1px;">STEP 1: ISOLATE KEY MATRIX</div>
                        <div style="color:#fff;">[ ${hillState.a}, ${hillState.b} ]</div>
                        <div style="color:#fff;">[ ${hillState.c}, ${hillState.d} ]</div>
                        <div style="margin-top:10px; color:var(--text-muted);">To decrypt the ciphertext, we must mathematically reverse this matrix. The first step is finding its determinant.</div>
                    `;
                }

                function nextHillStep() {
                    const container = document.getElementById('matrix-step-container');
                    hillStep++;
                    
                    if (hillStep === 2) {
                        let rawDet = (hillState.a * hillState.d) - (hillState.b * hillState.c);
                        hillState.det = rawDet % 26;
                        if (hillState.det < 0) hillState.det += 26;
                        
                        container.innerHTML = `
                            <div style="color:var(--accent-blue); font-weight:800; margin-bottom: 10px; letter-spacing: 1px;">STEP 2: CALCULATE DETERMINANT (MOD 26)</div>
                            <div style="color:var(--text-muted);">Formula: <span style="color:#fff">(ad - bc) mod 26</span></div>
                            <div style="margin-top:8px;">= ((${hillState.a} * ${hillState.d}) - (${hillState.b} * ${hillState.c})) mod 26</div>
                            <div>= ${rawDet} mod 26</div>
                            <div style="margin-top:10px; color:var(--accent-green); font-weight:bold; font-size: 16px;">Determinant = ${hillState.det}</div>
                        `;
                    } 
                    else if (hillStep === 3) {
                        hillState.detInv = -1;
                        for (let i = 1; i < 26; i++) {
                            if ((hillState.det * i) % 26 === 1) { hillState.detInv = i; break; }
                        }
                        
                        if (hillState.detInv === -1) {
                            container.innerHTML += `<div style="margin-top:15px; color:var(--danger); font-weight:bold;">CRITICAL ERROR: Determinant ${hillState.det} shares a factor with 26. Matrix is not invertible. Decryption impossible.</div>`;
                            document.getElementById('btn-matrix-next').style.display = 'none';
                            document.getElementById('btn-matrix-start').style.display = 'flex';
                            document.getElementById('btn-matrix-start').textContent = 'RESTART';
                            return;
                        }
                        
                        container.innerHTML = `
                            <div style="color:var(--accent-blue); font-weight:800; margin-bottom: 10px; letter-spacing: 1px;">STEP 3: MULTIPLICATIVE INVERSE</div>
                            <div style="color:var(--text-muted);">Find a number <span style="color:#fff">X</span> where <span style="color:#fff">(Determinant * X) mod 26 = 1</span></div>
                            <div style="margin-top:8px;">(${hillState.det} * X) mod 26 = 1</div>
                            <div style="margin-top:10px; color:var(--accent-green); font-weight:bold; font-size: 16px;">Inverse (D⁻¹) = ${hillState.detInv}</div>
                        `;
                    } 
                    else if (hillStep === 4) {
                        let adjA = hillState.d % 26; if(adjA < 0) adjA += 26;
                        let adjB = -hillState.b % 26; if(adjB < 0) adjB += 26;
                        let adjC = -hillState.c % 26; if(adjC < 0) adjC += 26;
                        let adjD = hillState.a % 26; if(adjD < 0) adjD += 26;
                        
                        hillState.invA = (adjA * hillState.detInv) % 26;
                        hillState.invB = (adjB * hillState.detInv) % 26;
                        hillState.invC = (adjC * hillState.detInv) % 26;
                        hillState.invD = (adjD * hillState.detInv) % 26;
                        
                        container.innerHTML = `
                            <div style="color:var(--accent-blue); font-weight:800; margin-bottom: 10px; letter-spacing: 1px;">STEP 4: GENERATE INVERSE MATRIX</div>
                            <div style="color:var(--text-muted);">Multiply the swapped, negated matrix (Adjugate) by D⁻¹ mod 26.</div>
                            <div style="margin: 12px 0;">
                                <div>[ (${hillState.d} * ${hillState.detInv})%26, (${-hillState.b} * ${hillState.detInv})%26 ]</div>
                                <div>[ (${-hillState.c} * ${hillState.detInv})%26, (${hillState.a} * ${hillState.detInv})%26 ]</div>
                            </div>
                            <div style="color:var(--accent-purple); font-weight:bold; margin-top: 10px;">Resulting Decryption Matrix:</div>
                            <div style="color:var(--accent-purple);">[ ${hillState.invA}, ${hillState.invB} ]</div>
                            <div style="color:var(--accent-purple);">[ ${hillState.invC}, ${hillState.invD} ]</div>
                        `;
                    } 
                    else if (hillStep === 5) {
                        container.innerHTML = `
                            <div style="color:var(--accent-green); font-weight:800; margin-bottom: 10px; letter-spacing: 1px;">STEP 5: DECRYPT PAYLOAD</div>
                            <div style="color:var(--text-muted);">By multiplying the ciphertext blocks by the Decryption Matrix, the original text is restored.</div>
                            <div style="margin-top:15px; color:#fff; font-size: 18px; font-family: var(--font-main); font-weight: 600;">"${activeOriginalMsg}"</div>
                            <div style="margin-top:20px; color:var(--accent-green); font-weight:bold; letter-spacing: 2px;">[ DECRYPTION COMPLETE ]</div>
                        `;
                        document.getElementById('btn-matrix-next').style.display = 'none';
                        document.getElementById('btn-matrix-start').style.display = 'flex';
                        document.getElementById('btn-matrix-start').textContent = 'RESTART PROCESS';
                    }
                }

                // --- INTERACTIVE VIGENERE STATISTICAL ALGORITHM ---
                let vigStep = 0;
                let vigState = {};

                function startVigenereSolver() {
                    const container = document.getElementById('vig-step-container');
                    
                    if (activeCipherType !== 'vigenere' || !activeCipherKey) {
                        container.style.display = 'block';
                        container.innerHTML = `<span style="color:var(--danger)">ERROR: This tool requires an active Vigenère Cipher message selected.</span>`;
                        return;
                    }

                    vigStep = 1;
                    vigState = {
                        key: String(activeCipherKey).toUpperCase(),
                        length: String(activeCipherKey).length,
                    };

                    document.getElementById('btn-vig-start').style.display = 'none';
                    document.getElementById('btn-vig-next').style.display = 'flex';
                    container.style.display = 'block';

                    container.innerHTML = `
                        <div style="color:var(--accent-blue); font-weight:800; margin-bottom: 10px; letter-spacing: 1px;">STEP 1: KASISKI EXAMINATION</div>
                        <div style="color:var(--text-muted);">The first step in breaking a Vigenère cipher is finding the length of the keyword. We look for repeating sequences of letters in the ciphertext.</div>
                        <div style="margin-top:10px; color:#fff;">Scanning payload for repeated n-grams...</div>
                    `;
                }

                function nextVigenereStep() {
                    const container = document.getElementById('vig-step-container');
                    vigStep++;

                    if (vigStep === 2) {
                        // Generate fake distances based on the actual key length for educational demonstration
                        let d1 = vigState.length * 3;
                        let d2 = vigState.length * 5;
                        container.innerHTML = `
                            <div style="color:var(--accent-blue); font-weight:800; margin-bottom: 10px; letter-spacing: 1px;">STEP 2: CALCULATE KEY LENGTH</div>
                            <div style="color:var(--text-muted);">We found repeating trigraphs separated by distances of ${d1} and ${d2} characters.</div>
                            <div style="margin-top:8px;">Finding the Greatest Common Divisor (GCD) of these distances...</div>
                            <div style="margin-top:10px; color:var(--accent-green); font-weight:bold; font-size: 16px;">Estimated Key Length = ${vigState.length}</div>
                        `;
                    }
                    else if (vigStep === 3) {
                        container.innerHTML = `
                            <div style="color:var(--accent-blue); font-weight:800; margin-bottom: 10px; letter-spacing: 1px;">STEP 3: FREQUENCY ANALYSIS</div>
                            <div style="color:var(--text-muted);">Now that we know the key is ${vigState.length} letters long, we can split the ciphertext into ${vigState.length} columns.</div>
                            <div style="margin-top:8px; color:#fff;">Each column is essentially encrypted with a simple Caesar cipher. We analyze the letter frequencies of each column against standard English (where 'E', 'T', 'A' are most common).</div>
                        `;
                    }
                    else if (vigStep === 4) {
                        let keyDisplay = vigState.key.split('').map((char, i) => `Col ${i+1} Shift ➔ <span style="color:var(--accent-purple); font-weight:bold;">${char}</span>`).join('<br>');
                        container.innerHTML = `
                            <div style="color:var(--accent-blue); font-weight:800; margin-bottom: 10px; letter-spacing: 1px;">STEP 4: RECOVER KEYWORD</div>
                            <div style="color:var(--text-muted);">By shifting each column until its frequency distribution maps to English, we recover the specific letter used for that column's shift.</div>
                            <div style="margin-top:10px; font-family:var(--font-mono);">${keyDisplay}</div>
                            <div style="margin-top:10px; color:var(--accent-green); font-weight:bold; font-size: 16px;">Keyword Recovered: ${vigState.key}</div>
                        `;
                    }
                    else if (vigStep === 5) {
                        container.innerHTML = `
                            <div style="color:var(--accent-green); font-weight:800; margin-bottom: 10px; letter-spacing: 1px;">STEP 5: DECRYPT PAYLOAD</div>
                            <div style="color:var(--text-muted);">Using the recovered keyword "${vigState.key}", we reverse the polyalphabetic shift to reveal the original message.</div>
                            <div style="margin-top:15px; color:#fff; font-size: 18px; font-family: var(--font-main); font-weight: 600;">"${activeOriginalMsg}"</div>
                            <div style="margin-top:20px; color:var(--accent-green); font-weight:bold; letter-spacing: 2px;">[ DECRYPTION COMPLETE ]</div>
                        `;
                        document.getElementById('btn-vig-next').style.display = 'none';
                        document.getElementById('btn-vig-start').style.display = 'flex';
                        document.getElementById('btn-vig-start').textContent = 'RESTART PROCESS';
                    }
                }


                // --- Visual Slider Updates (Encryption Menu) ---
                function updateExampleShift(shift) {
                    const shifted = ['A', 'B', 'C', 'D', 'E'].map(char => {
                        let newCode = char.charCodeAt(0) + shift;
                        if (newCode > 90) newCode -= 26;
                        return String.fromCharCode(newCode);
                    });
                    exampleShift.textContent = shifted.join(' ');
                }

                selection_box.addEventListener("change", function() {
                    cipher_text.textContent = selection_box.options[selection_box.selectedIndex].text;
                    
                    caesarControls.style.display = 'none';
                    hillControls.style.display = 'none';
                    textKeyControls.style.display = 'none';

                    if (selection_box.value === 'caesar') {
                        caesarControls.style.display = 'block';
                        updateExampleShift(parseInt(caesarSlider.value));
                    } else if (selection_box.value === 'hill') {
                        hillControls.style.display = 'block';
                    } else if (['aes', 'vigenere', 'quantum'].includes(selection_box.value)) {
                        textKeyControls.style.display = 'block';
                    }
                });

                caesarSlider.addEventListener('input', function() {
                    shiftDisplay.textContent = this.value;
                    updateExampleShift(parseInt(this.value));
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
    return render_template_string(HTML_TEMPLATE, page='home')

@app.route('/lab')
def lab():
    return render_template_string(HTML_TEMPLATE, page='home') 

@app.route('/local')
def local():
    return render_template_string(HTML_TEMPLATE, page='local', active_usernames=active_usernames)

@app.route('/host', methods=['POST'])
def host_server():
    session['username'] = request.form.get('username')
    code = generate_room_code()
    active_rooms[code] = {'users': 0, 'messages': []}
    active_usernames.append(session['username']) 
    session['room'] = code
    return render_template_string(HTML_TEMPLATE, page='chat', room_code=code, current_user=session['username'])

@app.route('/join', methods=['POST'])
def join_server():
    session['username'] = request.form.get('username')
    active_usernames.append(session['username']) 
    code = request.form.get('room_code').upper()
    
    if code in active_rooms:
        session['room'] = code
        return render_template_string(HTML_TEMPLATE, page='chat', room_code=code, current_user=session['username'])
    else:
        return redirect(url_for('local'))

@app.route('/leave')
def leave_server():
    room = session.get('room')
    username = session.get('username')
    session.pop('room', None)
    
    if room and room in active_rooms and username:
        sys_msg = {
            'id': str(uuid.uuid4()),
            'type': 'msg-system',
            'msg': f'[SYSTEM] {username} disconnected.',
            'reactions': {},
            'cipher': 'system',
            'key': 0
        }
        active_rooms[room]['messages'].append(sys_msg)
        socketio.send(sys_msg, to=room)

    return redirect(url_for('local'))

@app.route('/api/usernames')
def getUsernames():
    return jsonify(active_usernames)

# --- SOCKET EVENTS (The "Server" Logic) ---

@socketio.on('join')
def on_join(data):
    room = data['room']
    username = session.get('username', 'Guest')
    join_room(room)
    
    if room in active_rooms:
        emit('chat_history', active_rooms[room]['messages'], to=request.sid)

    sys_msg = {
        'id': str(uuid.uuid4()),
        'type': 'msg-system',
        'msg': f'[SYSTEM] {username} has joined Room {room}.',
        'reactions': {},
        'cipher': 'system',
        'key': 0
    }
    if room in active_rooms:
        active_rooms[room]['messages'].append(sys_msg)
    
    send(sys_msg, to=room)

@socketio.on('message')
def handle_message(data):
    room = data['room']
    msg = data['msg']
    encryption_type = data['encryption']
    
    # We now pull whatever value the dynamic UI sent
    encryption_value = data.get('encryption-value') 
    username = session.get('username', 'Guest')
    
    if encryption_type != "none":
        try:
            encrypted_bytes = encryption_manager.encrypt(encryption_type, msg.encode('utf-8'), encryption_value).decode('utf-8')
        except Exception as e:
            # Safe fallback if they enter a bad key format
            encrypted_bytes = f"[ENCRYPTION ERROR: {str(e)}]"
    else:
        encrypted_bytes = msg
    
    message_payload = {
        'id': str(uuid.uuid4()),
        'username': username,
        'msg': encrypted_bytes,
        'original_msg': msg, # <--- The secret weapon for the Solution Tab!
        'type': 'msg-user',
        'reactions': {},
        'cipher': encryption_type,
        'key': encryption_value
    }

    if room in active_rooms:
        active_rooms[room]['messages'].append(message_payload)
    
    send(message_payload, to=room)

@socketio.on('react_message')
def handle_reaction(data):
    room = data['room']
    msg_id = data['id']
    emoji = data['emoji']
    username = session.get('username')

    if room in active_rooms:
        for m in active_rooms[room]['messages']:
            if m.get('id') == msg_id:
                if emoji not in m['reactions']:
                    m['reactions'][emoji] = []
                
                if username in m['reactions'][emoji]:
                    m['reactions'][emoji].remove(username)
                else:
                    m['reactions'][emoji].append(username)
                
                emit('reactions_updated', {'id': msg_id, 'reactions': m['reactions']}, to=room)
                break

@socketio.on('delete_message')
def handle_delete(data):
    room = data['room']
    message_id = data['id']
    username = session.get('username')
    
    if room in active_rooms:
        for m in active_rooms[room]['messages']:
            if m.get('id') == message_id:
                if m.get('username') == username:
                    active_rooms[room]['messages'] = [msg for msg in active_rooms[room]['messages'] if msg.get('id') != message_id]
                    emit('message_deleted', {'id': message_id}, to=room)
                break

@socketio.on('disconnect')
def on_disconnect():
    username = session.get('username', 'Someone')
    if username in active_usernames:
        active_usernames.remove(username) 

# --- RUNNER ---
if __name__ == '__main__':
    threading.Timer(1.25, lambda: webbrowser.open("http://127.0.0.1:6767")).start() 
    socketio.run(app, host='0.0.0.0', port=6767, debug=True, allow_unsafe_werkzeug=True)