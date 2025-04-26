import os
import time
import pygame
import numpy as np
import rtmidi2
from scipy.signal import resample

# --- Optimization: Force ALSA audio driver ---
os.environ["SDL_AUDIODRIVER"] = "alsa"

# --- Optimization: Prioritize process ---
try:
    os.nice(-20)
except PermissionError:
    print("Warning: could not set high priority. Try running with sudo if needed.")

# Initialize pygame and mixer
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=256)  # smaller buffer = lower latency

# Setup MIDI input
midi_in = rtmidi2.MidiIn()
available_ports = rtmidi2.get_in_ports()
akai_port = 1  # Adjust if needed

if akai_port < len(available_ports):
    print(f"Opening MIDI port {akai_port}: {available_ports[akai_port]}")
    midi_in.open_port(akai_port)
else:
    print(f"Invalid port {akai_port}. Available ports: {available_ports}")
    exit(1)

# MIDI note number for C3 (base note)
C3_MIDI = 48

# Helper: MIDI note to frequency
def midi_to_freq(midi_note):
    return 440 * (2 ** ((midi_note - 69) / 12.0))

# Load base sound
base_sound_path = "samples/piano.wav"
if not os.path.exists(base_sound_path):
    print(f"Error: {base_sound_path} not found!")
    exit(1)

base_sound = pygame.mixer.Sound(base_sound_path)

# Pre-create pitched sounds
note_sounds = {}

def create_pitched_sound(note):
    base_freq = midi_to_freq(C3_MIDI)
    target_freq = midi_to_freq(note)
    pitch_factor = target_freq / base_freq
    
    sound_array = pygame.sndarray.array(base_sound)
    new_length = int(len(sound_array) / pitch_factor)
    
    pitched_array = resample(sound_array, new_length)
    pitched_sound = pygame.sndarray.make_sound(pitched_array.astype(np.int16))
    
    return pitched_sound

print("Preparing pitched sounds (one time only)...")
for note in range(21, 109):
    note_sounds[note] = create_pitched_sound(note)
print("All sounds ready.")

# --- MIDI event callback ---
def midi_callback(message, timestamp):
    if not message or len(message) < 3:
        return
    
    status_byte = message[0]
    channel = status_byte & 0xF
    msg_type = status_byte & 0xF0
    note = message[1]
    velocity = message[2]
    
    if msg_type == 0x90 and velocity > 0:  # Note On
        if note in note_sounds:
            snd = note_sounds[note]
            ch = snd.play(loops=-1)  # loops=-1 to make it loop indefinitely
            if ch is not None:
                ch.set_volume(velocity / 127.0)
                note_channels[note] = ch  # store channel
    elif (msg_type == 0x80) or (msg_type == 0x90 and velocity == 0):  # Note Off
        if note in note_channels:
            ch = note_channels.pop(note)  # remove from dict
            ch.fadeout(100)

# Attach callback
note_channels = {}
midi_in.callback = midi_callback

# --- Main loop ---
print("Listening for MIDI... Ctrl+C to quit.")
try:
    while True:
        time.sleep(0.01)  # Smaller sleep for quicker MIDI response
except KeyboardInterrupt:
    print("\nShutting down...")
finally:
    midi_in.close_port()
    pygame.quit()
    print("Cleanup done.")
