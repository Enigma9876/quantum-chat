Quantum Chat App

Run the simple WebSocket relay (requires Python 3.10+):

```bash
# create a venv
python -m venv .venv # first
source .venv/bin/activate # second
pip install -r requirements.txt # third

# start the server (listen on all interfaces so other devices can connect)
uvicorn main:app --reload --host 0.0.0.0 --port 8000 # fourth -> open pop up

pkill -f uvicorn # to shut down server
```

Open the app in a browser on two devices and use these example URLs:

- Device A: http://<server-ip>:8000/?client_id=client1
- Device B: http://<server-ip>:8000/?client_id=client2

Replace `<server-ip>` with your host's LAN IP (e.g. `192.168.1.42`) or `localhost` for the same machine.

The page will also show a quick "Copy link" button to open the matching client on a second device.
