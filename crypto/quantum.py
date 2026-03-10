import numpy as np # this creates an alis for numpy btw
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

class QuantumCipher:
    id = "quantum"



    def __init__(self):
        self.backend = None #BasicProvider().get_backend('bsk_simulator')
        self.service = None # this will be used to store the quantum service (like IBMQ or something) if we want to use real quantum hardware
        self.set_backend()



    def set_backend(self):
        #ima make it load on an IBM thing by default b/c i am not hooking up my key till we actually need it so this is just easier for me to think abt
        try:
            self.service = QiskitRuntimeService() # will not work till we have an API key
            self.backend = self.service.least_busy(operational=True, simulator=False) # this is saying it has to be operational and a real qc.
        except Exception as e:
            self.backend = AerSimulator() # there are other sims but idk all the refs i found use this or "Basic Simulator" and Aer sounds cooler



    def _process(self, text: str, key: int, decrypt: bool = False) -> str:
        return text



    def encrypt(self, plaintext: bytes, key: int, **kwargs) -> bytes:
        return plaintext



    def decrypt(self, ciphertext: bytes, key: int, meta: dict = None) -> bytes:
        return ciphertext
    

    """
    explaining ts rq
    ok so this def is doing OTP but not like in and "official way". Its doing otp by taking the text, keys allthat, converting them to ints
    and then doing XORs on said ints. The point of this is because Quantum computers do XOR super efficiently. After the XOR it converts the results back
    and what you return is a hex string representing the sting.
    if we were to do this in the real world what we would have to change is making a truily random key (quantum generated key using bb84). not saying that 
     using bb84 to make a key will not be done just saying that it has not been yet.
    """
    def _one_time_pad(self, text: str, key_hex : str) -> str:
        # this will use XOR to encrypt/decrypt, lowk

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
        # this will actuall also generare a key but in a real thing this would involve things across 2 diff machines
        
        pass


    def _run_circuit(self, circuit):
        #this needs support for running on sim or real quantum hardware
        pass