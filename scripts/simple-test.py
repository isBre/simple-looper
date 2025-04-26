import rtmidi2
import time
import os
import pygame
import numpy as np
from scipy.signal import resample

# Initialize pygame and its mixer
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

# Setup MIDI input
midi_in = rtmidi2.MidiIn()
available_ports = rtmidi2.get_in_ports()
akai_port = 1  # Akai Should be port n.1

if akai_port < len(available_ports):
    print(f"Opening MIDI port {akai_port}: {available_ports[akai_port]}")
    midi_in.open_port(akai_port)
else:
    print(f"Invalid port {akai_port}. Available ports: {available_ports}")
    exit(1)

# MIDI note number for C3 (where our sample is)
C3_MIDI = 48

# Create a mapping of MIDI note numbers to frequencies
def midi_to_freq(midi_note):
    return 440 * (2 ** ((midi_note - 69) / 12.0))

# Base sound file
base_sound_path = "samples/piano.wav"
if not os.path.exists(base_sound_path):
    print(f"Error: {base_sound_path} not found!")
    exit(1)

# Load the base sound
base_sound = pygame.mixer.Sound(base_sound_path)

# Dictionary to store created sounds for different notes
note_sounds = {}

# Function to create a pitch-shifted version of the base sound
def create_pitched_sound(note):
    # Calculate pitch shift factor
    base_freq = midi_to_freq(C3_MIDI)  # C3 frequency
    target_freq = midi_to_freq(note)
    pitch_factor = target_freq / base_freq
    
    # Load the sound file as a numpy array
    sound_array = pygame.sndarray.array(base_sound)
    
    # Calculate new length after pitch shift
    new_length = int(len(sound_array) / pitch_factor)
    
    # Resample the sound (changes pitch)
    pitched_array = resample(sound_array, new_length)
    
    # Convert back to pygame sound
    pitched_sound = pygame.sndarray.make_sound(pitched_array.astype(np.int16))
    return pitched_sound

# Pre-create sounds for all MIDI notes (21-108, standard 88-key piano)
print("Creating pitched sounds for all notes...")
for note in range(21, 109):
    note_sounds[note] = create_pitched_sound(note)
print("Done creating sounds.")

# Function to handle note on/off events
def midi_callback(message, time_stamp):
    # rtmidi2 callback provides the message as a list [status_byte, data1, data2]
    if not message:
        return
        
    status_byte = message[0]
    channel = status_byte & 0xF  # Extract channel (0-15)
    msg_type = status_byte & 0xF0  # Extract message type
    
    if len(message) >= 3:  # Make sure we have enough data
        note = message[1]
        velocity = message[2]
        
        # Note On: 0x90 (144) through 0x9F (159)
        if msg_type == 0x90 and velocity > 0:
            if note in note_sounds:
                note_sounds[note].set_volume(velocity / 127.0)
                note_sounds[note].play()
                print(f"Note ON: {note}, velocity: {velocity}, channel: {channel}")
        
        # We don't need to handle Note Off events (0x80) explicitly as sounds play once
        # But we could stop sounds if needed

# Set the callback for the MIDI input
midi_in.callback = midi_callback

print("Listening for MIDI messages. Press Ctrl+C to exit.")
try:
    # Keep the program running until Ctrl+C is pressed
    while True:
        time.sleep(0.1)  # Small delay to prevent CPU hogging
except KeyboardInterrupt:
    print("Exiting...")
finally:
    midi_in.close_port()
    pygame.quit()
    print("MIDI port closed and pygame shut down.")