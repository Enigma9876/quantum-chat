import numpy as np # this creates an alis for numpy btw
from qiskit import QuantumCircuit, transpile
from qiskit.providers.basic_provider import BasicProvider # Or Aer if installed
import os

class QuantumCipher:
    id = "quantum"



    def __init__(self):
        self.backend = BasicProvider().get_backend('bsk_simulator')



    def _process(self, text: str, key: int, decrypt: bool = False) -> str:
        return text



    def encrypt(self, plaintext: bytes, key: int, **kwargs) -> bytes:
        return plaintext



    def decrypt(self, ciphertext: bytes, key: int, meta: dict = None) -> bytes:
        return ciphertext