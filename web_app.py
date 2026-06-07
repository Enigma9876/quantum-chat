from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_socketio import SocketIO, join_room, leave_room, send, emit
from room_manager import RoomManager
import threading
import webbrowser
import uuid
from crypto import manager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'insightful_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")
encryption_manager = manager.CryptoManager()
rm = RoomManager()

# Track socket SID to username mapping
socket_users = {}

# -- Routes -------------------------------------------------------------------
@app.route('/')
def home(): 
    return render_template('home.html', page='home')

@app.route('/lab')
def lab(): 
    return render_template('lab.html', page='lab')

@app.route('/local')
def local(): 
    return render_template('local.html', page='local', active_usernames=rm.active_usernames)

@app.route('/host', methods=['POST'])
def host_server():
    session['username'] = request.form.get('username')
    code = rm.host_room(session['username'])
    session['room'] = code
    return render_template('chat.html', page='chat', room_code=code, current_user=session['username'], is_host=True)

@app.route('/join', methods=['POST'])
def join_server():
    session['username'] = request.form.get('username')
    code = request.form.get('room_code', '').upper()
    if rm.join_room(code, session['username']):
        session['room'] = code
        return render_template('chat.html', page='chat', room_code=code, current_user=session['username'], is_host=False)
    return redirect(url_for('local'))

@app.route('/leave')
def leave_server():
    room = session.get('room')
    username = session.get('username')
    session.pop('room', None)
    if room and room in rm.active_rooms and username:
        sys_msg = {'id': str(uuid.uuid4()), 'type': 'msg-system',
                   'msg': f'[SYSTEM] {username} disconnected.',
                   'reactions': {}, 'cipher': 'system', 'key': 0}
        rm.add_message(room, sys_msg)
        socketio.send(sys_msg, to=room)
    if username:
        rm.remove_user(username)
    return redirect(url_for('local'))

@app.route('/api/usernames')
def get_usernames(): 
    return jsonify(rm.active_usernames)

@app.route('/api/lab/encrypt', methods=['POST'])
def lab_encrypt():
    data = request.get_json()
    alg = data.get('algorithm', 'none')
    plaintext = data.get('plaintext', '')
    key = data.get('key')
    if alg == 'none':
        return jsonify({'ciphertext': plaintext})
    try:
        # Normalize AES key to exactly 16 bytes (pad or truncate)
        if alg == 'aes' and isinstance(key, str):
            key_bytes = key.encode('utf-8')
            key_bytes = (key_bytes + b'\x00' * 16)[:16]
            key = key_bytes
        result = encryption_manager.encrypt(alg, plaintext.encode('utf-8'), key)
        return jsonify({'ciphertext': result.decode('utf-8')})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/lab/decrypt', methods=['POST'])
def lab_decrypt():
    data = request.get_json()
    alg = data.get('algorithm', 'none')
    ciphertext = data.get('ciphertext', '')
    key = data.get('key')
    meta = data.get('meta', {})
    if alg == 'none':
        return jsonify({'plaintext': ciphertext})
    try:
        # Normalize AES key to exactly 16 bytes (pad or truncate)
        if alg == 'aes' and isinstance(key, str):
            key_bytes = key.encode('utf-8')
            key_bytes = (key_bytes + b'\x00' * 16)[:16]
            key = key_bytes
        result = encryption_manager.decrypt(alg, ciphertext.encode('utf-8'), key, meta)
        return jsonify({'plaintext': result.decode('utf-8')})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# -- Socket events -------------------------------------------------------------
@socketio.on('connect')
def on_connect():
    username = session.get('username', 'Guest')
    socket_users[request.sid] = username

@socketio.on('join')
def on_join(data):
    room = data['room']
    username = session.get('username', 'Guest')
    join_room(room)
    if room in rm.active_rooms:
        emit('chat_history', rm.get_messages(room), to=request.sid)
    sys_msg = {'id': str(uuid.uuid4()), 'type': 'msg-system',
               'msg': f'[SYSTEM] {username} has joined Room {room}.',
               'reactions': {}, 'cipher': 'system', 'key': 0}
    if room in rm.active_rooms:
        rm.add_message(room, sys_msg)
    send(sys_msg, to=room)

@socketio.on('message')
def handle_message(data):
    room = data['room']
    msg = data['msg']
    enc_type = data['encryption']
    enc_value = data.get('encryption-value')
    username = session.get('username', 'Guest')
    if not rm.can_send_message(room, username):
        return
    if enc_type != 'none':
        try:
            # Normalize AES key to exactly 16 bytes
            if enc_type == 'aes' and isinstance(enc_value, str):
                enc_value = (enc_value.encode('utf-8') + b'\x00' * 16)[:16]
            encrypted = encryption_manager.encrypt(enc_type, msg.encode('utf-8'), enc_value).decode('utf-8')
        except Exception as e:
            encrypted = f'[ENCRYPTION ERROR: {e}]'
    else:
        encrypted = msg
    payload = {'id': str(uuid.uuid4()), 'username': username,
               'msg': encrypted, 'original_msg': msg,
               'type': 'msg-user', 'reactions': {},
               'cipher': enc_type, 'key': enc_value,
               'is_bold': data.get('is_bold', False)}
    rm.add_message(room, payload)
    send(payload, to=room)

@socketio.on('react_message')
def handle_reaction(data):
    room, msg_id, emoji = data['room'], data['id'], data['emoji']
    username = session.get('username')
    if room in rm.active_rooms:
        for msg in rm.active_rooms[room]['messages']:
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
    if room in rm.active_rooms:
        for msg in rm.active_rooms[room]['messages']:
            if msg.get('id') == msg_id and rm.can_delete_message(room, username, msg.get('username')):
                rm.remove_message(room, msg_id)
                emit('message_deleted', {'id': msg_id}, to=room)
                break

@socketio.on('disconnect')
def on_disconnect():
    username = session.get('username', 'Someone')
    rm.remove_user(username)
    socket_users.pop(request.sid, None)

@socketio.on('host_action')
def handle_host_action(data):
    room = data['room']
    action = data['action']
    username = session.get('username')
    if not rm.is_host(room, username):
        return
    if action == 'force_cipher':
        cipher = data['cipher']
        rm.set_forced_cipher(room, cipher)
        emit('cipher_forced', {'cipher': cipher}, to=room)
    elif action == 'toggle_global_mute':
        state = rm.toggle_global_mute(room)
        emit('system_alert', {'msg': f'Global mute is now {"ON" if state else "OFF"}.'}, to=room)
    elif action == 'toggle_user_mute':
        target = data['target']
        state = rm.toggle_user_mute(room, target)
        emit('system_alert', {'msg': f'{target} has been {"muted" if state else "unmuted"}.'}, to=room)
    elif action == 'kick':
        target = data['target']
        rm.remove_user(target)
        emit('user_kicked', {'target': target}, to=room)
    elif action == 'rename':
        target = data['target']
        new_name = data['new_name']
        if not target or not new_name:
            return
        rm.rename_user(room, target, new_name)
        emit('user_renamed', {'old_name': target, 'new_name': new_name}, to=room)

@socketio.on('update_my_session_name')
def handle_session_update(data):
    if 'new_name' in data:
        new_name = data['new_name']
        socket_users[request.sid] = new_name
        session['username'] = new_name

# -- Runner --------------------------------------------------------------------
if __name__ == '__main__':
    threading.Timer(1.25, lambda: webbrowser.open("http://127.0.0.1:6000")).start()
    socketio.run(app, host='0.0.0.0', port=6000, debug=True, allow_unsafe_werkzeug=True)