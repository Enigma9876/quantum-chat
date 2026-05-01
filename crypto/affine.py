import sys

class AffineCipher :
    id = "affine"
 
    @staticmethod #turns out you need this here or everything breaks and sets itself alight
    def mod_inverse(a, m):
        m0 = m
        y = 0
        x = 1
        if m == 1:
            return 0
        while a > 1:
            q = a // m
            t = m
            m = a % m
            a = t
            t = y
            y = x - q * y
            x = t
        if x < 0:
            x += m0
        return x



    def encrypt(self, plaintext: bytes, key: tuple, **kwargs) -> bytes:
        a, b = key
        m = 256
        result = bytearray()
        for byte in plaintext:
            encrypted = (a * byte + b) % m
            result.append(encrypted)
        return bytes(result)




    def decrypt(self, ciphertext: bytes, key: tuple, meta: dict = None) -> bytes:
        a, b = key
        m = 256
        a_inv = self.mod_inverse(a, m)
        result = bytearray()
        for byte in ciphertext:
            decrypted = (a_inv * (byte - b)) % m
            result.append(decrypted)
        return bytes(result)



    # actuallz going to use this method for once
    def process(self, text: str, key: tuple, decrypt=False) -> str:
        a, b = key
        m = 26
        result = []
        for char in text:
            if char.isalpha():
                base = ord('A') if char.isupper() else ord('a')
                x = ord(char) - base
                if decrypt:
                    a_inv = self.mod_inverse(a, m)
                    y = (a_inv * (x - b)) % m
                else:
                    y = (a * x + b) % m
                result.append(chr(y + base))
            else:
                result.append(char)
        return ''.join(result)
    


    
if __name__ == "__main__":
    cipher = AffineCipher()

    msg = input("msg: ")

    if not msg:
        msg = "PLUH to the MAX"

    key = (5, 8)

    encrypted = cipher.process(msg, key)
    decrypted = cipher.process(encrypted, key, decrypt=True)
    
    print("Original: " + msg)
    print("Encrypted: " + encrypted)
    print("Decrypted: " + decrypted)
