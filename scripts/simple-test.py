import rtmidi
import time
import os
import pygame
import numpy as np
from scipy.signal import resample
from rtmidi import MidiMessage

# Initialize pygame and its mixer
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

# Setup MIDI input
midi_in = rtmidi.RtMidiIn()
available_ports = range(midi_in.getPortCount())

akai_port = 1  # Akai Should be port n.1
print(f"Opening MIDI port {akai_port}: {midi_in.getPortName(akai_port) if akai_port < len(available_ports) else 'Invalid port'}")
midi_in.openPort(akai_port)

# MIDI note number for C3 (where our sample is)
C3_MIDI = 48

# Create a mapping of MIDI note numbers to frequencies
def midi_to_freq(midi_note):
    return 440 * (2 ** ((midi_note - 69) / 12.0))

# Base sound file
base_sound_path = "piano.wav"
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
def handle_midi_message(message: MidiMessage):        
    status = message.isNoteOn()
    note = message.getNoteNumber()
    velocity = message.getVelocity()
    
    # Check if it's a note on message (144-159) with velocity > 0
    if status and velocity > 0:
        # Note on
        if note in note_sounds:
            note_sounds[note].set_volume(velocity / 127.0)  # 
            note_sounds[note].play()  
    
    # Note off is either a note on with velocity 0 or a note off message (128-143)
    # In pygame, we don't need to explicitly handle note off as sounds play once

print("Listening for MIDI messages. Press Ctrl+C to exit.")
try:
    while True:
        message = midi_in.getMessage(250)  # 250ms timeout
        if message:
            print(f"Raw MIDI message: {message}")
            handle_midi_message(message)
        # time.sleep(0.001)  # Small delay to prevent CPU hogging
except KeyboardInterrupt:
    print("Exiting...")
finally:
    midi_in.closePort()
    pygame.quit()
    print("MIDI port closed and pygame shut down.")