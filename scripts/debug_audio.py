#!/usr/bin/env python3
import os
import sys
import time
import numpy as np
import sounddevice as sd

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def main():
    # List available audio devices
    devices = sd.query_devices()
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
    
    # Print the selected device
    print(f"Using audio device: {selected_device}")
    
    # Generate a simple test tone (sine wave)
    sr = 44100  # Sample rate
    duration = 2.0  # Duration in seconds
    frequency = 440.0  # A4 frequency
    
    # Create a sine wave
    t = np.linspace(0, duration, int(sr * duration), False)
    tone = 0.5 * np.sin(2 * np.pi * frequency * t)
    
    # Play the tone
    print("Playing test tone...")
    try:
        sd.play(tone, sr, device=selected_device)
        sd.wait()
        print("Tone played successfully!")
    except Exception as e:
        print(f"Error playing tone: {e}")
        
    # Try a different approach with stream
    print("\nTrying alternative approach with output stream...")
    try:
        stream = sd.OutputStream(
            samplerate=sr,
            device=selected_device,
            channels=1
        )
        stream.start()
        
        # Write the tone to the stream in chunks
        chunk_size = 1024
        for i in range(0, len(tone), chunk_size):
            chunk = tone[i:i+chunk_size]
            if len(chunk) < chunk_size:
                # Pad the last chunk if necessary
                chunk = np.pad(chunk, (0, chunk_size - len(chunk)))
            stream.write(chunk)
            print(".", end="", flush=True)
        
        print("\nFinished writing to stream!")
        stream.stop()
        stream.close()
    except Exception as e:
        print(f"Error with stream approach: {e}")

if __name__ == "__main__":
    main()