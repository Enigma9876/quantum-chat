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
            --steam-danger: #ff4444;
            --font-stack: "Motiva Sans", "Helvetica Neue", Helvetica, Arial, sans-serif;
        }

        body {
            background-color: var(--steam-dark);
            color: var(--steam-text);
            font-family: var(--font-stack);
            margin: 0; display: flex; flex-direction: column; align-items: center;
            height: 100vh; overflow: hidden;
            background-image: 
                linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px),
                radial-gradient(circle at 50% 50%, rgba(27, 40, 56, 0.8) 0%, rgba(23, 26, 33, 1) 100%);
            background-size: 40px 40px, 40px 40px, 100% 100%;
            background-position: center center; background-repeat: repeat, repeat, no-repeat; 
        }

        .header { width: 100%; background: linear-gradient(to bottom, #1b2838 0%, #171a21 100%); padding: 15px; box-shadow: 0 10px 20px rgba(0,0,0,0.4); display: flex; justify-content: center; border-bottom: 1px solid #2a3f5a; }
        h1 { margin: 0; font-size: 28px; text-transform: uppercase; letter-spacing: 4px; color: #fff; font-weight: 300; text-shadow: 0 0 15px rgba(102, 192, 244, 0.3); }

        .container { width: 95%; max-width: 1400px; background: rgba(23, 26, 33, 0.9); padding: 30px; border-radius: 8px; backdrop-filter: blur(10px); box-shadow: 0 0 30px rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.05); margin-top: 2vh; height: 85vh; display: flex; flex-direction: column; }

        .btn { display: flex; align-items: center; width: 100%; padding: 20px; margin: 15px 0; background: linear-gradient(to right, var(--steam-button-gray) 0%, #2a3f5a 100%); color: #fff; font-size: 18px; text-decoration: none; text-transform: uppercase; border: none; border-radius: 2px; cursor: pointer; transition: all 0.2s; box-shadow: 0 4px 10px rgba(0,0,0,0.3); justify-content: center; font-family: var(--font-stack); font-weight: bold;}
        .btn:hover { background: linear-gradient(to right, #47bfff 0%, #1a44c2 100%); transform: translateX(5px); }
        .btn-host { background: linear-gradient(to bottom, var(--steam-green-top) 5%, var(--steam-green-bot) 100%); font-size: 24px; padding: 20px; text-align: center; }
        .btn-host:hover { background: linear-gradient(to bottom, #b6d634 5%, #536904 100%); transform: scale(1.02); }

        .input-username { width: 100%; padding: 15px 20px; background: #10141b; border: 1px solid #2a3f5a; color: #fff; font-size: 18px; border-radius: 4px; box-sizing: border-box; text-align: center; margin-bottom: 30px; transition: all 0.3s; font-family: var(--font-stack); }
        .input-username:focus { outline: none; border-color: var(--steam-blue); box-shadow: 0 0 10px rgba(102, 192, 244, 0.2); background: #141922; }
        .join-row { display: flex; gap: 10px; }
        .input-code { flex: 1; padding: 15px; background: #000; border: 1px solid #444; color: var(--steam-blue); font-family: monospace; font-size: 24px; text-transform: uppercase; text-align: center; letter-spacing: 5px; box-sizing: border-box; }
        .input-code:focus { outline: 1px solid var(--steam-blue); }
        .btn-join { width: auto; padding: 0 40px; margin: 0; background: #2a3f5a; }

        .chat-layout { display: flex; width: 100%; height: 100%; gap: 20px; }
        .chat-column { flex: 2; display: flex; flex-direction: column; }
        .encryption-panel { flex: 3.5; background: rgba(0, 0, 0, 0.4); border: 1px solid #333; border-radius: 4px; display: flex; flex-direction: column; overflow: hidden; }
        
        .panel-section { padding: 20px; display: flex; flex-direction: column; }
        .panel-top { height: 25%; flex: none; overflow-y: auto;} 
        .panel-bottom { height: 75%; flex: none; display: flex; flex-direction: column; padding-bottom: 0; overflow: hidden;} 
        
        .panel-divider { height: 1px; background: #444; width: 100%; flex-shrink: 0; }
        .panel-header { color: var(--steam-blue); font-weight: bold; font-size: 18px; text-transform: uppercase; letter-spacing: 2px; border-bottom: 1px solid #444; padding-bottom: 10px; margin-bottom: 15px; flex-shrink: 0; }
        .chat-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #444; padding-bottom: 15px; margin-bottom: 15px; }
        .chat-log { flex: 1; background: rgba(0, 0, 0, 0.4); border: 1px solid #333; padding: 20px; overflow-y: auto; margin-bottom: 20px; font-family: monospace; display: flex; flex-direction: column; gap: 8px; }

        .message-row { display: flex; flex-direction: column; margin-bottom: 4px; }
        .msg-content-wrapper { display: flex; align-items: flex-start; justify-content: space-between; padding: 5px 10px; border-radius: 4px; transition: background-color 0.2s, border-color 0.2s; box-sizing: border-box; border: 1px solid transparent; }
        .msg-text-area { flex: 1; line-height: 1.5; padding-top: 4px; word-break: break-all;}
        .msg-system { color: #ffd700; font-style: italic; }
        .msg-user { color: #fff; cursor: pointer; }
        .msg-content-wrapper.selected { background-color: rgba(102, 192, 244, 0.15); border: 1px solid var(--steam-blue); }

        .msg-actions { display: flex; align-items: center; justify-content: flex-end; gap: 8px; width: 60px; min-width: 60px; opacity: 0; transition: opacity 0.2s; padding-top: 4px; }
        .msg-content-wrapper:hover { background-color: rgba(255, 255, 255, 0.05); }
        .msg-content-wrapper:hover .msg-actions { opacity: 1; }

        .action-btn { background: none; border: none; cursor: pointer; color: #8f98a0; opacity: 0.7; padding: 4px; display: flex; align-items: center; justify-content: center; transition: all 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275); }
        .action-btn:hover { opacity: 1; color: #fff; transform: scale(1.2) rotate(-5deg); }
        .btn-trash:hover { color: var(--steam-danger); }
        .btn-emoji:hover { color: #fce205; }

        .emoji-picker-container { position: absolute; z-index: 1000; display: none; box-shadow: 0 10px 30px rgba(0,0,0,0.8); border-radius: 8px; border: 1px solid #333; background: #1b2838; }
        .reactions-row { display: flex; gap: 6px; flex-wrap: wrap; padding-left: 10px; margin-top: 4px; }
        .reaction-badge { background: rgba(255, 255, 255, 0.05); border: 1px solid #444; border-radius: 6px; padding: 2px 6px; font-size: 12px; cursor: pointer; color: #ccc; display: flex; align-items: center; gap: 4px; user-select: none; transition: all 0.2s; font-family: var(--font-stack); }
        .reaction-badge:hover { background: rgba(255, 255, 255, 0.1); }
        .reaction-badge.active { background: rgba(102, 192, 244, 0.2); border-color: var(--steam-blue); color: #fff; }

        .chat-controls { display: flex; gap: 10px; }
        .chat-input { flex: 1; padding: 15px; background: #101216; border: 1px solid #333; color: white; font-size: 16px; }

        #encryption-selector { padding: 15px; background: #101216; border: 1px solid #333; color: white; font-size: 16px; font-family: var(--font-stack); border-radius: 2px; cursor: pointer; outline: none; }
        #encryption-selector:focus { border-color: var(--steam-blue); }
        #encryption-selector option { background: var(--steam-dark); color: white; }

        input[type=range] { -webkit-appearance: none; width: 100%; background: transparent; }
        input[type=range]::-webkit-slider-thumb { -webkit-appearance: none; height: 18px; width: 18px; border-radius: 50%; background: var(--steam-blue); cursor: pointer; margin-top: -7px; box-shadow: 0 0 5px rgba(102, 192, 244, 0.5); }
        input[type=range]::-webkit-slider-runnable-track { width: 100%; height: 4px; cursor: pointer; background: #333; border-radius: 2px; }
        input[type=range]:focus { outline: none; }

        /* TABS STYLING */
        .tabs-container { display: flex; flex-direction: column; height: 100%; overflow: hidden;}
        .tabs-header { display: flex; border-bottom: 1px solid #444; flex-shrink: 0; }
        .tab-btn { flex: 1; background: none; border: none; color: #8f98a0; padding: 12px 10px; cursor: pointer; transition: 0.2s; font-weight: bold; text-transform: uppercase; font-size: 13px; letter-spacing: 1px; border-bottom: 2px solid transparent; font-family: var(--font-stack); }
        .tab-btn:hover { color: #fff; background: rgba(255,255,255,0.05); }
        .tab-btn.active { color: var(--steam-blue); border-bottom-color: var(--steam-blue); background: rgba(102, 192, 244, 0.05); }
        
        .tab-content { display: none; flex: 1; overflow-y: auto; padding: 15px 0 40px 0; color: #ccc; line-height: 1.6; font-size: 14px; min-height: 0;}
        .tab-content.active { display: flex; flex-direction: column; }
        
        /* INNER SIDEBAR STYLING FOR DECRYPTION TOOLS */
        .side-btn { background: none; border: none; color: #8f98a0; padding: 12px 10px; cursor: pointer; transition: 0.2s; font-weight: bold; font-size: 12px; text-transform: uppercase; text-align: left; border-left: 2px solid transparent; width: 100%; border-bottom: 1px solid rgba(255,255,255,0.05); font-family: var(--font-stack); }
        .side-btn:hover { color: #fff; background: rgba(255,255,255,0.05); }
        .side-btn.active { color: var(--steam-blue); border-left-color: var(--steam-blue); background: rgba(102, 192, 244, 0.05); }
        .tool-pane { display: none; height: 100%; flex-direction: column;}
        .tool-pane.active { display: flex; }
        
        /* SOLVER OUTPUTS */
        .brute-force-output { background: rgba(0,0,0,0.5); border: 1px solid #333; border-radius: 4px; padding: 15px; margin-top: 15px; font-family: monospace; font-size: 16px; text-align: center; color: var(--steam-green-top); letter-spacing: 1px; min-height: 60px; word-break: break-all;}
        .solution-box { background: rgba(0,0,0,0.5); border: 1px solid #333; border-radius: 4px; padding: 15px; margin-bottom: 15px;}
        .sol-title { color: #8f98a0; font-size: 11px; font-weight: bold; letter-spacing: 1px; margin-bottom: 8px; border-bottom: 1px solid #333; padding-bottom: 4px;}
        .math-row { font-family: monospace; color: #fff; margin: 5px 0; display: flex; align-items: center; gap: 10px; font-size: 15px;}
        .math-arrow { color: var(--steam-blue); }
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
                <h2 style="color:white; margin-bottom: 5px;">Local Connection</h2>
                <p style="color:#8f98a0; margin-top: 0;">Configure your session to begin.</p>
            </div>

            <form method="post" id="local-connection-form" style="width: 100%; max-width: 450px; margin: 0 auto;">
                <div style="text-align: center; color:#8f98a0; font-size: 13px; font-weight: bold; margin-bottom: 8px; letter-spacing: 1px;">1. SET YOUR ALIAS</div>
                <input type="text" id="username_input" name="username" class="input-username" placeholder="Enter Username" maxlength="12" required>
                <div id="username_warning" style="color: #ff4444; font-size: 14px; margin-top: -20px; margin-bottom: 20px; height: 16px; text-align: center;"></div>

                <div style="text-align: center; color:#8f98a0; font-size: 13px; font-weight: bold; margin-bottom: 8px; letter-spacing: 1px;">2. CHOOSE ACTION</div>
                <button type="submit" formaction="/host" id="btn-host" class="btn btn-host" style="width: 100%; margin-top: 0;">HOST NEW SERVER</button>

                <div style="text-align: center; color: #44566c; margin: 25px 0; font-weight: bold; font-size: 14px; letter-spacing: 2px;">— OR JOIN EXISTING —</div>
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
                        usernameInput.style.borderColor = "#ff4444";
                    } else {
                        warningDiv.textContent = "";
                        usernameInput.style.borderColor = "#2a3f5a";
                        hostButton.disabled = false; joinButton.disabled = false;
                    } 
                    });
                });
                
                document.getElementById('btn-host').addEventListener('click', () => document.getElementById('room_code_box').required = false);
                document.getElementById('btn-join').addEventListener('click', () => document.getElementById('room_code_box').required = true);
            </script>
            <a href="/" style="color:#66c0f4; text-decoration:none; display:block; text-align:center; margin-top:40px;">Back to Menu</a>
 
        {% elif page == 'chat' %}
            
            <div class="chat-layout">
                <div class="chat-column">
                    <div class="chat-header">
                        <h2 style="margin:0; color:#fff;">ROOM: <span style="color:var(--steam-green-top); font-family:monospace;">{{ room_code }}</span></h2>
                        <a href="/leave" style="color:#ff4444; text-decoration:none; border:1px solid #ff4444; padding:5px 15px; border-radius:4px;">DISCONNECT</a>
                    </div>

                    <div id="chat-box" class="chat-log"></div>

                    <div class="chat-controls">
                        <input type="text" id="msg-input" class="chat-input" placeholder="Type an encrypted message..." autofocus>
                        <select id="encryption-selector">
                            <option value="none">None</option> 
                            <option value="caesar">Caesar Cipher</option> 
                        </select>
                        <button onclick="sendMessage()" class="btn" style="width:auto; margin:0; padding:0 30px;">SEND</button>
                    </div>
                </div>

                <div class="encryption-panel">
                    <div class="panel-section panel-top">
                        <div class="panel-header">Encryption - <span id="current-cipher" style="color: var(--steam-text);">None</span></div>
                        
                        <div id="caesar-controls" style="display: none; margin-top: 5px;">
                            <label for="caesar-slider" style="color: #8f98a0; font-size: 14px; font-weight: bold; letter-spacing: 1px;">
                                SHIFT VALUE: <span id="shift-display" style="color: var(--steam-blue); font-size: 16px;">1</span>
                            </label>
                            <input type="range" id="caesar-slider" min="1" max="25" value="1" style="margin: 15px 0 20px 0;">
                            
                            <div style="background: rgba(0,0,0,0.5); padding: 10px; border-radius: 4px; border: 1px solid #333; text-align: center;">
                                <div style="color: #8f98a0; font-size: 11px; margin-bottom: 8px; font-weight: bold; letter-spacing: 1px;">EXAMPLE SHIFT</div>
                                <div style="font-family: monospace; font-size: 14px; color: #fff; letter-spacing: 2px;">A B C D E</div>
                                <div id="example-shift" style="font-family: monospace; font-size: 14px; color: var(--steam-green-top); letter-spacing: 2px;">B C D E F</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="panel-divider"></div>
                    
                    <div class="panel-section panel-bottom">
                        <div class="panel-header" style="flex-shrink: 0;">Selected Message</div>
                        
                        <div id="selection-placeholder" style="color: #666; font-style: italic; text-align: center; margin-top: 20px;">
                            Click a message in the chat to view details.
                        </div>

                        <div id="selection-details" class="tabs-container" style="display: none;">
                            
                            <div style="background: rgba(0,0,0,0.5); padding: 10px; border-radius: 4px; border: 1px solid #333; margin-bottom: 15px; flex-shrink: 0;">
                                <div style="color: #8f98a0; font-size: 10px; margin-bottom: 5px; font-weight: bold; letter-spacing: 1px;">MESSAGE</div>
                                <div id="sel-payload" style="color: #fff; font-family: monospace; word-wrap: break-word; font-size: 14px;"></div>
                            </div>

                            <div class="tabs-header" style="flex-shrink: 0;">
                                <button class="tab-btn active" onclick="switchTab('decryption')">Decryption</button>
                                <button class="tab-btn" onclick="switchTab('solution')">Solution</button>
                                <button class="tab-btn" onclick="switchTab('history')">History</button>
                            </div>

                            <div id="tab-decryption" class="tab-content active">
                                <div id="tool-container-none" style="display:block; text-align: center; color: #666; font-style: italic; padding-top: 20px;">
                                    No decryption tools needed for plaintext.
                                </div>

                                <div id="tool-container-active" style="display:none; height: 100%; min-height: 0;">
                                    <div style="display: flex; height: 100%; gap: 15px;">
                                        
                                        <div style="width: 170px; flex-shrink: 0; display: flex; flex-direction: column; border-right: 1px solid #333; padding-right: 15px; overflow-y: auto;">
                                            <button class="side-btn active" onclick="switchTool(this, 'tool-shift')">Linear Shift Analysis</button>
                                            <button class="side-btn" onclick="switchTool(this, 'tool-matrix')">Matrix Factorization</button>
                                            <button class="side-btn" onclick="switchTool(this, 'tool-kasiski')">Statistical Attack</button>
                                        </div>
                                        
                                        <div style="flex: 1; overflow-y: auto; padding-right: 10px; padding-bottom: 40px;">
                                            
                                            <div id="tool-shift" class="tool-pane active">
                                                <h3 style="color: #fff; margin: 0 0 10px 0; font-size: 16px;">Linear Shift Analysis</h3>
                                                <p style="margin-top: 0;">This method systematically tests all 25 possible alphabetical shifts against the encrypted message. By sliding through every potential reverse shift and displaying the result, you can visually scan to identify the step that produces readable English.</p>
                                                
                                                <div style="margin-top: 15px;">
                                                    <label for="analyzer-slider" style="color: #8f98a0; font-size: 12px; font-weight: bold; letter-spacing: 1px; display:block;">
                                                        TEST REVERSE SHIFT: <span id="analyzer-display" style="color: var(--steam-blue); font-size: 14px;">1</span>
                                                    </label>
                                                    <input type="range" id="analyzer-slider" min="1" max="25" value="1" style="margin: 10px 0;">
                                                    <div id="analyzer-output" class="brute-force-output"></div>
                                                </div>
                                            </div>

                                            <div id="tool-matrix" class="tool-pane">
                                                <h3 style="color: #fff; margin: 0 0 10px 0; font-size: 16px;">Matrix Factorization</h3>
                                                <p style="margin-top: 0;">This method targets ciphers structured by linear algebra (specifically matrix multiplication modulo 26). The script generates every possible valid (invertible) key matrix, decrypts a small block, and scores the output using English letter frequencies.</p>
                                                
                                                <div style="margin-top: 15px;">
                                                    <button class="btn" style="padding: 10px; font-size: 14px;" onclick="simulateDecryption('hill-output', 'MATRIX_SOLVER_INITIALIZED...')">EXECUTE MATRIX CRACKER</button>
                                                    <div id="hill-output" class="brute-force-output" style="display:none; text-align: left; font-size: 12px;"></div>
                                                </div>
                                            </div>

                                            <div id="tool-kasiski" class="tool-pane">
                                                <h3 style="color: #fff; margin: 0 0 10px 0; font-size: 16px;">Statistical Keyword Attack</h3>
                                                <p style="margin-top: 0;">This method breaks ciphers that use a shifting keyword. First, it runs a Kasiski Examination to guess the keyword's length. If the key is estimated to be 5 letters, it knows every 5th letter shares the same shift, allowing it to fracture the complex cipher into 5 simple ones.</p>
                                                
                                                <div style="margin-top: 15px;">
                                                    <button class="btn" style="padding: 10px; font-size: 14px;" onclick="simulateDecryption('vig-output', 'COMMENCING_KASISKI_EXAM...')">INITIATE STATISTICAL ATTACK</button>
                                                    <div id="vig-output" class="brute-force-output" style="display:none; text-align: left; font-size: 12px;"></div>
                                                </div>
                                            </div>

                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div id="tab-solution" class="tab-content">
                                <div id="sol-none" style="display:block; text-align: center; color: #666; font-style: italic; padding-top: 20px;">
                                    Message was sent without encryption.
                                </div>
                                <div id="sol-dynamic" style="display:none;">
                                    
                                    <div class="solution-box">
                                        <div class="sol-title">1. ENCRYPTION PROCESS</div>
                                        <div class="math-row">
                                            <span style="color:#888;">Plaintext:</span> <span id="dyn-plain-1" style="color:var(--steam-blue);"></span>
                                        </div>
                                        <div class="math-row" style="color:#a4d007; font-size: 13px;">
                                            <span class="math-arrow">↳</span> <span id="dyn-enc-op"></span>
                                        </div>
                                        <div class="math-row">
                                            <span style="color:#888;">Ciphertext:</span> <span id="dyn-cipher-1"></span>
                                        </div>
                                    </div>

                                    <div class="solution-box" style="border-color: var(--steam-blue); background: rgba(102, 192, 244, 0.05);">
                                        <div class="sol-title" style="color: var(--steam-blue); border-bottom-color: var(--steam-blue);">2. RECOMMENDED TOOL</div>
                                        <div id="dyn-tool" style="color: #fff; font-size: 14px; margin-top: 5px;"></div>
                                    </div>

                                    <div class="solution-box">
                                        <div class="sol-title">3. DECRYPTION SOLUTION</div>
                                        <div class="math-row">
                                            <span style="color:#888;">Ciphertext:</span> <span id="dyn-cipher-2"></span>
                                        </div>
                                        <div class="math-row" style="color:#a4d007; font-size: 13px;">
                                            <span class="math-arrow">↳</span> <span id="dyn-dec-op"></span>
                                        </div>
                                        <div class="math-row">
                                            <span style="color:#888;">Plaintext:</span> <span id="dyn-plain-2" style="color:var(--steam-blue);"></span>
                                        </div>
                                    </div>

                                </div>
                            </div>

                            <div id="tab-history" class="tab-content">
                                <div id="hist-none" style="display:block; text-align: center; color: #666; font-style: italic; padding-top: 20px;">
                                    No cipher history to display.
                                </div>
                                <div id="hist-caesar" style="display:none;">
                                    <h3 style="color: #fff; margin: 0 0 10px 0; font-size: 16px;">History of the Caesar Cipher</h3>
                                    <p style="margin-top: 0;">The Caesar cipher is named after Julius Caesar, who, according to Suetonius, used it with a shift of three (A becoming D when encrypting, and D becoming A when decrypting) to protect messages of military significance. While Caesar's cipher is the first recorded use of this scheme, other substitution ciphers are known to have been used earlier.</p>
                                    <p>By the 19th century, the personal advertisements section in newspapers would sometimes be used to exchange messages encrypted using simple cipher schemes. Kahn (1967) describes instances of lovers engaging in secret communications enciphered using the Caesar cipher in <i>The Times</i>.</p>
                                    <p>Today, the Caesar cipher is completely unsuitable for secure communication due to its microscopic key space, but it is often incorporated as a part of more complex schemes, such as the Vigenère cipher, and still has modern applications in the ROT13 system (which obfuscates spoilers or punchlines on internet forums).</p>
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

                let selectedMessageId = null;
                let activeMessageIdForEmoji = null;
                let activePayloadForTools = ""; 

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
                                .nav { display: none !important; }
                                h2.category { display: none !important; }
                                .preview { display: none !important; }
                                input.search { color: white !important; }
                                .search-row { margin-top: 10px; margin-bottom: 5px; }
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
                        textArea.textContent = data.username + ': ' + data.msg;
                        
                        // Pass cipher type and key to selection function
                        contentWrapper.onclick = () => selectMessage(data.id, data.username, data.msg, data.cipher || 'none', data.key || 0);

                        const actionContainer = document.createElement('div');
                        actionContainer.className = 'msg-actions';

                        const emojiBtn = document.createElement('button');
                        emojiBtn.className = 'action-btn btn-emoji';
                        emojiBtn.innerHTML = `<svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none"><circle cx="12" cy="12" r="10"></circle><path d="M8 14s1.5 2 4 2 4-2 4-2"></path><line x1="9" y1="9" x2="9.01" y2="9"></line><line x1="15" y1="9" x2="15.01" y2="9"></line></svg>`;
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
                            delBtn.innerHTML = `<svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>`; 
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
                        socket.send({
                            msg: input.value, 
                            room: room, 
                            encryption: selection_box.value,
                            'encryption-value': parseInt(caesarSlider.value) || 0
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

                function selectMessage(id, username, msgText, cipherType, cipherKey) {
                    if (selectedMessageId) {
                        let prevMsg = document.getElementById('msg-content-' + selectedMessageId);
                        if(prevMsg) prevMsg.classList.remove('selected');
                    }
                    selectedMessageId = id;
                    let currentMsg = document.getElementById('msg-content-' + id);
                    if(currentMsg) currentMsg.classList.add('selected');

                    activePayloadForTools = msgText;

                    document.getElementById('selection-placeholder').style.display = 'none';
                    document.getElementById('selection-details').style.display = 'flex';
                    document.getElementById('sel-payload').textContent = msgText;

                    // Toggle specific cipher content sections
                    document.getElementById('tool-container-none').style.display = 'none';
                    document.getElementById('tool-container-active').style.display = 'none';
                    document.getElementById('sol-none').style.display = 'none';
                    document.getElementById('sol-dynamic').style.display = 'none';
                    document.getElementById('hist-none').style.display = 'none';
                    document.getElementById('hist-caesar').style.display = 'none';

                    // If encrypted (by ANY cipher in the future), show the tool array so they have to test and guess
                    if (cipherType !== 'none' && cipherType !== 'system') {
                        // Activate Decryption Tools Panel
                        document.getElementById('tool-container-active').style.display = 'block';
                        
                        // Activate Dynamic Solution Builder
                        document.getElementById('sol-dynamic').style.display = 'block';

                        if (cipherType === 'caesar') {
                            document.getElementById('hist-caesar').style.display = 'block';
                            
                            const shiftVal = parseInt(cipherKey) || 0;
                            // FIXED THE BUG HERE: performCaesarShift inherently subtracts the amount.
                            // Passing positive shiftVal perfectly reverses the cipher to get the exact original text.
                            const originalPlaintext = performCaesarShift(msgText, shiftVal); 
                            
                            // Process 1: Encryption
                            document.getElementById('dyn-plain-1').textContent = originalPlaintext;
                            document.getElementById('dyn-enc-op').textContent = `Applied Caesar Shift: +${shiftVal}`;
                            document.getElementById('dyn-cipher-1').textContent = msgText;
                            
                            // Process 2: Tool Recommendation
                            document.getElementById('dyn-tool').innerHTML = `To solve this without knowing the key, use the <strong>Linear Shift Analysis</strong> tool to systematically check all 25 possible shifts until readable English appears.`;
                            
                            // Process 3: Decryption
                            document.getElementById('dyn-cipher-2').textContent = msgText;
                            document.getElementById('dyn-dec-op').textContent = `Reverse Caesar Shift: -${shiftVal}`;
                            document.getElementById('dyn-plain-2').textContent = originalPlaintext;

                        } else {
                            // Fallback for future ciphers (Hill, Vigenere, etc.)
                            document.getElementById('hist-none').style.display = 'block';

                            document.getElementById('dyn-plain-1').textContent = "[UNKNOWN PLAINTEXT]";
                            document.getElementById('dyn-enc-op').textContent = `Applied ${cipherType.toUpperCase()} Encryption Algorithm`;
                            document.getElementById('dyn-cipher-1').textContent = msgText;
                            
                            document.getElementById('dyn-tool').innerHTML = `Identify the cipher characteristics and select the appropriate Decryption Tool to analyze this message.`;
                            
                            document.getElementById('dyn-cipher-2').textContent = msgText;
                            document.getElementById('dyn-dec-op').textContent = `Applied ${cipherType.toUpperCase()} Decryption Algorithm`;
                            document.getElementById('dyn-plain-2').textContent = "[UNKNOWN PLAINTEXT]";
                        }

                        // Reset visual outputs for tools
                        document.getElementById('hill-output').style.display = 'none';
                        document.getElementById('vig-output').style.display = 'none';
                        document.getElementById('analyzer-slider').value = 1;
                        document.getElementById('analyzer-display').textContent = 1;
                        runCaesarBruteForceSlider(1);

                    } else {
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

                // --- COOL HACKER SIMULATIONS ---
                function simulateDecryption(targetId, startMsg) {
                    const out = document.getElementById(targetId);
                    out.style.display = 'block';
                    out.style.color = '#a4d007';
                    out.innerHTML = startMsg + '<br>';
                    
                    let count = 0;
                    const max = 15;
                    const interval = setInterval(() => {
                        let gibberish = '';
                        for(let i=0; i<30; i++) gibberish += String.fromCharCode(33 + Math.floor(Math.random() * 94));
                        out.innerHTML += `[TESTING] ${gibberish}<br>`;
                        out.scrollTop = out.scrollHeight;
                        
                        count++;
                        if (count >= max) {
                            clearInterval(interval);
                            out.innerHTML += `<br><span style="color:var(--steam-danger)">ERROR: INVALID CIPHER CONFIGURATION DETECTED.</span><br>`;
                            out.innerHTML += `<span style="color:#888">Target payload does not match expected matrix/dictionary structure.</span>`;
                            out.scrollTop = out.scrollHeight;
                        }
                    }, 100);
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
                    if (selection_box.value === 'caesar') {
                        caesarControls.style.display = 'block';
                        updateExampleShift(parseInt(caesarSlider.value));
                    } else {
                        caesarControls.style.display = 'none';
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
    encryption_value = data.get('encryption-value', 0) 
    username = session.get('username', 'Guest')
    
    if encryption_type != "none":
        encrypted_bytes = encryption_manager.encrypt(encryption_type, msg.encode('utf-8'), encryption_value).decode('utf-8')
    else:
        encrypted_bytes = msg
    
    message_payload = {
        'id': str(uuid.uuid4()),
        'username': username,
        'msg': encrypted_bytes,
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