import sys

class CaesarCipher:
    id = "caesar"
    

    #the main logic of it all
    def _shift_char(self, char: str, shift: int) -> str:
        if not char.isalpha():
            return char
        
        start = ord('A') if char.isupper() else ord('a')

        #in english: (char Code - start + shift) mod 26 + start
        return chr((ord(char) - start + shift) % 26 + start)
    

    #Encrypts the plaintext using the Caesar cipher logic that was made in _shift_char.
    #It takes the plaintext, decodes it to a string, applies the shift to each character, and then encodes it back to bytes.
    def encrypt(self, plaintext: bytes, key: int, **kwargs) -> bytes:
        text = plaintext.decode('utf-8')

        encrypted_char = [self._shift_char(c, key) for c in text]
        ciphertext = ''.join(encrypted_char)

        return ciphertext.encode('utf-8')
    

    #i am smarter then ai rahhh
    #it wanted me to write a decrypt function but the logic is the same as encrypt just with a negative shift so here we are
    def decrypt(self, ciphertext: bytes, key: int, meta: dict = None) -> bytes:
        return self.encrypt(ciphertext, -key)