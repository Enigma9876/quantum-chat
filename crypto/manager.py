from typing import Dict, Any

class CryptoManager :
    def __init__(self):
        self._modules: Dict[str, Any] = {}



    def register(self, module):
        if getattr(module, "id", None) is None:
            raise ValueError("Module must have an 'id' attribute")
        self._modules[module.id] = module



    def get(self, alg_id):
        return self._modules.get(alg_id)
    


    def available(self):
        return list(self._modules.keys())
    


    def encrypt(self, alg_id: str, plaintext: bytes, key, **kwargs) -> bytes:
        mod = self.get(alg_id)
        if not mod:
            raise ValueError("Unknown algorithm " + alg_id)
        return mod.encrypt(plaintext, key, **kwargs)
    


    def decrypt(self, alg_id: str, ciphertext: bytes, key, meta: dict):
        mod = self.get(alg_id)
        if not mod:
            raise ValueError("Unknown algorithm " + alg_id)
        return mod.decrypt(ciphertext, key, meta)