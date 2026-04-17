import numpy as np # this creates an alis for numpy btw
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

class LiamQuantumCipher:
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
        pass

    def encrypt(self, plaintext: bytes, key: int, **kwargs) -> bytes:
        pass

    def decrypt(self, ciphertext: bytes, key: int, **kwargs) -> bytes:
        pass
    