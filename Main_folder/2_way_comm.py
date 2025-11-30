import sys
import os
import asyncio
import logging
import math
import struct
import time
from fractions import Fraction
from contextlib import asynccontextmanager

# Required for the channel mismatch fix
import numpy as np 

import av
import sounddevice as sd
from sounddevice import PortAudioError # Import specific error for robust handling

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from aiortc import RTCPeerConnection, RTCSessionDescription, MediaStreamTrack
from aiortc.contrib.media import MediaPlayer
from aiortc.sdp import candidate_from_sdp

# --- Configuration and Setup ---


# Windows: use Selector loop
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logging.basicConfig(level=logging.INFO)

# CORS: TEMPORARILY set to allow all origins
origins = ["*"] 

pcs = set()

# --- Lifespan Event Handler (Fixes Deprecation Warning) ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Application Startup ---
    logging.info("Application starting up...")
    
    # --- The Application Runs (Yield control to Uvicorn) ---
    yield
    
    # --- Application Shutdown (Cleanup Logic) ---
    logging.info("Application shutting down. Closing PeerConnections...")
    await asyncio.gather(*(pc.close() for pc in list(pcs)), return_exceptions=True)
    pcs.clear()

# Pass the lifespan function to the FastAPI app initialization
app = FastAPI(lifespan=lifespan)

# Add CORS Middleware to the application
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Utility Tracks and Functions ---

class SineWaveTrack(MediaStreamTrack):
    kind = "audio"

    def __init__(self, frequency: int = 440, sample_rate: int = 48000):
        super().__init__()
        self.frequency = frequency
        self.sample_rate = sample_rate
        self.samples_per_frame = 960
        self.phase = 0.0
        self.phase_increment = 2 * math.pi * self.frequency / self.sample_rate
        self._timestamp = 0
        self._start = time.time()

    async def recv(self):
        target_time = self._start + (self._timestamp / self.sample_rate)
        wait = target_time - time.time()
        if wait > 0:
            await asyncio.sleep(wait)

        frame = av.AudioFrame(format="s16", layout="mono", samples=self.samples_per_frame)
        pcm = bytearray()
        for _ in range(self.samples_per_frame):
            sample_val = int(32767 * math.sin(self.phase))
            pcm.extend(struct.pack("<h", sample_val))
            self.phase += self.phase_increment
            if self.phase > 2 * math.pi:
                self.phase -= 2 * math.pi
        frame.planes[0].update(bytes(pcm))

        frame.sample_rate = self.sample_rate
        frame.time_base = Fraction(1, self.sample_rate)
        frame.pts = self._timestamp

        self._timestamp += self.samples_per_frame
        return frame

async def play_incoming_to_speaker(track: MediaStreamTrack):
    """
    Browser -> server audio to local speaker, with robust channel and error handling.
    """
    stream = None
    # 💡 FIX 4: Set the determined speaker index
    SPEAKER_DEVICE_INDEX = 3 
    
    try:
        first = await track.recv()
        sr = first.sample_rate or 48000
        
        # --- Channel Mismatch Handling ---
        ch = 1 # Start with the safest default (Mono)
        
        # Function to attempt opening the stream
        def open_stream(channels):
            return sd.OutputStream(
                samplerate=sr, 
                channels=channels, 
                dtype="int16", 
                device=SPEAKER_DEVICE_INDEX
            )

        # Attempt 1: 1 Channel (Mono)
        try:
            stream = open_stream(1)
            stream.start()
            ch = 1
            logging.info(f"Opened speaker stream with {ch} channel(s) (Mono).")
        except PortAudioError as e:
            # Attempt 2: 2 Channels (Stereo)
            stream = open_stream(2)
            stream.start()
            ch = 2
            logging.info(f"Opened speaker stream with {ch} channel(s) (Stereo).")
        # --- End Channel Handling ---

        # Function to process frame data for writing
        def write_frame(frame, ch_count):
            # 💡 FIX 5: PyAV compatibility: call to_ndarray() without 'format' arg
            pcm = frame.to_ndarray() 
            
            # Reshape based on PyAV output
            if pcm.ndim == 2 and pcm.shape[0] <= 8:
                pcm = pcm.T
            
            # Reshape to match the successful channel count 'ch' (Mono to Stereo duplication)
            if pcm.ndim == 1 and ch_count == 2:
                # Need numpy for this
                pcm = np.stack((pcm, pcm), axis=1) 
            
            stream.write(pcm)
        
        write_frame(first, ch) # Write first frame

        while True:
            frame = await track.recv()
            write_frame(frame, ch) # Write subsequent frames

    except Exception as e:
        logging.warning(f"Inbound audio playback failed: {e}") 
    finally:
        if stream and stream.active: 
            stream.stop()
            stream.close()

async def wait_for_ice_gathering_complete(pc: RTCPeerConnection):
    while pc.iceGatheringState != "complete":
        await asyncio.sleep(0.05)

# --- FastAPI Endpoints ---

@app.options("/offer")
async def options_offer():
    return Response(status_code=204)

@app.options("/candidate")
async def options_candidate():
    return Response(status_code=204)

@app.post("/offer")
async def offer(request: Request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("track")
    def on_track(track):
        if track.kind == "audio":
            logging.info("!!! RECEIVED INBOUND AUDIO TRACK FROM BROWSER !!!")
            asyncio.create_task(play_incoming_to_speaker(track))

    @pc.on("connectionstatechange")
    async def on_state_change():
        if pc.connectionState in ("failed", "closed", "disconnected"):
            try:
                await pc.close()
            finally:
                pcs.discard(pc)

    # Server -> Browser outbound audio
    outbound_added = False
    player = None 

    try:
        if sys.platform.startswith("win"):
            # 💡 Use your determined mic string
            MIC_DEVICE_STRING = 'audio=Microphone Array (2- Intel® Smart Sound Technology for Digital Microphones)'
            logging.info(f"Using hardcoded Windows mic device: {MIC_DEVICE_STRING}")
            player = MediaPlayer(MIC_DEVICE_STRING, format="dshow") 
        else:
            player = MediaPlayer("default", format="pulse")

    except Exception as e:
        logging.warning(f"Mic open failed (exception raised): {e}")

    if player and player.audio:
        pc.addTrack(player.audio)
        outbound_added = True
        logging.info("Attached microphone track to PeerConnection")
    elif player:
        logging.error("MediaPlayer opened successfully, but **no audio track found**. Check if the device is in use.")

    if not outbound_added:
        pc.addTrack(SineWaveTrack())
        logging.info("Using SineWaveTrack fallback for outbound audio")

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    await wait_for_ice_gathering_complete(pc)

    return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}

@app.post("/candidate")
async def candidate(request: Request):
    params = await request.json()
    cand_str = params.get("candidate")
    if not cand_str:
        for pc in list(pcs):
            try:
                await pc.addIceCandidate(None)
            except Exception:
                pass
        return {"ok": True}

    cand = candidate_from_sdp(cand_str)
    cand.sdpMid = params.get("sdpMid")
    cand.sdpMLineIndex = params.get("sdpMLineIndex")

    for pc in list(pcs):
        try:
            await pc.addIceCandidate(cand)
        except Exception:
            pass
    return {"ok": True}

@app.get("/health")
async def health():
    return {"status": "ok"}



if __name__ == "__main__":
    print("RUNNING")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)