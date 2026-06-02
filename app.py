from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
from flask_socketio import SocketIO, join_room, leave_room, send, emit
import threading
import webbrowser
import uuid
from crypto import manager
from room_manager import RoomManager
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'insightful_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")
encryption_manager = manager.CryptoManager()
rm = RoomManager()
socket_users = {}

@app.route('/favicon.ico')
def favicon():
   
    target_dir = os.path.join(app.root_path, '..', 'static')
    
    return send_from_directory(
        target_dir,
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )

# -- Routes -------------------------------------------------------------------
@app.route('/')
def home(): 
    return render_template('home.html', page='home')

@app.route('/classroom')
def classroom(): 
    return render_template('home.html', page='home')

@app.route('/lab')
def lab(): 
    return render_template('home.html', page='home')

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
        is_host = rm.is_host(code, session['username'])
        return render_template('chat.html', page='chat', room_code=code, current_user=session['username'], is_host=is_host)
    return redirect(url_for('local'))

@app.route('/leave')
def leave_server():
    room = session.get('room')
    username = session.get('username')
    session.pop('room', None)
    if room and username:
        sys_msg = {'id': str(uuid.uuid4()), 'type': 'msg-system',
                   'msg': f'[SYSTEM] {username} disconnected.',
                   'reactions': {}, 'cipher': 'system', 'key': 0}
        rm.add_message(room, sys_msg)
        socketio.send(sys_msg, to=room)
    return redirect(url_for('local'))

@app.route('/api/usernames')
def get_usernames(): 
    return jsonify(rm.active_usernames)

# -- Socket events -------------------------------------------------------------
@socketio.on('join')
def on_join(data):
    room = data['room']
    username = session.get('username', 'Guest')
    socket_users[request.sid] = username
    join_room(room)
    emit('chat_history', rm.get_messages(room), to=request.sid)
    
    # Provide late-joiners with current restrictions if applied
    room_state = rm.active_rooms.get(room, {})
    if room_state.get('forced_cipher'):
        emit('cipher_forced', {'cipher': room_state['forced_cipher']}, to=request.sid)

    sys_msg = {'id': str(uuid.uuid4()), 'type': 'msg-system',
               'msg': f'[SYSTEM] {username} has joined Room {room}.',
               'reactions': {}, 'cipher': 'system', 'key': 0}
    rm.add_message(room, sys_msg)
    send(sys_msg, to=room)

@socketio.on('message')
def handle_message(data):
    room = data['room']
    msg = data['msg']
    enc_type = data['encryption']
    enc_value = data.get('encryption-value')
    username = socket_users.get(request.sid, session.get('username', 'Guest'))
    
    if not rm.can_send_message(room, username):
        emit('system_alert', {'msg': 'You are currently muted and cannot send messages.'}, to=request.sid)
        return
        
    is_bold = data.get('is_bold', False) if rm.is_host(room, username) else False
    
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
               'cipher': enc_type, 'key': enc_value, 'is_bold': is_bold}
               
    rm.add_message(room, payload)
    send(payload, to=room)

@socketio.on('host_action')
def handle_host_action(data):
    room = data['room']
    action = data['action']
    username = session.get('username')
    
    # Master validation
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
        
        #made it so the flask session is also updating the usernames so it shows on the front end
        if session.get('username') == target:
            session['username'] = new_name        
        emit('user_renamed', {'old_name': target, 'new_name': new_name}, to=room)


@socketio.on('update_my_session_name')
def handle_session_update(data):
    #think of this like updating the user catch ig
    if 'new_name' in data:
        socket_users[request.sid] = data['new_name']

@socketio.on('react_message')
def handle_reaction(data):
    room, msg_id, emoji = data['room'], data['id'], data['emoji']
    username = session.get('username')
    
    messages = rm.get_messages(room)
    for msg in messages:
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
    
    messages = rm.get_messages(room)
    for msg in messages:
        if msg.get('id') == msg_id:
            # PERMISSION CHECK utilizing the RoomManager (Hosts can inherently bypass this loop rule)
            if rm.can_delete_message(room, username, msg.get('username')):
                rm.remove_message(room, msg_id)
                emit('message_deleted', {'id': msg_id}, to=room)
            break

@socketio.on('disconnect')
def on_disconnect():
    username = session.get('username')
    if username:
        rm.remove_user(username)

# -- Runner --------------------------------------------------------------------
if __name__ == '__main__':
    #threading.Timer(1.25, lambda: webbrowser.open("http://127.0.0.1:6000")).start()
    socketio.run(app, host='0.0.0.0', port=6000, debug=True, allow_unsafe_werkzeug=True)