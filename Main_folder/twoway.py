# # client.py
# import socket
# import threading
# import pyaudio



# # Audio Configuration (Must match Server)
# CHUNK = 1024
# FORMAT = pyaudio.paInt16
# CHANNELS = 1
# RATE = 44100

# # Network Configuration
# HOST = # REPLACE with Server's IP Address (e.g., 192.168.1.X)
# PORT = 8008

# def send_audio(sock, stream):
#     """Captures audio from microphone and sends to server."""
#     print("🎤 Sending audio...")
#     while True:
#         try:
#             data = stream.read(CHUNK)
#             sock.sendall(data)
#         except:
#             break

# def receive_audio(sock, stream):
#     """Receives audio from server and plays it."""
#     print("🔊 Receiving audio...")
#     while True:
#         try:
#             data = sock.recv(CHUNK)
#             if not data: break
#             stream.write(data)
#         except:
#             break

# # Main Setup
# p = pyaudio.PyAudio()

# # Setup Audio Streams
# input_stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
# output_stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)

# # Setup Socket
# client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# try:
#     client_socket.connect((HOST, PORT))
#     print(f"Connected to {HOST}:{PORT}")

#     # Start Threads
#     send_thread = threading.Thread(target=send_audio, args=(client_socket, input_stream))
#     recv_thread = threading.Thread(target=receive_audio, args=(client_socket, output_stream))

#     send_thread.start()
#     recv_thread.start()

#     send_thread.join()
#     recv_thread.join()

# except Exception as e:
#     print(f"Could not connect: {e}")

# finally:
#     client_socket.close()
#     input_stream.stop_stream()
#     output_stream.stop_stream()
#     p.terminate()