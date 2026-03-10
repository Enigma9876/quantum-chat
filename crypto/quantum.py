import numpy as np # this creates an alis for numpy btw
from qiskit import QuantumCircuit, transpile
from qiskit.providers.basic_provider import BasicProvider # Or Aer if installed
import os

class QuantumCipher:
    id = "quantum"



    def __init__(self):
        self.backend = None #BasicProvider().get_backend('bsk_simulator')
        self.service = None # this will be used to store the quantum service (like IBMQ or something) if we want to use real quantum hardware
        self.set_backend()



    def set_backend(self):
        pass



    def _process(self, text: str, key: int, decrypt: bool = False) -> str:
        return text



    def encrypt(self, plaintext: bytes, key: int, **kwargs) -> bytes:
        return plaintext



    def decrypt(self, ciphertext: bytes, key: int, meta: dict = None) -> bytes:
        return ciphertext
    


    def _one_time_pad(self, text: str, key_hex : str) -> str:
        # this will use XOR to encrypt/decrypt

        text_bytes = text.encode('utf-8')
        text_int = int.from_bytes(text_bytes, 'big') #the reason this has the 'big' (note 'big' is big-endian and that is the standard for most systems) is because we want to convert the text into an integer representation that can be easily manipulated using bitwise operations


        #we want to repeat the key if its to short (THIS WOULD NOT BE DONE IN REAL OTP)
        key_int = int
        if key_int == 0: key_int = 1 # to avoid division by zero

        while key_int.bit_length() < text_int.bit_length():
            key_int = (key_int << key_int.bit_length()) | key_int

        #XOR that bish
        cipher_int = text_int ^ key_int

        return hex(cipher_int)[2:] # convert back to hex string, and removes da "0x" prefix
    


    def _simulate_bb84_key_exchange():
        pass


    def _run_circuit(self, circuit):
        #this needs support for running on sim or real quantum hardware
        pass