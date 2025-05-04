#!/usr/bin/env python3
import os
import sys
import time
import numpy as np
import sounddevice as sd

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.midi_sound_player import SoundLibrary, SoundPlayer

def main():
    # List available audio devices
    devices = SoundPlayer.list_audio_devices()
    print("Available audio devices:")
    for i, device in enumerate(devices):
        print(f"[{i}] {device['name']} ({'in' if device['max_input_channels'] > 0 else ''}{': ' + str(device['max_input_channels']) if device['max_input_channels'] > 0 else ''}{', ' if device['max_input_channels'] > 0 and device['max_output_channels'] > 0 else ''}{'out' if device['max_output_channels'] > 0 else ''}{': ' + str(device['max_output_channels']) if device['max_output_channels'] > 0 else ''})")
    
    # Find PipeWire device
    pipewire_device = None
    for i, device in enumerate(devices):
        if "pipewire" in device['name'].lower() and device['max_output_channels'] > 0:
            pipewire_device = i
            print(f"Found PipeWire device: [{pipewire_device}] {device['name']}")
            break
    
    # Allow user to select device
    device_choice = input(f"Select audio device (default: {'PipeWire' if pipewire_device is not None else 'system default'}): ")
    if device_choice.strip():
        try:
            device_index = int(device_choice)
            selected_device = device_index
        except ValueError:
            selected_device = pipewire_device if pipewire_device is not None else None
    else:
        selected_device = pipewire_device if pipewire_device is not None else None
    
    # Create a sound library and player
    library = SoundLibrary(device=selected_device)
    player = SoundPlayer(device=selected_device)
    
    # Load some sound files
    sounds_dir = os.path.join(os.path.dirname(__file__), 'sounds')
    
    # Check if the sounds directory exists
    if not os.path.exists(sounds_dir):
        print(f"Creating sounds directory: {sounds_dir}")
        os.makedirs(sounds_dir)
        print("Please add some .wav files to the sounds directory and run again.")
        return
    
    # Load all sound files in the sounds directory
    for filename in os.listdir(sounds_dir):
        if filename.lower().endswith('.wav'):
            name = os.path.splitext(filename)[0]
            file_path = os.path.join(sounds_dir, filename)
            # Assume middle C (MIDI note 60) as the base note
            library.add_sound(name, file_path, base_note=60)
            print(f"Loaded sound: {name}")
    
    # Check if any sounds were loaded
    sound_names = library.get_sound_names()
    if not sound_names:
        print("No sound files found. Please add some .wav files to the sounds directory.")
        return
    
    # Test playing each sound at different pitches
    for name in sound_names:
        print(f"Testing sound: {name}")
        sound_data, base_note = library.get_sound(name)
        
        # Play the sound at different pitches
        for semitones in [-12, -7, -5, 0, 5, 7, 12]:
            note = base_note + semitones
            print(f"  Playing at {semitones:+d} semitones (MIDI note {note})")
            player.play_note(note, sound_data, base_note)
            time.sleep(1)
            player.stop_note(note)
            time.sleep(0.5)

if __name__ == "__main__":
    main()