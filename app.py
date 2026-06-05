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
        
        # We removed the flawed session update here. 
        # The host cannot update the target's session cookie directly.
        emit('user_renamed', {'old_name': target, 'new_name': new_name}, to=room)


@socketio.on('update_my_session_name')
def handle_session_update(data):
    if 'new_name' in data:
        new_name = data['new_name']
        # Update the active socket user mapping
        socket_users[request.sid] = new_name
        # CRITICAL FIX: Update the actual Flask HTTP session for the specific user who fired this event
        session['username'] = new_name