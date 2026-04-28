import sys

class AffineCipher :
    id = "affine"

    def encrypt(self, plaintext: bytes, key: tuple, **kwargs) -> bytes:
        pass

    def decrypt(self, ciphertext: bytes, key: tuple, meta: dict = None) -> bytes:
        pass

    def process(self, text: str, key: tuple, decrypt=False) -> str:
        pass