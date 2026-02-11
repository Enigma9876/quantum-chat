import sys


class HillCipher:
    id = "hill"
    


    def _process(self, text: str, key_matrix, decrypt: bool = False) -> str:
        return text
    


    def encrypt(self, plaintext: bytes, key_matrix, **kwargs) -> bytes:
        return plaintext

    
    def decrypt(self, ciphertext: bytes, key_matrix, meta: dict = None) -> bytes:
        return ciphertext
    


if __name__ == "__main__":
    cipher = HillCipher()