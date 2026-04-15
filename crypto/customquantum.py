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