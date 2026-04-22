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
        :root {
            --bg-dark: #0f172a;
            --bg-panel: rgba(30, 41, 59, 0.75);
            --text-main: #e2e8f0;
            --text-muted: #94a3b8;
            --accent-blue: #3b82f6;
            --accent-blue-hover: #60a5fa;
            --accent-green: #10b981;
            --accent-purple: #8b5cf6;
            --danger: #ef4444;
            --border-light: rgba(255, 255, 255, 0.15);
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
                radial-gradient(circle at 15% 50%, rgba(59, 130, 246, 0.12), transparent 25%),
                radial-gradient(circle at 85% 30%, rgba(139, 92, 246, 0.12), transparent 25%);
            background-attachment: fixed;
        }
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.2); border-radius: 10px; }
        ::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.3); }
        
        .header { width: 100%; background: rgba(15, 23, 42, 0.85); padding: 20px 15px; backdrop-filter: blur(12px); display: flex; justify-content: center; border-bottom: 1px solid var(--border-light); z-index: 10; }
        h1 { margin: 0; font-size: 26px; text-transform: uppercase; letter-spacing: 5px; color: #fff; font-weight: 800; background: linear-gradient(to right, #60a5fa, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        
        .container { width: 95%; max-width: 1400px; background: var(--bg-panel); padding: 25px; border-radius: 16px; backdrop-filter: blur(20px); box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5); border: 1px solid var(--border-light); margin-top: 3vh; height: 82vh; display: flex; flex-direction: column; }
        
        /* HOMEPAGE CARDS */
        .module-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; width: 100%; max-width: 1000px; margin: 20px auto; }
        .module-card { background: rgba(0,0,0,0.4); border: 1px solid var(--border-light); border-radius: 12px; padding: 30px 20px; text-align: center; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); text-decoration: none; display: flex; flex-direction: column; align-items: center; justify-content: center;}
        .module-card:hover { transform: translateY(-5px); border-color: var(--accent-blue); box-shadow: 0 10px 30px rgba(59, 130, 246, 0.2); background: rgba(59, 130, 246, 0.05); }
        .module-card h3 { color: #fff; font-size: 20px; margin: 0 0 10px 0; text-transform: uppercase; letter-spacing: 2px; }
        .module-card p { color: var(--text-muted); font-size: 14px; margin: 0; line-height: 1.5;}

        .btn { display: flex; align-items: center; justify-content: center; padding: 16px 24px; background: linear-gradient(135deg, var(--accent-blue) 0%, #2563eb 100%); color: #fff; font-size: 14px; text-decoration: none; text-transform: uppercase; border: none; border-radius: 8px; cursor: pointer; transition: all 0.3s; font-weight: 800; letter-spacing: 1.5px;}
        .btn:hover { background: linear-gradient(135deg, #60a5fa 0%, var(--accent-blue) 100%); transform: translateY(-2px); box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4); }
        .btn-host { background: linear-gradient(135deg, var(--accent-green) 0%, #059669 100%); font-size: 18px; box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3); }
        .btn-host:hover { background: linear-gradient(135deg, #34d399 0%, var(--accent-green) 100%); box-shadow: 0 8px 25px rgba(16, 185, 129, 0.4); }
        .btn-join { width: auto; padding: 0 40px; margin: 0; background: #334155; box-shadow: none;}
        .btn-join:hover { background: #475569; }
        
        .input-username { width: 100%; padding: 18px 20px; background: rgba(0,0,0,0.3); border: 1px solid var(--border-light); color: #fff; font-size: 18px; border-radius: 8px; box-sizing: border-box; text-align: center; margin-bottom: 25px; transition: all 0.3s; font-family: var(--font-main); }
        .input-username:focus { outline: none; border-color: var(--accent-blue); box-shadow: 0 0 15px rgba(59, 130, 246, 0.2); background: rgba(0,0,0,0.5); }
        .join-row { display: flex; gap: 12px; }
        .input-code { flex: 1; padding: 15px; background: rgba(0,0,0,0.4); border: 1px solid var(--border-light); color: var(--accent-blue); font-family: var(--font-mono); font-size: 24px; text-transform: uppercase; text-align: center; letter-spacing: 8px; border-radius: 8px; box-sizing: border-box; transition: all 0.3s; }
        .input-code:focus { outline: none; border-color: var(--accent-purple); box-shadow: 0 0 15px rgba(139, 92, 246, 0.2); }
        
        /* CHAT LAYOUT */
        .chat-layout { display: flex; width: 100%; height: 100%; gap: 25px; }
        .chat-column { flex: 2; display: flex; flex-direction: column; }
        .encryption-panel { flex: 3.5; background: rgba(15, 23, 42, 0.8); border: 1px solid var(--border-light); border-radius: 12px; display: flex; flex-direction: column; overflow: hidden; box-shadow: inset 0 0 20px rgba(0,0,0,0.3); }
        .panel-section { padding: 25px; display: flex; flex-direction: column; }
        .panel-top { height: 28%; flex: none; overflow-y: auto;} 
        .panel-bottom { height: 72%; flex: none; display: flex; flex-direction: column; padding-bottom: 0; overflow: hidden;} 
        .panel-divider { height: 1px; background: linear-gradient(to right, transparent, var(--border-light), transparent); width: 100%; flex-shrink: 0; }
        .panel-header { color: var(--accent-purple); font-weight: 800; font-size: 14px; text-transform: uppercase; letter-spacing: 2px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 12px; margin-bottom: 15px; flex-shrink: 0; }
        
        .chat-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-light); padding-bottom: 15px; margin-bottom: 15px; }
        .chat-log { flex: 1; background: rgba(0, 0, 0, 0.3); border: 1px solid var(--border-light); border-radius: 12px; padding: 20px; overflow-y: auto; margin-bottom: 20px; font-family: var(--font-mono); display: flex; flex-direction: column; gap: 12px; box-shadow: inset 0 4px 20px rgba(0,0,0,0.2);}
        
        .message-row { display: flex; flex-direction: column; margin-bottom: 4px; }
        .msg-content-wrapper { display: flex; align-items: flex-start; justify-content: space-between; padding: 12px 16px; border-radius: 8px; transition: all 0.2s; box-sizing: border-box; border: 1px solid transparent; background: rgba(255,255,255,0.02); }
        .msg-text-area { flex: 1; line-height: 1.5; font-size: 14px; word-break: break-all;}
        .msg-system { color: var(--accent-purple); font-style: italic; background: transparent; border: none; padding: 5px 10px;}
        .msg-user { color: #f8fafc; cursor: pointer; }
        .msg-content-wrapper.selected { background-color: rgba(59, 130, 246, 0.15); border: 1px solid var(--accent-blue); transform: scale(1.01); box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
        
        .msg-actions { display: flex; align-items: center; justify-content: flex-end; gap: 8px; width: 60px; min-width: 60px; opacity: 0; transition: opacity 0.2s; }
        .msg-content-wrapper:hover { background-color: rgba(255, 255, 255, 0.08); }
        .msg-content-wrapper:hover .msg-actions { opacity: 1; }
        .action-btn { background: none; border: none; cursor: pointer; color: var(--text-muted); opacity: 0.7; padding: 4px; display: flex; align-items: center; justify-content: center; transition: all 0.2s; }
        .action-btn:hover { opacity: 1; color: #fff; transform: scale(1.2); }
        .btn-trash:hover { color: var(--danger); }
        .btn-emoji:hover { color: #fbbf24; }
        .emoji-picker-container { position: absolute; z-index: 1000; display: none; box-shadow: 0 15px 35px rgba(0,0,0,0.6); border-radius: 12px; border: 1px solid var(--border-light); background: var(--bg-dark); overflow: hidden; }
        
        .reactions-row { display: flex; gap: 6px; flex-wrap: wrap; padding-left: 10px; margin-top: 6px; }
        .reaction-badge { background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 4px 8px; font-size: 13px; cursor: pointer; color: var(--text-muted); display: flex; align-items: center; gap: 5px; user-select: none; transition: all 0.2s; font-family: var(--font-main); }
        .reaction-badge:hover { background: rgba(255, 255, 255, 0.15); color: #fff; }
        .reaction-badge.active { background: rgba(59, 130, 246, 0.2); border-color: var(--accent-blue); color: #fff; }
        
        .chat-controls { display: flex; gap: 12px; }
        .chat-input { flex: 1; padding: 15px; background: rgba(0,0,0,0.4); border: 1px solid var(--border-light); color: white; font-size: 15px; border-radius: 8px; font-family: var(--font-main); transition: all 0.3s;}
        .chat-input:focus { outline: none; border-color: var(--accent-blue); box-shadow: 0 0 10px rgba(59, 130, 246, 0.2); }
        #encryption-selector { padding: 15px; background: rgba(0,0,0,0.4); border: 1px solid var(--border-light); color: white; font-size: 15px; font-family: var(--font-main); border-radius: 8px; cursor: pointer; outline: none; transition: all 0.3s;}
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
        .tab-btn { flex: 1; background: none; border: none; color: var(--text-muted); padding: 14px 10px; cursor: pointer; transition: all 0.3s; font-weight: 800; text-transform: uppercase; font-size: 12px; letter-spacing: 1px; border-bottom: 2px solid transparent; font-family: var(--font-main); }
        .tab-btn:hover { color: #fff; background: rgba(255,255,255,0.03); }
        .tab-btn.active { color: var(--accent-blue); border-bottom-color: var(--accent-blue); background: linear-gradient(to top, rgba(59, 130, 246, 0.1), transparent); }
        .tab-content { display: none; flex: 1; overflow-y: auto; padding: 5px 0 150px 0; color: var(--text-muted); line-height: 1.6; font-size: 14px; min-height: 0;}
        .tab-content.active { display: flex; flex-direction: column; }
        
        /* INNER SIDEBAR STYLING FOR DECRYPTION TOOLS */
        .side-btn { background: none; border: none; color: var(--text-muted); padding: 14px 12px; cursor: pointer; transition: all 0.2s; font-weight: 600; font-size: 12px; text-transform: uppercase; text-align: left; border-left: 3px solid transparent; width: 100%; border-bottom: 1px solid rgba(255,255,255,0.02); font-family: var(--font-main); }
        .side-btn:hover { color: #fff; background: rgba(255,255,255,0.03); padding-left: 16px;}
        .side-btn.active { color: var(--accent-blue); border-left-color: var(--accent-blue); background: linear-gradient(to right, rgba(59, 130, 246, 0.1), transparent); padding-left: 16px;}
        .tool-pane { display: none; height: 100%; flex-direction: column;}
        .tool-pane.active { display: flex; animation: fadeIn 0.4s ease; }
        
        /* SOLVER OUTPUTS */
        .brute-force-output { background: rgba(0,0,0,0.4); border: 1px solid var(--border-light); border-radius: 8px; padding: 20px; margin-top: 15px; font-family: var(--font-mono); font-size: 15px; color: var(--accent-green); letter-spacing: 1px; min-height: 80px; word-break: break-all; box-shadow: inset 0 0 15px rgba(0,0,0,0.5);}
        .solution-box { background: rgba(0,0,0,0.3); border: 1px solid var(--border-light); border-radius: 8px; padding: 20px; margin-bottom: 15px;}
        .sol-title { color: var(--text-muted); font-size: 11px; font-weight: 800; letter-spacing: 1.5px; margin-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 6px;}
        .math-row { font-family: var(--font-mono); color: #fff; margin: 8px 0; display: flex; align-items: flex-start; gap: 12px; font-size: 14px;}
        .math-arrow { color: var(--accent-purple); font-weight: bold; margin-top: 2px;}
        
        /* ALIGNED HILL GRID PICKER & MATRIX */
        .grid-picker-cell { width: 16px; height: 16px; border: 1px solid rgba(255,255,255,0.15); border-radius: 2px; background: rgba(255,255,255,0.04); transition: all 0.08s; cursor: pointer; }
        .grid-picker-cell:hover { transform: scale(1.1); }
        #hill-matrix-container { display: grid; gap: 10px; justify-content: center; align-content: center; background: rgba(0,0,0,0.3); padding: 20px; border-radius: 8px; border: 1px solid var(--border-light); width: 100%; box-sizing: border-box;}
        .hill-cell { aspect-ratio: 1 / 1; width: 100%; max-width: 60px; text-align: center; font-family: var(--font-mono); font-size: 18px; font-weight: bold; padding: 0; box-sizing: border-box; border-radius: 6px; }

        /* INTERACTIVE STEP BOXES */
        .step-box { background: rgba(0,0,0,0.35); border: 1px solid var(--border-light); border-radius: 10px; padding: 20px; margin-bottom: 15px; }
        .step-title { color: var(--accent-blue); font-weight: 800; font-size: 13px; letter-spacing: 1.5px; margin-bottom: 10px; text-transform: uppercase; }
        .step-input-row { display: flex; align-items: center; gap: 10px; margin-top: 12px; flex-wrap: wrap; }
        .step-input { width: 70px; padding: 10px; background: rgba(0,0,0,0.5); border: 1px solid var(--border-light); color: white; font-family: var(--font-mono); font-size: 18px; border-radius: 6px; text-align: center; outline: none; transition: border-color 0.2s; }
        .step-input:focus { border-color: var(--accent-blue); }
        .check-btn { padding: 10px 20px; background: rgba(59,130,246,0.2); border: 1px solid var(--accent-blue); color: var(--accent-blue); border-radius: 6px; cursor: pointer; font-family: var(--font-main); font-weight: 800; font-size: 12px; letter-spacing: 1px; text-transform: uppercase; transition: all 0.2s; }
        .check-btn:hover { background: rgba(59,130,246,0.4); color: #fff; }
        .feedback-ok { color: var(--accent-green); font-size: 13px; font-weight: 600; margin-top: 8px; }
        .feedback-err { color: var(--danger); font-size: 13px; font-weight: 600; margin-top: 8px; }
        .matrix-display { font-family: var(--font-mono); background: rgba(0,0,0,0.4); padding: 15px; border-radius: 6px; border: 1px solid var(--border-light); display: inline-block; line-height: 1.9; color: #fff; margin: 8px 0; }
        
        /* TABLES FOR STEP BY STEP */
        .solution-table { width: 100%; border-collapse: collapse; margin-top: 10px; font-family: var(--font-mono); font-size: 13px; }
        .solution-table th { text-align: left; padding: 8px; border-bottom: 1px solid var(--border-light); color: var(--text-muted); font-size: 11px; letter-spacing: 1px; font-family: var(--font-main);}
        .solution-table td { padding: 8px; border-bottom: 1px solid rgba(255,255,255,0.05); color: #fff; }
        .solution-table tr:last-child td { border-bottom: none; }
        .highlight-cell { color: var(--accent-purple); font-weight: bold; }

        @keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
    </style>
</head>
<body>
    <div class="header">
        <h1>Insightful Encryptions</h1>
    </div>
    
    <div class="container">
        {% if page == 'home' %}
            <div style="text-align: center; margin-bottom: 10px;">
                <h2 style="color:white; margin-bottom: 8px; font-size: 32px; letter-spacing: 2px;">SELECT MODULE</h2>
                <p style="color:var(--text-muted); margin-top: 0; font-size: 16px;">Choose an environment to begin your cryptographic analysis.</p>
            </div>
            
            <div class="module-grid">
                <a href="/classroom" class="module-card">
                    <svg viewBox="0 0 24 24" width="48" height="48" stroke="var(--accent-blue)" stroke-width="1.5" fill="none" style="margin-bottom:15px;"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path></svg>
                    <h3>Classroom Interface</h3>
                    <p>Guided, step-by-step cryptographic lessons for structured learning.</p>
                </a>
                <a href="/lab" class="module-card">
                    <svg viewBox="0 0 24 24" width="48" height="48" stroke="var(--accent-purple)" stroke-width="1.5" fill="none" style="margin-bottom:15px;"><path d="M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2V9M9 21H5a2 2 0 0 1-2-2V9m0 0h18"></path></svg>
                    <h3>The Lab</h3>
                    <p>An open sandbox to freely experiment with different encryption algorithms.</p>
                </a>
                <a href="/local" class="module-card" style="border-color: var(--accent-green); background: rgba(16, 185, 129, 0.05);">
                    <svg viewBox="0 0 24 24" width="48" height="48" stroke="var(--accent-green)" stroke-width="1.5" fill="none" style="margin-bottom:15px;"><rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect><rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect><line x1="6" y1="6" x2="6.01" y2="6"></line><line x1="6" y1="18" x2="6.01" y2="18"></line></svg>
                    <h3 style="color: var(--accent-green);">Local Connection</h3>
                    <p>Host or join an interactive multi-user cryptographic communication room.</p>
                </a>
            </div>

        {% elif page == 'local' %}
            <div style="text-align: center; margin-bottom: 40px; padding-top: 20px;">
                <h2 style="color:white; margin-bottom: 8px; font-size: 32px; letter-spacing: 2px;">SECURE CONNECTION</h2>
                <p style="color:var(--text-muted); margin-top: 0; font-size: 16px;">Configure your session identity and access point.</p>
            </div>
            <form method="post" id="local-connection-form" style="width: 100%; max-width: 450px; margin: 0 auto; background: rgba(0,0,0,0.2); padding: 40px; border-radius: 12px; border: 1px solid var(--border-light); box-shadow: 0 10px 30px rgba(0,0,0,0.2);">
                <div style="text-align: center; color:var(--accent-blue); font-size: 12px; font-weight: 800; margin-bottom: 10px; letter-spacing: 1.5px;">1. SET YOUR ALIAS</div>
                <input type="text" id="username_input" name="username" class="input-username" placeholder="Enter Username" maxlength="12" required>
                <div id="username_warning" style="color: var(--danger); font-size: 14px; margin-top: -15px; margin-bottom: 25px; height: 16px; text-align: center; font-weight: 600;"></div>
                
                <div style="text-align: center; color:var(--accent-green); font-size: 12px; font-weight: 800; margin-bottom: 10px; letter-spacing: 1.5px;">2. INITIALIZE SERVER</div>
                <button type="submit" formaction="/host" id="btn-host" class="btn btn-host" style="width: 100%; margin-top: 0;">HOST NEW ROOM</button>
                
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
                        warningDiv.textContent = "Alias already in use on network.";
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
            <a href="/" style="color:var(--accent-blue); text-decoration:none; display:block; text-align:center; margin-top:40px; font-weight:600; font-size: 14px; letter-spacing: 1px; text-transform: uppercase;">Back to Main Menu</a>
 
        {% elif page == 'chat' %}
            
            <div class="chat-layout">
                <div class="chat-column">
                    <div class="chat-header">
                        <h2 style="margin:0; color:#fff; font-size: 18px; letter-spacing:1px;">SECURE ROOM: <span style="color:var(--accent-green); font-family:var(--font-mono); font-size: 24px; margin-left: 8px; text-shadow: 0 0 10px rgba(16,185,129,0.4);">${{ room_code }}</span></h2>
                        <a href="/leave" class="btn" style="padding: 10px 20px; background: rgba(239, 68, 68, 0.1); border: 1px solid var(--danger); color: var(--danger); box-shadow: none;">DISCONNECT</a>
                    </div>
                    <div id="chat-box" class="chat-log"></div>
                    <div class="chat-controls">
                        <input type="text" id="msg-input" class="chat-input" placeholder="Type an encrypted message..." autofocus>
                        <select id="encryption-selector">
                            <option value="none">Plaintext (None)</option> 
                            <option value="caesar">Caesar Cipher</option> 
                            <option value="hill">Hill Cipher</option>
                            <option value="vigenere">Vigenère Cipher</option>
                            <option value="aes">AES-256</option>
                            <option value="quantum">BB84 Quantum</option>
                        </select>
                        <button onclick="sendMessage()" class="btn" style="width:auto; margin:0; padding:0 35px;">SEND</button>
                    </div>
                </div>
                
                <div class="encryption-panel">
                    <div class="panel-section panel-top">
                        <div class="panel-header">Encryption Parameter: <span id="current-cipher" style="color: #fff;">Plaintext (None)</span></div>
                        
                        <div id="caesar-controls" style="display: none; margin-top: 5px;">
                            <label for="caesar-slider" style="color: var(--text-muted); font-size: 12px; font-weight: 800; letter-spacing: 1px;">
                                SHIFT VALUE: <span id="shift-display" style="color: var(--accent-blue); font-size: 18px;">1</span>
                            </label>
                            <input type="range" id="caesar-slider" min="1" max="25" value="1" style="margin: 15px 0 20px 0;">
                            <div style="background: rgba(0,0,0,0.4); padding: 12px; border-radius: 8px; border: 1px solid var(--border-light); text-align: center;">
                                <div style="color: var(--text-muted); font-size: 10px; margin-bottom: 8px; font-weight: 800; letter-spacing: 1px;">EXAMPLE SHIFT</div>
                                <div style="font-family: var(--font-mono); font-size: 15px; color: #fff; letter-spacing: 4px;">A B C D E</div>
                                <div id="example-shift" style="font-family: var(--font-mono); font-size: 15px; color: var(--accent-green); letter-spacing: 4px; margin-top: 4px;">B C D E F</div>
                            </div>
                        </div>
                        
                        <div id="hill-controls" style="display: none; margin-top: 15px;">
                            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
                                <label style="color: var(--text-muted); font-size: 12px; font-weight: 800; letter-spacing: 1px; padding-top: 6px;">KEY MATRIX:</label>
                                <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 5px;">
                                    <span id="hill-size-label" style="color: var(--accent-blue); font-size: 14px; font-weight: 800; letter-spacing: 1px; font-family: var(--font-mono);">2 × 2</span>
                                    <div id="hill-grid-picker" style="display: grid; grid-template-columns: repeat(4, 16px); gap: 3px; padding: 6px; background: rgba(0,0,0,0.4); border-radius: 6px; border: 1px solid var(--border-light); cursor: pointer;"></div>
                                    <span style="color: var(--text-muted); font-size: 10px; letter-spacing: 0.5px;">drag to resize</span>
                                </div>
                            </div>
                            <div id="hill-matrix-container"></div>
                        </div>
                        
                        <div id="text-key-controls" style="display: none; margin-top: 15px;">
                            <label style="color: var(--text-muted); font-size: 12px; font-weight: 800; letter-spacing: 1px;">ENCRYPTION KEYWORD / SEED:</label>
                            <input type="text" id="text-key-input" class="chat-input" value="SECRET" style="width: 100%; padding: 15px; margin-top: 12px; font-family: var(--font-mono); font-size: 18px; box-sizing: border-box; text-align: center; text-transform: uppercase;">
                        </div>
                    </div>
                    
                    <div class="panel-divider"></div>
                    
                    <div class="panel-section panel-bottom">
                        <div class="panel-header" style="flex-shrink: 0; color: var(--accent-blue);">Message Inspector</div>
                        
                        <div id="selection-placeholder" style="color: var(--text-muted); font-style: italic; text-align: center; margin-top: 30px; font-size: 15px;">
                            <svg viewBox="0 0 24 24" width="48" height="48" stroke="rgba(255,255,255,0.2)" stroke-width="1.5" fill="none" style="margin-bottom:15px; display:block; margin: 0 auto 15px;"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
                            Click a message in the chat feed to analyze its cryptographic payload.
                        </div>
                        
                        <div id="selection-details" class="tabs-container" style="display: none;">
                            <div style="background: rgba(0,0,0,0.4); padding: 15px; border-radius: 8px; border: 1px solid var(--border-light); margin-bottom: 15px; flex-shrink: 0;">
                                <div style="color: var(--text-muted); font-size: 10px; margin-bottom: 8px; font-weight: 800; letter-spacing: 1px;">INTERCEPTED PAYLOAD</div>
                                <div id="sel-payload" style="color: #fff; font-family: var(--font-mono); word-wrap: break-word; font-size: 15px;"></div>
                            </div>
                            
                            <div class="tabs-header" style="flex-shrink: 0;">
                                <button class="tab-btn active" onclick="switchTab('decryption', event)">Interactive Cracker</button>
                                <button class="tab-btn" onclick="switchTab('solution', event)">Solution Breakdown</button>
                                <button class="tab-btn" onclick="switchTab('history', event)">Cryptography Lore</button>
                            </div>
                            
                            <div id="tab-decryption" class="tab-content active">
                                <div id="tool-container-none" style="display:block; text-align: center; color: var(--text-muted); font-style: italic; padding-top: 20px;">
                                    No tools required for plaintext.
                                </div>
                                <div id="tool-container-active" style="display:none; height: 100%; min-height: 0;">
                                    <div style="display: flex; height: 100%; gap: 15px;">
                                        <div style="width: 190px; flex-shrink: 0; display: flex; flex-direction: column; border-right: 1px solid var(--border-light); padding-right: 15px; overflow-y: auto;">
                                            <button class="side-btn" id="btn-t-shift" onclick="switchTool(this, 'tool-shift')">Shift Analysis</button>
                                            <button class="side-btn" id="btn-t-matrix" onclick="switchTool(this, 'tool-matrix')">Matrix Factorization</button>
                                            <button class="side-btn" id="btn-t-kasiski" onclick="switchTool(this, 'tool-kasiski')">Statistical Attack</button>
                                            <button class="side-btn" id="btn-t-aes" onclick="switchTool(this, 'tool-aes')">AES Visualizer</button>
                                            <button class="side-btn" id="btn-t-quantum" onclick="switchTool(this, 'tool-quantum')">Quantum Intercept</button>
                                        </div>
                                        <div style="flex: 1; overflow-y: auto; padding-right: 10px; padding-bottom: 150px;">
                                            
                                            <div id="tool-shift" class="tool-pane">
                                                <h3 style="color: #fff; margin: 0 0 8px 0; font-size: 18px; font-weight: 800; letter-spacing: 1px;">Linear Shift Analysis</h3>
                                                <p style="margin: 0 0 16px 0; color: var(--text-muted);">Drag the slider to brute-force the reverse shift. Stop when the output reads clearly.</p>
                                                <div>
                                                    <label style="color: var(--text-muted); font-size: 12px; font-weight: 800; letter-spacing: 1px; display:block; margin-bottom: 6px;">
                                                        TEST REVERSE SHIFT: <span id="analyzer-display" style="color: var(--accent-blue); font-size: 18px;">1</span>
                                                    </label>
                                                    <input type="range" id="analyzer-slider" min="1" max="25" value="1" style="margin: 10px 0;">
                                                    <div id="analyzer-output" class="brute-force-output" style="min-height: 55px; font-size: 16px;"></div>
                                                </div>
                                                <div style="margin-top: 16px; padding: 20px; background: rgba(0,0,0,0.3); border-radius: 8px; border: 1px solid var(--border-light);">
                                                    <div style="color: var(--text-muted); font-size: 11px; font-weight: 800; letter-spacing: 1.5px; margin-bottom: 8px;">LOCK IN YOUR ANSWER</div>
                                                    <button onclick="submitCaesarAnswer()" class="btn" style="width: 100%; padding: 12px; margin-top: 10px; font-size: 14px;">
                                                        SUBMIT — SHIFT <span id="shift-submit-display" style="margin-left: 5px;">1</span>
                                                    </button>
                                                    <div id="caesar-submit-feedback" style="margin-top: 10px; font-size: 13px; font-weight: 600; text-align: center;"></div>
                                                </div>
                                            </div>
                                            
                                            <div id="tool-matrix" class="tool-pane">
                                                <h3 style="color: #fff; margin: 0 0 8px 0; font-size: 18px; font-weight: 800; letter-spacing: 1px;">Matrix Factorization</h3>
                                                <p style="margin: 0 0 16px 0; color: var(--text-muted);">Derive the inverse of the key matrix (mod 26) to decode the cipher blocks.</p>
                                                <div id="hill-solver-area"></div>
                                                <button id="btn-matrix-start" class="btn" style="padding: 12px; font-size: 14px; margin-top: 8px; width: 100%;" onclick="initHillSolver()">INITIALIZE MATH ENGINE</button>
                                            </div>
                                            
                                            <div id="tool-kasiski" class="tool-pane">
                                                <h3 style="color: #fff; margin: 0 0 8px 0; font-size: 18px; font-weight: 800; letter-spacing: 1px;">Statistical Keyword Attack</h3>
                                                <p style="margin: 0 0 16px 0; color: var(--text-muted);">Conduct a Kasiski Examination to deduce keyword length, then run frequency analysis on the interwoven alphabets.</p>
                                                <div id="vig-solver-area"></div>
                                                <button id="btn-vig-start" class="btn" style="padding: 12px; font-size: 14px; margin-top: 8px; width: 100%;" onclick="initVigenereSolver()">INITIATE STATISTICAL ATTACK</button>
                                            </div>

                                            <div id="tool-aes" class="tool-pane">
                                                <h3 style="color: #fff; margin: 0 0 8px 0; font-size: 18px; font-weight: 800; letter-spacing: 1px;">AES Round Visualizer</h3>
                                                <p style="margin: 0 0 16px 0; color: var(--text-muted);">AES is mathematically secure. Instead of cracking it, observe the diffusion caused by a single AES round transformation on a dummy state matrix.</p>
                                                <div id="aes-solver-area"></div>
                                                <button id="btn-aes-start" class="btn" style="padding: 12px; font-size: 14px; margin-top: 8px; width: 100%;" onclick="initAesSolver()">SIMULATE AES ROUND</button>
                                            </div>

                                            <div id="tool-quantum" class="tool-pane">
                                                <h3 style="color: #fff; margin: 0 0 8px 0; font-size: 18px; font-weight: 800; letter-spacing: 1px;">Quantum Interception</h3>
                                                <p style="margin: 0 0 16px 0; color: var(--text-muted);">Attempt an eavesdrop (Eve) on a BB84 photon stream. Pick the wrong measurement basis, and you corrupt the data, alerting the sender.</p>
                                                <div id="quantum-solver-area"></div>
                                                <button id="btn-quantum-start" class="btn" style="padding: 12px; font-size: 14px; margin-top: 8px; width: 100%;" onclick="initQuantumSolver()">INITIALIZE EAVESDROP</button>
                                            </div>

                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div id="tab-solution" class="tab-content">
                                <div id="sol-none" style="display:block; text-align: center; color: var(--text-muted); font-style: italic; padding-top: 20px;">
                                    Message was sent in plaintext. No cryptographic analysis required.
                                </div>
                                <div id="sol-dynamic" style="display:none;">
                                    <div class="solution-box" style="border-color: var(--accent-blue); background: rgba(59, 130, 246, 0.05);">
                                        <div class="sol-title" style="color: var(--accent-blue); border-bottom-color: rgba(59,130,246,0.2);">1. ENCRYPTION TRACE</div>
                                        <div id="dyn-enc-steps"></div>
                                    </div>
                                    
                                    <div class="solution-box" style="border-color: var(--accent-purple); background: rgba(139, 92, 246, 0.05);">
                                        <div class="sol-title" style="color: var(--accent-purple); border-bottom-color: rgba(139, 92, 246, 0.2);">2. ATTACK VECTOR</div>
                                        <div id="dyn-tool" style="color: #fff; font-size: 14px; margin-top: 8px; line-height: 1.6;"></div>
                                    </div>
                                    
                                    <div class="solution-box" style="border-color: var(--accent-green); background: rgba(16, 185, 129, 0.05);">
                                        <div class="sol-title" style="color: var(--accent-green); border-bottom-color: rgba(16,185,129,0.2);">3. RECOVERED PLAINTEXT</div>
                                        <div class="math-row"><span id="dyn-plain-2" style="color:#fff; font-size: 16px; font-weight: bold;"></span></div>
                                    </div>
                                </div>
                            </div>
                            
                            <div id="tab-history" class="tab-content">
                                <div id="hist-none" style="display:block; text-align: center; color: var(--text-muted); font-style: italic; padding-top: 20px;">No historical data for plaintext.</div>
                                <div id="hist-caesar" class="history-block" style="display:none;">
                                    <h3 style="color: #fff; margin: 0 0 10px 0; font-size: 18px; font-weight: 800;">Julius Caesar's Cipher</h3>
                                    <p style="margin-top: 0;">Historically utilized by Julius Caesar to protect messages of military significance, this substitution cipher shifted the alphabet by three positions.</p>
                                    <p>Though trivial to break today via brute force or frequency analysis, it remains the foundational building block for complex modern algorithms.</p>
                                </div>
                                <div id="hist-hill" class="history-block" style="display:none;">
                                    <h3 style="color: #fff; margin: 0 0 10px 0; font-size: 18px; font-weight: 800;">Lester S. Hill's Matrix Cipher</h3>
                                    <p style="margin-top: 0;">Invented in 1929, the Hill cipher revolutionized cryptology by introducing linear algebra. By operating on blocks of letters simultaneously via matrix multiplication, it thwarted basic frequency analysis.</p>
                                    <p>Its complete linearity makes it vulnerable to Known-Plaintext attacks, but its concept of matrix diffusion heavily influenced modern block ciphers like AES.</p>
                                </div>
                                <div id="hist-aes" class="history-block" style="display:none;">
                                    <h3 style="color: #fff; margin: 0 0 10px 0; font-size: 18px; font-weight: 800;">Advanced Encryption Standard</h3>
                                    <p style="margin-top: 0;">Adopted by NIST in 2001, the Rijndael cipher (AES) is the definitive global standard for symmetric key encryption. It relies on a Substitution-Permutation Network rather than a Feistel network.</p>
                                    <p>With key sizes up to 256 bits, there are more possible keys than atoms in the universe. It is considered impenetrable by classical brute force.</p>
                                </div>
                                <div id="hist-vigenere" class="history-block" style="display:none;">
                                    <h3 style="color: #fff; margin: 0 0 10px 0; font-size: 18px; font-weight: 800;">Le Chiffre Indéchiffrable</h3>
                                    <p style="margin-top: 0;">Described in 1553, the Vigenère cipher uses interwoven Caesar shifts determined by a keyword. For 300 years, it was considered entirely unbreakable.</p>
                                    <p>It was ultimately defeated in 1863 by Friedrich Kasiski, who realized that repeated patterns in the ciphertext could deduce the keyword length, reducing the cipher to multiple simple Caesar shifts.</p>
                                </div>
                                <div id="hist-quantum" class="history-block" style="display:none;">
                                    <h3 style="color: #fff; margin: 0 0 10px 0; font-size: 18px; font-weight: 800;">BB84 Quantum Cryptography</h3>
                                    <p style="margin-top: 0;">Developed in 1984, BB84 escapes mathematical vulnerability by relying on physics. Data is transmitted via polarized photons.</p>
                                    <p>According to the Heisenberg Uncertainty Principle, measuring a quantum state alters it. If a hacker intercepts the photons, their state collapses, generating an uncorrectable error rate that immediately alerts the authorized parties to the breach.</p>
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
                const hillMatrixContainer = document.getElementById('hill-matrix-container');
                const textKeyControls = document.getElementById('text-key-controls');
                const textKeyInput = document.getElementById('text-key-input');
                
                let selectedMessageId = null;
                let activeMessageIdForEmoji = null;
                let activePayloadForTools = ""; 
                let activeOriginalMsg = "";
                let activeCipherKey = null;
                let activeCipherType = null;

                // --- MATH UTILITIES FOR N-BY-N HILL ---
                function mod26(n) { return ((n % 26) + 26) % 26; }
                
                function getMatrixDet(m) {
                    if (m.length === 1) return m[0][0];
                    if (m.length === 2) return m[0][0] * m[1][1] - m[0][1] * m[1][0];
                    let det = 0;
                    for (let c = 0; c < m.length; c++) {
                        let sub = m.slice(1).map(r => r.filter((_, j) => j !== c));
                        det += (c % 2 === 1 ? -1 : 1) * m[0][c] * getMatrixDet(sub);
                    }
                    return det;
                }

                function getMatrixCofactor(m, r, c) {
                    let sub = m.filter((_, i) => i !== r).map(row => row.filter((_, j) => j !== c));
                    return ((r + c) % 2 === 1 ? -1 : 1) * getMatrixDet(sub);
                }

                function getMatrixAdjugate(m) {
                    let adj = Array(m.length).fill(0).map(() => Array(m.length).fill(0));
                    for (let i = 0; i < m.length; i++) {
                        for (let j = 0; j < m.length; j++) {
                            // Transpose during cofactor assignment
                            adj[j][i] = getMatrixCofactor(m, i, j); 
                        }
                    }
                    return adj;
                }

                // ─── HILL GRID PICKER ────────────────────────────────────────
                let currentHillSize = 2;
                (function initGridPicker() {
                    const picker = document.getElementById('hill-grid-picker');
                    const label  = document.getElementById('hill-size-label');
                    let isDragging = false;
                    let hoverSize  = 2;
                    function setHighlight(sz, committed) {
                        [...picker.children].forEach(el => {
                            const lit = parseInt(el.dataset.r) <= sz && parseInt(el.dataset.c) <= sz;
                            el.style.background   = lit ? (committed ? 'rgba(59,130,246,0.5)' : 'rgba(59,130,246,0.3)') : 'rgba(255,255,255,0.04)';
                            el.style.borderColor  = lit ? 'var(--accent-blue)' : 'rgba(255,255,255,0.15)';
                            el.style.boxShadow    = lit && committed ? 'inset 0 0 4px rgba(59,130,246,0.5)' : 'none';
                        });
                        label.textContent = sz + ' × ' + sz;
                    }
                    for (let r = 1; r <= 4; r++) {
                        for (let c = 1; c <= 4; c++) {
                            const cell = document.createElement('div');
                            cell.className = 'grid-picker-cell';
                            cell.dataset.r = r; cell.dataset.c = c;
                            cell.addEventListener('mouseenter', () => {
                                hoverSize = Math.max(r, c);
                                if (hoverSize < 2) hoverSize = 2; // Min size 2
                                setHighlight(hoverSize, false);
                            });
                            cell.addEventListener('mousedown', e => { e.preventDefault(); isDragging = true; });
                            cell.addEventListener('mouseup', () => {
                                if (!isDragging) return;
                                isDragging = false;
                                currentHillSize = hoverSize;
                                renderHillMatrix(currentHillSize);
                                setHighlight(currentHillSize, true);
                            });
                            picker.appendChild(cell);
                        }
                    }
                    picker.addEventListener('mouseleave', () => { isDragging = false; setHighlight(currentHillSize, true); });
                    setHighlight(2, true);
                })();

                function renderHillMatrix(size) {
                    hillMatrixContainer.style.gridTemplateColumns = `repeat(${size}, 1fr)`;
                    hillMatrixContainer.innerHTML = '';
                    const defaultVals = [3, 3, 2, 5];
                    let count = 0;
                    for (let i = 0; i < size; i++) {
                        for (let j = 0; j < size; j++) {
                            const inp = document.createElement('input');
                            inp.type = 'number';
                            inp.className = 'chat-input hill-cell';
                            inp.value = (size === 2) ? (defaultVals[count] ?? 0) : (i === j ? 1 : 0);
                            hillMatrixContainer.appendChild(inp);
                            count++;
                        }
                    }
                }
                renderHillMatrix(2);

                // ─── EMOJI PICKER ────────────────────────────────────────────
                const pickerContainer = document.createElement('div');
                pickerContainer.className = 'emoji-picker-container';
                const emojiPicker = document.createElement('emoji-picker');
                pickerContainer.appendChild(emojiPicker);
                document.body.appendChild(pickerContainer);
                customElements.whenDefined('emoji-picker').then(() => {
                    const check = setInterval(() => {
                        if (!emojiPicker.shadowRoot) return;
                        clearInterval(check);
                        const style = document.createElement('style');
                        style.textContent = `:host{--background:var(--bg-dark);--border-color:rgba(255,255,255,0.1);--input-border-color:rgba(255,255,255,0.2);--input-font-color:#fff;--indicator-color:#3b82f6;--button-hover-background:rgba(59,130,246,0.15);--search-background:rgba(0,0,0,0.3);--category-font-color:#94a3b8;}.nav{display:none!important;}.preview{display:none!important;}input.search{border-radius:6px!important;}`;
                        emojiPicker.shadowRoot.appendChild(style);
                    }, 50);
                });
                emojiPicker.addEventListener('emoji-click', event => {
                    if (activeMessageIdForEmoji) {
                        socket.emit('react_message', { room, id: activeMessageIdForEmoji, emoji: event.detail.unicode });
                        pickerContainer.style.display = 'none';
                    }
                });
                document.addEventListener('click', event => {
                    if (!pickerContainer.contains(event.target) && !event.target.closest('.btn-emoji'))
                        pickerContainer.style.display = 'none';
                });

                // ─── SOCKET & CHAT ───────────────────────────────────────────
                socket.emit('join', {room});
                
                function appendMessageToDOM(data) {
                    const row = document.createElement('div');
                    row.className = 'message-row';
                    if (data.id) row.id = 'msg-row-' + data.id;
                    const wrap = document.createElement('div');
                    wrap.className = 'msg-content-wrapper ' + (data.type || 'msg-user');
                    if (data.id) wrap.id = 'msg-content-' + data.id;
                    const textArea = document.createElement('div');
                    textArea.className = 'msg-text-area';
                    if (data.type === 'msg-system') {
                        textArea.textContent = data.msg;
                        wrap.appendChild(textArea);
                    } else {
                        textArea.innerHTML = `<span style="color:var(--accent-blue);font-weight:800;letter-spacing:1px;font-size:12px;text-transform:uppercase;">${data.username}</span><br><span style="font-size:15px; margin-top:4px; display:inline-block;">${data.msg}</span>`;
                        wrap.onclick = () => selectMessage(data.id, data.username, data.msg, data.original_msg, data.cipher || 'none', data.key || 0);
                        const actionContainer = document.createElement('div');
                        actionContainer.className = 'msg-actions';
                        const emojiBtn = document.createElement('button');
                        emojiBtn.className = 'action-btn btn-emoji';
                        emojiBtn.innerHTML = `<svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none"><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg>`;
                        emojiBtn.onclick = (e) => {
                            e.stopPropagation();
                            activeMessageIdForEmoji = data.id;
                            const rect = emojiBtn.getBoundingClientRect();
                            pickerContainer.style.display = 'block';
                            pickerContainer.style.top  = (rect.bottom + window.scrollY + 5) + 'px';
                            pickerContainer.style.left = (rect.left  + window.scrollX - 250) + 'px';
                        };
                        actionContainer.appendChild(emojiBtn);
                        if (data.username === myUsername) {
                            const delBtn = document.createElement('button');
                            delBtn.className = 'action-btn btn-trash';
                            delBtn.innerHTML = `<svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>`;
                            delBtn.onclick = (e) => { e.stopPropagation(); socket.emit('delete_message', { room, id: data.id }); };
                            actionContainer.appendChild(delBtn);
                        }
                        wrap.appendChild(textArea);
                        wrap.appendChild(actionContainer);
                    }
                    row.appendChild(wrap);
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
                            badge.onclick = () => socket.emit('react_message', { room, id: msgId, emoji });
                            row.appendChild(badge);
                        }
                    }
                }

                socket.on('chat_history', messages => messages.forEach(msg => appendMessageToDOM(msg)));
                socket.on('message', data => appendMessageToDOM(data));
                socket.on('reactions_updated', data => renderReactions(data.id, data.reactions));
                socket.on('message_deleted', data => {
                    const el = document.getElementById('msg-row-' + data.id);
                    if (el) el.remove();
                    if (selectedMessageId === data.id) clearSelection();
                });

                function sendMessage() {
                    if (!input.value.trim()) return;
                    let encVal = 0;
                    if (selection_box.value === 'caesar') {
                        encVal = parseInt(caesarSlider.value) || 0;
                    } else if (selection_box.value === 'hill') {
                        const cells = document.querySelectorAll('.hill-cell');
                        let matrix = [], row = [], ci = 0;
                        cells.forEach(c => {
                            row.push(parseInt(c.value) || 0);
                            if (row.length === currentHillSize) { matrix.push(row); row = []; }
                        });
                        encVal = matrix;
                    } else if (['aes', 'vigenere', 'quantum'].includes(selection_box.value)) {
                        encVal = textKeyInput.value;
                    }
                    socket.send({ msg: input.value, room, encryption: selection_box.value, 'encryption-value': encVal });
                    input.value = '';
                }
                input.addEventListener('keypress', e => { if (e.key === 'Enter') sendMessage(); });

                // ─── TABS & SIDEBAR TOOLS ────────────────────────────────────
                function switchTab(tabId, event) {
                    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                    if (event) event.target.classList.add('active');
                    else {
                        // Handle auto-switching logic to pick correct button visually
                        document.querySelectorAll('.tab-btn').forEach(b => {
                            if (b.innerText.toLowerCase().includes(tabId)) b.classList.add('active');
                        });
                    }
                    document.querySelectorAll('.tab-content').forEach(p => p.classList.remove('active'));
                    document.getElementById('tab-' + tabId).classList.add('active');
                }
                function switchTool(btn, paneId) {
                    document.querySelectorAll('.side-btn').forEach(b => {
                        b.classList.remove('active');
                        b.style.display = 'block'; // Ensure visibility when switching normally
                    });
                    btn.classList.add('active');
                    document.querySelectorAll('.tool-pane').forEach(p => p.classList.remove('active'));
                    document.getElementById(paneId).classList.add('active');
                }

                // Helper to format tables for Solution breakdown
                function generateStepsTable(plain, cipher, cipherType, key) {
                    let html = `<table class="solution-table"><tr><th>PLAINTEXT</th><th>OPERATION</th><th>CIPHERTEXT</th></tr>`;
                    let pClean = plain.replace(/[^a-zA-Z]/g, '').toUpperCase();
                    let cClean = cipher.replace(/[^a-zA-Z]/g, '').toUpperCase();
                    
                    if(cipherType === 'caesar') {
                        const s = parseInt(key) || 0;
                        for(let i=0; i<Math.min(pClean.length, 5); i++) {
                            html += `<tr><td>${pClean[i]} <span style="color:var(--text-muted);font-size:10px;">(${pClean[i].charCodeAt(0)-65})</span></td>
                                     <td style="color:var(--accent-green);">+ ${s}</td>
                                     <td class="highlight-cell">${cClean[i]} <span style="color:var(--text-muted);font-size:10px;">(${cClean[i].charCodeAt(0)-65})</span></td></tr>`;
                        }
                    } else if (cipherType === 'vigenere') {
                        const kStr = String(key).toUpperCase();
                        for(let i=0; i<Math.min(pClean.length, 5); i++) {
                            const kChar = kStr[i % kStr.length];
                            const s = kChar.charCodeAt(0) - 65;
                            html += `<tr><td>${pClean[i]}</td>
                                     <td style="color:var(--accent-green);">+ ${kChar} <span style="font-size:10px;">(Shift ${s})</span></td>
                                     <td class="highlight-cell">${cClean[i]}</td></tr>`;
                        }
                    } else if (cipherType === 'hill') {
                        // Show first block matrix multiplication
                        const n = key.length;
                        html += `<tr><td colspan="3" style="text-align:center; color:var(--text-muted);">Matrix Multiplication (Block Size ${n})</td></tr>`;
                        html += `<tr><td>[ ${pClean.substring(0, n).split('').join(', ')} ]</td>
                                 <td style="color:var(--accent-green);">× Key Matrix</td>
                                 <td class="highlight-cell">[ ${cClean.substring(0, n).split('').join(', ')} ]</td></tr>`;
                    }
                    if(pClean.length > 5) html += `<tr><td colspan="3" style="text-align:center; color:var(--text-muted);">... (Continued) ...</td></tr>`;
                    html += `</table>`;
                    return html;
                }

                // ─── MESSAGE SELECTION ───────────────────────────────────────
                function selectMessage(id, username, msgText, originalMsg, cipherType, cipherKey) {
                    if (selectedMessageId) {
                        const prev = document.getElementById('msg-content-' + selectedMessageId);
                        if (prev) prev.classList.remove('selected');
                    }
                    selectedMessageId = id;
                    document.getElementById('msg-content-' + id)?.classList.add('selected');
                    activePayloadForTools = msgText;
                    activeOriginalMsg = originalMsg || msgText;
                    activeCipherKey   = cipherKey;
                    activeCipherType  = cipherType;
                    
                    document.getElementById('selection-placeholder').style.display = 'none';
                    document.getElementById('selection-details').style.display = 'flex';
                    document.getElementById('sel-payload').textContent = msgText;
                    
                    // Reset UI State
                    ['tool-container-none','tool-container-active','sol-none','sol-dynamic','hist-none'].forEach(el => document.getElementById(el).style.display = 'none');
                    document.querySelectorAll('.history-block').forEach(el => el.style.display = 'none');
                    
                    document.querySelectorAll('.side-btn').forEach(btn => btn.style.display = 'none'); // Hide all tool buttons initially

                    // Reset Solvers
                    document.getElementById('btn-matrix-start').style.display = 'block'; document.getElementById('hill-solver-area').innerHTML = '';
                    document.getElementById('btn-vig-start').style.display = 'block'; document.getElementById('vig-solver-area').innerHTML = '';
                    document.getElementById('btn-aes-start').style.display = 'block'; document.getElementById('aes-solver-area').innerHTML = '';
                    document.getElementById('btn-quantum-start').style.display = 'block'; document.getElementById('quantum-solver-area').innerHTML = '';

                    if (cipherType !== 'system' && cipherType !== 'none') {
                        document.getElementById('tool-container-active').style.display = 'block';
                        document.getElementById('sol-dynamic').style.display = 'block';
                        document.getElementById('dyn-plain-2').textContent = activeOriginalMsg;
                        
                        document.getElementById('dyn-enc-steps').innerHTML = generateStepsTable(activeOriginalMsg, msgText, cipherType, cipherKey);

                        if (cipherType === 'caesar') {
                            document.getElementById('hist-caesar').style.display = 'block';
                            document.getElementById('btn-t-shift').style.display = 'block';
                            switchTool(document.getElementById('btn-t-shift'), 'tool-shift');
                            document.getElementById('dyn-tool').innerHTML = `<strong>Linear Shift Analysis:</strong> Force the reverse shift iteratively until semantic text appears.`;
                        } else if (cipherType === 'hill') {
                            document.getElementById('hist-hill').style.display = 'block';
                            document.getElementById('btn-t-matrix').style.display = 'block';
                            switchTool(document.getElementById('btn-t-matrix'), 'tool-matrix');
                            document.getElementById('dyn-tool').innerHTML = `<strong>Matrix Factorization:</strong> Compute determinant, find modular inverse, and multiply by adjugate matrix to recover key.`;
                        } else if (cipherType === 'aes') {
                            document.getElementById('hist-aes').style.display = 'block';
                            document.getElementById('btn-t-aes').style.display = 'block';
                            switchTool(document.getElementById('btn-t-aes'), 'tool-aes');
                            document.getElementById('dyn-enc-steps').innerHTML = `<div style="padding:10px; color:var(--text-muted); text-align:center; font-family:var(--font-mono);">[128-bit blocks processed via Rijndael key schedules]</div>`;
                            document.getElementById('dyn-tool').innerHTML = `<strong>None:</strong> Mathematically secure against classical attacks. Open visualizer to observe diffusion.`;
                        } else if (cipherType === 'vigenere') {
                            document.getElementById('hist-vigenere').style.display = 'block';
                            document.getElementById('btn-t-kasiski').style.display = 'block';
                            switchTool(document.getElementById('btn-t-kasiski'), 'tool-kasiski');
                            document.getElementById('dyn-tool').innerHTML = `<strong>Kasiski Examination:</strong> Exploit repeated sequences to find key length, then execute column-based frequency analysis.`;
                        } else if (cipherType === 'quantum') {
                            document.getElementById('hist-quantum').style.display = 'block';
                            document.getElementById('btn-t-quantum').style.display = 'block';
                            switchTool(document.getElementById('btn-t-quantum'), 'tool-quantum');
                            document.getElementById('dyn-enc-steps').innerHTML = `<div style="padding:10px; color:var(--text-muted); text-align:center; font-family:var(--font-mono);">[Photon stream transmitted over Quantum Channel]</div>`;
                            document.getElementById('dyn-tool').innerHTML = `<strong>Eavesdropping (Eve):</strong> Try to measure photon polarity without collapsing the quantum wave function.`;
                        }
                        
                        // Run Caesar analyzer
                        document.getElementById('analyzer-slider').value = 1; document.getElementById('analyzer-display').textContent = 1;
                        document.getElementById('shift-submit-display').textContent = 1; document.getElementById('caesar-submit-feedback').innerHTML = '';
                        runCaesarAnalyzer(1);
                    } else {
                        document.getElementById('tool-container-none').style.display = 'block';
                        document.getElementById('sol-none').style.display = 'block';
                        document.getElementById('hist-none').style.display = 'block';
                    }
                    // Auto-switch to decryption tab on click
                    switchTab('decryption');
                }

                function clearSelection() {
                    selectedMessageId = null;
                    document.getElementById('selection-placeholder').style.display = 'block';
                    document.getElementById('selection-details').style.display = 'none';
                }

                // ════════════════════════════════════════════════════════════
                // TOOL 1 — LINEAR SHIFT ANALYSIS (Caesar)
                // ════════════════════════════════════════════════════════════
                function performCaesarShift(text, amount) {
                    return text.split('').map(char => {
                        const code = char.charCodeAt(0);
                        if (code >= 65 && code <= 90) return String.fromCharCode(((code - 65 - amount + 260) % 26) + 65);
                        if (code >= 97 && code <= 122) return String.fromCharCode(((code - 97 - amount + 260) % 26) + 97);
                        return char;
                    }).join('');
                }
                function runCaesarAnalyzer(shift) {
                    if (!activePayloadForTools) return;
                    document.getElementById('analyzer-output').textContent = performCaesarShift(activePayloadForTools, shift);
                }
                const analyzerSlider = document.getElementById('analyzer-slider');
                analyzerSlider.addEventListener('input', function() {
                    document.getElementById('analyzer-display').textContent = this.value;
                    document.getElementById('shift-submit-display').textContent = this.value;
                    runCaesarAnalyzer(parseInt(this.value));
                });
                function submitCaesarAnswer() {
                    const currentShift = parseInt(analyzerSlider.value);
                    const fb = document.getElementById('caesar-submit-feedback');
                    if (activeCipherType !== 'caesar') return;
                    const correct = parseInt(activeCipherKey);
                    if (currentShift === correct) {
                        fb.innerHTML = `<span class="feedback-ok">✓ SUCCESS! Key recovered.</span>`;
                    } else {
                        fb.innerHTML = `<span class="feedback-err">✗ Output is garbled. Keep searching.</span>`;
                    }
                }

                // ════════════════════════════════════════════════════════════
                // TOOL 2 — MATRIX FACTORIZATION (Hill N-by-N)
                // ════════════════════════════════════════════════════════════
                let hillState = {};
                
                function initHillSolver() {
                    const area = document.getElementById('hill-solver-area');
                    const startBtn = document.getElementById('btn-matrix-start');
                    if (activeCipherType !== 'hill' || !Array.isArray(activeCipherKey)) return;
                    
                    const m = activeCipherKey;
                    const size = m.length;
                    
                    hillState = { matrix: m, size: size };
                    startBtn.style.display = 'none';

                    if (size === 2) {
                        // Interactive step-by-step for 2x2
                        hillState.a = m[0][0]; hillState.b = m[0][1];
                        hillState.c = m[1][0]; hillState.d = m[1][1];
                        renderHillStep1_2x2();
                    } else {
                        // Automated visual breakdown for NxN (Math is too heavy for hand calculation)
                        renderHillNxNBreakdown();
                    }
                }

                // --- 2x2 Interactive Flow ---
                function renderHillStep1_2x2() {
                    const {a, b, c, d} = hillState;
                    document.getElementById('hill-solver-area').innerHTML = `
                        <div class="step-box">
                            <div class="step-title">Step 1 — Determinant (mod 26)</div>
                            <div class="matrix-display">[ ${a},  ${b} ]<br>[ ${c},  ${d} ]</div>
                            <div style="color:var(--text-muted); margin: 10px 0 6px;">Formula: <span style="font-family:var(--font-mono); color:#fff;">(a×d − b×c) mod 26</span></div>
                            <div class="step-input-row">
                                <input id="hill-inp-1" type="number" class="step-input" min="0" max="25" placeholder="0-25">
                                <button class="check-btn" onclick="checkHillStep1_2x2()">Check →</button>
                            </div>
                            <div id="hill-fb-1"></div>
                        </div>`;
                }
                function checkHillStep1_2x2() {
                    const {a, b, c, d} = hillState;
                    const correct = mod26((a * d) - (b * c));
                    const user = parseInt(document.getElementById('hill-inp-1').value);
                    const fb = document.getElementById('hill-fb-1');
                    if (user === correct) {
                        hillState.det = correct;
                        fb.innerHTML = `<div class="feedback-ok">✓ Correct! det = ${correct}.</div>`;
                        setTimeout(renderHillStep2_2x2, 600);
                    } else {
                        fb.innerHTML = `<div class="feedback-err">✗ Incorrect calculation.</div>`;
                    }
                }
                function renderHillStep2_2x2() {
                    const {det} = hillState;
                    document.getElementById('hill-solver-area').innerHTML += `
                        <div class="step-box">
                            <div class="step-title">Step 2 — Modular Inverse</div>
                            <div style="color:var(--text-muted); margin-bottom:8px;">Find X where <span style="font-family:var(--font-mono); color:#fff;">(${det} × X) mod 26 = 1</span></div>
                            <div class="step-input-row">
                                <input id="hill-inp-2" type="number" class="step-input" min="1" max="25" placeholder="X">
                                <button class="check-btn" onclick="checkHillStep2_2x2()">Check →</button>
                            </div>
                            <div id="hill-fb-2"></div>
                        </div>`;
                }
                function checkHillStep2_2x2() {
                    let correctInv = -1;
                    for (let i = 1; i < 26; i++) if ((hillState.det * i) % 26 === 1) { correctInv = i; break; }
                    if (correctInv === -1) {
                        document.getElementById('hill-fb-2').innerHTML = `<div class="feedback-err">CRITICAL ERROR: Matrix is non-invertible.</div>`;
                        return;
                    }
                    const user = parseInt(document.getElementById('hill-inp-2').value);
                    if (user === correctInv) {
                        hillState.detInv = correctInv;
                        document.getElementById('hill-fb-2').innerHTML = `<div class="feedback-ok">✓ D−1 = ${correctInv}.</div>`;
                        setTimeout(renderHillStep3_2x2, 600);
                    } else {
                        document.getElementById('hill-fb-2').innerHTML = `<div class="feedback-err">✗ That value does not equal 1 mod 26.</div>`;
                    }
                }
                function renderHillStep3_2x2() {
                    const {a, b, c, d, detInv} = hillState;
                    const invA = mod26(d * detInv), invB = mod26(-b * detInv);
                    const invC = mod26(-c * detInv), invD = mod26(a * detInv);
                    document.getElementById('hill-solver-area').innerHTML += `
                        <div class="step-box" style="border-color:var(--accent-green); background:rgba(16,185,129,0.05);">
                            <div class="step-title" style="color:var(--accent-green);">Step 3 — Decryption Matrix Recovered</div>
                            <div class="matrix-display" style="color:var(--accent-purple);">K−1 = [ ${invA}, ${invB} ]<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[ ${invC}, ${invD} ]</div>
                            
                            <hr style="border-color: rgba(16, 185, 129, 0.2); margin: 15px 0;">
                            
                            <div class="step-title" style="color:var(--accent-green);">Step 4 — Matrix Multiplication</div>
                            <div style="color:var(--text-muted); margin-bottom:8px; font-size: 13px;">To decrypt, split the ciphertext into blocks of 2 letters. Convert letters to numbers (A=0, B=1...). Multiply each block vector by <strong>K⁻¹</strong>, take modulo 26, and convert back to letters.</div>
                            <div class="matrix-display" style="font-size:12px; color:var(--text-muted); background: rgba(0,0,0,0.2);">
                                [P₁, P₂] = [C₁, C₂] × K⁻¹ (mod 26)
                            </div>
                            <div style="margin-top:15px; color:#fff; font-size:16px;"><strong>Final Decrypted Message:</strong> "${activeOriginalMsg}"</div>
                        </div>`;
                    document.getElementById('btn-matrix-start').style.display = 'block';
                    document.getElementById('btn-matrix-start').innerText = 'RESET';
                }

                // --- NxN Automated Flow ---
                function renderHillNxNBreakdown() {
                    const m = hillState.matrix;
                    const det = mod26(getMatrixDet(m));
                    let detInv = -1;
                    for (let i = 1; i < 26; i++) if ((det * i) % 26 === 1) { detInv = i; break; }
                    
                    let breakdownHTML = `<div class="step-box"><div class="step-title">Automated Matrix Factorization (${hillState.size}x${hillState.size})</div>`;
                    
                    if (detInv === -1) {
                        breakdownHTML += `<div style="color:var(--danger)">Matrix Determinant is ${det}, which shares a factor with 26. Invertible matrix cannot be formed. Data corrupted.</div></div>`;
                    } else {
                        const adj = getMatrixAdjugate(m);
                        const invM = adj.map(row => row.map(val => mod26(val * detInv)));
                        
                        function printMat(mat) {
                            return mat.map(row => "[ " + row.map(v => v.toString().padStart(2, ' ')).join(', ') + " ]").join('<br>');
                        }

                        breakdownHTML += `
                            <div style="color:var(--text-muted); font-size: 13px; margin-bottom: 15px;">Due to the complexity of calculating cofactors for ${hillState.size}x${hillState.size} matrices, the system has automated the linear algebra.</div>
                            
                            <div style="margin-bottom: 10px; font-weight: bold; color: var(--accent-blue);">1. Determinant (mod 26) = ${det}</div>
                            <div style="margin-bottom: 10px; font-weight: bold; color: var(--accent-blue);">2. Modular Inverse (D⁻¹) = ${detInv}</div>
                            
                            <div style="margin-bottom: 5px; font-weight: bold; color: var(--accent-purple);">3. Adjugate Matrix:</div>
                            <div class="matrix-display" style="font-size:12px;">${printMat(adj.map(row => row.map(mod26)))}</div>
                            
                            <div style="margin-bottom: 5px; font-weight: bold; color: var(--accent-green);">4. Final Decryption Key Matrix (K⁻¹):</div>
                            <div class="matrix-display" style="font-size:14px; color:var(--accent-green);">${printMat(invM)}</div>
                            
                            <div style="margin-top:15px; color:#fff; font-size:16px;">Decrypted: "${activeOriginalMsg}"</div>
                        </div>`;
                    }
                    document.getElementById('hill-solver-area').innerHTML = breakdownHTML;
                    document.getElementById('btn-matrix-start').style.display = 'block';
                    document.getElementById('btn-matrix-start').innerText = 'RECALCULATE';
                }

                // ════════════════════════════════════════════════════════════
                // TOOL 3 — STATISTICAL KEYWORD ATTACK (Vigenère)
                // ════════════════════════════════════════════════════════════
                // (Using existing logic, just cleaning up UI transitions)
                let vigState = {};
                function findRepeatedTrigrams(text) {
                    const pos = {};
                    for (let i = 0; i <= text.length - 3; i++) {
                        const t = text.substr(i, 3);
                        if (!pos[t]) pos[t] = [];
                        pos[t].push(i);
                    }
                    return Object.entries(pos).filter(([,p]) => p.length > 1).slice(0, 5);
                }
                function initVigenereSolver() {
                    const area = document.getElementById('vig-solver-area');
                    if (activeCipherType !== 'vigenere') return;
                    vigState = { key: String(activeCipherKey).toUpperCase(), keyLen: String(activeCipherKey).length, ct: activePayloadForTools.toUpperCase().replace(/[^A-Z]/g, '') };
                    document.getElementById('btn-vig-start').style.display = 'none';
                    renderVigStep1();
                }
                function renderVigStep1() {
                    const {ct, keyLen} = vigState;
                    const repeated = findRepeatedTrigrams(ct);
                    let html = `<div class="step-box"><div class="step-title">Step 1 — Kasiski Gap Analysis</div>`;
                    if(repeated.length === 0) {
                        html += `<div style="color:var(--text-muted);">Ciphertext too short to find repeated trigrams. Bypassing Kasiski examination.<br><br><b>Estimated Key Length:</b> ${keyLen}</div>`;
                        html += `<button class="check-btn" onclick="renderVigStep3()" style="margin-top:15px;">PROCEED TO FREQUENCY ANALYSIS</button>`;
                    } else {
                        const firstTri = repeated[0];
                        const gap = firstTri[1][1] - firstTri[1][0];
                        vigState.expectedGap = gap;
                        html += `<div style="color:var(--text-muted); margin-bottom:10px;">The sequence <b>"${firstTri[0]}"</b> repeats at pos ${firstTri[1][0]} and ${firstTri[1][1]}. What is the distance gap?</div>
                                 <div class="step-input-row">
                                    <input id="vig-inp-1" type="number" class="step-input" placeholder="Gap">
                                    <button class="check-btn" onclick="checkVigStep1()">Check</button>
                                 </div><div id="vig-fb-1"></div>`;
                    }
                    document.getElementById('vig-solver-area').innerHTML = html + "</div>";
                }
                function checkVigStep1() {
                    if (parseInt(document.getElementById('vig-inp-1').value) === vigState.expectedGap) {
                        document.getElementById('vig-fb-1').innerHTML = `<div class="feedback-ok">✓ Correct. The keyword length must be a factor of ${vigState.expectedGap}. Moving to analysis...</div>`;
                        setTimeout(renderVigStep3, 1000);
                    } else {
                        document.getElementById('vig-fb-1').innerHTML = `<div class="feedback-err">✗ Incorrect subtraction.</div>`;
                    }
                }
                function renderVigStep3() {
                    document.getElementById('vig-solver-area').innerHTML = `
                        <div class="step-box">
                            <div class="step-title">Step 2 — Column Frequency</div>
                            <div style="color:var(--text-muted); margin-bottom:12px;">The cipher is split into ${vigState.keyLen} columns. We run basic frequency analysis on each to guess the shift.</div>
                            <div style="color:var(--accent-purple); font-family:var(--font-mono); margin-bottom: 15px;">[Automated Frequency Analysis Running...]</div>
                            <div style="color:var(--text-muted); margin-bottom:10px;">Enter deduced ${vigState.keyLen}-letter keyword:</div>
                            <input id="vig-final-key" type="text" class="chat-input" style="text-transform:uppercase; font-family:var(--font-mono); letter-spacing:3px; text-align:center;">
                            <button class="check-btn" style="margin-top:10px; width:100%;" onclick="checkVigStep3()">DECRYPT</button>
                            <div id="vig-fb-3"></div>
                        </div>`;
                }
                function checkVigStep3() {
                    const guess = document.getElementById('vig-final-key').value.toUpperCase();
                    if(guess === vigState.key) {
                        document.getElementById('vig-fb-3').innerHTML = `<div class="feedback-ok" style="margin-top:15px; font-size:15px;">✓ Decrypted: "${activeOriginalMsg}"</div>`;
                        document.getElementById('btn-vig-start').style.display = 'block'; document.getElementById('btn-vig-start').innerText = 'RESET';
                    } else {
                        document.getElementById('vig-fb-3').innerHTML = `<div class="feedback-err">✗ Incorrect Keyword.</div>`;
                    }
                }

                // ════════════════════════════════════════════════════════════
                // TOOL 4 — AES VISUALIZER
                // ════════════════════════════════════════════════════════════
                function initAesSolver() {
                    const area = document.getElementById('aes-solver-area');
                    document.getElementById('btn-aes-start').style.display = 'none';
                    
                    let html = `
                    <div class="step-box" id="aes-anim-box">
                        <div class="step-title">AES Round Transformation</div>
                        <div style="display:grid; grid-template-columns:1fr 1fr; gap:20px; align-items:center;">
                            <div id="aes-matrix" style="display:grid; grid-template-columns:repeat(4, 1fr); gap:4px; font-family:var(--font-mono); font-size:12px; color:#fff; text-align:center;">
                                ${Array(16).fill(0).map(()=>`<div style="background:rgba(255,255,255,0.1); padding:8px; border-radius:4px;">A4</div>`).join('')}
                            </div>
                            <div id="aes-steps-list" style="color:var(--text-muted); font-size:13px; line-height:2.2;">
                                <div id="aes-s1">1. SubBytes()</div>
                                <div id="aes-s2">2. ShiftRows()</div>
                                <div id="aes-s3">3. MixColumns()</div>
                                <div id="aes-s4">4. AddRoundKey()</div>
                            </div>
                        </div>
                    </div>`;
                    area.innerHTML = html;

                    // Simple mock animation sequence
                    setTimeout(() => { document.getElementById('aes-s1').style.color = "var(--accent-blue)"; document.getElementById('aes-matrix').innerHTML = Array(16).fill(0).map(()=>`<div style="background:rgba(59,130,246,0.3); padding:8px; border-radius:4px;">B7</div>`).join(''); }, 1000);
                    setTimeout(() => { document.getElementById('aes-s1').style.color = "var(--text-muted)"; document.getElementById('aes-s2').style.color = "var(--accent-purple)"; }, 2000);
                    setTimeout(() => { document.getElementById('aes-s2').style.color = "var(--text-muted)"; document.getElementById('aes-s3').style.color = "var(--accent-green)"; document.getElementById('aes-matrix').innerHTML = Array(16).fill(0).map(()=>`<div style="background:rgba(16,185,129,0.3); padding:8px; border-radius:4px;">F2</div>`).join(''); }, 3000);
                    setTimeout(() => { 
                        document.getElementById('aes-s3').style.color = "var(--text-muted)"; document.getElementById('aes-s4').style.color = "#fff"; 
                        document.getElementById('aes-anim-box').innerHTML += `<div style="margin-top:20px; color:var(--text-muted);">AES completes 10-14 of these rounds. To reverse it, you need the exact 256-bit key to generate the inverse subkeys.</div>`;
                        document.getElementById('btn-aes-start').style.display = 'block'; document.getElementById('btn-aes-start').innerText = 'REPLAY ANIMATION';
                    }, 4000);
                }

                // ════════════════════════════════════════════════════════════
                // TOOL 5 — QUANTUM BB84 INTERCEPT
                // ════════════════════════════════════════════════════════════
                function initQuantumSolver() {
                    const area = document.getElementById('quantum-solver-area');
                    document.getElementById('btn-quantum-start').style.display = 'none';
                    
                    let html = `
                    <div class="step-box">
                        <div class="step-title">Eavesdrop on Photon Stream</div>
                        <div style="color:var(--text-muted); font-size:12px; margin-bottom:15px;">Alice is sending a photon. You (Eve) must guess the correct measurement basis (+ or x) to read it without destroying the state.</div>
                        <div style="display:flex; justify-content:space-around; margin-bottom:20px;">
                            <button class="check-btn" style="width:45%; font-size:18px;" onclick="quantumGuess('+')">+</button>
                            <button class="check-btn" style="width:45%; font-size:18px;" onclick="quantumGuess('x')">x</button>
                        </div>
                        <div id="quantum-fb"></div>
                    </div>`;
                    area.innerHTML = html;
                }
                function quantumGuess(basis) {
                    const isCorrect = Math.random() > 0.5; // 50% chance Eve guesses wrong
                    const fb = document.getElementById('quantum-fb');
                    if(isCorrect) {
                        fb.innerHTML = `<div class="feedback-ok">✓ Basis matched! You intercepted 1 bit. But you need hundreds to form a key...</div>`;
                    } else {
                        fb.innerHTML = `<div class="feedback-err">✗ Basis mismatch! The photon state collapsed. Alice and Bob's error rate just spiked. You have been detected.</div>`;
                        document.getElementById('btn-quantum-start').style.display = 'block'; document.getElementById('btn-quantum-start').innerText = 'RESTART EAVESDROP';
                    }
                }

                // ─── ENCRYPTION SELECTOR CONTROLS ───────────────────────────
                selection_box.addEventListener('change', function() {
                    cipher_text.textContent = selection_box.options[selection_box.selectedIndex].text;
                    caesarControls.style.display = 'none'; hillControls.style.display = 'none'; textKeyControls.style.display = 'none';
                    if (selection_box.value === 'caesar') {
                        caesarControls.style.display = 'block';
                    } else if (selection_box.value === 'hill') {
                        hillControls.style.display = 'block';
                    } else if (['aes','vigenere','quantum'].includes(selection_box.value)) {
                        textKeyControls.style.display = 'block';
                    }
                });
                caesarSlider.addEventListener('input', function() {
                    shiftDisplay.textContent = this.value;
                    exampleShift.textContent = ['A','B','C','D','E'].map(c => {
                        let n = c.charCodeAt(0) + parseInt(this.value);
                        if (n > 90) n -= 26;
                        return String.fromCharCode(n);
                    }).join(' ');
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
            'id': str(uuid.uuid4()), 'type': 'msg-system',
            'msg': f'[SYSTEM] {username} disconnected.',
            'reactions': {}, 'cipher': 'system', 'key': 0
        }
        active_rooms[room]['messages'].append(sys_msg)
        socketio.send(sys_msg, to=room)
    return redirect(url_for('local'))

@app.route('/api/usernames')
def getUsernames():
    return jsonify(active_usernames)

# --- SOCKET EVENTS ---
@socketio.on('join')
def on_join(data):
    room = data['room']
    username = session.get('username', 'Guest')
    join_room(room)
    if room in active_rooms:
        emit('chat_history', active_rooms[room]['messages'], to=request.sid)
    sys_msg = {
        'id': str(uuid.uuid4()), 'type': 'msg-system',
        'msg': f'[SYSTEM] {username} has joined Room {room}.',
        'reactions': {}, 'cipher': 'system', 'key': 0
    }
    if room in active_rooms:
        active_rooms[room]['messages'].append(sys_msg)
    send(sys_msg, to=room)

@socketio.on('message')
def handle_message(data):
    room = data['room']
    msg  = data['msg']
    encryption_type  = data['encryption']
    encryption_value = data.get('encryption-value') 
    username = session.get('username', 'Guest')
    if encryption_type != "none":
        try:
            encrypted_bytes = encryption_manager.encrypt(encryption_type, msg.encode('utf-8'), encryption_value).decode('utf-8')
        except Exception as e:
            encrypted_bytes = f"[ENCRYPTION ERROR: {str(e)}]"
    else:
        encrypted_bytes = msg
    message_payload = {
        'id': str(uuid.uuid4()), 'username': username,
        'msg': encrypted_bytes, 'original_msg': msg,
        'type': 'msg-user', 'reactions': {},
        'cipher': encryption_type, 'key': encryption_value
    }
    if room in active_rooms:
        active_rooms[room]['messages'].append(message_payload)
    send(message_payload, to=room)

@socketio.on('react_message')
def handle_reaction(data):
    room = data['room']; msg_id = data['id']; emoji = data['emoji']
    username = session.get('username')
    if room in active_rooms:
        for m in active_rooms[room]['messages']:
            if m.get('id') == msg_id:
                if emoji not in m['reactions']: m['reactions'][emoji] = []
                if username in m['reactions'][emoji]: m['reactions'][emoji].remove(username)
                else: m['reactions'][emoji].append(username)
                emit('reactions_updated', {'id': msg_id, 'reactions': m['reactions']}, to=room)
                break

@socketio.on('delete_message')
def handle_delete(data):
    room = data['room']; message_id = data['id']
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
    threading.Timer(1.25, lambda: webbrowser.open("http://127.0.0.1:67667")).start() 
    socketio.run(app, host='0.0.0.0', port=67667, debug=True, allow_unsafe_werkzeug=True)