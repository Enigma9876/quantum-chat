import sys

class AESCipher:
    id = "aes"



# AES S-box for substitution
    S_BOX = [
        0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5, 0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76,
        0xca, 0x82, 0xc9, 0x7d, 0xfa, 0x59, 0x47, 0xf0, 0xad, 0xd4, 0xa2, 0xaf, 0x9c, 0xa4, 0x72, 0xc0,
        0xb7, 0xfd, 0x93, 0x26, 0x36, 0x3f, 0xf7, 0xcc, 0x34, 0xa5, 0xe5, 0xf1, 0x71, 0xd8, 0x31, 0x15,
        0x04, 0xc7, 0x23, 0xc3, 0x18, 0x96, 0x05, 0x9a, 0x07, 0x12, 0x80, 0xe2, 0xeb, 0x27, 0xb2, 0x75,
        0x09, 0x83, 0x2c, 0x1a, 0x1b, 0x6e, 0x5a, 0xa0, 0x52, 0x3b, 0xd6, 0xb3, 0x29, 0xe3, 0x2f, 0x84,
        0x53, 0xd1, 0x00, 0xed, 0x20, 0xfc, 0xb1, 0x5b, 0x6a, 0xcb, 0xbe, 0x39, 0x4a, 0x4c, 0x58, 0xcf,
        0xd0, 0xef, 0xaa, 0xfb, 0x43, 0x4d, 0x33, 0x85, 0x45, 0xf9, 0x02, 0x7f, 0x50, 0x3c, 0x9f, 0xa8,
        0x51, 0xa3, 0x40, 0x8f, 0x92, 0x9d, 0x38, 0xf5, 0xbc, 0xb6, 0xda, 0x21, 0x10, 0xff, 0xf3, 0xd2,
        0xcd, 0x0c, 0x13, 0xec, 0x5f, 0x97, 0x44, 0x17, 0xc4, 0xa7, 0x7e, 0x3d, 0x64, 0x5d, 0x19, 0x73,
        0x60, 0x81, 0x4f, 0xdc, 0x22, 0x2a, 0x90, 0x88, 0x46, 0xee, 0xb8, 0x14, 0xde, 0x5e, 0x0b, 0xdb,
        0xe0, 0x32, 0x3a, 0x0a, 0x49, 0x06, 0x24, 0x5c, 0xc2, 0xd3, 0xac, 0x62, 0x91, 0x95, 0xe4, 0x79,
        0xe7, 0xc8, 0x37, 0x6d, 0x8d, 0xd5, 0x4e, 0xa9, 0x6c, 0x56, 0xf4, 0xea, 0x65, 0x7a, 0xae, 0x08,
        0xba, 0x78, 0x25, 0x2e, 0x1c, 0xa6, 0xb4, 0xc6, 0xe8, 0xdd, 0x74, 0x1f, 0x4b, 0xbd, 0x8b, 0x8a,
        0x70, 0x3e, 0xb5, 0x66, 0x48, 0x03, 0xf6, 0x0e, 0x61, 0x35, 0x57, 0xb9, 0x86, 0xc1, 0x1d, 0x9e,
        0xe1, 0xf8, 0x98, 0x11, 0x69, 0xd9, 0x8e, 0x94, 0x9b, 0x1e, 0x87, 0xe9, 0xce, 0x55, 0x28, 0xdf,
        0x8c, 0xa1, 0x89, 0x0d, 0xbf, 0xe6, 0x42, 0x68, 0x41, 0x99, 0x2d, 0x0f, 0xb0, 0x54, 0xbb, 0x16
    ]

    # Inverse S-box for decryption

    INV_S_BOX = [
        0x52, 0x09, 0x6a, 0xd5, 0x30, 0x36, 0xa5, 0x38, 0xbf, 0x40, 0xa3, 0x9e, 0x81, 0xf3, 0xd7, 0xfb,
        0x7c, 0xe3, 0x39, 0x82, 0x9b, 0x2f, 0xff, 0x87, 0x34, 0x8e, 0x43, 0x44, 0xc4, 0xde, 0xe9, 0xcb,
        0x54, 0x7b, 0x94, 0x32, 0xa6, 0xc2, 0x23, 0x3d, 0xee, 0x4c, 0x95, 0x0b, 0x42, 0xfa, 0xc3, 0x4e,
        0x08, 0x2e, 0xa1, 0x66, 0x28, 0xd9, 0x24, 0xb2, 0x76, 0x5b, 0xa2, 0x49, 0x6d, 0x8b, 0xd1, 0x25,
        0x72, 0xf8, 0xf6, 0x64, 0x86, 0x68, 0x98, 0x16, 0xd4, 0xa4, 0x5c, 0xcc, 0x5d, 0x65, 0xb6, 0x92,
        0x6c, 0x70, 0x48, 0x50, 0xfd, 0xed, 0xb9, 0xda, 0x5e, 0x15, 0x46, 0x57, 0xa7, 0x8d, 0x9d, 0x84,
        0x90, 0xd8, 0xab, 0x00, 0x8c, 0xbc, 0xd3, 0x0a, 0xf7, 0xe4, 0x58, 0x05, 0xb8, 0xb3, 0x45, 0x06,
        0xd0, 0x2c, 0x1e, 0x8f, 0xca, 0x3f, 0x0f, 0x02, 0xc1, 0xaf, 0xbd, 0x03, 0x01, 0x13, 0x8a, 0x6b,
        0x3a, 0x91, 0x11, 0x41, 0x4f, 0x67, 0xdc, 0xea, 0x97, 0xf2, 0xcf, 0xce, 0xf0, 0xb4, 0xe6, 0x73,
        0x96, 0xac, 0x74, 0x22, 0xe7, 0xad, 0x35, 0x85, 0xe2, 0xf9, 0x37, 0xe8, 0x1c, 0x75, 0xdf, 0x6e,
        0x47, 0xf1, 0x1a, 0x71, 0x1d, 0x29, 0xc5, 0x89, 0x6f, 0xb7, 0x62, 0x0e, 0xaa, 0x18, 0xbe, 0x1b,
        0xfc, 0x56, 0x3e, 0x4b, 0xc6, 0xd2, 0x79, 0x20, 0x9a, 0xdb, 0xc0, 0xfe, 0x78, 0xcd, 0x5a, 0xf4,
        0x1f, 0xdd, 0xa8, 0x33, 0x88, 0x07, 0xc7, 0x31, 0xb1, 0x12, 0x10, 0x59, 0x27, 0x80, 0xec, 0x5f,
        0x60, 0x51, 0x7f, 0xa9, 0x19, 0xb5, 0x4a, 0x0d, 0x2d, 0xe5, 0x7a, 0x9f, 0x93, 0xc9, 0x9c, 0xef,
        0xa0, 0xe0, 0x3b, 0x4d, 0xae, 0x2a, 0xf5, 0xb0, 0xc8, 0xeb, 0xbb, 0x3c, 0x83, 0x53, 0x99, 0x61,
        0x17, 0x2b, 0x04, 0x7e, 0xba, 0x77, 0xd6, 0x26, 0xe1, 0x69, 0x14, 0x63, 0x55, 0x21, 0x0c, 0x7d
    ]



    # Round constants for key expansion
    RCON = [0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1b, 0x36]



    # gf means Galois Field and its also sometimes called finite field
    # this is used in AES for the MixColumns step, where we need to multiply bytes in a finite field
    def _gf_multiply(self, a: int, b: int) -> int:

        p = 0

        for _ in range(8):
            if b & 1:
                p ^= a

            hi_bit = a & 0x80
            a = (a << 1) & 0xff

            if hi_bit:
                a ^= 0x1b

            b >>= 1

        return p



    # rot words are used in the key expansion step of AES, where we rotate the bytes of a word to the left
    def _rot_word(self, word: list) -> list:
        return word[1:] + [word[0]]



    # sub words annother part of da key expanding but it subs each byte using that big s table from above.
    def _sub_word(self, word: list) -> list:
        return [self.S_BOX[byte] for byte in word]



    # this is the main key expanding process and what it is doing is basically using the og key and making new keys by applying the rot and sub functions and also XORing with the previous words to create a new set of round keys that will be used in each round of encryption and decryption.
    def _key_expansion(self, key: bytes, num_rounds: int) -> list:

        key_words = [list(key[4*i:4*i+4]) for i in range(4)]

        for i in range(4, 4 * (num_rounds + 1)):

            temp = list(key_words[i - 1])

            if i % 4 == 0:
                temp = self._rot_word(temp)
                temp = self._sub_word(temp)
                temp[0] ^= self.RCON[(i // 4) - 1]

            new_word = [key_words[i - 4][j] ^ temp[j] for j in range(4)]
            key_words.append(new_word)

        return key_words



    # AES is operating within a 4x4 matrix (of bytes) and each one is called a state and we use this to convert between the byte representation of the plaintext/ciphertext and then the interval state that we use for the transformation steps
    def _bytes_to_state(self, data: bytes) -> list:

        state = [[0] * 4 for _ in range(4)]

        for i in range(16):
            row = i % 4
            col = i // 4
            state[row][col] = data[i]

        return state



    # this is just re reversing of above
    def _state_to_bytes(self, state: list) -> bytes:
        data = []

        for col in range(4):
            for row in range(4):
                data.append(state[row][col])

        return bytes(data)



    # sub bytes is allways the first step and what it does is replaces each byte in the state with its value from the s-box
    def _sub_bytes(self, state: list) -> list:
        return [[self.S_BOX[byte] for byte in row] for row in state]




    # undoes the sub bytes step and we need this for dyncryption 
    def _inv_sub_bytes(self, state: list) -> list:
        return [[self.INV_S_BOX[byte] for byte in row] for row in state]



    # this is taking the state and shifting rows to the left by amounts, these amounts are set by the row num and this creates diffusion
    def _shift_rows(self, state: list) -> list:

        state[1] = state[1][1:] + state[1][:1]
        state[2] = state[2][2:] + state[2][:2]
        state[3] = state[3][3:] + state[3][:3]

        return state




    # you will never guess what this one does!!!!!!!!!!! Its the opposite of above
    def _inv_shift_rows(self, state: list) -> list:

        state[1] = state[1][-1:] + state[1][:-1]
        state[2] = state[2][-2:] + state[2][:-2]
        state[3] = state[3][-3:] + state[3][:-3]

        return state



    # REMEBER DONT APPLY THIS ON THE LAST ROUND OF ENCRYPTION OR THE FIRST ROUND OF DECRYPTION
    # dw fam i remembered. Anywho this is the step where wa are taking the col and doing some math, specifically we are multiplying the bytes in the column by certain values in the finite field and then XORing them together to create new values for the column. This is what creates diffusion in AES as it mixes the bytes together in a way that makes it hard to reverse without the key, OUR key.
    def _mix_columns(self, state: list) -> list:

        new_state = [[0] * 4 for _ in range(4)]

        for col in range(4):
            a0, a1, a2, a3 = [state[row][col] for row in range(4)]
            new_state[0][col] = self._gf_multiply(2, a0) ^ self._gf_multiply(3, a1) ^ a2 ^ a3
            new_state[1][col] = a0 ^ self._gf_multiply(2, a1) ^ self._gf_multiply(3, a2) ^ a3
            new_state[2][col] = a0 ^ a1 ^ self._gf_multiply(2, a2) ^ self._gf_multiply(3, a3)
            new_state[3][col] = self._gf_multiply(3, a0) ^ a1 ^ a2 ^ self._gf_multiply(2, a3)

        return new_state



    # OML THIS DOES THE OPPOSITE OF ABOVE!!!! WHO WOULD HAVE GUESSED!!!!!
    def _inv_mix_columns(self, state: list) -> list:

        new_state = [[0] * 4 for _ in range(4)]

        for col in range(4):
            a0, a1, a2, a3 = [state[row][col] for row in range(4)] #someething to mention is that these number (0x0b, 0x0d, 0x0e, 0x09, ect) are not random they are specific values that are used in the inverse mix columns step to reverse the mixing process and they are derived from the properties of the finite field and the original mix columns transformation. They are chosen to ensure that when we apply the inverse mix columns step, we can recover the original state before the mix columns was applied, which is super important if we want da decryption to work correctly
            new_state[0][col] = self._gf_multiply(0x0e, a0) ^ self._gf_multiply(0x0b, a1) ^ self._gf_multiply(0x0d, a2) ^ self._gf_multiply(0x09, a3)
            new_state[1][col] = self._gf_multiply(0x09, a0) ^ self._gf_multiply(0x0e, a1) ^ self._gf_multiply(0x0b, a2) ^ self._gf_multiply(0x0d, a3)
            new_state[2][col] = self._gf_multiply(0x0d, a0) ^ self._gf_multiply(0x09, a1) ^ self._gf_multiply(0x0e, a2) ^ self._gf_multiply(0x0b, a3)
            new_state[3][col] = self._gf_multiply(0x0b, a0) ^ self._gf_multiply(0x0d, a1) ^ self._gf_multiply(0x09, a2) ^ self._gf_multiply(0x0e, a3)

        return new_state




    # so when we are adding the round key its not like __ + round key rather we take the state and XOR it with the round key and this adds the key into the mix and its what makes it so that without the key you cannot reverse the transformations we have applied to this who jaz
    def _add_round_key(self, state: list, round_keys_slice: list) -> list:
        for col in range(4):
            for row in range(4):
                state[row][col] ^= round_keys_slice[col][row]
        return state



    # applied all of the steps together
    def encrypt(self, plaintext: bytes, key: bytes, **kwargs) -> bytes:
        if isinstance(plaintext, str):
            plaintext = plaintext.encode()
        if isinstance(key, str):
            key = key.encode()
            
        #added da padding so the length is perfectly divisible by 16 (for the thing said before)
        pad_len = 16 - (len(plaintext) % 16)
        plaintext += bytes([pad_len] * pad_len)
        
        num_rounds = 10 if len(key) == 16 else 12 if len(key) == 24 else 14 # thx gemni for teaching me this syntax in python (its called a ternary operator (does the same in java but looks goofier here) and now i need less lines)
        round_keys = self._key_expansion(key, num_rounds)
        
        ciphertext = b""
        
        for i in range(0, len(plaintext), 16):
            state = self._bytes_to_state(plaintext[i:i+16])
            state = self._add_round_key(state, round_keys[0:4])
            
            for round_num in range(1, num_rounds):
                state = self._sub_bytes(state)
                state = self._shift_rows(state)
                state = self._mix_columns(state)
                state = self._add_round_key(state, round_keys[round_num * 4 : (round_num + 1) * 4])
                
            state = self._sub_bytes(state)
            state = self._shift_rows(state)
            state = self._add_round_key(state, round_keys[num_rounds * 4 : (num_rounds + 1) * 4])
            ciphertext += self._state_to_bytes(state)
            
        #rturn hex-encoded output as UTF-8 bytes so callums thing does not implode
        return ciphertext.hex().encode('utf-8')



    # just above but with the reverse order 
    def decrypt(self, ciphertext: bytes, key: bytes, meta: dict = None) -> bytes:
        if isinstance(key, str):
            key = key.encode()
        
        # Convert hex string back to bytes if needed
        if isinstance(ciphertext, bytes):
            try:
                ciphertext = bytes.fromhex(ciphertext.decode('utf-8'))
            except (ValueError, UnicodeDecodeError):
                pass  # If not hex use asis
        
        num_rounds = 10 if len(key) == 16 else 12 if len(key) == 24 else 14
        round_keys = self._key_expansion(key, num_rounds)
        
        plaintext = b""
        
        #
        for i in range(0, len(ciphertext), 16):
            state = self._bytes_to_state(ciphertext[i:i+16])
            state = self._add_round_key(state, round_keys[num_rounds * 4 : (num_rounds + 1) * 4])
            
            for round_num in range(num_rounds - 1, 0, -1):
                state = self._inv_shift_rows(state)
                state = self._inv_sub_bytes(state)
                state = self._add_round_key(state, round_keys[round_num * 4 : (round_num + 1) * 4])
                state = self._inv_mix_columns(state)
                
            state = self._inv_shift_rows(state)
            state = self._inv_sub_bytes(state)
            state = self._add_round_key(state, round_keys[0:4])
            plaintext += self._state_to_bytes(state)

        pad_len = plaintext[-1]
        plaintext = plaintext[:-pad_len]
            
        return plaintext
    
#test case runner curtisy of gemini
if __name__ == "__main__":
    cipher = AESCipher()
    
    # Needs to be exactly 16 bytes (128-bit) for this barebones implementation!
    key = b"ThatsMyKungFuKey" 
    
    # Making the plaintext much longer to test the chunking, and unaligned to test padding!
    plaintext = b"SecretMessage123 that is now way longer than sixteen bytes to test the chunking and padding!" 


    print(f"Original text: {plaintext}")
    print(f"Key used:      {key}\n")

    # Time to scramble it up
    ciphertext = cipher.encrypt(plaintext, key)
    print(f"Ciphertext (hex): {ciphertext.hex()}")

    # Time to unscramble it
    decrypted = cipher.decrypt(ciphertext, key)
    print(f"Decrypted text:   {decrypted}")

    # The moment of truth
    if plaintext == decrypted:
        print("\n The math checked out. I did it!")
    else:
        print("\n something went wrong")