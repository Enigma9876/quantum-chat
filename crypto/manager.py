from typing import Dict, Any
import os
import inspect
import sys
import importlib.util

class CryptoManager :
    #Makes it possible to registar moduals (cryptographic algorithms) and use them by their id. 
    #This allows for a flexible and extensible design where new algorithms can be added without modifying the core logic of encryption and decryption.
    def __init__(self):
        self._modules: Dict[str, Any] = {}
        self.crypto_dir = os.path.dirname(os.path.abspath(__file__))
        self.add_files() 
    


    #the thing letting me edit my comments to be easier to understand is broken so gl with the ons i put rn
    def add_files(self):        
            if self.crypto_dir not in sys.path:
                sys.path.insert(0, self.crypto_dir)
            
            for filename in os.listdir(self.crypto_dir):
                if filename.endswith(".py") and filename not in ["manager.py"]: #if u add nore files make sure toi add em here
                    
                    module_name = filename[:-3]
                    full_path = os.path.join(self.crypto_dir, filename)
                    
                    try:
                        # this should let it be able to lead anything in this folder without me havin to put in like a specific name
                        spec = importlib.util.spec_from_file_location(module_name, full_path)
                        if spec is None or spec.loader is None:
                            continue
                        
                        module = importlib.util.module_from_spec(spec)
                        
                        if module_name not in sys.modules:
                            sys.modules[module_name] = module
                            
                        spec.loader.exec_module(module)
                        
                        for name, obj in inspect.getmembers(module, inspect.isclass):
                            if hasattr(obj, 'id'):
                                
                                self.register(obj())
                                print(f"[CryptoManager] Auto-loaded '{obj.id}' from {filename}")
                                
                    except Exception as e:
                        print(f"[CryptoManager] Was not able to load this file: {filename}: {e}")



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