import socket
import sounddevice as sd
import numpy as np
from collections import deque
import threading
import os
from dotenv import load_dotenv

from flask import Flask, jsonify
from flask_cors import CORS

load_dotenv(".env")

# ============ CONFIG ============
TARGET_IP = os.getenv("IP_SUT")   # change per laptop
PORT = 50005

RATE = 48000
BLOCK = 1920        # 40 ms (CRITICAL)
CHANNELS = 1

GAIN = 1.2
JITTER_BUFFER = 6
# ================================

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", PORT))
sock.setblocking(False)

rx_buffer = deque(maxlen=JITTER_BUFFER)

def net_recv():
    while True:
        try:
            data, _ = sock.recvfrom(BLOCK * 2)
            rx_buffer.append(data)
        except BlockingIOError:
            pass

threading.Thread(target=net_recv, daemon=True).start()

def callback(indata, outdata, frames, time, status):
    if status:
        print(status)  # will now be silent

    # SEND (minimal work)
    sock.sendto(indata.tobytes(), (TARGET_IP, PORT))

    # RECEIVE (clocked)
    if len(rx_buffer) > 0:
        outdata[:] = np.frombuffer(
            rx_buffer.popleft(), dtype=np.int16
        ).reshape(-1, 1)
    else:
        outdata[:] = np.zeros((frames, 1), dtype=np.int16)

with sd.Stream(
    samplerate=RATE,
    blocksize=BLOCK,
    channels=CHANNELS,
    dtype='int16',
    latency='high',          # 🔑 THIS MATTERS
    callback=callback
):
    print("🎧 Ultra-stable two-way audio running")
    while True:
        pass