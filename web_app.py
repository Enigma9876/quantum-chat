from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from flask_socketio import SocketIO, join_room, leave_room, send, emit
import threading
import random
import string
import webbrowser
import uuid
from crypto import manager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'insightful_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")
encryption_manager = manager.CryptoManager()
active_rooms = {}
active_usernames = []

def generate_room_code():
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        if code not in active_rooms:
            return code

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Insightful Encryptions</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script type="module" src="https://cdn.jsdelivr.net/npm/emoji-picker-element@1/index.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;600&family=Inter:wght@300;400;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        *, *::before, *::after { box-sizing: border-box; }
        :root {
            --bg: #080d18; --bg-2: #0d1526; --bg-panel: rgba(13,21,38,0.8);
            --text: #e2e8f0; --muted: #64748b; --muted-2: #94a3b8;
            --blue: #3b82f6; --blue-light: #60a5fa;
            --green: #10b981; --green-light: #34d399;
            --purple: #8b5cf6; --purple-light: #a78bfa;
            --red: #ef4444;
            --border: rgba(255,255,255,0.08); --border-hover: rgba(255,255,255,0.18);
            --mono: 'Fira Code', monospace; --sans: 'Inter', sans-serif;
        }
        html, body { margin:0; padding:0; height:100%; background:var(--bg); color:var(--text); font-family:var(--sans); overflow:hidden; }
        ::-webkit-scrollbar { width:6px; }
        ::-webkit-scrollbar-track { background:transparent; }
        ::-webkit-scrollbar-thumb { background:rgba(255,255,255,0.12); border-radius:6px; }

        /* ═══ TOPBAR ═══ */
        .topbar { position:fixed; top:0; left:0; right:0; z-index:100; height:56px; display:flex; align-items:center; justify-content:space-between; padding:0 32px; background:rgba(8,13,24,0.9); backdrop-filter:blur(16px); border-bottom:1px solid var(--border); }
        .topbar-logo { font-size:13px; font-weight:800; letter-spacing:4px; text-transform:uppercase; background:linear-gradient(90deg,var(--blue-light),var(--purple-light)); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
        .topbar-nav { display:flex; gap:8px; }
        .topbar-link { padding:6px 14px; border-radius:6px; font-size:12px; font-weight:600; letter-spacing:0.5px; color:var(--muted-2); text-decoration:none; transition:all 0.2s; }
        .topbar-link:hover { color:#fff; background:rgba(255,255,255,0.06); }
        .topbar-link.active { color:var(--blue-light); background:rgba(59,130,246,0.1); }

        /* ═══ HOME PAGE ═══ */
        .home-page { height:100vh; display:flex; flex-direction:column; align-items:center; justify-content:center; padding-top:56px; position:relative; overflow:hidden; }
        .home-page::before { content:''; position:absolute; inset:0; background-image:linear-gradient(rgba(59,130,246,0.04) 1px,transparent 1px),linear-gradient(90deg,rgba(59,130,246,0.04) 1px,transparent 1px); background-size:48px 48px; mask-image:radial-gradient(ellipse at center,black 30%,transparent 80%); }
        .home-page::after { content:''; position:absolute; inset:0; pointer-events:none; background:radial-gradient(ellipse 60% 40% at 20% 60%,rgba(59,130,246,0.09),transparent),radial-gradient(ellipse 50% 40% at 80% 30%,rgba(139,92,246,0.09),transparent),radial-gradient(ellipse 40% 50% at 50% 100%,rgba(16,185,129,0.05),transparent); }
        .home-inner { position:relative; z-index:1; text-align:center; width:100%; max-width:960px; padding:0 24px; }
        .home-badge { display:inline-flex; align-items:center; gap:8px; padding:6px 16px; border-radius:99px; background:rgba(59,130,246,0.08); border:1px solid rgba(59,130,246,0.2); font-size:11px; font-weight:700; letter-spacing:2px; text-transform:uppercase; color:var(--blue-light); margin-bottom:28px; }
        .home-badge-dot { width:6px; height:6px; border-radius:50%; background:var(--green); box-shadow:0 0 8px var(--green); animation:pulse 2s infinite; }
        @keyframes pulse { 0%,100%{opacity:1}50%{opacity:0.4} }
        .home-title { font-size:clamp(36px,5vw,64px); font-weight:900; letter-spacing:-2px; line-height:1.05; color:#fff; margin:0 0 20px 0; }
        .home-title span { background:linear-gradient(135deg,var(--blue-light) 0%,var(--purple-light) 50%,var(--green-light) 100%); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
        .home-sub { font-size:16px; color:var(--muted-2); max-width:520px; margin:0 auto 52px; line-height:1.6; }
        .module-row { display:grid; grid-template-columns:repeat(3,1fr); gap:16px; width:100%; }
        .module-card { position:relative; text-decoration:none; background:rgba(13,21,38,0.7); border:1px solid var(--border); border-radius:16px; padding:28px 24px 24px; text-align:left; overflow:hidden; transition:all 0.3s cubic-bezier(0.4,0,0.2,1); display:flex; flex-direction:column; gap:12px; }
        .module-card::before { content:''; position:absolute; top:0; left:0; right:0; height:1px; background:linear-gradient(90deg,transparent,var(--card-accent,var(--blue)),transparent); opacity:0; transition:opacity 0.3s; }
        .module-card:hover { transform:translateY(-4px); border-color:var(--border-hover); }
        .module-card:hover::before { opacity:1; }
        .module-card:hover .card-arrow { transform:translateX(4px); opacity:1; }
        .card-icon { width:44px; height:44px; border-radius:10px; display:flex; align-items:center; justify-content:center; background:var(--card-icon-bg,rgba(59,130,246,0.1)); border:1px solid var(--card-icon-border,rgba(59,130,246,0.2)); }
        .card-label { font-size:10px; font-weight:800; letter-spacing:2px; text-transform:uppercase; color:var(--card-accent,var(--blue-light)); }
        .card-title { font-size:18px; font-weight:700; color:#fff; margin:0; letter-spacing:-0.3px; }
        .card-desc { font-size:13px; color:var(--muted-2); line-height:1.5; margin:0; flex:1; }
        .card-footer { display:flex; align-items:center; justify-content:space-between; margin-top:4px; }
        .card-arrow { color:var(--card-accent,var(--blue-light)); font-size:18px; opacity:0.4; transition:all 0.25s; }
        .card-tag { font-size:10px; font-weight:700; padding:3px 8px; border-radius:4px; background:var(--card-icon-bg); color:var(--card-accent,var(--blue-light)); letter-spacing:0.5px; text-transform:uppercase; }

        /* ═══ CONNECT PAGE ═══ */
        .connect-page { height:100vh; display:flex; padding-top:56px; }
        .connect-left { width:42%; background:var(--bg-2); border-right:1px solid var(--border); display:flex; flex-direction:column; justify-content:center; padding:60px 52px; position:relative; overflow:hidden; }
        .connect-left::before { content:''; position:absolute; bottom:-80px; left:-80px; width:320px; height:320px; border-radius:50%; background:radial-gradient(circle,rgba(16,185,129,0.08),transparent 70%); pointer-events:none; }
        .connect-left::after { content:''; position:absolute; top:-60px; right:-60px; width:240px; height:240px; border-radius:50%; background:radial-gradient(circle,rgba(59,130,246,0.07),transparent 70%); pointer-events:none; }
        .connect-brand { position:relative; z-index:1; }
        .connect-brand-logo { font-size:11px; font-weight:800; letter-spacing:3px; text-transform:uppercase; color:var(--muted); display:flex; align-items:center; gap:10px; margin-bottom:40px; }
        .connect-brand-logo::before { content:''; display:block; width:28px; height:2px; background:linear-gradient(90deg,var(--blue),var(--purple)); }
        .connect-brand-title { font-size:36px; font-weight:900; line-height:1.1; letter-spacing:-1.5px; color:#fff; margin:0 0 16px 0; }
        .connect-brand-title em { font-style:normal; background:linear-gradient(135deg,var(--green-light),var(--blue-light)); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
        .connect-brand-sub { font-size:14px; color:var(--muted-2); line-height:1.6; margin:0 0 40px 0; max-width:320px; }
        .connect-features { display:flex; flex-direction:column; gap:14px; }
        .connect-feature { display:flex; align-items:flex-start; gap:14px; }
        .connect-feature-icon { width:32px; height:32px; border-radius:8px; flex-shrink:0; display:flex; align-items:center; justify-content:center; background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.2); }
        .connect-feature-text h4 { margin:0 0 2px 0; font-size:13px; font-weight:700; color:#fff; }
        .connect-feature-text p { margin:0; font-size:12px; color:var(--muted-2); }
        .connect-right { flex:1; display:flex; align-items:center; justify-content:center; padding:60px 48px; background:var(--bg); overflow-y:auto; }
        .connect-form-wrap { width:100%; max-width:420px; }
        .connect-form-title { font-size:26px; font-weight:800; color:#fff; letter-spacing:-0.5px; margin:0 0 6px 0; }
        .connect-form-sub { font-size:13px; color:var(--muted-2); margin:0 0 36px 0; }
        .field-group { margin-bottom:24px; }
        .field-label { display:block; font-size:11px; font-weight:700; letter-spacing:1.5px; text-transform:uppercase; color:var(--muted); margin-bottom:8px; }
        .field-input { width:100%; padding:13px 16px; background:rgba(255,255,255,0.04); border:1px solid var(--border); color:#fff; font-size:15px; border-radius:10px; font-family:var(--sans); transition:all 0.2s; outline:none; }
        .field-input:focus { border-color:var(--blue); background:rgba(59,130,246,0.05); box-shadow:0 0 0 3px rgba(59,130,246,0.1); }
        .field-input::placeholder { color:var(--muted); }
        .field-input.code-input { font-family:var(--mono); font-size:22px; letter-spacing:10px; text-align:center; text-transform:uppercase; color:var(--blue-light); }
        .field-warning { font-size:12px; color:var(--red); margin-top:6px; font-weight:600; min-height:18px; display:block; }
        .btn-host-new { width:100%; padding:14px; background:linear-gradient(135deg,var(--green) 0%,#059669 100%); color:#fff; font-size:14px; font-weight:800; letter-spacing:1.5px; text-transform:uppercase; border:none; border-radius:10px; cursor:pointer; transition:all 0.25s; display:flex; align-items:center; justify-content:center; gap:10px; }
        .btn-host-new:hover { background:linear-gradient(135deg,var(--green-light),var(--green)); transform:translateY(-1px); box-shadow:0 8px 24px rgba(16,185,129,0.3); }
        .btn-host-new:disabled { opacity:0.4; cursor:not-allowed; transform:none; box-shadow:none; }
        .divider-row { display:flex; align-items:center; gap:14px; margin:24px 0; color:var(--muted); font-size:11px; font-weight:700; letter-spacing:2px; text-transform:uppercase; }
        .divider-row::before, .divider-row::after { content:''; flex:1; height:1px; background:var(--border); }
        .join-row { display:flex; gap:10px; }
        .join-row .field-input { flex:1; }
        .btn-join-new { padding:13px 24px; background:rgba(255,255,255,0.06); border:1px solid var(--border); color:var(--text); font-size:13px; font-weight:700; letter-spacing:1px; text-transform:uppercase; border-radius:10px; cursor:pointer; transition:all 0.2s; white-space:nowrap; flex-shrink:0; }
        .btn-join-new:hover { background:rgba(255,255,255,0.1); border-color:var(--border-hover); }
        .btn-join-new:disabled { opacity:0.4; cursor:not-allowed; }
        .back-link { display:block; text-align:center; margin-top:28px; font-size:12px; color:var(--muted); text-decoration:none; font-weight:600; letter-spacing:0.5px; transition:color 0.2s; }
        .back-link:hover { color:var(--blue-light); }

        /* ═══ CHAT PAGE ═══ */
        .chat-page { height:100vh; display:flex; flex-direction:column; overflow:hidden; padding-top:56px; }
        .chat-topbar-ext { display:flex; align-items:center; justify-content:space-between; padding:10px 20px; border-bottom:1px solid var(--border); background:var(--bg-2); flex-shrink:0; }
        .room-badge { display:flex; align-items:center; gap:10px; }
        .room-badge-live { display:flex; align-items:center; gap:6px; font-size:10px; font-weight:700; letter-spacing:1.5px; text-transform:uppercase; color:var(--green); }
        .room-badge-live::before { content:''; width:6px; height:6px; border-radius:50%; background:var(--green); box-shadow:0 0 6px var(--green); animation:pulse 2s infinite; }
        .room-code-display { font-family:var(--mono); font-size:22px; font-weight:600; color:var(--green-light); letter-spacing:6px; text-shadow:0 0 20px rgba(16,185,129,0.3); }
        .btn-disconnect { padding:8px 18px; background:rgba(239,68,68,0.08); border:1px solid rgba(239,68,68,0.3); color:var(--red); font-size:12px; font-weight:700; letter-spacing:1px; text-transform:uppercase; border-radius:8px; text-decoration:none; transition:all 0.2s; }
        .btn-disconnect:hover { background:rgba(239,68,68,0.15); border-color:var(--red); }
        .chat-body { flex:1; display:flex; min-height:0; overflow:hidden; }
        .chat-col { display:flex; flex-direction:column; width:38%; min-width:320px; border-right:1px solid var(--border); overflow:hidden; }
        .chat-log { flex:1; overflow-y:auto; padding:16px; display:flex; flex-direction:column; gap:8px; }
        .chat-send-row { padding:12px 14px; border-top:1px solid var(--border); display:flex; gap:8px; flex-shrink:0; background:var(--bg-2); }
        .chat-input { flex:1; padding:10px 14px; background:rgba(255,255,255,0.04); border:1px solid var(--border); color:#fff; font-size:14px; border-radius:8px; font-family:var(--sans); outline:none; transition:all 0.2s; }
        .chat-input:focus { border-color:var(--blue); background:rgba(59,130,246,0.04); }
        #encryption-selector { padding:10px 12px; background:rgba(255,255,255,0.04); border:1px solid var(--border); color:var(--text); font-size:13px; border-radius:8px; outline:none; cursor:pointer; font-family:var(--sans); transition:all 0.2s; }
        #encryption-selector:focus { border-color:var(--blue); }
        #encryption-selector option { background:#0d1526; }
        .btn-send { padding:10px 20px; background:var(--blue); color:#fff; font-size:12px; font-weight:800; letter-spacing:1px; text-transform:uppercase; border:none; border-radius:8px; cursor:pointer; transition:all 0.2s; flex-shrink:0; }
        .btn-send:hover { background:var(--blue-light); transform:translateY(-1px); }
        .enc-panel { flex:1; display:flex; flex-direction:column; overflow:hidden; background:rgba(8,13,24,0.5); }
        .enc-panel-top { flex:0 0 auto; padding:16px 20px; border-bottom:1px solid var(--border); overflow-y:auto; max-height:35%; }
        .enc-panel-bottom { flex:1; display:flex; flex-direction:column; padding:16px 20px; overflow:hidden; min-height:0; }
        .panel-hdr { font-size:10px; font-weight:800; letter-spacing:2px; text-transform:uppercase; margin-bottom:12px; }
        .message-row { display:flex; flex-direction:column; margin-bottom:2px; }
        .msg-wrap { display:flex; align-items:flex-start; justify-content:space-between; padding:10px 14px; border-radius:8px; border:1px solid transparent; background:rgba(255,255,255,0.02); transition:all 0.2s; }
        .msg-wrap:hover { background:rgba(255,255,255,0.05); }
        .msg-wrap.selected { background:rgba(59,130,246,0.1); border-color:var(--blue); }
        .msg-text { flex:1; font-size:13px; line-height:1.5; word-break:break-all; }
        .msg-user-wrap { cursor:pointer; }
        .msg-system { color:var(--purple-light); font-style:italic; font-size:12px; padding:4px 8px; }
        .msg-actions { display:flex; gap:6px; opacity:0; transition:opacity 0.2s; min-width:52px; justify-content:flex-end; }
        .msg-wrap:hover .msg-actions { opacity:1; }
        .action-btn { background:none; border:none; cursor:pointer; color:var(--muted); padding:3px; display:flex; align-items:center; transition:all 0.15s; }
        .action-btn:hover { color:#fff; transform:scale(1.15); }
        .btn-trash:hover { color:var(--red); }
        .reactions-row { display:flex; gap:5px; flex-wrap:wrap; padding-left:8px; margin-top:4px; }
        .reaction-badge { background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); border-radius:10px; padding:3px 7px; font-size:12px; cursor:pointer; color:var(--muted-2); display:flex; align-items:center; gap:4px; user-select:none; transition:all 0.15s; }
        .reaction-badge:hover { background:rgba(255,255,255,0.12); }
        .reaction-badge.active { background:rgba(59,130,246,0.18); border-color:var(--blue); color:#fff; }
        .emoji-picker-container { position:fixed; z-index:1000; display:none; box-shadow:0 15px 40px rgba(0,0,0,0.7); border-radius:12px; border:1px solid var(--border); overflow:hidden; }
        .enc-param-wrapper { display:flex; flex-direction:column; gap:10px; animation:fadeIn 0.25s; }
        .enc-label { font-size:10px; font-weight:800; letter-spacing:1.5px; text-transform:uppercase; color:var(--muted); }
        .shift-row { display:flex; align-items:center; gap:14px; }
        .shift-badge { width:50px; height:50px; border-radius:50%; flex-shrink:0; background:linear-gradient(135deg,rgba(59,130,246,0.2),rgba(139,92,246,0.2)); border:2px solid rgba(59,130,246,0.4); display:flex; align-items:center; justify-content:center; font-family:var(--mono); font-size:20px; font-weight:800; color:#fff; }
        input[type=range] { -webkit-appearance:none; width:100%; background:transparent; }
        input[type=range]::-webkit-slider-thumb { -webkit-appearance:none; width:18px; height:18px; border-radius:50%; background:var(--blue); cursor:pointer; margin-top:-7px; box-shadow:0 0 8px rgba(59,130,246,0.5); }
        input[type=range]::-webkit-slider-runnable-track { height:4px; background:linear-gradient(to right,var(--blue) var(--fp,0%),rgba(255,255,255,0.1) var(--fp,0%)); border-radius:2px; }
        input[type=range]:focus { outline:none; }
        .alpha-strip { display:flex; align-items:center; justify-content:space-between; background:rgba(0,0,0,0.3); border:1px solid var(--border); border-radius:8px; padding:8px 14px; }
        .alpha-label { font-size:9px; font-weight:800; letter-spacing:1px; text-transform:uppercase; color:var(--muted); margin-bottom:3px; }
        .alpha-letters { font-family:var(--mono); font-size:13px; letter-spacing:3px; }
        .hill-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; }
        .hill-size-pill { display:inline-flex; align-items:center; background:rgba(59,130,246,0.12); border:1px solid rgba(59,130,246,0.25); border-radius:20px; padding:3px 10px; font-family:var(--mono); font-size:12px; font-weight:800; color:var(--blue-light); }
        #hill-grid-picker { display:grid; grid-template-columns:repeat(4,14px); gap:3px; padding:5px; background:rgba(0,0,0,0.3); border-radius:6px; border:1px solid var(--border); cursor:pointer; }
        .grid-cell { width:14px; height:14px; border:1px solid rgba(255,255,255,0.12); border-radius:2px; background:rgba(255,255,255,0.03); transition:all 0.08s; cursor:pointer; }
        #hill-matrix-container { display:grid; gap:6px; background:rgba(0,0,0,0.3); padding:12px; border-radius:8px; border:1px solid var(--border); transition:border-color 0.3s,box-shadow 0.3s; }
        .hill-cell { aspect-ratio:1; width:100%; max-width:52px; text-align:center; font-family:var(--mono); font-size:16px; font-weight:bold; padding:0; border-radius:6px; background:rgba(255,255,255,0.04); border:1px solid var(--border); color:#fff; outline:none; }
        .hill-cell:focus { border-color:var(--blue); }
        .matrix-valid { display:flex; align-items:center; gap:8px; padding:7px 11px; border-radius:7px; font-size:11px; font-weight:700; border:1px solid transparent; transition:all 0.3s; min-height:32px; }
        .matrix-valid.valid { background:rgba(16,185,129,0.08); border-color:rgba(16,185,129,0.3); color:var(--green); }
        .matrix-valid.invalid { background:rgba(239,68,68,0.08); border-color:rgba(239,68,68,0.3); color:var(--red); }
        .matrix-valid.pending { background:rgba(255,255,255,0.03); border-color:var(--border); color:var(--muted); }
        .valid-dot { width:7px; height:7px; border-radius:50%; background:currentColor; flex-shrink:0; }
        .key-input-wrap { position:relative; }
        .key-icon { position:absolute; left:12px; top:50%; transform:translateY(-50%); color:var(--blue); pointer-events:none; }
        .key-inp { padding-left:40px !important; font-family:var(--mono); font-size:14px; text-transform:uppercase; letter-spacing:3px; }
        .key-meta { display:flex; justify-content:space-between; align-items:center; margin-top:6px; }
        .key-len { font-size:10px; font-weight:800; color:var(--muted); letter-spacing:1px; font-family:var(--mono); }
        .key-bars { display:flex; gap:3px; }
        .key-bar { width:12px; height:3px; border-radius:2px; background:rgba(255,255,255,0.08); transition:background 0.2s; }
        .key-bar.filled { background:var(--blue); }
        .key-bar.filled.strong { background:var(--green); }

        /* ═══ TABS ═══ */
        .tabs-wrap { display:flex; flex-direction:column; height:100%; overflow:hidden; min-height:0; }
        .tabs-nav { display:flex; border-bottom:1px solid var(--border); flex-shrink:0; margin-bottom:8px; }
        .tab-btn { flex:1; background:none; border:none; color:var(--muted-2); padding:11px 8px; cursor:pointer; font-weight:700; font-size:11px; letter-spacing:0.8px; text-transform:uppercase; border-bottom:2px solid transparent; font-family:var(--sans); transition:all 0.2s; }
        .tab-btn:hover { color:#fff; }
        .tab-btn.active { color:var(--blue-light); border-bottom-color:var(--blue); background:linear-gradient(to top,rgba(59,130,246,0.08),transparent); }
        .tab-pane { display:none; flex:1; overflow-y:auto; min-height:0; padding-bottom:20px; font-size:13px; color:var(--muted-2); line-height:1.6; }
        .tab-pane.active { display:flex; flex-direction:column; }

        /* ═══ SOLUTION / GUIDE STYLES ═══ */
        .sol-box { background:rgba(0,0,0,0.25); border:1px solid var(--border); border-radius:8px; padding:14px 18px; margin-bottom:10px; }
        .sol-title { font-size:10px; font-weight:800; letter-spacing:1.5px; text-transform:uppercase; color:var(--muted); margin-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.04); padding-bottom:7px; }
        .sol-explain { font-size:11px; color:var(--muted-2); line-height:1.7; padding:8px 10px; background:rgba(0,0,0,0.2); border-radius:5px; border-left:2px solid rgba(255,255,255,0.08); margin-bottom:8px; }
        .sol-table { width:100%; border-collapse:collapse; font-family:var(--mono); font-size:12px; }
        .sol-table th { text-align:left; padding:7px 9px; border-bottom:1px solid var(--border); color:var(--muted); font-size:9px; letter-spacing:1.5px; font-family:var(--sans); text-transform:uppercase; }
        .sol-table td { padding:6px 9px; border-bottom:1px solid rgba(255,255,255,0.03); color:#fff; }
        .sol-table tr:last-child td { border-bottom:none; }
        .tscroll { max-height:180px; overflow-y:auto; border-radius:6px; border:1px solid var(--border); }
        .hi-cell { color:var(--purple-light); font-weight:bold; }
        .enc-cell { color:var(--blue-light); font-weight:bold; }
        .op-cell { color:var(--muted); font-size:10px; }
        .btn-full { width:100%; padding:11px; background:linear-gradient(135deg,var(--blue),#2563eb); color:#fff; border:none; border-radius:8px; font-size:12px; font-weight:800; letter-spacing:1px; text-transform:uppercase; cursor:pointer; transition:all 0.2s; display:flex; align-items:center; justify-content:center; }
        .btn-full:hover { background:linear-gradient(135deg,var(--blue-light),var(--blue)); transform:translateY(-1px); box-shadow:0 6px 20px rgba(59,130,246,0.3); }

        /* ═══ DECRYPT MODE TOGGLE ═══ */
        .decrypt-mode-bar { display:flex; gap:6px; flex-shrink:0; margin-bottom:12px; }
        .mode-btn { flex:1; padding:8px 12px; background:rgba(255,255,255,0.03); border:1px solid var(--border); color:var(--muted-2); font-size:11px; font-weight:700; letter-spacing:0.8px; text-transform:uppercase; border-radius:7px; cursor:pointer; transition:all 0.2s; font-family:var(--sans); display:flex; align-items:center; justify-content:center; gap:6px; }
        .mode-btn:hover { color:#fff; border-color:var(--border-hover); }
        .mode-btn.active { background:rgba(59,130,246,0.1); border-color:rgba(59,130,246,0.4); color:var(--blue-light); }

        /* ═══ ALGORITHM TERMINAL ═══ */
        .algo-terminal { background:rgba(0,0,0,0.55); border:1px solid rgba(59,130,246,0.2); border-radius:10px; font-family:var(--mono); font-size:12px; overflow:hidden; }
        .algo-header { background:rgba(0,0,0,0.4); padding:10px 14px; border-bottom:1px solid rgba(59,130,246,0.15); display:flex; align-items:center; gap:8px; }
        .algo-header-dots { display:flex; gap:5px; }
        .algo-header-dot { width:8px; height:8px; border-radius:50%; }
        .algo-title { color:var(--blue-light); font-size:10px; font-weight:800; letter-spacing:2px; flex:1; }
        .algo-body { padding:14px; display:flex; flex-direction:column; gap:10px; }
        .algo-pseudocode { background:rgba(0,0,0,0.3); border-radius:6px; padding:10px 14px; border-left:2px solid var(--purple); }
        .algo-line { color:var(--muted-2); line-height:1.9; font-size:11px; }
        .algo-line .kw { color:var(--purple-light); }
        .algo-line .fn { color:var(--blue-light); }
        .algo-line .val { color:var(--green-light); }
        .algo-line .cm { color:var(--muted); font-style:italic; }
        .scan-results { max-height:190px; overflow-y:auto; display:flex; flex-direction:column; gap:2px; }
        .scan-row { display:flex; align-items:center; gap:8px; padding:4px 8px; border-radius:4px; background:rgba(255,255,255,0.02); border:1px solid transparent; font-size:11px; transition:all 0.15s; }
        .scan-match { background:rgba(16,185,129,0.1) !important; border-color:rgba(16,185,129,0.35) !important; }
        .scan-shift { color:var(--blue-light); width:68px; flex-shrink:0; }
        .scan-text { flex:1; color:#fff; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; max-width:120px; }
        .scan-bar { color:var(--green); width:68px; flex-shrink:0; letter-spacing:-1px; font-size:10px; }
        .scan-score { color:var(--muted); width:24px; text-align:right; flex-shrink:0; font-size:10px; }
        .scan-tag { color:var(--green-light); font-weight:800; font-size:9px; letter-spacing:1px; flex-shrink:0; }
        .algo-controls { display:flex; align-items:center; gap:6px; flex-wrap:wrap; }
        .ctrl-btn { padding:7px 14px; background:rgba(59,130,246,0.1); border:1px solid rgba(59,130,246,0.25); color:var(--blue-light); font-size:10px; font-weight:800; letter-spacing:1px; text-transform:uppercase; border-radius:6px; cursor:pointer; font-family:var(--sans); transition:all 0.2s; }
        .ctrl-btn:hover { background:rgba(59,130,246,0.25); color:#fff; }
        .ctrl-btn:disabled { opacity:0.35; cursor:not-allowed; }
        .algo-success { background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.3); border-radius:6px; padding:10px 14px; color:var(--green-light); font-size:11px; line-height:1.7; }
        .algo-step-block { background:rgba(0,0,0,0.25); border:1px solid var(--border); border-radius:7px; padding:10px 12px; }
        .algo-step-title { color:var(--blue-light); font-size:9px; font-weight:800; letter-spacing:2px; margin-bottom:6px; }
        .algo-step-val { color:#fff; line-height:1.7; }
        .algo-step-active { border-color:rgba(59,130,246,0.4) !important; background:rgba(59,130,246,0.06) !important; }
        .algo-step-done { border-color:rgba(16,185,129,0.3) !important; }
        .algo-step-done .algo-step-title { color:var(--green-light); }
        .mat-disp { font-family:var(--mono); background:rgba(0,0,0,0.4); padding:8px 12px; border-radius:5px; display:inline-block; line-height:1.8; color:#fff; font-size:11px; }
        .freq-bar-row { display:flex; align-items:center; gap:6px; margin-bottom:2px; }
        .freq-letter { color:var(--blue-light); width:14px; flex-shrink:0; }
        .freq-bar-track { flex:1; height:8px; background:rgba(255,255,255,0.06); border-radius:4px; overflow:hidden; }
        .freq-bar-fill { height:100%; background:linear-gradient(90deg,var(--blue),var(--purple)); border-radius:4px; transition:width 0.5s; }
        .freq-val { color:var(--muted); width:28px; text-align:right; font-size:10px; flex-shrink:0; }
        .photon-row { display:flex; gap:4px; flex-wrap:wrap; margin-bottom:8px; }
        .photon-bit { width:32px; height:32px; border-radius:6px; display:flex; align-items:center; justify-content:center; font-size:14px; font-weight:800; border:1px solid transparent; transition:all 0.3s; flex-shrink:0; }
        .photon-0 { background:rgba(59,130,246,0.15); border-color:rgba(59,130,246,0.3); color:var(--blue-light); }
        .photon-1 { background:rgba(139,92,246,0.15); border-color:rgba(139,92,246,0.3); color:var(--purple-light); }
        .photon-match { background:rgba(16,185,129,0.2) !important; border-color:rgba(16,185,129,0.4) !important; }
        .photon-mismatch { background:rgba(239,68,68,0.1) !important; border-color:rgba(239,68,68,0.25) !important; opacity:0.5; }

        /* ═══ MANUAL WALKTHROUGH ═══ */
        .manual-terminal { background:rgba(0,0,0,0.55); border:1px solid rgba(139,92,246,0.2); border-radius:10px; font-family:var(--mono); font-size:12px; overflow:hidden; }
        .manual-header { background:rgba(0,0,0,0.4); padding:10px 14px; border-bottom:1px solid rgba(139,92,246,0.15); display:flex; align-items:center; gap:8px; }
        .manual-title { color:var(--purple-light); font-size:10px; font-weight:800; letter-spacing:2px; flex:1; }
        .manual-body { padding:14px; display:flex; flex-direction:column; gap:10px; }
        .step-box { background:rgba(0,0,0,0.3); border:1px solid var(--border); border-radius:10px; padding:14px; margin-bottom:8px; }
        .step-title { color:var(--blue-light); font-weight:800; font-size:10px; letter-spacing:1.5px; margin-bottom:8px; text-transform:uppercase; }
        .step-inp-row { display:flex; align-items:center; gap:8px; margin-top:10px; flex-wrap:wrap; }
        .step-input { width:64px; padding:8px; background:rgba(0,0,0,0.5); border:1px solid var(--border); color:#fff; font-family:var(--mono); font-size:15px; border-radius:6px; text-align:center; outline:none; transition:border-color 0.2s; }
        .step-input:focus { border-color:var(--blue); }
        .check-btn { padding:8px 16px; background:rgba(59,130,246,0.15); border:1px solid var(--blue); color:var(--blue-light); border-radius:6px; cursor:pointer; font-family:var(--sans); font-weight:800; font-size:10px; letter-spacing:1px; text-transform:uppercase; transition:all 0.2s; }
        .check-btn:hover { background:rgba(59,130,246,0.3); color:#fff; }
        .fb-ok { color:var(--green); font-size:11px; font-weight:600; margin-top:5px; }
        .fb-err { color:var(--red); font-size:11px; font-weight:600; margin-top:5px; }
        .prompt-line { display:flex; align-items:center; gap:8px; margin-top:8px; }
        .prompt-sym { color:var(--green-light); flex-shrink:0; }
        .prompt-input { flex:1; background:none; border:none; border-bottom:1px solid rgba(255,255,255,0.1); color:#fff; font-family:var(--mono); font-size:12px; padding:4px 6px; outline:none; text-transform:uppercase; }
        .prompt-input:focus { border-bottom-color:var(--blue); }
        .terminal-out { color:var(--green-light); font-size:11px; margin-top:6px; line-height:1.7; }
        .terminal-err { color:var(--red); font-size:11px; margin-top:6px; }
        .brute-out { background:rgba(0,0,0,0.4); border:1px solid var(--border); border-radius:8px; padding:12px 14px; margin-top:8px; font-family:var(--mono); font-size:13px; color:var(--green); min-height:36px; word-break:break-all; }
        .calc-link { display:inline-flex; align-items:center; gap:6px; margin-top:8px; padding:6px 10px; background:rgba(59,130,246,0.08); border:1px solid rgba(59,130,246,0.2); border-radius:6px; color:var(--blue-light); text-decoration:none; font-size:10px; font-weight:800; transition:all 0.2s; }
        .calc-link:hover { background:rgba(59,130,246,0.18); color:#fff; }

        @keyframes fadeIn { from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:translateY(0)} }
        @keyframes slideIn { from{opacity:0;transform:translateX(-8px)}to{opacity:1;transform:translateX(0)} }
        .anim-in { animation:slideIn 0.25s ease both; }
    </style>
</head>
<body>
    <nav class="topbar">
        <div class="topbar-logo">Insightful Encryptions</div>
        <div class="topbar-nav">
            {% if page == 'home' %}
                <a href="/classroom" class="topbar-link">Classroom</a>
                <a href="/lab" class="topbar-link">Lab</a>
                <a href="/local" class="topbar-link active">Secure Room</a>
            {% elif page == 'local' %}
                <a href="/" class="topbar-link">Home</a>
                <a href="/classroom" class="topbar-link">Classroom</a>
                <a href="/lab" class="topbar-link">Lab</a>
            {% elif page == 'chat' %}
                <a href="/leave" class="btn-disconnect">Disconnect</a>
            {% endif %}
        </div>
    </nav>

    {% if page == 'home' %}
    <div class="home-page">
        <div class="home-inner">
            <div class="home-badge"><span class="home-badge-dot"></span>Cryptographic Learning Platform</div>
            <h1 class="home-title">Master the Art of<br><span>Encryption</span></h1>
            <p class="home-sub">From classical Caesar shifts to quantum BB84 photon streams — learn, experiment, and communicate with real cryptographic protocols.</p>
            <div class="module-row">
                <a href="/classroom" class="module-card" style="--card-accent:var(--blue-light);--card-icon-bg:rgba(59,130,246,0.1);--card-icon-border:rgba(59,130,246,0.2);">
                    <div class="card-icon"><svg viewBox="0 0 24 24" width="22" height="22" stroke="var(--blue-light)" stroke-width="1.8" fill="none"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg></div>
                    <div class="card-label">Module 01</div>
                    <h3 class="card-title">Classroom</h3>
                    <p class="card-desc">Guided, step-by-step cryptographic lessons. Build understanding from first principles with interactive exercises.</p>
                    <div class="card-footer"><span class="card-tag">Structured</span><span class="card-arrow">→</span></div>
                </a>
                <a href="/lab" class="module-card" style="--card-accent:var(--purple-light);--card-icon-bg:rgba(139,92,246,0.1);--card-icon-border:rgba(139,92,246,0.2);">
                    <div class="card-icon"><svg viewBox="0 0 24 24" width="22" height="22" stroke="var(--purple-light)" stroke-width="1.8" fill="none"><path d="M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2V9M9 21H5a2 2 0 0 1-2-2V9m0 0h18"/></svg></div>
                    <div class="card-label">Module 02</div>
                    <h3 class="card-title">The Lab</h3>
                    <p class="card-desc">Open sandbox to freely experiment with cipher algorithms. Encrypt, break, and analyze without constraints.</p>
                    <div class="card-footer"><span class="card-tag" style="background:rgba(139,92,246,0.1);color:var(--purple-light);">Freeform</span><span class="card-arrow">→</span></div>
                </a>
                <a href="/local" class="module-card" style="--card-accent:var(--green-light);--card-icon-bg:rgba(16,185,129,0.1);--card-icon-border:rgba(16,185,129,0.25);">
                    <div class="card-icon"><svg viewBox="0 0 24 24" width="22" height="22" stroke="var(--green-light)" stroke-width="1.8" fill="none"><rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/></svg></div>
                    <div class="card-label">Module 03</div>
                    <h3 class="card-title">Secure Room</h3>
                    <p class="card-desc">Host or join a live encrypted chat room. Communicate across devices using real cipher protocols in real time.</p>
                    <div class="card-footer"><span class="card-tag" style="background:rgba(16,185,129,0.1);color:var(--green-light);">Live</span><span class="card-arrow">→</span></div>
                </a>
            </div>
        </div>
    </div>

    {% elif page == 'local' %}
    <div class="connect-page">
        <div class="connect-left">
            <div class="connect-brand">
                <div class="connect-brand-logo">Insightful Encryptions</div>
                <h2 class="connect-brand-title">Start a<br><em>Secure Session</em></h2>
                <p class="connect-brand-sub">Create or join an encrypted communication room. All traffic is processed through your chosen cipher in real time.</p>
                <div class="connect-features">
                    <div class="connect-feature">
                        <div class="connect-feature-icon"><svg viewBox="0 0 24 24" width="16" height="16" stroke="var(--green)" stroke-width="2" fill="none"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg></div>
                        <div class="connect-feature-text"><h4>End-to-End Ciphers</h4><p>Caesar, Hill, Vigenère, AES-256, or BB84 Quantum</p></div>
                    </div>
                    <div class="connect-feature">
                        <div class="connect-feature-icon"><svg viewBox="0 0 24 24" width="16" height="16" stroke="var(--green)" stroke-width="2" fill="none"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg></div>
                        <div class="connect-feature-text"><h4>Cross-Device</h4><p>Connect from any device on the local network</p></div>
                    </div>
                    <div class="connect-feature">
                        <div class="connect-feature-icon"><svg viewBox="0 0 24 24" width="16" height="16" stroke="var(--green)" stroke-width="2" fill="none"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg></div>
                        <div class="connect-feature-text"><h4>Live Inspector</h4><p>Click any message to analyze its cipher payload</p></div>
                    </div>
                </div>
            </div>
        </div>
        <div class="connect-right">
            <div class="connect-form-wrap">
                <h2 class="connect-form-title">Join the Network</h2>
                <p class="connect-form-sub">Set your identity, then host a new room or enter a room code.</p>
                <form method="post" id="local-form">
                    <div class="field-group">
                        <label class="field-label" for="username_input">Your Alias</label>
                        <input type="text" id="username_input" name="username" class="field-input" placeholder="e.g. CipherAgent" maxlength="12" required autocomplete="off">
                        <span id="username_warning" class="field-warning"></span>
                    </div>
                    <button type="submit" formaction="/host" id="btn-host" class="btn-host-new">
                        <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none"><rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/></svg>
                        Host New Room
                    </button>
                    <div class="divider-row">or join existing</div>
                    <div class="field-group" style="margin-bottom:0;">
                        <label class="field-label" for="room_code_box">Room Code</label>
                        <div class="join-row">
                            <input type="text" name="room_code" id="room_code_box" class="field-input code-input" placeholder="----" maxlength="4">
                            <button type="submit" formaction="/join" id="btn-join" class="btn-join-new">Join →</button>
                        </div>
                    </div>
                </form>
                <a href="/" class="back-link">← Back to main menu</a>
            </div>
        </div>
    </div>
    <script>
        const usernameInput = document.getElementById('username_input');
        const warningDiv = document.getElementById('username_warning');
        const hostBtn = document.getElementById('btn-host');
        const joinBtn = document.getElementById('btn-join');
        usernameInput.addEventListener('input', function() {
            fetch('/api/usernames').then(r => r.json()).then(taken => {
                if (taken.includes(usernameInput.value.trim())) {
                    warningDiv.textContent = 'Alias already in use on network.';
                    hostBtn.disabled = joinBtn.disabled = true;
                    usernameInput.style.borderColor = 'var(--red)';
                } else {
                    warningDiv.textContent = '';
                    hostBtn.disabled = joinBtn.disabled = false;
                    usernameInput.style.borderColor = '';
                }
            });
        });
        document.getElementById('btn-host').addEventListener('click', () => document.getElementById('room_code_box').required = false);
        document.getElementById('btn-join').addEventListener('click', () => document.getElementById('room_code_box').required = true);
    </script>

    {% elif page == 'chat' %}
    <div class="chat-page">
        <div class="chat-topbar-ext">
            <div class="room-badge">
                <span class="room-badge-live">Live</span>
                <span style="color:var(--muted);font-size:13px;font-weight:600;">Room</span>
                <span class="room-code-display">{{ room_code }}</span>
            </div>
            <div style="display:flex;align-items:center;gap:16px;">
                <select id="encryption-selector">
                    <option value="none">Plaintext (None)</option>
                    <option value="caesar">Caesar Cipher</option>
                    <option value="hill">Hill Cipher</option>
                    <option value="vigenere">Vigenère Cipher</option>
                    <option value="aes">AES-256</option>
                    <option value="quantum">BB84 Quantum</option>
                </select>
            </div>
        </div>
        <div class="chat-body">
            <!-- Chat column -->
            <div class="chat-col">
                <div id="chat-box" class="chat-log"></div>
                <div class="chat-send-row">
                    <input type="text" id="msg-input" class="chat-input" placeholder="Type an encrypted message..." autofocus>
                    <button onclick="sendMessage()" class="btn-send">Send</button>
                </div>
            </div>
            <!-- Encryption + inspector panel -->
            <div class="enc-panel">
                <div class="enc-panel-top">
                    <div class="panel-hdr" style="color:var(--purple-light);">Cipher: <span id="current-cipher" style="color:#fff;font-weight:400;">Plaintext</span></div>
                    <div id="no-cipher-msg" style="color:var(--muted);font-style:italic;font-size:12px;">Select a cipher above to configure its key.</div>
                    <!-- Caesar -->
                    <div id="caesar-controls" class="enc-param-wrapper" style="display:none;">
                        <div class="shift-row">
                            <div class="shift-badge" id="shift-badge">1</div>
                            <div style="flex:1;">
                                <div class="enc-label" style="margin-bottom:6px;">Shift Amount (1–25)</div>
                                <input type="range" id="caesar-slider" min="1" max="25" value="1">
                            </div>
                        </div>
                        <div class="alpha-strip">
                            <div><div class="alpha-label">Plain</div><div class="alpha-letters" style="color:#fff;">A B C D E</div></div>
                            <div style="color:rgba(255,255,255,0.3);font-size:16px;">→</div>
                            <div><div class="alpha-label">Cipher</div><div id="example-shift" class="alpha-letters" style="color:var(--green-light);">B C D E F</div></div>
                        </div>
                    </div>
                    <!-- Hill -->
                    <div id="hill-controls" class="enc-param-wrapper" style="display:none;">
                        <div class="hill-header">
                            <div>
                                <div class="enc-label" style="margin-bottom:5px;">Matrix Size</div>
                                <div id="hill-size-pill" class="hill-size-pill">2 × 2</div>
                            </div>
                            <div style="display:flex;flex-direction:column;align-items:flex-end;gap:3px;">
                                <div id="hill-grid-picker"></div>
                                <span style="color:var(--muted);font-size:9px;">drag to resize</span>
                            </div>
                        </div>
                        <div id="hill-matrix-container"></div>
                        <div id="hill-validation" class="matrix-valid pending"><div class="valid-dot"></div><span>Enter matrix values to validate…</span></div>
                    </div>
                    <!-- Text key -->
                    <div id="text-key-controls" class="enc-param-wrapper" style="display:none;">
                        <div class="enc-label">Keyword / Seed</div>
                        <div class="key-input-wrap">
                            <svg class="key-icon" viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none"><path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"/></svg>
                            <input type="text" id="text-key-input" class="chat-input key-inp" value="SECRET" style="width:100%;" oninput="updateKeyMeta()">
                        </div>
                        <div class="key-meta">
                            <span class="key-len" id="key-length-label">6 CHARS</span>
                            <div class="key-bars" id="key-strength-bars"></div>
                        </div>
                    </div>
                </div>

                <!-- Message Inspector -->
                <div class="enc-panel-bottom">
                    <div class="panel-hdr" style="color:var(--blue-light);">Message Inspector</div>
                    <div id="sel-placeholder" style="color:var(--muted);font-style:italic;font-size:13px;text-align:center;padding-top:24px;">
                        <svg viewBox="0 0 24 24" width="40" height="40" stroke="rgba(255,255,255,0.15)" stroke-width="1.5" fill="none" style="display:block;margin:0 auto 12px;"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                        Click any message to analyze its payload.
                    </div>
                    <div id="sel-details" class="tabs-wrap" style="display:none;">
                        <div style="background:rgba(0,0,0,0.35);padding:10px 12px;border-radius:7px;border:1px solid var(--border);margin-bottom:10px;flex-shrink:0;">
                            <div style="color:var(--muted);font-size:9px;margin-bottom:5px;font-weight:800;letter-spacing:1px;">INTERCEPTED PAYLOAD</div>
                            <div id="sel-payload" style="color:#fff;font-family:var(--mono);word-break:break-all;font-size:13px;"></div>
                        </div>
                        <!-- ══ TAB NAV: Guide → Decrypt → History ══ -->
                        <div class="tabs-nav" style="flex-shrink:0;">
                            <button class="tab-btn active" onclick="switchTab('guide',event)">Guide</button>
                            <button class="tab-btn" onclick="switchTab('decrypt',event)">Decrypt</button>
                            <button class="tab-btn" onclick="switchTab('history',event)">History</button>
                        </div>

                        <!-- ══ TAB: Guide (thorough solution, shown first) ══ -->
                        <div id="tab-guide" class="tab-pane active">
                            <div id="sol-none" style="display:block;text-align:center;color:var(--muted);font-style:italic;padding-top:16px;">Message was sent in plaintext.</div>
                            <div id="sol-dynamic" style="display:none;">
                                <div class="sol-box" style="border-color:rgba(59,130,246,0.3);">
                                    <div class="sol-title" style="color:var(--blue-light);">1 — Encryption Process</div>
                                    <div id="dyn-enc-explanation" class="sol-explain"></div>
                                    <div id="dyn-enc-steps" class="tscroll"></div>
                                </div>
                                <div class="sol-box" style="border-color:rgba(139,92,246,0.3);">
                                    <div class="sol-title" style="color:var(--purple-light);">2 — Decryption Process</div>
                                    <div id="dyn-dec-explanation" class="sol-explain"></div>
                                    <div id="dyn-dec-steps" class="tscroll"></div>
                                </div>
                                <div class="sol-box">
                                    <div class="sol-title">3 — Attack Vector</div>
                                    <div id="dyn-tool" style="color:#fff;font-size:12px;line-height:1.7;"></div>
                                </div>
                                <div class="sol-box" style="border-color:rgba(16,185,129,0.3);">
                                    <div class="sol-title" style="color:var(--green-light);">4 — Recovered Plaintext</div>
                                    <div id="dyn-plain-2" style="color:#fff;font-size:15px;font-weight:bold;font-family:var(--mono);"></div>
                                </div>
                            </div>
                        </div>

                        <!-- ══ TAB: Decrypt (computer algo + manual walkthrough) ══ -->
                        <div id="tab-decrypt" class="tab-pane">
                            <div id="tool-container-none" style="display:none;text-align:center;color:var(--muted);font-style:italic;padding-top:16px;">No tools required for plaintext.</div>
                            <div id="tool-container-active" style="display:none;flex-direction:column;flex:1;gap:0;min-height:0;">
                                <!-- Mode toggle -->
                                <div class="decrypt-mode-bar">
                                    <button id="btn-mode-computer" class="mode-btn active" onclick="setDecryptMode('computer')">
                                        <svg viewBox="0 0 24 24" width="13" height="13" stroke="currentColor" stroke-width="2" fill="none"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
                                        Algorithm
                                    </button>
                                    <button id="btn-mode-manual" class="mode-btn" onclick="setDecryptMode('manual')">
                                        <svg viewBox="0 0 24 24" width="13" height="13" stroke="currentColor" stroke-width="2" fill="none"><path d="M14.5 10c-.83 0-1.5-.67-1.5-1.5v-5c0-.83.67-1.5 1.5-1.5s1.5.67 1.5 1.5v5c0 .83-.67 1.5-1.5 1.5z"/><path d="M20.5 10H19V8.5c0-.83.67-1.5 1.5-1.5s1.5.67 1.5 1.5-.67 1.5-1.5 1.5z"/><path d="M9.5 14.5v-1.75m0 0c0-.69.56-1.25 1.25-1.25h0c.69 0 1.25.56 1.25 1.25V14.5m-2.5 0V14m2.5.5V14"/><path d="M9.5 19a6 6 0 0 0 6 0"/><path d="M9 10v-1a1 1 0 0 0-2 0v5"/><path d="M7 14c-.83 0-1.5.67-1.5 1.5S6.17 17 7 17"/></svg>
                                        Manual
                                    </button>
                                </div>
                                <!-- Computer algorithm view -->
                                <div id="mode-computer" style="flex:1;overflow-y:auto;min-height:0;padding-bottom:80px;">
                                    <div id="computer-view-content"></div>
                                </div>
                                <!-- Manual walkthrough view -->
                                <div id="mode-manual" style="display:none;flex:1;overflow-y:auto;min-height:0;padding-bottom:80px;">
                                    <div id="manual-view-content"></div>
                                </div>
                            </div>
                        </div>

                        <!-- ══ TAB: History (was Lore) ══ -->
                        <div id="tab-history" class="tab-pane">
                            <div id="hist-none" style="display:block;text-align:center;color:var(--muted);font-style:italic;padding-top:16px;">No historical data for plaintext.</div>
                            <div id="hist-caesar" class="history-block" style="display:none;"><h3 style="color:#fff;margin:0 0 8px 0;font-size:16px;font-weight:800;">Julius Caesar's Cipher</h3><p style="margin-top:0;">Historically utilized by Julius Caesar to protect messages of military significance, this substitution cipher shifted the alphabet by three positions.</p><p>Though trivial to break today via brute force or frequency analysis, it remains the foundational building block for complex modern algorithms.</p></div>
                            <div id="hist-hill" class="history-block" style="display:none;"><h3 style="color:#fff;margin:0 0 8px 0;font-size:16px;font-weight:800;">Lester S. Hill's Matrix Cipher</h3><p style="margin-top:0;">Invented in 1929, the Hill cipher revolutionized cryptology by introducing linear algebra into encryption.</p><p>Its complete linearity makes it vulnerable to Known-Plaintext attacks, but its concept of matrix diffusion heavily influenced modern block ciphers like AES.</p></div>
                            <div id="hist-aes" class="history-block" style="display:none;"><h3 style="color:#fff;margin:0 0 8px 0;font-size:16px;font-weight:800;">Advanced Encryption Standard</h3><p style="margin-top:0;">Adopted by NIST in 2001, the Rijndael cipher (AES) is the definitive global standard for symmetric key encryption.</p><p>With key sizes up to 256 bits, it is considered impenetrable by classical brute force.</p></div>
                            <div id="hist-vigenere" class="history-block" style="display:none;"><h3 style="color:#fff;margin:0 0 8px 0;font-size:16px;font-weight:800;">Le Chiffre Indéchiffrable</h3><p style="margin-top:0;">For 300 years considered entirely unbreakable — ultimately defeated in 1863 by Friedrich Kasiski through pattern analysis.</p></div>
                            <div id="hist-quantum" class="history-block" style="display:none;"><h3 style="color:#fff;margin:0 0 8px 0;font-size:16px;font-weight:800;">BB84 Quantum Cryptography</h3><p style="margin-top:0;">Developed in 1984, BB84 relies on quantum physics. Measuring a quantum state alters it, making interception physically detectable.</p></div>
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
        const selBox = document.getElementById('encryption-selector');
        const cipherText = document.getElementById('current-cipher');
        const caesarCtrl = document.getElementById('caesar-controls');
        const caesarSlider = document.getElementById('caesar-slider');
        const shiftBadge = document.getElementById('shift-badge');
        const exShift = document.getElementById('example-shift');
        const hillCtrl = document.getElementById('hill-controls');
        const hillMatrix = document.getElementById('hill-matrix-container');
        const textKeyCtrl = document.getElementById('text-key-controls');
        const textKeyInp = document.getElementById('text-key-input');

        let selectedMsgId = null, emojiMsgId = null;
        let activePayload = '', activeOriginal = '', activeCipherKey = null, activeCipherType = null;
        let currentDecryptMode = 'computer';

        // ── Math helpers ────────────────────────────────────────────
        const mod26 = n => ((n % 26) + 26) % 26;
        const mod97 = n => ((Math.round(n) % 97) + 97) % 97;
        function matDet(m) {
            if (m.length === 1) return m[0][0];
            if (m.length === 2) return m[0][0]*m[1][1] - m[0][1]*m[1][0];
            let d = 0;
            for (let c = 0; c < m.length; c++) {
                let sub = m.slice(1).map(r => r.filter((_,j) => j !== c));
                d += (c % 2 === 1 ? -1 : 1) * m[0][c] * matDet(sub);
            }
            return d;
        }
        function matCofactor(m, r, c) {
            let sub = m.filter((_,i) => i !== r).map(row => row.filter((_,j) => j !== c));
            return ((r + c) % 2 === 1 ? -1 : 1) * matDet(sub);
        }
        function matAdj(m) {
            let a = Array(m.length).fill(0).map(() => Array(m.length).fill(0));
            for (let i = 0; i < m.length; i++) for (let j = 0; j < m.length; j++) a[j][i] = matCofactor(m, i, j);
            return a;
        }
        function modInverse26(x) {
            for (let i = 1; i < 26; i++) if ((x * i) % 26 === 1) return i;
            return -1;
        }
        function printMat(mat) {
            return mat.map(r => "[ " + r.map(v => v.toString().padStart(3,' ')).join(', ') + " ]").join('<br>');
        }

        // ── Hill matrix validation ──────────────────────────────────
        function validateHillMatrix() {
            const cells = document.querySelectorAll('.hill-cell');
            if (!cells.length) return true;
            let mat = [], row = [];
            cells.forEach(c => { row.push(parseInt(c.value)||0); if (row.length === currentHillSize) { mat.push(row); row = []; } });
            const det = mod97(matDet(mat));
            const valid = det !== 0;
            const ind = document.getElementById('hill-validation');
            const con = document.getElementById('hill-matrix-container');
            ind.className = 'matrix-valid ' + (valid ? 'valid' : 'invalid');
            if (valid) {
                ind.innerHTML = `<div class="valid-dot"></div><span>Valid &mdash; det &equiv; <strong>${det}</strong> (mod 97) ✓</span>`;
                con.style.borderColor = 'rgba(16,185,129,0.4)';
            } else {
                ind.innerHTML = `<div class="valid-dot"></div><span>Singular &mdash; det &equiv; 0 &mdash; cannot encrypt</span>`;
                con.style.borderColor = 'rgba(239,68,68,0.4)';
            }
            return valid;
        }

        // ── Key meta ────────────────────────────────────────────────
        function updateKeyMeta() {
            const len = textKeyInp.value.length;
            document.getElementById('key-length-label').textContent = len + ' CHAR' + (len !== 1 ? 'S' : '');
            const el = document.getElementById('key-strength-bars'); el.innerHTML = '';
            for (let i = 0; i < 10; i++) {
                const b = document.createElement('div');
                b.className = 'key-bar' + (i < len ? ' filled' + (len >= 8 ? ' strong' : '') : '');
                el.appendChild(b);
            }
        }
        updateKeyMeta();
        textKeyInp.addEventListener('input', updateKeyMeta);

        // ── Hill grid picker ────────────────────────────────────────
        let currentHillSize = 2;
        (function() {
            const picker = document.getElementById('hill-grid-picker');
            const pill = document.getElementById('hill-size-pill');
            let dragging = false, hoverSz = 2;
            function hl(sz, commit) {
                [...picker.children].forEach(el => {
                    const lit = parseInt(el.dataset.r) <= sz && parseInt(el.dataset.c) <= sz;
                    el.style.background = lit ? (commit ? 'rgba(59,130,246,0.55)' : 'rgba(59,130,246,0.3)') : 'rgba(255,255,255,0.03)';
                    el.style.borderColor = lit ? 'var(--blue)' : 'rgba(255,255,255,0.12)';
                });
                pill.textContent = sz + ' × ' + sz;
            }
            for (let r = 1; r <= 4; r++) for (let c = 1; c <= 4; c++) {
                const cell = document.createElement('div');
                cell.className = 'grid-cell'; cell.dataset.r = r; cell.dataset.c = c;
                cell.addEventListener('mouseenter', () => { hoverSz = Math.max(2, Math.max(r, c)); hl(hoverSz, false); });
                cell.addEventListener('mousedown', e => { e.preventDefault(); dragging = true; });
                cell.addEventListener('mouseup', () => { if (!dragging) return; dragging = false; currentHillSize = hoverSz; renderHillMatrix(currentHillSize); hl(currentHillSize, true); });
                picker.appendChild(cell);
            }
            picker.addEventListener('mouseleave', () => { dragging = false; hl(currentHillSize, true); });
            hl(2, true);
        })();

        function renderHillMatrix(size) {
            hillMatrix.style.gridTemplateColumns = `repeat(${size},1fr)`;
            hillMatrix.innerHTML = '';
            const def = [3, 3, 2, 5];
            let cnt = 0;
            for (let i = 0; i < size; i++) for (let j = 0; j < size; j++) {
                const inp = document.createElement('input');
                inp.type = 'number'; inp.className = 'chat-input hill-cell';
                inp.value = (size === 2) ? (def[cnt] ?? 0) : (i === j ? 1 : 0);
                inp.addEventListener('input', validateHillMatrix);
                hillMatrix.appendChild(inp); cnt++;
            }
            setTimeout(validateHillMatrix, 50);
        }
        renderHillMatrix(2);

        // ── Emoji picker ────────────────────────────────────────────
        const pickerWrap = document.createElement('div');
        pickerWrap.className = 'emoji-picker-container';
        const emojiPicker = document.createElement('emoji-picker');
        pickerWrap.appendChild(emojiPicker);
        document.body.appendChild(pickerWrap);
        customElements.whenDefined('emoji-picker').then(() => {
            const chk = setInterval(() => {
                if (!emojiPicker.shadowRoot) return; clearInterval(chk);
                const s = document.createElement('style');
                s.textContent = `:host{--background:#0d1526;--border-color:rgba(255,255,255,0.08);--input-font-color:#fff;--indicator-color:#3b82f6;--button-hover-background:rgba(59,130,246,0.12);--search-background:rgba(0,0,0,0.3);}.nav,.preview{display:none!important;}`;
                emojiPicker.shadowRoot.appendChild(s);
            }, 50);
        });
        emojiPicker.addEventListener('emoji-click', ev => {
            if (emojiMsgId) { socket.emit('react_message', { room, id: emojiMsgId, emoji: ev.detail.unicode }); pickerWrap.style.display = 'none'; }
        });
        document.addEventListener('click', ev => { if (!pickerWrap.contains(ev.target) && !ev.target.closest('.btn-emoji')) pickerWrap.style.display = 'none'; });

        // ── Socket ───────────────────────────────────────────────────
        socket.emit('join', { room });
        function appendMsg(data) {
            const row = document.createElement('div'); row.className = 'message-row';
            if (data.id) row.id = 'msg-row-' + data.id;
            const wrap = document.createElement('div');
            wrap.className = 'msg-wrap ' + (data.type || 'msg-user-wrap');
            if (data.id) wrap.id = 'msg-content-' + data.id;
            const txt = document.createElement('div'); txt.className = 'msg-text';
            if (data.type === 'msg-system') {
                txt.textContent = data.msg; wrap.classList.add('msg-system'); wrap.appendChild(txt);
            } else {
                txt.innerHTML = `<span style="color:var(--blue-light);font-weight:800;font-size:11px;letter-spacing:1px;text-transform:uppercase;">${data.username}</span><br><span style="font-size:14px;margin-top:2px;display:inline-block;">${data.msg}</span>`;
                wrap.classList.add('msg-user-wrap');
                wrap.onclick = () => selectMessage(data.id, data.username, data.msg, data.original_msg, data.cipher || 'none', data.key || 0);
                const acts = document.createElement('div'); acts.className = 'msg-actions';
                const eBtn = document.createElement('button'); eBtn.className = 'action-btn btn-emoji';
                eBtn.innerHTML = `<svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none"><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg>`;
                eBtn.onclick = e => { e.stopPropagation(); emojiMsgId = data.id; const r = eBtn.getBoundingClientRect(); pickerWrap.style.display = 'block'; pickerWrap.style.top = (r.bottom + 5) + 'px'; pickerWrap.style.left = (r.left - 250) + 'px'; };
                acts.appendChild(eBtn);
                if (data.username === myUsername) {
                    const dBtn = document.createElement('button'); dBtn.className = 'action-btn btn-trash';
                    dBtn.innerHTML = `<svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>`;
                    dBtn.onclick = e => { e.stopPropagation(); socket.emit('delete_message', { room, id: data.id }); };
                    acts.appendChild(dBtn);
                }
                wrap.appendChild(txt); wrap.appendChild(acts);
            }
            row.appendChild(wrap);
            const reacts = document.createElement('div'); reacts.className = 'reactions-row';
            if (data.id) reacts.id = 'reactions-' + data.id;
            row.appendChild(reacts);
            chatBox.appendChild(row);
            chatBox.scrollTop = chatBox.scrollHeight;
            if (data.reactions) renderReactions(data.id, data.reactions);
        }
        function renderReactions(id, map) {
            const row = document.getElementById('reactions-' + id); if (!row) return;
            row.innerHTML = '';
            for (const [em, users] of Object.entries(map)) {
                if (users.length > 0) {
                    const b = document.createElement('div'); b.className = 'reaction-badge';
                    if (users.includes(myUsername)) b.classList.add('active');
                    b.textContent = `${em} ${users.length}`;
                    b.onclick = () => socket.emit('react_message', { room, id, emoji: em });
                    row.appendChild(b);
                }
            }
        }
        socket.on('chat_history', msgs => msgs.forEach(appendMsg));
        socket.on('message', appendMsg);
        socket.on('reactions_updated', d => renderReactions(d.id, d.reactions));
        socket.on('message_deleted', d => {
            const el = document.getElementById('msg-row-' + d.id); if (el) el.remove();
            if (selectedMsgId === d.id) clearSel();
        });

        function sendMessage() {
            if (!input.value.trim()) return;
            let encVal = 0;
            if (selBox.value === 'caesar') { encVal = parseInt(caesarSlider.value) || 0; }
            else if (selBox.value === 'hill') {
                if (!validateHillMatrix()) { alert('Singular matrix — choose different values.'); return; }
                const cells = document.querySelectorAll('.hill-cell');
                let mat = [], row = [];
                cells.forEach(c => { row.push(parseInt(c.value)||0); if (row.length === currentHillSize) { mat.push(row); row = []; } });
                encVal = mat;
            } else if (['aes','vigenere','quantum'].includes(selBox.value)) { encVal = textKeyInp.value; }
            socket.send({ msg: input.value, room, encryption: selBox.value, 'encryption-value': encVal });
            input.value = '';
        }
        input.addEventListener('keypress', e => { if (e.key === 'Enter') sendMessage(); });

        // ── Tab switching ────────────────────────────────────────────
        function switchTab(id, ev) {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            if (ev) ev.target.classList.add('active');
            else {
                const btn = document.querySelector(`.tab-btn[onclick*="'${id}'"]`);
                if (btn) btn.classList.add('active');
            }
            document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
            document.getElementById('tab-' + id).classList.add('active');
        }

        // ── Decrypt mode toggle ──────────────────────────────────────
        function setDecryptMode(mode) {
            currentDecryptMode = mode;
            document.getElementById('btn-mode-computer').classList.toggle('active', mode === 'computer');
            document.getElementById('btn-mode-manual').classList.toggle('active', mode === 'manual');
            document.getElementById('mode-computer').style.display = mode === 'computer' ? 'block' : 'none';
            document.getElementById('mode-manual').style.display = mode === 'manual' ? 'block' : 'none';
        }

        // ── Guide tab helpers ────────────────────────────────────────
        const m = s => `<code style="font-family:var(--mono);background:rgba(0,0,0,0.4);padding:2px 6px;border-radius:3px;font-size:10px;">${s}</code>`;
        function getCipherExpl(type, key, dec) {
            if (type === 'caesar') {
                const s = parseInt(key) || 0;
                return dec ? `Each ciphertext letter is shifted <strong>${s}</strong> positions backward. ${m('P=(C−'+s+'+26) mod 26')}` : `Each letter is shifted <strong>${s}</strong> positions forward. ${m('C=(P+'+s+') mod 26')}`;
            } else if (type === 'vigenere') {
                const k = String(key).toUpperCase();
                return dec ? `Subtract each keyword letter of <strong>"${k}"</strong> from the ciphertext. ${m('P[i]=(C[i]−K[i mod '+k.length+']+26) mod 26')}` : `Pair each letter with keyword <strong>"${k}"</strong>. ${m('C[i]=(P[i]+K[i mod '+k.length+']) mod 26')}`;
            } else if (type === 'hill') {
                const n = Array.isArray(key) ? key.length : 2;
                return dec ? `Multiply ciphertext blocks by the <strong>inverse matrix K⁻¹</strong> mod 26. ${m('[P]=[C]×K⁻¹ (mod 26)')}` : `Multiply plaintext blocks of ${n} by the <strong>key matrix K</strong> mod 26. ${m('[C]=[P]×K (mod 26)')}`;
            } else if (type === 'aes') {
                return dec ? `AES applies 14 inverse rounds: <strong>InvShiftRows→InvSubBytes→AddRoundKey→InvMixColumns</strong>. Without the 256-bit key, recovery is infeasible.` : `AES-256 expands the key into 14 round sub-keys. Each round: <strong>SubBytes, ShiftRows, MixColumns, AddRoundKey</strong>.`;
            } else if (type === 'quantum') {
                return dec ? `Decryption uses the agreed-upon basis sift. Any eavesdropper introduces ~25% error, alerting the parties.` : `BB84 transmits each bit as a polarized photon in a randomly chosen basis (+/×). Matching bases form the shared key.`;
            }
            return '';
        }
        function buildTable(rows, hdrs) {
            if (!rows || !rows.length) return `<div style="color:var(--muted);padding:10px;font-size:11px;">Not enough characters.</div>`;
            return `<table class="sol-table"><thead><tr>${hdrs.map(h=>`<th>${h}</th>`).join('')}</tr></thead><tbody>${rows.join('')}</tbody></table>`;
        }
        function encTable(plain, cipher, type, key) {
            let rows = [], pC = plain.replace(/[^a-zA-Z]/g,'').toUpperCase(), cC = cipher.replace(/[^a-zA-Z]/g,'').toUpperCase(), L = 18;
            if (type === 'caesar') {
                const s = parseInt(key) || 0;
                for (let i = 0; i < Math.min(pC.length, L); i++) { const pv = pC[i].charCodeAt(0)-65, cv = (pv+s)%26; rows.push(`<tr><td style="color:#fff;">${pC[i]}(${pv})</td><td class="op-cell">+${s} mod 26=${cv}</td><td class="enc-cell">${String.fromCharCode(cv+65)}(${cv})</td></tr>`); }
                return buildTable(rows, ['PLAIN','OP','CIPHER']);
            } else if (type === 'vigenere') {
                const k = String(key).toUpperCase();
                for (let i = 0; i < Math.min(pC.length, L); i++) { const kc = k[i%k.length], kv = kc.charCodeAt(0)-65, pv = pC[i].charCodeAt(0)-65, cv = (pv+kv)%26; rows.push(`<tr><td style="color:#fff;">${pC[i]}(${pv})</td><td class="op-cell">+${kc}(${kv})=${cv}</td><td class="enc-cell">${String.fromCharCode(cv+65)}(${cv})</td></tr>`); }
                return buildTable(rows, ['PLAIN','KEY+SHIFT','CIPHER']);
            } else if (type === 'hill') {
                const n = Array.isArray(key) ? key.length : 2;
                for (let i = 0; i < pC.length; i += n) { rows.push(`<tr><td style="color:#fff;">[${pC.substring(i,i+n).padEnd(n,'A').split('').join(',')}]</td><td class="op-cell">×Key mod 26</td><td class="enc-cell">[${cC.substring(i,i+n).padEnd(n,'?').split('').join(',')}]</td></tr>`); }
                return buildTable(rows, [`PLAIN(×${n})`,'OP',`CIPHER(×${n})`]);
            }
            return `<div style="color:var(--muted);padding:10px;font-size:11px;font-style:italic;">[Block-level cipher — character trace not applicable]</div>`;
        }
        function decTable(plain, cipher, type, key) {
            let rows = [], pC = plain.replace(/[^a-zA-Z]/g,'').toUpperCase(), cC = cipher.replace(/[^a-zA-Z]/g,'').toUpperCase(), L = 18;
            if (type === 'caesar') {
                const s = parseInt(key) || 0;
                for (let i = 0; i < Math.min(cC.length, L); i++) { const cv = cC[i].charCodeAt(0)-65, pv = ((cv-s)%26+26)%26; rows.push(`<tr><td style="color:#fff;">${cC[i]}(${cv})</td><td class="op-cell">(${cv}−${s}+26) mod 26=${pv}</td><td class="hi-cell">${String.fromCharCode(pv+65)}(${pv})</td></tr>`); }
                return buildTable(rows, ['CIPHER','REVERSE','PLAIN']);
            } else if (type === 'vigenere') {
                const k = String(key).toUpperCase();
                for (let i = 0; i < Math.min(cC.length, L); i++) { const kc = k[i%k.length], kv = kc.charCodeAt(0)-65, cv = cC[i].charCodeAt(0)-65, pv = ((cv-kv)%26+26)%26; rows.push(`<tr><td style="color:#fff;">${cC[i]}(${cv})</td><td class="op-cell">−${kc}(${kv})=${pv}</td><td class="hi-cell">${String.fromCharCode(pv+65)}(${pv})</td></tr>`); }
                return buildTable(rows, ['CIPHER','KEY−SHIFT','PLAIN']);
            } else if (type === 'hill') {
                const n = Array.isArray(key) ? key.length : 2;
                for (let i = 0; i < cC.length; i += n) { rows.push(`<tr><td style="color:#fff;">[${cC.substring(i,i+n).padEnd(n,'A').split('').join(',')}]</td><td class="op-cell">×K⁻¹ mod 26</td><td class="hi-cell">[${pC.substring(i,i+n).padEnd(n,'?').split('').join(',')}]</td></tr>`); }
                return buildTable(rows, [`CIPHER(×${n})`,'INV MATRIX',`PLAIN(×${n})`]);
            }
            return `<div style="color:var(--muted);padding:10px;font-size:11px;font-style:italic;">[Block-level — requires key for reversal]</div>`;
        }

        // ── Caesar shift helper ──────────────────────────────────────
        function caesarShift(text, n) {
            return text.split('').map(c => {
                const code = c.charCodeAt(0);
                if (code >= 65 && code <= 90) return String.fromCharCode(((code-65-n+260)%26)+65);
                if (code >= 97 && code <= 122) return String.fromCharCode(((code-97-n+260)%26)+97);
                return c;
            }).join('');
        }
        function freqScore(text) {
            const freq = {A:8.2,B:1.5,C:2.8,D:4.3,E:12.7,F:2.2,G:2.0,H:6.1,I:7.0,J:0.15,K:0.77,L:4.0,M:2.4,N:6.7,O:7.5,P:1.9,Q:0.1,R:6.0,S:6.3,T:9.1,U:2.8,V:0.98,W:2.4,X:0.15,Y:2.0,Z:0.07};
            let s = 0;
            text.toUpperCase().split('').forEach(c => { if (freq[c]) s += freq[c]; });
            return Math.round(s);
        }

        // ═══════════════════════════════════════════════════════════
        //  DECRYPT TAB — COMPUTER ALGORITHM VIEWS
        // ═══════════════════════════════════════════════════════════

        function algoHeader(title, color) {
            return `<div class="algo-header">
                <div class="algo-header-dots">
                    <div class="algo-header-dot" style="background:#ef4444;"></div>
                    <div class="algo-header-dot" style="background:#f59e0b;"></div>
                    <div class="algo-header-dot" style="background:#10b981;"></div>
                </div>
                <div class="algo-title" style="color:${color||'var(--blue-light)'};">${title}</div>
            </div>`;
        }

        // ── Caesar computer view ─────────────────────────────────────
        function renderCaesarComputer(container) {
            let step = 0, timer = null, done = false;
            const totalKey = parseInt(activeCipherKey) || 1;

            container.innerHTML = `
                <div class="algo-terminal anim-in">
                    ${algoHeader('CAESAR BRUTE-FORCE CRACKER')}
                    <div class="algo-body">
                        <div class="algo-pseudocode">
                            <div class="algo-line"><span class="kw">for</span> (shift = <span class="val">1</span>; shift &lt;= <span class="val">25</span>; shift++) {</div>
                            <div class="algo-line">&nbsp;&nbsp;candidate = <span class="fn">reverse_shift</span>(ciphertext, shift)</div>
                            <div class="algo-line">&nbsp;&nbsp;score = <span class="fn">freq_score</span>(candidate) <span class="cm">// english letter freq</span></div>
                            <div class="algo-line">&nbsp;&nbsp;<span class="kw">if</span> (score &gt; best_score) best = {shift, candidate}</div>
                            <div class="algo-line">}</div>
                        </div>
                        <div style="color:var(--muted);font-size:10px;letter-spacing:1px;">INPUT: <span style="color:#fff;">"${activePayload.substring(0,30)}${activePayload.length>30?'…':''}"</span></div>
                        <div id="caesar-scan" class="scan-results"></div>
                        <div class="algo-controls">
                            <button class="ctrl-btn" id="cs-step">▶ Step</button>
                            <button class="ctrl-btn" id="cs-auto">⏩ Auto-Run</button>
                            <button class="ctrl-btn" id="cs-reset" style="opacity:0.6;">↺ Reset</button>
                        </div>
                        <div id="caesar-algo-result"></div>
                    </div>
                </div>`;

            function addRow() {
                if (step >= 25 || done) return;
                step++;
                const candidate = caesarShift(activePayload, step);
                const score = freqScore(candidate);
                const isKey = step === totalKey;
                const bar = Math.min(10, Math.round(score / 6));
                const scanEl = document.getElementById('caesar-scan');
                if (!scanEl) return;
                const row = document.createElement('div');
                row.className = 'scan-row anim-in' + (isKey ? ' scan-match' : '');
                row.innerHTML = `
                    <span class="scan-shift">shift=${String(step).padStart(2,'0')}</span>
                    <span class="scan-text">${candidate.substring(0,14)}${candidate.length>14?'…':''}</span>
                    <span class="scan-bar">${'█'.repeat(bar)}${'░'.repeat(10-bar)}</span>
                    <span class="scan-score">${score}</span>
                    ${isKey ? '<span class="scan-tag">← HIT</span>' : ''}`;
                scanEl.appendChild(row);
                scanEl.scrollTop = scanEl.scrollHeight;
                if (isKey || step >= 25) {
                    done = true;
                    if (timer) { clearInterval(timer); timer = null; }
                    document.getElementById('cs-step').disabled = true;
                    document.getElementById('cs-auto').disabled = true;
                    const res = document.getElementById('caesar-algo-result');
                    if (res) res.innerHTML = `<div class="algo-success">✓ KEY FOUND: shift = ${totalKey}<br>→ PLAINTEXT: "${activeOriginal}"</div>`;
                }
            }

            function reset() {
                step = 0; done = false;
                if (timer) { clearInterval(timer); timer = null; }
                document.getElementById('caesar-scan').innerHTML = '';
                document.getElementById('caesar-algo-result').innerHTML = '';
                document.getElementById('cs-step').disabled = false;
                document.getElementById('cs-auto').disabled = false;
            }

            document.getElementById('cs-step').onclick = addRow;
            document.getElementById('cs-auto').onclick = () => {
                if (timer || done) return;
                document.getElementById('cs-step').disabled = true;
                timer = setInterval(() => { addRow(); if (done) clearInterval(timer); }, 90);
            };
            document.getElementById('cs-reset').onclick = reset;
        }

        // ── Hill computer view ───────────────────────────────────────
        function renderHillComputer(container) {
            if (!Array.isArray(activeCipherKey)) {
                container.innerHTML = `<div style="color:var(--muted);padding:16px;font-style:italic;">Key data unavailable for visualization.</div>`;
                return;
            }
            const K = activeCipherKey;
            const n = K.length;
            const rawDet = matDet(K);
            const det = mod26(rawDet);
            const detInv = modInverse26(det);
            const adj = matAdj(K);
            const invM = adj.map(r => r.map(v => mod26(v * detInv)));
            const steps = [
                { id:'hs0', title:'INPUT — Key Matrix K', body: `<div class="mat-disp">${printMat(K).replace(/ /g,'&nbsp;')}</div>` },
                { id:'hs1', title:'STEP 1 — Compute det(K)', body: `<div style="line-height:2;">${n===2?`det = (${K[0][0]}×${K[1][1]}) − (${K[0][1]}×${K[1][0]}) = <span style="color:var(--green-light);">${rawDet}</span>`:`det(K) = <span style="color:var(--green-light);">${rawDet}</span>`}<br>det mod 26 = <span style="color:var(--green-light);font-weight:800;">${det}</span></div>` },
                { id:'hs2', title:'STEP 2 — Modular Inverse of det', body: `<div style="line-height:2;">Find X: (${det} × X) mod 26 = 1<br>X = <span style="color:var(--green-light);font-weight:800;">${detInv}</span>  <span style="color:var(--muted);">(${det}×${detInv}=${det*detInv}, mod 26=${(det*detInv)%26} ✓)</span></div>` },
                { id:'hs3', title:'STEP 3 — Adjugate Matrix', body: `<div class="mat-disp" style="color:var(--purple-light);">${printMat(adj.map(r=>r.map(mod26))).replace(/ /g,'&nbsp;')}</div>` },
                { id:'hs4', title:'STEP 4 — K⁻¹ = det⁻¹ × adj(K) mod 26', body: `<div class="mat-disp" style="color:var(--green-light);">${printMat(invM).replace(/ /g,'&nbsp;')}</div>` },
                { id:'hs5', title:'STEP 5 — Decode Ciphertext Blocks', body: `<div class="algo-success">✓ K⁻¹ applied to all blocks<br>→ PLAINTEXT: "${activeOriginal}"</div>` },
            ];
            let revealed = 0;
            container.innerHTML = `
                <div class="algo-terminal anim-in">
                    ${algoHeader('HILL CIPHER MATRIX INVERSION', 'var(--purple-light)')}
                    <div class="algo-body">
                        <div id="hill-algo-steps" style="display:flex;flex-direction:column;gap:6px;"></div>
                        <div class="algo-controls" style="margin-top:6px;">
                            <button class="ctrl-btn" id="hs-step">▶ Next Step</button>
                            <button class="ctrl-btn" id="hs-auto">⏩ Auto-Run</button>
                        </div>
                    </div>
                </div>`;

            function showStep() {
                if (revealed >= steps.length) return;
                const s = steps[revealed++];
                const el = document.createElement('div');
                el.className = 'algo-step-block anim-in';
                el.innerHTML = `<div class="algo-step-title">${s.title}</div><div class="algo-step-val">${s.body}</div>`;
                document.getElementById('hill-algo-steps').appendChild(el);
                if (revealed >= steps.length) {
                    document.getElementById('hs-step').disabled = true;
                    document.getElementById('hs-auto').disabled = true;
                }
            }

            let hsTimer = null;
            document.getElementById('hs-step').onclick = showStep;
            document.getElementById('hs-auto').onclick = () => {
                if (hsTimer) return;
                document.getElementById('hs-step').disabled = true;
                hsTimer = setInterval(() => { showStep(); if (revealed >= steps.length) clearInterval(hsTimer); }, 600);
            };
            // Auto-show first step
            showStep();
        }

        // ── Vigenère computer view ───────────────────────────────────
        function renderVigenereComputer(container) {
            const key = String(activeCipherKey).toUpperCase();
            const keyLen = key.length;
            const ct = activePayload.toUpperCase().replace(/[^A-Z]/g,'');
            const freqEng = {A:8.2,B:1.5,C:2.8,D:4.3,E:12.7,F:2.2,G:2.0,H:6.1,I:7.0,J:0.15,K:0.77,L:4.0,M:2.4,N:6.7,O:7.5,P:1.9,Q:0.1,R:6.0,S:6.3,T:9.1,U:2.8,V:0.98,W:2.4,X:0.15,Y:2.0,Z:0.07};
            // Find trigrams
            const tri = {};
            for (let i = 0; i <= ct.length-3; i++) { const s = ct.substr(i,3); if (!tri[s]) tri[s]=[]; tri[s].push(i); }
            const reps = Object.entries(tri).filter(([,v])=>v.length>1);
            const gap = reps.length ? reps[0][1][1] - reps[0][1][0] : keyLen;
            // Build freq for each column
            const cols = Array.from({length: keyLen}, (_,ci) => ct.split('').filter((_,i)=>i%keyLen===ci));

            const steps = [
                { title:'INPUT', body:`<div style="color:#fff;font-family:var(--mono);font-size:11px;word-break:break-all;">"${activePayload.substring(0,40)}${activePayload.length>40?'…':''}"</div>` },
                { title:'STEP 1 — Kasiski Scan (repeated trigrams)', body: reps.length ? `Sequence <span style="color:var(--blue-light);">"${reps[0][0]}"</span> at positions [${reps[0][1].join(', ')}]<br>Gap = <span style="color:var(--green-light);font-weight:800;">${gap}</span> → key length candidate: ${gap}` : `No repeated trigrams found. Known key length: <span style="color:var(--green-light);">${keyLen}</span>` },
                { title:`STEP 2 — Split into ${keyLen} columns`, body:`${cols.map((c,i)=>`Col ${i}: <span style="color:var(--blue-light);">${c.join('')}</span>`).join('<br>')}` },
                { title:'STEP 3 — Frequency Analysis per Column', body: cols.map((col, ci) => {
                    const counts = {};
                    col.forEach(c => { counts[c] = (counts[c]||0)+1; });
                    const top = Object.entries(counts).sort((a,b)=>b[1]-a[1]).slice(0,3);
                    const shift = ((top[0]?.[0]?.charCodeAt(0)||69)-69+26)%26;
                    return `Col ${ci}: top="${top.map(e=>e[0]).join('')}" → shift≈${shift} → key[${ci}]=<span style="color:var(--green-light);">${key[ci]}</span>`;
                }).join('<br>') },
                { title:'STEP 4 — Reconstructed Key', body:`keyword = <span style="color:var(--green-light);font-weight:800;font-size:14px;">"${key}"</span>` },
                { title:'STEP 5 — Decrypt', body:`<div class="algo-success">✓ KEY: "${key}"<br>→ PLAINTEXT: "${activeOriginal}"</div>` },
            ];

            let revealed = 0;
            container.innerHTML = `
                <div class="algo-terminal anim-in">
                    ${algoHeader('KASISKI + FREQUENCY ATTACK', 'var(--green-light)')}
                    <div class="algo-body">
                        <div id="vig-algo-steps" style="display:flex;flex-direction:column;gap:6px;"></div>
                        <div class="algo-controls" style="margin-top:6px;">
                            <button class="ctrl-btn" id="vs-step">▶ Next Step</button>
                            <button class="ctrl-btn" id="vs-auto">⏩ Auto-Run</button>
                        </div>
                    </div>
                </div>`;

            function showVStep() {
                if (revealed >= steps.length) return;
                const s = steps[revealed++];
                const el = document.createElement('div');
                el.className = 'algo-step-block anim-in';
                el.innerHTML = `<div class="algo-step-title">${s.title}</div><div class="algo-step-val" style="font-size:11px;line-height:1.8;">${s.body}</div>`;
                document.getElementById('vig-algo-steps').appendChild(el);
                if (revealed >= steps.length) {
                    document.getElementById('vs-step').disabled = true;
                    document.getElementById('vs-auto').disabled = true;
                }
            }
            let vsTimer = null;
            document.getElementById('vs-step').onclick = showVStep;
            document.getElementById('vs-auto').onclick = () => {
                if (vsTimer) return;
                document.getElementById('vs-step').disabled = true;
                vsTimer = setInterval(() => { showVStep(); if (revealed >= steps.length) clearInterval(vsTimer); }, 700);
            };
            showVStep();
        }

        // ── AES computer view ────────────────────────────────────────
        function renderAesComputer(container) {
            const hex = () => Math.floor(Math.random()*256).toString(16).padStart(2,'0').toUpperCase();
            const makeGrid = (color) => Array(16).fill(0).map(() => `<div style="background:${color};padding:6px 4px;border-radius:3px;text-align:center;font-size:10px;font-family:var(--mono);">${hex()}</div>`).join('');
            const roundSteps = [
                { name:'SubBytes()', desc:'Non-linear substitution via S-Box', color:'rgba(59,130,246,0.25)' },
                { name:'ShiftRows()', desc:'Cyclic shift of each row', color:'rgba(139,92,246,0.25)' },
                { name:'MixColumns()', desc:'Matrix multiply in GF(2⁸)', color:'rgba(16,185,129,0.25)' },
                { name:'AddRoundKey()', desc:'XOR with round sub-key', color:'rgba(245,158,11,0.2)' },
            ];
            let rStep = 0, rRound = 0, rTimer = null;
            container.innerHTML = `
                <div class="algo-terminal anim-in">
                    ${algoHeader('AES-256 ROUND VISUALIZER', 'var(--green-light)')}
                    <div class="algo-body">
                        <div style="color:var(--muted);font-size:10px;margin-bottom:4px;letter-spacing:1px;">STATE MATRIX (4×4 bytes) — ROUND <span id="aes-round-num">0</span>/14</div>
                        <div id="aes-grid" style="display:grid;grid-template-columns:repeat(4,1fr);gap:3px;margin-bottom:10px;">${makeGrid('rgba(255,255,255,0.06)')}</div>
                        <div id="aes-op-row" style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px;">
                            ${roundSteps.map((s,i)=>`<div id="aes-op-${i}" style="padding:5px 10px;border-radius:5px;border:1px solid rgba(255,255,255,0.08);font-size:10px;color:var(--muted);transition:all 0.3s;">${s.name}</div>`).join('')}
                        </div>
                        <div id="aes-desc" style="color:var(--muted-2);font-size:11px;min-height:18px;"></div>
                        <div class="algo-controls" style="margin-top:8px;">
                            <button class="ctrl-btn" id="aes-step-btn">▶ Next Op</button>
                            <button class="ctrl-btn" id="aes-auto-btn">⏩ Auto-Run</button>
                            <button class="ctrl-btn" id="aes-reset-btn" style="opacity:0.6;">↺ Reset</button>
                        </div>
                        <div id="aes-result"></div>
                    </div>
                </div>`;

            function aesStep() {
                const ops = document.querySelectorAll('[id^="aes-op-"]');
                ops.forEach(o => o.style.cssText = 'padding:5px 10px;border-radius:5px;border:1px solid rgba(255,255,255,0.08);font-size:10px;color:var(--muted);transition:all 0.3s;');
                const op = roundSteps[rStep];
                const opEl = document.getElementById('aes-op-' + rStep);
                if (opEl) { opEl.style.background = op.color; opEl.style.color = '#fff'; opEl.style.borderColor = 'rgba(255,255,255,0.3)'; }
                document.getElementById('aes-grid').innerHTML = makeGrid(op.color);
                document.getElementById('aes-desc').textContent = op.desc;
                rStep = (rStep + 1) % 4;
                if (rStep === 0) {
                    rRound++;
                    document.getElementById('aes-round-num').textContent = rRound;
                    if (rRound >= 14) {
                        if (rTimer) { clearInterval(rTimer); rTimer = null; }
                        document.getElementById('aes-step-btn').disabled = true;
                        document.getElementById('aes-auto-btn').disabled = true;
                        document.getElementById('aes-result').innerHTML = `<div class="algo-success">✓ 14 rounds complete — Avalanche effect: 1 bit change diffuses to all 128 bits<br>→ Ciphertext: "${activePayload.substring(0,20)}…"</div>`;
                    }
                }
            }
            function aesReset() {
                rStep = 0; rRound = 0;
                if (rTimer) { clearInterval(rTimer); rTimer = null; }
                document.getElementById('aes-grid').innerHTML = makeGrid('rgba(255,255,255,0.06)');
                document.getElementById('aes-round-num').textContent = '0';
                document.getElementById('aes-desc').textContent = '';
                document.getElementById('aes-result').innerHTML = '';
                document.querySelectorAll('[id^="aes-op-"]').forEach(o => o.style.cssText = 'padding:5px 10px;border-radius:5px;border:1px solid rgba(255,255,255,0.08);font-size:10px;color:var(--muted);transition:all 0.3s;');
                document.getElementById('aes-step-btn').disabled = false;
                document.getElementById('aes-auto-btn').disabled = false;
            }
            document.getElementById('aes-step-btn').onclick = aesStep;
            document.getElementById('aes-auto-btn').onclick = () => {
                if (rTimer) return;
                document.getElementById('aes-step-btn').disabled = true;
                rTimer = setInterval(aesStep, 350);
            };
            document.getElementById('aes-reset-btn').onclick = aesReset;
            aesStep();
        }

        // ── Quantum computer view ────────────────────────────────────
        function renderQuantumComputer(container) {
            const N = 12;
            const aliceBits = Array.from({length:N}, () => Math.random()>0.5?1:0);
            const aliceBases = Array.from({length:N}, () => Math.random()>0.5?'+':'×');
            const eveBases = Array.from({length:N}, () => Math.random()>0.5?'+':'×');
            const bobBases = Array.from({length:N}, () => Math.random()>0.5?'+':'×');
            const photonSyms = {'+0':'↕','+1':'↔','×0':'↗','×1':'↘'};
            let step = -1;
            container.innerHTML = `
                <div class="algo-terminal anim-in">
                    ${algoHeader('BB84 QUANTUM CHANNEL SIMULATION', 'var(--purple-light)')}
                    <div class="algo-body">
                        <div id="q-stage-label" style="color:var(--muted);font-size:10px;letter-spacing:1.5px;margin-bottom:6px;">WAITING TO START…</div>
                        <div id="q-photon-display" style="display:flex;flex-direction:column;gap:6px;"></div>
                        <div class="algo-controls" style="margin-top:8px;">
                            <button class="ctrl-btn" id="q-step-btn">▶ Next Stage</button>
                            <button class="ctrl-btn" id="q-auto-btn">⏩ Auto-Run</button>
                        </div>
                        <div id="q-result"></div>
                    </div>
                </div>`;

            const stages = [
                () => {
                    document.getElementById('q-stage-label').textContent = 'STAGE 1 — Alice encodes bits as polarized photons';
                    document.getElementById('q-photon-display').innerHTML = `
                        <div style="font-size:10px;color:var(--muted);margin-bottom:4px;">BIT&nbsp;&nbsp;&nbsp;BASIS&nbsp;&nbsp;PHOTON</div>
                        <div class="photon-row">${aliceBits.map((b,i)=>`<div style="text-align:center;"><div style="font-size:9px;color:var(--muted);">${aliceBases[i]}</div><div class="photon-bit ${b?'photon-1':'photon-0'}">${photonSyms[aliceBases[i]+b]}</div><div style="font-size:9px;color:var(--muted);">${b}</div></div>`).join('')}</div>`;
                },
                () => {
                    document.getElementById('q-stage-label').textContent = 'STAGE 2 — Eve intercepts: measures in random bases';
                    const eveResults = aliceBits.map((b,i) => eveBases[i]===aliceBases[i]?b:Math.random()>0.5?1:0);
                    document.getElementById('q-photon-display').innerHTML += `
                        <div style="font-size:10px;color:var(--muted);margin:6px 0 2px;">EVE'S BASES</div>
                        <div class="photon-row">${eveResults.map((b,i)=>`<div style="text-align:center;"><div style="font-size:9px;color:${eveBases[i]===aliceBases[i]?'var(--green)':'var(--red)'};">${eveBases[i]}</div><div class="photon-bit ${b?'photon-1':'photon-0'} ${eveBases[i]===aliceBases[i]?'photon-match':'photon-mismatch'}">${photonSyms[eveBases[i]+b]}</div></div>`).join('')}</div>`;
                },
                () => {
                    document.getElementById('q-stage-label').textContent = 'STAGE 3 — Bob measures, compares bases with Alice';
                    const matches = aliceBases.map((a,i)=>a===bobBases[i]);
                    const errorRate = matches.filter((m,i)=>m&&eveBases[i]!==aliceBases[i]).length / matches.filter(m=>m).length;
                    document.getElementById('q-photon-display').innerHTML += `
                        <div style="font-size:10px;color:var(--muted);margin:6px 0 2px;">BOB'S BASES (matching Alice = shared key bit)</div>
                        <div class="photon-row">${aliceBits.map((b,i)=>`<div style="text-align:center;"><div style="font-size:9px;color:${matches[i]?'var(--green)':'var(--muted)'};">${bobBases[i]}</div><div class="photon-bit ${b?'photon-1':'photon-0'}" style="opacity:${matches[i]?1:0.3};">${matches[i]?b:'–'}</div></div>`).join('')}</div>
                        <div style="margin-top:8px;padding:8px;background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);border-radius:6px;font-size:11px;color:var(--red);">⚠ Eve's interception introduced ~${Math.round(errorRate*100)||22}% error rate — DETECTED</div>`;
                    document.getElementById('q-result').innerHTML = `<div class="algo-success" style="margin-top:8px;">✓ Simulation complete<br>Eve detected via error spike<br>→ Shared key bits: [${aliceBits.filter((_,i)=>aliceBases[i]===bobBases[i]).join('')}]</div>`;
                    document.getElementById('q-step-btn').disabled = true;
                    document.getElementById('q-auto-btn').disabled = true;
                }
            ];

            let qStep = 0, qTimer = null;
            function doQStage() { if (qStep < stages.length) stages[qStep++](); }
            document.getElementById('q-step-btn').onclick = doQStage;
            document.getElementById('q-auto-btn').onclick = () => {
                if (qTimer) return;
                document.getElementById('q-step-btn').disabled = true;
                qTimer = setInterval(() => { doQStage(); if (qStep >= stages.length) clearInterval(qTimer); }, 900);
            };
            doQStage();
        }

        // ═══════════════════════════════════════════════════════════
        //  DECRYPT TAB — MANUAL WALKTHROUGH VIEWS
        // ═══════════════════════════════════════════════════════════

        function renderCaesarManual(container) {
            container.innerHTML = `
                <div class="manual-terminal anim-in">
                    ${algoHeader('MANUAL DECRYPTION — CAESAR SHIFT', 'var(--purple-light)').replace('algo-terminal','manual-terminal').replace('algo-header','manual-header').replace('algo-title','manual-title')}
                    <div class="manual-body">
                        <div style="color:var(--muted);font-size:10px;">Try each reverse shift until the plaintext makes sense.</div>
                        <div>
                            <div style="color:var(--muted);font-size:10px;letter-spacing:1px;margin-bottom:4px;">REVERSE SHIFT: <span id="manual-shift-val" style="color:var(--blue-light);font-weight:800;">1</span></div>
                            <input type="range" id="manual-caesar-slider" min="1" max="25" value="1" style="margin-bottom:4px;">
                            <div id="manual-caesar-out" class="brute-out" style="font-size:12px;min-height:28px;padding:8px 12px;"></div>
                        </div>
                        <div class="step-box" style="margin-top:4px;">
                            <div class="step-title">Submit Answer</div>
                            <div class="prompt-line">
                                <span class="prompt-sym">$</span>
                                <span style="color:var(--muted-2);font-size:11px;">shift =</span>
                                <input type="number" id="manual-caesar-ans" class="step-input" min="1" max="25" placeholder="?">
                                <button class="check-btn" onclick="checkCaesarManual()">Execute</button>
                            </div>
                            <div id="manual-caesar-fb"></div>
                        </div>
                    </div>
                </div>`;
            const slider = document.getElementById('manual-caesar-slider');
            const out = document.getElementById('manual-caesar-out');
            const lbl = document.getElementById('manual-shift-val');
            function update() { const v = parseInt(slider.value); lbl.textContent = v; out.textContent = caesarShift(activePayload, v); }
            slider.oninput = update; update();
        }
        function checkCaesarManual() {
            const ans = parseInt(document.getElementById('manual-caesar-ans').value);
            const fb = document.getElementById('manual-caesar-fb');
            if (ans === parseInt(activeCipherKey)) fb.innerHTML = `<div class="fb-ok">✓ Correct! Shift = ${ans} → "${activeOriginal}"</div>`;
            else fb.innerHTML = `<div class="fb-err">✗ Shift ${ans} garbles the text. Keep searching.</div>`;
        }

        function renderHillManual(container) {
            if (!Array.isArray(activeCipherKey)) { container.innerHTML = `<div style="color:var(--muted);padding:16px;font-style:italic;">Key data unavailable.</div>`; return; }
            const K = activeCipherKey;
            let hs = { matrix: K, size: K.length, det: null, detInv: null };
            container.innerHTML = `
                <div class="manual-terminal anim-in">
                    ${algoHeader('MANUAL DECRYPTION — HILL MATRIX', 'var(--purple-light)').replace('algo-terminal','manual-terminal').replace('algo-header','manual-header').replace('algo-title','manual-title')}
                    <div class="manual-body">
                        <div style="color:var(--muted);font-size:10px;">Work through each mathematical step to invert the key matrix.</div>
                        <div class="mat-disp" style="margin-bottom:4px;">${printMat(K).replace(/ /g,'&nbsp;')}</div>
                        <div id="hill-manual-steps"></div>
                    </div>
                </div>`;
            renderHillManualStep1();
        }
        function renderHillManualStep1() {
            const K = activeCipherKey;
            const rawDet = matDet(K);
            const container = document.getElementById('hill-manual-steps');
            container.innerHTML = `<div class="step-box anim-in">
                <div class="step-title">Step 1 — Compute det(K) mod 26</div>
                <div style="color:var(--muted-2);font-size:11px;margin-bottom:8px;">${K.length===2?`Formula: (${K[0][0]}×${K[1][1]}) − (${K[0][1]}×${K[1][0]}) = ${rawDet}. Now take mod 26.`:'Compute determinant, then take mod 26.'}</div>
                <div class="prompt-line">
                    <span class="prompt-sym">$</span>
                    <span style="color:var(--muted-2);font-size:11px;">det(K) mod 26 =</span>
                    <input type="number" id="hm-inp1" class="step-input" placeholder="?">
                    <button class="check-btn" onclick="checkHillManual1()">Check</button>
                </div>
                <div id="hm-fb1"></div>
            </div>`;
        }
        function checkHillManual1() {
            const K = activeCipherKey;
            const correct = mod26(matDet(K));
            const user = parseInt(document.getElementById('hm-inp1').value);
            if (user === correct) {
                document.getElementById('hm-fb1').innerHTML = `<div class="fb-ok">✓ det ≡ ${correct} (mod 26)</div>`;
                document.getElementById('hm-inp1').disabled = true;
                document.getElementById('hill-manual-steps').innerHTML += `<div class="step-box anim-in">
                    <div class="step-title">Step 2 — Modular Inverse: find X where (${correct}×X) mod 26 = 1</div>
                    <div class="prompt-line">
                        <span class="prompt-sym">$</span>
                        <span style="color:var(--muted-2);font-size:11px;">X =</span>
                        <input type="number" id="hm-inp2" class="step-input" placeholder="?">
                        <button class="check-btn" onclick="checkHillManual2(${correct})">Check</button>
                    </div>
                    <div id="hm-fb2"></div>
                </div>`;
            } else document.getElementById('hm-fb1').innerHTML = `<div class="fb-err">✗ Got ${user}, expected value in 0–25 range.</div>`;
        }
        function checkHillManual2(det) {
            const correct = modInverse26(det);
            const user = parseInt(document.getElementById('hm-inp2').value);
            if (user === correct) {
                const K = activeCipherKey;
                const adj = matAdj(K);
                const invM = adj.map(r => r.map(v => mod26(v * correct)));
                document.getElementById('hm-fb2').innerHTML = `<div class="fb-ok">✓ det⁻¹ = ${correct}  (${det}×${correct}=${det*correct} mod 26=1)</div>`;
                document.getElementById('hm-inp2').disabled = true;
                document.getElementById('hill-manual-steps').innerHTML += `<div class="step-box anim-in" style="border-color:rgba(16,185,129,0.3);">
                    <div class="step-title" style="color:var(--green-light);">Steps 3–5 — Adjugate → K⁻¹ → Decrypt</div>
                    <div style="color:var(--muted);font-size:10px;margin-bottom:4px;">K⁻¹ = ${correct} × adj(K) mod 26:</div>
                    <div class="mat-disp" style="color:var(--green-light);">${printMat(invM).replace(/ /g,'&nbsp;')}</div>
                    <div class="algo-success" style="margin-top:8px;">✓ PLAINTEXT: "${activeOriginal}"</div>
                </div>`;
            } else document.getElementById('hm-fb2').innerHTML = `<div class="fb-err">✗ (${det}×${user}) mod 26 = ${(det*user)%26} ≠ 1</div>`;
        }

        function renderVigenereManual(container) {
            const key = String(activeCipherKey).toUpperCase();
            const ct = activePayload.toUpperCase().replace(/[^A-Z]/g,'');
            const tri = {};
            for (let i = 0; i <= ct.length-3; i++) { const s = ct.substr(i,3); if (!tri[s]) tri[s]=[]; tri[s].push(i); }
            const reps = Object.entries(tri).filter(([,v])=>v.length>1);
            container.innerHTML = `
                <div class="manual-terminal anim-in">
                    ${algoHeader('MANUAL DECRYPTION — VIGENÈRE', 'var(--purple-light)').replace('algo-terminal','manual-terminal').replace('algo-header','manual-header').replace('algo-title','manual-title')}
                    <div class="manual-body">
                        <div class="step-box">
                            <div class="step-title">Step 1 — Kasiski: Find key length</div>
                            ${reps.length ? `<div style="color:var(--muted-2);font-size:11px;">Trigram <span style="color:var(--blue-light);">"${reps[0][0]}"</span> repeats at [${reps[0][1].join(', ')}]<br>Gap = ${reps[0][1][1]-reps[0][1][0]} → factors include key length</div>` : `<div style="color:var(--muted-2);font-size:11px;">Text too short for Kasiski. Estimate key length by other means.</div>`}
                            <div class="prompt-line" style="margin-top:8px;">
                                <span class="prompt-sym">$</span><span style="color:var(--muted-2);font-size:11px;">key_length =</span>
                                <input type="number" id="vm-inp1" class="step-input" placeholder="?">
                                <button class="check-btn" onclick="checkVigManual1()">Check</button>
                            </div>
                            <div id="vm-fb1"></div>
                        </div>
                        <div id="vig-manual-step2" style="display:none;">
                            <div class="step-box anim-in">
                                <div class="step-title">Step 2 — Enter the decoded keyword</div>
                                <div style="color:var(--muted-2);font-size:11px;margin-bottom:8px;">Frequency-analyze each column (most frequent letter → shift → key letter)</div>
                                <div class="prompt-line">
                                    <span class="prompt-sym">$</span><span style="color:var(--muted-2);font-size:11px;">keyword =</span>
                                    <input type="text" id="vm-inp2" class="prompt-input" placeholder="TYPE KEY…" style="text-transform:uppercase;width:90px;">
                                    <button class="check-btn" onclick="checkVigManual2()">Decrypt</button>
                                </div>
                                <div id="vm-fb2"></div>
                            </div>
                        </div>
                    </div>
                </div>`;
        }
        function checkVigManual1() {
            const key = String(activeCipherKey).toUpperCase();
            const user = parseInt(document.getElementById('vm-inp1').value);
            if (user === key.length) {
                document.getElementById('vm-fb1').innerHTML = `<div class="fb-ok">✓ Key length = ${key.length}</div>`;
                document.getElementById('vm-inp1').disabled = true;
                document.getElementById('vig-manual-step2').style.display = 'block';
            } else document.getElementById('vm-fb1').innerHTML = `<div class="fb-err">✗ Incorrect length.</div>`;
        }
        function checkVigManual2() {
            const key = String(activeCipherKey).toUpperCase();
            const user = document.getElementById('vm-inp2').value.toUpperCase();
            if (user === key) document.getElementById('vm-fb2').innerHTML = `<div class="fb-ok">✓ Key: "${key}" → PLAINTEXT: "${activeOriginal}"</div>`;
            else document.getElementById('vm-fb2').innerHTML = `<div class="fb-err">✗ Wrong keyword.</div>`;
        }

        function renderAesManual(container) {
            container.innerHTML = `
                <div class="manual-terminal anim-in">
                    ${algoHeader('AES-256 — MANUAL NOTE', 'var(--purple-light)').replace('algo-terminal','manual-terminal').replace('algo-header','manual-header').replace('algo-title','manual-title')}
                    <div class="manual-body">
                        <div style="color:var(--muted-2);font-size:12px;line-height:1.8;">
                            AES-256 has no practical manual decryption path — it is designed to be computationally infeasible without the key.<br><br>
                            <span style="color:var(--blue-light);">Best approach:</span> Use the Algorithm view to observe how each round transforms the state, or check the Guide tab for the full mathematical breakdown.
                        </div>
                        <a href="https://www.nist.gov/publications/advanced-encryption-standard-aes" target="_blank" class="calc-link">→ NIST AES Specification</a>
                    </div>
                </div>`;
        }

        function renderQuantumManual(container) {
            let score = 0, attempts = 0;
            container.innerHTML = `
                <div class="manual-terminal anim-in">
                    ${algoHeader('BB84 — INTERACTIVE EAVESDROP', 'var(--purple-light)').replace('algo-terminal','manual-terminal').replace('algo-header','manual-header').replace('algo-title','manual-title')}
                    <div class="manual-body">
                        <div style="color:var(--muted-2);font-size:11px;line-height:1.7;">A photon is sent in a random basis. Choose your measurement basis. Wrong choice = state collapse = detected.</div>
                        <div style="margin:10px 0;padding:10px;background:rgba(0,0,0,0.3);border-radius:6px;border:1px solid var(--border);text-align:center;">
                            <div style="font-size:28px;margin-bottom:6px;" id="q-photon-show">?</div>
                            <div style="color:var(--muted);font-size:10px;">Incoming photon polarization (basis unknown)</div>
                        </div>
                        <div style="display:flex;gap:8px;">
                            <button class="ctrl-btn" style="flex:1;padding:12px;" onclick="qManualGuess('+')">+ Rectilinear</button>
                            <button class="ctrl-btn" style="flex:1;padding:12px;" onclick="qManualGuess('x')">× Diagonal</button>
                        </div>
                        <div id="q-manual-fb" style="margin-top:8px;"></div>
                        <div style="color:var(--muted);font-size:10px;margin-top:6px;">Attempts: <span id="q-attempts">0</span> | Correct: <span id="q-score">0</span></div>
                    </div>
                </div>`;
            window._qManualScore = 0; window._qManualAttempts = 0;
            const symbols = ['↕','↔','↗','↘'];
            document.getElementById('q-photon-show').textContent = symbols[Math.floor(Math.random()*4)];
        }
        function qManualGuess(basis) {
            window._qManualAttempts = (window._qManualAttempts||0)+1;
            const hit = Math.random() > 0.5;
            if (hit) { window._qManualScore = (window._qManualScore||0)+1; document.getElementById('q-manual-fb').innerHTML = `<div class="fb-ok">✓ Basis matched! Bit intercepted undetected.</div>`; }
            else document.getElementById('q-manual-fb').innerHTML = `<div class="fb-err">✗ Wrong basis — photon collapsed. Error rate spiked. Alice & Bob will notice ~25% error.</div>`;
            document.getElementById('q-attempts').textContent = window._qManualAttempts;
            document.getElementById('q-score').textContent = window._qManualScore;
            const symbols = ['↕','↔','↗','↘'];
            document.getElementById('q-photon-show').textContent = symbols[Math.floor(Math.random()*4)];
        }

        // ═══════════════════════════════════════════════════════════
        //  Main: initialize decrypt tools (auto, no button needed)
        // ═══════════════════════════════════════════════════════════
        function initDecryptTools(cipher) {
            const cv = document.getElementById('computer-view-content');
            const mv = document.getElementById('manual-view-content');
            cv.innerHTML = '';
            mv.innerHTML = '';
            if (cipher === 'caesar') { renderCaesarComputer(cv); renderCaesarManual(mv); }
            else if (cipher === 'hill') { renderHillComputer(cv); renderHillManual(mv); }
            else if (cipher === 'vigenere') { renderVigenereComputer(cv); renderVigenereManual(mv); }
            else if (cipher === 'aes') { renderAesComputer(cv); renderAesManual(mv); }
            else if (cipher === 'quantum') { renderQuantumComputer(cv); renderQuantumManual(mv); }
            // Always start in computer mode
            setDecryptMode('computer');
        }

        // ═══════════════════════════════════════════════════════════
        //  Message selection — auto-init, switch to Guide tab first
        // ═══════════════════════════════════════════════════════════
        function selectMessage(id, user, msg, orig, cipher, key) {
            if (selectedMsgId) document.getElementById('msg-content-' + selectedMsgId)?.classList.remove('selected');
            selectedMsgId = id;
            document.getElementById('msg-content-' + id)?.classList.add('selected');
            activePayload = msg; activeOriginal = orig || msg; activeCipherKey = key; activeCipherType = cipher;

            document.getElementById('sel-placeholder').style.display = 'none';
            document.getElementById('sel-details').style.display = 'flex';
            document.getElementById('sel-payload').textContent = msg;

            ['tool-container-none','tool-container-active','sol-none','sol-dynamic','hist-none'].forEach(eid => {
                const el = document.getElementById(eid); if (el) el.style.display = 'none';
            });
            document.querySelectorAll('.history-block').forEach(e => e.style.display = 'none');

            if (cipher !== 'system' && cipher !== 'none') {
                document.getElementById('tool-container-active').style.display = 'flex';
                document.getElementById('sol-dynamic').style.display = 'block';

                // Populate Guide tab
                document.getElementById('dyn-plain-2').textContent = activeOriginal;
                document.getElementById('dyn-enc-explanation').innerHTML = getCipherExpl(cipher, key, false);
                document.getElementById('dyn-dec-explanation').innerHTML = getCipherExpl(cipher, key, true);
                document.getElementById('dyn-enc-steps').innerHTML = encTable(activeOriginal, msg, cipher, key);
                document.getElementById('dyn-dec-steps').innerHTML = decTable(activeOriginal, msg, cipher, key);

                const toolMap = {
                    caesar: ['hist-caesar', '<strong>Linear Shift Analysis:</strong> Only 25 keys — trivially brute-forced by testing all reverse shifts.'],
                    hill:   ['hist-hill',    '<strong>Known-Plaintext Attack:</strong> The Hill cipher is linear; one n²-char plaintext–ciphertext pair reveals K via Gaussian elimination over Z₂₆.'],
                    aes:    ['hist-aes',     '<strong>None (Computationally Secure):</strong> AES-256 has no known practical attacks. The Algorithm view shows per-round diffusion.'],
                    vigenere:['hist-vigenere','<strong>Kasiski + Frequency Analysis:</strong> Repeated trigrams reveal key length; each column is then a simple Caesar shift.'],
                    quantum: ['hist-quantum', '<strong>Quantum Channel Attack:</strong> Measuring a photon in the wrong basis collapses its state, introducing ~25% error — detected by Alice and Bob.'],
                };
                if (toolMap[cipher]) {
                    document.getElementById(toolMap[cipher][0]).style.display = 'block';
                    document.getElementById('dyn-tool').innerHTML = toolMap[cipher][1];
                }

                // Auto-initialize decrypt tools (no button press needed)
                initDecryptTools(cipher);

            } else {
                document.getElementById('tool-container-none').style.display = 'block';
                document.getElementById('sol-none').style.display = 'block';
                document.getElementById('hist-none').style.display = 'block';
            }

            // Always open to Guide tab first
            switchTab('guide');
        }

        function clearSel() {
            selectedMsgId = null;
            document.getElementById('sel-placeholder').style.display = 'block';
            document.getElementById('sel-details').style.display = 'none';
        }

        // ── Cipher selector ──────────────────────────────────────────
        selBox.addEventListener('change', function() {
            cipherText.textContent = selBox.options[selBox.selectedIndex].text;
            document.getElementById('no-cipher-msg').style.display = 'none';
            caesarCtrl.style.display = hillCtrl.style.display = textKeyCtrl.style.display = 'none';
            if (selBox.value === 'caesar') caesarCtrl.style.display = 'flex';
            else if (selBox.value === 'hill') hillCtrl.style.display = 'flex';
            else if (['aes','vigenere','quantum'].includes(selBox.value)) textKeyCtrl.style.display = 'flex';
            else document.getElementById('no-cipher-msg').style.display = 'block';
        });
        caesarSlider.addEventListener('input', function() {
            const v = parseInt(this.value);
            shiftBadge.textContent = v;
            this.style.setProperty('--fp', ((v-1)/24*100).toFixed(1)+'%');
            exShift.textContent = ['A','B','C','D','E'].map(c => { let n = c.charCodeAt(0)+v; if(n>90)n-=26; return String.fromCharCode(n); }).join(' ');
        });
        caesarSlider.style.setProperty('--fp','0%');
    </script>
    {% endif %}
</body>
</html>
"""

# ── Routes ───────────────────────────────────────────────────────────────────
@app.route('/')
def home(): return render_template_string(HTML_TEMPLATE, page='home')
@app.route('/classroom')
def classroom(): return render_template_string(HTML_TEMPLATE, page='home')
@app.route('/lab')
def lab(): return render_template_string(HTML_TEMPLATE, page='home')
@app.route('/local')
def local(): return render_template_string(HTML_TEMPLATE, page='local', active_usernames=active_usernames)
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
    code = request.form.get('room_code', '').upper()
    if code in active_rooms:
        session['room'] = code
        return render_template_string(HTML_TEMPLATE, page='chat', room_code=code, current_user=session['username'])
    return redirect(url_for('local'))
@app.route('/leave')
def leave_server():
    room = session.get('room')
    username = session.get('username')
    session.pop('room', None)
    if room and room in active_rooms and username:
        sys_msg = {'id': str(uuid.uuid4()), 'type': 'msg-system',
                   'msg': f'[SYSTEM] {username} disconnected.',
                   'reactions': {}, 'cipher': 'system', 'key': 0}
        active_rooms[room]['messages'].append(sys_msg)
        socketio.send(sys_msg, to=room)
    return redirect(url_for('local'))
@app.route('/api/usernames')
def get_usernames(): return jsonify(active_usernames)

# ── Socket events ─────────────────────────────────────────────────────────────
@socketio.on('join')
def on_join(data):
    room = data['room']
    username = session.get('username', 'Guest')
    join_room(room)
    if room in active_rooms:
        emit('chat_history', active_rooms[room]['messages'], to=request.sid)
    sys_msg = {'id': str(uuid.uuid4()), 'type': 'msg-system',
               'msg': f'[SYSTEM] {username} has joined Room {room}.',
               'reactions': {}, 'cipher': 'system', 'key': 0}
    if room in active_rooms:
        active_rooms[room]['messages'].append(sys_msg)
    send(sys_msg, to=room)

@socketio.on('message')
def handle_message(data):
    room = data['room']
    msg = data['msg']
    enc_type = data['encryption']
    enc_value = data.get('encryption-value')
    username = session.get('username', 'Guest')
    if enc_type != 'none':
        try:
            encrypted = encryption_manager.encrypt(enc_type, msg.encode('utf-8'), enc_value).decode('utf-8')
        except Exception as e:
            encrypted = f'[ENCRYPTION ERROR: {e}]'
    else:
        encrypted = msg
    payload = {'id': str(uuid.uuid4()), 'username': username,
               'msg': encrypted, 'original_msg': msg,
               'type': 'msg-user', 'reactions': {},
               'cipher': enc_type, 'key': enc_value}
    if room in active_rooms:
        active_rooms[room]['messages'].append(payload)
    send(payload, to=room)

@socketio.on('react_message')
def handle_reaction(data):
    room, msg_id, emoji = data['room'], data['id'], data['emoji']
    username = session.get('username')
    if room in active_rooms:
        for msg in active_rooms[room]['messages']:
            if msg.get('id') == msg_id:
                if emoji not in msg['reactions']: msg['reactions'][emoji] = []
                if username in msg['reactions'][emoji]: msg['reactions'][emoji].remove(username)
                else: msg['reactions'][emoji].append(username)
                emit('reactions_updated', {'id': msg_id, 'reactions': msg['reactions']}, to=room)
                break

@socketio.on('delete_message')
def handle_delete(data):
    room, msg_id = data['room'], data['id']
    username = session.get('username')
    if room in active_rooms:
        for msg in active_rooms[room]['messages']:
            if msg.get('id') == msg_id and msg.get('username') == username:
                active_rooms[room]['messages'] = [x for x in active_rooms[room]['messages'] if x.get('id') != msg_id]
                emit('message_deleted', {'id': msg_id}, to=room)
                break

@socketio.on('disconnect')
def on_disconnect():
    username = session.get('username', 'Someone')
    if username in active_usernames:
        active_usernames.remove(username)

# ── Runner ────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    threading.Timer(1.25, lambda: webbrowser.open("http://127.0.0.1:67667")).start()
    socketio.run(app, host='0.0.0.0', port=67667, debug=True, allow_unsafe_werkzeug=True)