# server.py
import socket
import threading
import pyaudio

# Audio Configuration
CHUNK = 1024              # Size of audio chunks
FORMAT = pyaudio.paInt16  # Audio format (16-bit PCM)
CHANNELS = 1              # Single channel (Mono)
RATE = 44100              # Sample rate (Hz)

# Network Configuration
HOST = '0.0.0.0'          # Listen on all available interfaces
PORT = 8008              # Port to listen on

def send_audio(conn, stream):
    """Captures audio from microphone and sends to client."""
    print("🎤 Sending audio...")
    while True:
        try:
            data = stream.read(CHUNK)
            conn.sendall(data)
        except:
            break

def receive_audio(conn, stream):
    """Receives audio from client and plays it."""
    print("🔊 Receiving audio...")
    while True:
        try:
            data = conn.recv(CHUNK)
            if not data: break
            stream.write(data)
        except:
            break

# Main Setup
p = pyaudio.PyAudio()

# Setup Audio Streams (Input = Mic, Output = Speaker)
input_stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
output_stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)

# Setup Socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(1)

print(f"Listening on {HOST}:{PORT}...")
conn, addr = server_socket.accept()
print(f"Connected by {addr}")

# Start Threads for simultaneous Send/Receive
send_thread = threading.Thread(target=send_audio, args=(conn, input_stream))
recv_thread = threading.Thread(target=receive_audio, args=(conn, output_stream))

send_thread.start()
recv_thread.start()

send_thread.join()
recv_thread.join()

# Cleanup
conn.close()
input_stream.stop_stream()
output_stream.stop_stream()
p.terminate()