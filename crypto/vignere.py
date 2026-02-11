import sys

class VigenereCipher:
    id = "vigenere"



    def _process(self, text: str, key: str, decrypt: bool = False) -> str:

        clean_key = ''.join(c for c in key if c.isalpha())
     
        
        if not clean_key:
            return text #this is if the key is blank or invalid btw
        
        result = []
        #Keeps track of our current letter in the ciphering
        key_inx = 0 

        for char in text:
            if char.isalpha():
                key_char_code = ord(clean_key[key_inx])
                shift = key_char_code - ord('A')
                if decrypt:
                    shift = -shift
                start = ord('A') if char.isupper() else ord('a')
                
                shifted_char = chr((ord(char) - start + shift) % 26 + start)
                result.append(shifted_char)

                key_inx = (key_inx + 1) % len(clean_key)
            else:
                result.append(char)

        return ''.join(result)
    


    def encrypt(self, plaintext: bytes, key: str, **kwargs) -> bytes:
        text = plaintext.decode('utf-8')
        ciphertext = self._process(text, key, decrypt=False)

        return ciphertext.encode('utf-8')
    


    def decrypt(self, ciphertext: bytes, key: str, meta: dict = None) -> bytes:
        text = ciphertext.decode('utf-8')
        decrypted_text = self._process(text, key, decrypt=True)

        return decrypted_text.encode('utf-8')
    

if __name__ == "__main__": 
    cipher = VigenereCipher()
    
    msg = input("Enter a message to encrypt: ")
    if not msg: msg = "Hello, World!"

    # Note: Vigenere needs a string for a key, not an integer!
    shift_key = input("Enter the key (word/string, e.g., 'SECRET'): ")
    if not shift_key: shift_key = "SECRET"

    encrypted_bytes = cipher.encrypt(msg.encode('utf-8'), shift_key)
    encrypted_text = encrypted_bytes.decode('utf-8')

    print(f"Encrypted message: {encrypted_text}")
    
    decrypted_bytes = cipher.decrypt(encrypted_bytes, shift_key)
    decrypted_text = decrypted_bytes.decode('utf-8')

    print(f"Decrypted message: {decrypted_text}")