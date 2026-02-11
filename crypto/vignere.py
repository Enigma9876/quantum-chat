import sys

class VigenereCipher:
    id = "vigenere"



    def _process(self, text: str, key: str, decrypt: bool = False) -> str:

        clean_key = ''.join(c for c in self.key if c.isalpha())
     
        c.isalpha().upper()
        if not clean_key:
            return text #this is if the key is blank or invalid btw
        
        result = []
        #Keeps track of our current letter in the ciphering
        key_inx = 0 

