import rtmidi2
import sounddevice as sd
import numpy as np
import scipy.signal
import soundfile as sf
import time
import os

# Constants
C3_MIDI = 48  # MIDI note for C3
sample_rate = 44100

# Load base sample
base_sound_path = "samples/piano.wav"
if not os.path.exists(base_sound_path):
    print(f"Error: {base_sound_path} not found!")
    exit(1)

# Load full wav file
base_sound, base_sr = sf.read(base_sound_path)
if base_sound.ndim == 1:
    base_sound = np.expand_dims(base_sound, axis=1)  # Make mono into (N,1)

print(f"Loaded sample shape: {base_sound.shape}, samplerate: {base_sr}")

# Resample to standard 44100 if needed
if base_sr != sample_rate:
    print("Resampling to 44100Hz...")
    number_of_samples = round(len(base_sound) * float(sample_rate) / base_sr)
    base_sound = scipy.signal.resample(base_sound, number_of_samples)

# MIDI setup
midi_in = rtmidi2.MidiIn()
available_ports = rtmidi2.get_in_ports()
akai_port = 1

if akai_port < len(available_ports):
    print(f"Opening MIDI port {akai_port}: {available_ports[akai_port]}")
    midi_in.open_port(akai_port)
else:
    print(f"Invalid port {akai_port}. Available ports: {available_ports}")
    exit(1)

# Helper functions
def midi_to_freq(midi_note):
    return 440 * (2 ** ((midi_note - 69) / 12.0))

def create_pitched_sample(target_note):
    base_freq = midi_to_freq(C3_MIDI)
    target_freq = midi_to_freq(target_note)
    pitch_factor = target_freq / base_freq
    
    # Resample sound
    new_length = int(len(base_sound) / pitch_factor)
    pitched_array = scipy.signal.resample(base_sound, new_length)
    return pitched_array

# Sound playback handling
active_streams = {}  # Note -> Stream

def note_on(note, velocity):
    if note in active_streams:
        return  # Already playing
    
    pitched_sound = create_pitched_sample(note)
    scaled_sound = pitched_sound * (velocity / 127.0)
    
    # Create a callback stream
    def callback(outdata, frames, time_info, status):
        # Loop sound endlessly
        nonlocal pos
        chunk = scaled_sound[pos:pos+frames]
        if len(chunk) < frames:
            chunk = np.vstack((chunk, scaled_sound[:frames - len(chunk)]))  # Loop back to start
        outdata[:] = chunk
        pos = (pos + frames) % len(scaled_sound)

    pos = 0
    stream = sd.OutputStream(
        samplerate=sample_rate,
        channels=scaled_sound.shape[1],
        callback=callback,
        blocksize=512,
        latency='low'
    )
    stream.start()
    active_streams[note] = stream

def note_off(note):
    stream = active_streams.pop(note, None)
    if stream:
        stream.stop()
        stream.close()

# MIDI handling
def midi_callback(message, timestamp):
    if not message or len(message) < 3:
        return
    
    status_byte = message[0]
    msg_type = status_byte & 0xF0
    note = message[1]
    velocity = message[2]
    
    if msg_type == 0x90 and velocity > 0:
        note_on(note, velocity)
    elif (msg_type == 0x80) or (msg_type == 0x90 and velocity == 0):
        note_off(note)

# Assign MIDI callback
midi_in.callback = midi_callback

print("Ready! Listening for MIDI notes. Press Ctrl+C to quit.")

try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    print("Stopping...")
finally:
    midi_in.close_port()
    for s in active_streams.values():
        s.stop()
        s.close()
    print("Closed all streams.")
