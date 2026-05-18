import random
import string

class RoomManager:
    def __init__(self):
        # Stores room state: { 'CODE': {'host': 'username', 'messages': [], 'users': [], 'forced_cipher': '', 'global_mute': False, 'muted_users': []} }
        self.active_rooms = {}
        self.active_usernames = []

    def generate_room_code(self):
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            if code not in self.active_rooms:
                return code

    def host_room(self, username):
        code = self.generate_room_code()
        self.active_rooms[code] = {
            'host': username,
            'messages': [],
            'users': [username],
            'forced_cipher': '',
            'global_mute': False,
            'muted_users': []
        }
        if username not in self.active_usernames:
            self.active_usernames.append(username)
        return code

    def join_room(self, code, username):
        if code in self.active_rooms:
            if username not in self.active_usernames:
                self.active_usernames.append(username)
            if username not in self.active_rooms[code]['users']:
                self.active_rooms[code]['users'].append(username)
            return True
        return False

    def is_host(self, code, username):
        room = self.active_rooms.get(code)
        if room:
            return room.get('host') == username
        return False

    def can_delete_message(self, code, action_user, message_owner):
        """
        Permissions: 
        - The Host can delete ANY message.
        - Regular users can only delete their OWN messages.
        """
        if self.is_host(code, action_user):
            return True
        return action_user == message_owner

    def get_messages(self, code):
        room = self.active_rooms.get(code)
        return room['messages'] if room else []

    def add_message(self, code, payload):
        if code in self.active_rooms:
            self.active_rooms[code]['messages'].append(payload)

    def remove_message(self, code, msg_id):
        if code in self.active_rooms:
            self.active_rooms[code]['messages'] = [
                x for x in self.active_rooms[code]['messages'] if x.get('id') != msg_id
            ]

    def remove_user(self, username):
        if username in self.active_usernames:
            self.active_usernames.remove(username)
        for room in self.active_rooms.values():
            if 'users' in room and username in room['users']:
                room['users'].remove(username)

    def can_send_message(self, code, username):
        room = self.active_rooms.get(code)
        if not room: return False
        if room['host'] == username: return True
        if room.get('global_mute', False): return False
        if username in room.get('muted_users', []): return False
        return True

    def set_forced_cipher(self, code, cipher):
        if code in self.active_rooms:
            self.active_rooms[code]['forced_cipher'] = cipher

    def toggle_global_mute(self, code):
        if code in self.active_rooms:
            self.active_rooms[code]['global_mute'] = not self.active_rooms[code].get('global_mute', False)
            return self.active_rooms[code]['global_mute']
        return False

    def toggle_user_mute(self, code, target_user):
        if code in self.active_rooms:
            muted = self.active_rooms[code].get('muted_users', [])
            if target_user in muted:
                muted.remove(target_user)
                return False
            else:
                muted.append(target_user)
                return True
        return False

    def rename_user(self, code, old_name, new_name):
        if old_name in self.active_usernames:
            self.active_usernames.remove(old_name)
        if new_name not in self.active_usernames:
            self.active_usernames.append(new_name)
        
        if code in self.active_rooms:
            room = self.active_rooms[code]
            if old_name in room.get('users', []):
                room['users'].remove(old_name)
                room['users'].append(new_name)
            if old_name in room.get('muted_users', []):
                room['muted_users'].remove(old_name)
                room['muted_users'].append(new_name)
            
            # Auto-update if the host renamed themselves
            if room.get('host') == old_name:
                room['host'] = new_name