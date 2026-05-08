import random
import string

class RoomManager:
    def __init__(self):
        # Stores room state: { 'CODE': {'host': 'username', 'messages': []} }
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
            'messages': []
        }
        if username not in self.active_usernames:
            self.active_usernames.append(username)
        return code

    def join_room(self, code, username):
        if code in self.active_rooms:
            if username not in self.active_usernames:
                self.active_usernames.append(username)
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