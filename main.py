from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import os

#run with "uvicorn main:app --reload --host 0.0.0.0 --port 8000" in console
app = FastAPI()

# Enable CORS for all origins (needed for dev/testing across different hosts)
app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

# Simple allow list: update as needed
ALLOWED_CLIENTS = {"client1", "client2"}

# Connected websockets
connections: List[WebSocket] = []


@app.get("/")
async def root():
	html_path = os.path.join(os.path.dirname(__file__), "index.html")
	if os.path.exists(html_path):
		return HTMLResponse(open(html_path, "r", encoding="utf-8").read())
	return {"status": "index.html not found"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
	client_id = websocket.query_params.get("client_id")
	if client_id not in ALLOWED_CLIENTS:
		await websocket.close(code=1008)
		return

	await websocket.accept()
	connections.append(websocket)
	try:
		while True:
			message = await websocket.receive_text()
			# Broadcast to all other connected clients immediately
			stale = []
			for conn in connections:
				if conn is websocket:
					continue
				try:
					await conn.send_text(message)
				except Exception:
					stale.append(conn)
			for s in stale:
				if s in connections:
					connections.remove(s)
	except WebSocketDisconnect:
		if websocket in connections:
			connections.remove(websocket)

