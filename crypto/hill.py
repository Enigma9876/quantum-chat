import sys
from typing import List, Optional
class HillCipher:
    id = "hill"

    #looks goofy cuz i need a prime num of chars
    ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 !@#$%^&*()_+{}|:\"<>?~`-=[];',./\\£€"
    MODULUS = len(ALPHABET) # 97

    # this is just calculating the det for the matrix to make it so that it does not look supper messy when invertin
    def _matrix_determinant(self, matrix: List[List[int]]) -> int:
        n = len(matrix)
        if n == 1:
            return matrix[0][0]
        if n == 2:
            return matrix[0][0]*matrix[1][1] - matrix[0][1]*matrix[1][0]
        det = 0
        for c in range(n):
             
            minor = [row[:c] + row[c+1:] for row in matrix[1:]]
            det += ((-1) ** c) * matrix[0][c] * self._matrix_determinant(minor)
        return det
    

    #actually doing the inversion
    def _mod_inverse(self, a: int, modulus: int) -> Optional[int]:
        a = a % modulus
        for x in range(1, modulus):
            if (a * x) % modulus == 1:
                return x
        return None



    #gets the letter/number that assosiates with the number and then makes it upper or lower case depending on the original letter
    def _matrix_mod_inv(self, matrix: List[List[int]], modulus: int) -> List[List[int]]:
        n = len(matrix)
        det = self._matrix_determinant(matrix) % modulus
        det_inv = self._mod_inverse(det, modulus)
        if det_inv is None:
            raise ValueError("Key matrix is not invertible modulo {}".format(modulus))

          
        adj = [[0]*n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                  
                minor = [row[:j] + row[j+1:] for k,row in enumerate(matrix) if k != i]
                cof = ((-1) ** (i + j)) * self._matrix_determinant(minor)
                adj[j][i] = cof % modulus    
          
        inv = [[(adj[i][j] * det_inv) % modulus for j in range(n)] for i in range(n)]
        return inv



    #this uses our key to actually encrypt the text block 
    def _encrypt_block(self, block: List[str], matrix: List[List[int]]) -> List[str]:
        n = len(matrix)
        vec = [ord(ch.upper()) - ord('A') for ch in block]
        result_nums = []

        for i in range(n):
            total = 0
            for j in range(n):
                total += matrix[i][j] * vec[j]
            result_nums.append(total % 26)

        out = []

        for num, orig in zip(result_nums, block):
            ch = chr(num + ord('A'))
            if orig.islower():
                ch = ch.lower()
            out.append(ch)

        return out
    


    #this is the main function that does the actual encryption and decryption. It processes the text in blocks of size n 
    # (the size of the key matrix) and applies the appropriate transformation based on whether we are encrypting or decrypting. 
    def _process(self, text: str, key_matrix, decrypt: bool = False) -> str:
        if not isinstance(key_matrix, list) or not key_matrix:
             raise ValueError("Key matrix must be a non-empty list")
        
        n = len(key_matrix)

        if any(len(row) != n for row in key_matrix):
            raise ValueError("Key matrix must be square")

        modulus = 26
        mat = self._matrix_mod_inv(key_matrix, modulus) if decrypt else key_matrix

        #Map non-alphabetic characters and extract only letters for the cipher
        alpha_chars = []
        non_alpha_map = {}

        for index, char in enumerate(text):
            if char.isalpha():
                alpha_chars.append(char)
            else:
                non_alpha_map[index] = char

        #Handle Padding (ONLY during encryption)
        if not decrypt:
            while len(alpha_chars) % n != 0:
                alpha_chars.append('X') # Pad with X to complete the matrix block

        processed_alphas = []
        for i in range(0, len(alpha_chars), n):
            block = alpha_chars[i:i+n]
            
            # If decrypting and we hit a partial block, the ciphertext is malformed/truncated
            if len(block) < n and decrypt:
                processed_alphas.extend(block) 
                continue
                
            processed_alphas.extend(self._encrypt_block(block, mat))

        
        result_str = ""
        alpha_ptr = 0
        
        for i in range(len(text)):
            if i in non_alpha_map:
                result_str += non_alpha_map[i]
            else:
                result_str += processed_alphas[alpha_ptr]
                alpha_ptr += 1
                
        while alpha_ptr < len(processed_alphas):
            result_str += processed_alphas[alpha_ptr]
            alpha_ptr += 1

        return result_str



    # just a caller thing to allow manager.py to do things uniformly across all ciphers
    def encrypt(self, plaintext: bytes, key_matrix, **kwargs) -> bytes:
         text = plaintext.decode('utf-8')
         ciphertext = self._process(text, key_matrix, decrypt=False)
         return ciphertext.encode('utf-8')



    def decrypt(self, ciphertext: bytes, key_matrix, meta: dict = None) -> bytes:
        text = ciphertext.decode('utf-8')
        decrypted = self._process(text, key_matrix, decrypt=True)
          
        if meta and meta.get("padding"):
            padding = meta["padding"]
            if padding > 0:
                decrypted = decrypted[:-padding]
        return decrypted.encode('utf-8')



if __name__ == "__main__":
    cipher = HillCipher()

    msg = input("Enter a message to encrypt: ")
    if not msg:
        msg = "HELLO"    
    
    key = [[3, 3], [2, 5]]

    encrypted_bytes = cipher.encrypt(msg.encode('utf-8'), key)
    print("Encrypted:", encrypted_bytes.decode('utf-8'))

    decrypted_bytes = cipher.decrypt(encrypted_bytes, key)
    print("Decrypted:", decrypted_bytes.decode('utf-8'))