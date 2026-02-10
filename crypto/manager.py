from typing import Dict, Any

class CryptoManager :
    #Makes it possible to registar moduals (cryptographic algorithms) and use them by their id. 
    #This allows for a flexible and extensible design where new algorithms can be added without modifying the core logic of encryption and decryption.
    def __init__(self):
        self._modules: Dict[str, Any] = {}


    #Registers new moduals and ensures that they have an id
    def register(self, module):
        if getattr(module, "id", None) is None:
            raise ValueError("Module must have an 'id' attribute")
        self._modules[module.id] = module



    def get(self, alg_id):
        return self._modules.get(alg_id)
    

    #Shows all avalable algo by id so the user can see what they can use
    def available(self):
        return list(self._modules.keys())
    

    #Encrypts the plaintext using the specified algorithm and key. 
    #It retrieves the appropriate module based on the algorithm ID and calls its encrypt method. 
    #If the algorithm is not found then it will raise an error.
    def encrypt(self, alg_id: str, plaintext: bytes, key, **kwargs) -> bytes:
        mod = self.get(alg_id)
        if not mod:
            raise ValueError("Unknown algorithm " + alg_id)
        return mod.encrypt(plaintext, key, **kwargs)
    

    #Decrypts the ciphertext using the specified algorithm and key (BASICALLY THE SAME AS ENCRYPT)
    def decrypt(self, alg_id: str, ciphertext: bytes, key, meta: dict):
        mod = self.get(alg_id)
        if not mod:
            raise ValueError("Unknown algorithm " + alg_id)
        return mod.decrypt(ciphertext, key, meta)