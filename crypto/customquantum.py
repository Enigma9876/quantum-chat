import numpy as np # this creates an alis for numpy btw
import secrets
import random
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

class CustomQuantumCipher:
    id = "customquantum"

    def __init__(self):
        self.backend = None #BasicProvider().get_backend('bsk_simulator')
        self.service = None 
        self.set_backend()

    def set_backend(self):
        try:
            self.service = QiskitRuntimeService() 
            self.backend = self.service.least_busy(operational=True, simulator=False) 
        except Exception as e:
            self.backend = AerSimulator()

    def _simulate_tripwire_key(self, n_bits, eve_listening=False):
        sifted_key = []
        sacrificed_bits = [] #these are like the ones we are gonna ignore 
        

        while len(sifted_key) < n_bits:
            chunk_size = 16

            alice_bits = np.random.randint(2, size=chunk_size)
            alice_bases = np.random.randint(2, size=chunk_size) 
            bob_bases = np.random.randint(2, size=chunk_size)

            if eve_listening:
                eve_bases = np.random.randint(2, size=chunk_size)
            
            qc = QuantumCircuit(chunk_size, chunk_size)

            for i in range(chunk_size):
                if alice_bits[i] == 1:
                    qc.x(i)
                if alice_bases[i] == 1:
                    qc.h(i)

            if eve_listening:
                for i in range(chunk_size):
                    if eve_bases[i] == 1:
                        qc.h(i)
                    qc.measure(i, i) #this shuld force it to collapse

                    if eve_bases[i] == 1:
                        qc.h(i)  #simulating "hiding there tracks"
            
            for i in range(chunk_size):
                if bob_bases[i] == 1:
                    qc.h(i)
                qc.measure(i, i)
            
            measured_bits_str = self._run_circuit(qc)
            bob_bits = [int(bit) for bit in measured_bits_str[::-1]] #un reverse the bits

            for i in range(chunk_size):
                if alice_bases[i] == bob_bases[i]:
                    #sacrificing hte first 10 to hcek for eve
                    if len(sacrificed_bits) < 10:
                        sacrificed_bits.append((alice_bits[i], bob_bits[i]))
                    else: #using the rest of the bits for like the real key
                        sifted_key.append(alice_bits[i])
                        if len(sifted_key) >= n_bits:
                            break
            
        compramised = False
        for alice_bit, bob_bit in sacrificed_bits:
            if alice_bit != bob_bit:
                compramised = True
                print("tripwire triggered")
                break
        
        key_int = 0
        for bit in sifted_key[:n_bits]:
            key_int = (key_int << 1) | int(bit)

        hex_key = hex(key_int)[2:]
        return hex_key, compramised

    def _run_circuit(self, qc):
        if isinstance(self.backend, AerSimulator) :
            job = self.backend.run(transpile(qc, self.backend), shots=1, memory = True)
            result = job.result()

            return result.get_memory()[0] #bit string
        else:
            print("[Quantum] Queuing for a job")

            pm = generate_preset_pass_manager(backend = self.backend, optimization_level=1)
            isa_circuit = pm.run(qc)
            sampler = SamplerV2(mode = self.backend)
            job = sampler.run([isa_circuit])
            result = job.result()

            counts = result[0].data.c.get_bitstring_counts()

            return counts[0]
        

    def encrypt(self, plaintext: bytes, key: int, **kwargs) -> bytes:
            plaintext_str = plaintext.decode('utf-8')
            required_bits = len(plaintext_str.encode('utf-8')) * 8

            decoy_text = "SYSTEM LOG: NO ANOMALIES FOUND" 
            key_b_hex = secrets.token_hex(16)
            decoy_cipher = self._one_time_pad(decoy_text, key_b_hex)

            eve_active = kwargs.get('eve_listening', random.choice([True, False]))
            key_a_hex, compromised = self._simulate_tripwire_key(required_bits, eve_active)

            real_cipher = self._one_time_pad(plaintext_str, key_a_hex)

            comp_flag = "1" if compromised else "0"
            combined_texts = f"{decoy_cipher}:{key_b_hex}:{real_cipher}:{key_a_hex}:{comp_flag}"

            return combined_texts.encode('utf-8')

    def decrypt(self, ciphertext: bytes, key: int, meta: dict = None) -> bytes:
        parts = ciphertext.decode('utf-8').split(':')
        #decoy_cipher:key_b_hex:real_cipher:key_a_hex:comp_flag
        real_cipher_hex = parts[2]
        key_a_hex = parts[3]
        comp_flag = parts[4]

        if comp_flag == "1":
            print("Warning: this transmission was flagged as potentially compromised")

        cipher_int = int(real_cipher_hex, 16)
        key_int = int(key_a_hex, 16)
        if key_int == 0: key_int = 1

        while key_int.bit_length() < cipher_int.bit_length():
            key_int = (key_int << key_int.bit_length()) | key_int

        plain_int = cipher_int ^ key_int
        byte_length = (plain_int.bit_length() + 7) // 8
        return plain_int.to_bytes(byte_length, 'big')
    


    def _one_time_pad(self, text: str, key_hex : str) -> str:
        # this will use XOR to encrypt/decrypt, lowk

        text_bytes = text.encode('utf-8')
        text_int = int.from_bytes(text_bytes, 'big') #the reason this has the 'big' (note 'big' is big-endian and that is the standard for most systems) is because we want 
                                                     #to convert the text into an integer representation that can be easily manipulated using bitwise operations


        #we want to repeat the key if its to short (THIS WOULD NOT BE DONE IN REAL OTP)
        key_int = int(key_hex, 16)
        if key_int == 0: key_int = 1 # to avoid division by zero

        while key_int.bit_length() < text_int.bit_length():
            key_int = (key_int << key_int.bit_length()) | key_int

        #XOR that bish
        cipher_int = text_int ^ key_int

        return hex(cipher_int)[2:] # convert back to hex string, and removes da "0x" prefix
    


if __name__ == "__main__":
    cipher = CustomQuantumCipher()
   
    msg = input("Enter top secret payload: ")
    if not msg: 
        msg = "The gold is buried under the old oak tree."
    
   
    
    secure_payload = cipher.encrypt(msg.encode('utf-8'), 0, eve_listening=False)
    print("sucsess")
    print(f"raw : {secure_payload.decode('utf-8')}")

    print(f"decrypted: {cipher.decrypt(secure_payload, 0)}")

    
    print("\nSimulating eavesdropper interception")
    compromised_payload = cipher.encrypt(msg.encode('utf-8'), 0, eve_listening=True)
    print("decryption")
    print(f"raw: {compromised_payload.decode('utf-8')}")

    print(f"decrypted: {cipher.decrypt(compromised_payload, 0)}")
