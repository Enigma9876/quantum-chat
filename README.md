# 🔐 Insightful Encryptions

An interactive cryptographic learning platform that lets you explore, experiment with, and understand real cipher algorithms from first principles.

## Features

### 🧪 The Lab
A standalone encryption sandbox where you can:
- Type any message and encrypt it with 6 different cipher algorithms
- Configure encryption keys (shift values, matrices, keywords)
- See a live ciphertext preview that updates as you type
- Explore step-by-step character-by-character encryption breakdowns
- Use decrypt tools: automated algorithm visualizations and manual walkthrough exercises

### 💬 Online Room
Host or join a live encrypted chat room:
- Real-time messaging via WebSockets
- Each participant selects their own cipher and key
- Messages are encrypted before transmission
- Click the inspect icon on any message to see the full encryption/decryption analysis
- Host controls: force cipher, mute users, kick, rename

### Cipher Algorithms
| Cipher | Type | Key |
|--------|------|-----|
| Caesar Shift | Substitution | Integer shift (1–25) |
| Affine | Substitution | Multiplier A (coprime w/ 26) + Shift B |
| Hill Matrix | Polygraphic | n×n invertible matrix |
| Vigenère | Polyalphabetic | Keyword string |
| AES-256 | Block cipher | 256-bit key |
| BB84 Quantum | Quantum KD | Qubit count (simulated) |

### Educational Tools
- **Cipher Guides**: History, mathematical formulas, and how-it-works explanations
- **Step-by-Step Tables**: Character-by-character encryption math breakdowns
- **Algorithm Decrypt Mode**: Animated visualizations of cipher-breaking techniques (brute force, Kasiski attack, matrix inversion)
- **Manual Decrypt Mode**: Interactive exercises where you work through the math yourself

## How to Run

```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
python web_app.py
```

The app will automatically open in your browser at `http://127.0.0.1:6000`.

## Tech Stack
- **Backend**: Python, Flask, Flask-SocketIO
- **Frontend**: HTML, CSS, JavaScript (vanilla)
- **Quantum Simulation**: Qiskit AerSimulator
- **Crypto**: All cipher algorithms implemented from scratch (no library wrappers)

## Project Structure
```
quantum-chat/
├── web_app.py              # Flask server + Socket.IO events
├── room_manager.py         # Chat room state management
├── crypto/                 # Cipher algorithm implementations
│   ├── manager.py          # Auto-discovery plugin loader
│   ├── caesar.py           # Caesar shift cipher
│   ├── affine.py           # Affine cipher
│   ├── hill.py             # Hill matrix cipher
│   ├── vignere.py          # Vigenère cipher
│   ├── aes.py              # AES-256 (built from scratch)
│   ├── quantum.py          # BB84 quantum key distribution
│   └── customquantum.py    # Enhanced BB84 with eavesdrop detection
├── templates/
│   ├── base.html           # Base layout + CSS design system
│   ├── home.html           # Landing page
│   ├── lab.html            # Encryption sandbox
│   ├── local.html          # Chat room lobby
│   ├── chat.html           # Live chat room
│   └── chat/               # Chat page partials
└── requirements.txt
```