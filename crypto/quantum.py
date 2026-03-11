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
        alic_bits = np.random.randint(2, size = n_bits)
        alic_bases = np.random.randint(2, size = n_bits) # so 0=zbase and 1=xbase -wikipidia
        bob_bases =np.random.randint(2, size = n_bits)
        

        qc = QuantumCircuit(n_bits, n_bits)

        for i in range(n_bits):
            if alice_bits[i] == 1:
                qc.x(i) # so like this is saying basically if the bit is 1 then we apply an X gate to the qbit flips it from |0> to |1>
            if alice_bases[i] == 1:
                qc.h(i) #hammond!! gate.
            
            if bob_bases[i] == 1:
                qc.h(i) # basically if bob's base is diff then we know we should discard it later (apply h to measure in x basis)

            qc.measure(i, i) 

        measured_bits_str = self._run_circuit(qc) 
        bob_bits = [int(bit) for bit in measured_bits_str[::-1]]

        sift_key = []
        for i in range(n_bits):
            if alice_bases[i] == bob_bases[i]: 
                sift_key.append(alice_bits[i])

        key_int = 0 
        for bit in sift_key:
            key_int = (key_int << 1) | bit

        return hex(key_int)[2::]



    def _run_circuit(self, circuit):
        #this needs support for running on sim or real quantum hardware
        if isinstance(self.backend, AerSimulator) : 
            job = self.backend.run(transpile(circuit, self.backend), shots=1, memory = True)
            result = job.result()

            return result.get_memory()[0] #bit string
        else:
            print("[Quantum] Queuing for a job")

            pm = generate_preset_pass_manager(backend = self.backend, optimization_level=1)
            isa_circuit = pm.run(circuit) #isa stand for intermediate representation (its what we actually send to rub)
            sampler = SamplerV2(mode = self.backend)
            job = sampler.run([isa_circuit]) #, shots = ### btw
            result = job.result()

            counts = result[0].data.c.get_bitstring_counts() # this is a dict of bitstring: count
            
            return counts[0]


if __name__ == "__main__":
    cipher = QuantumCipher()
    
    print("\n--- Quantum Chat Encryption ---")
    msg = input("Enter message: ")
    if not msg: msg = "QuantumHello"
    
    # Trigger the BB84 simulation
    print("Encrypting using BB84 Protocol...")
    encrypted = cipher.encrypt(msg.encode(), "BB84")
    print(f"Encrypted Payload: {encrypted.decode()}")
    
    decrypted = cipher.decrypt(encrypted, "BB84")
    print(f"Decrypted: {decrypted.decode()}")
        