#!/usr/bin/env python3
"""
Test script for the MIDI sound player.
"""
import sys
import time
import argparse
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the package modules directly
from src.midi_sound_player import MidiListener, SoundLibrary, load_pipewire_device
import sounddevice as sd

def main():
    parser = argparse.ArgumentParser(description='Test MIDI sound playback')
    parser.add_argument('--sounds', type=str, required=True, 
                       help='Directory containing sound files')
    parser.add_argument('--port', type=int, default=1,
                       help='MIDI input port (default: 1)')
    parser.add_argument('--config', type=str,
                       help='Configuration file (optional)')
    parser.add_argument('--device', type=int, default=9,
                       help='PipeWire device ID (default: 8)')
    args = parser.parse_args()
    
    # Configure audio device
    device_config = load_pipewire_device(args.device, 64, 64)
    sd.default.device = device_config['id']
    
    # Print available devices
    print("Available audio devices:")
    print(sd.query_devices())
    print(f"Using device: {sd.default.device}")
    
    # Initialize sound library
    sound_lib = SoundLibrary(args.sounds)
    
    # Load configuration if provided
    if args.config and Path(args.config).exists():
        sound_lib.load_configuration(args.config)
    
    # Print available sounds
    print("\nAvailable sounds:")
    for sound in sound_lib.get_available_sounds():
        print(f"- {sound}")
    
    # If no sounds are assigned to channels, assign defaults
    if not sound_lib.channel_sounds:
        available = sound_lib.get_available_sounds()
        if available:
            print("\nAssigning default sound to channel 0...")
            sound_lib.assign_sound_to_channel(0, available[0])
    
    print("\nChannel assignments:")
    for channel, sound_path in sound_lib.channel_sounds.items():
        for name, path in sound_lib.available_sounds.items():
            if path == sound_path:
                print(f"Channel {channel}: {name}")
                break
    
    # Start MIDI listener
    print(f"\nListening for MIDI on port {args.port}...")
    print("Press Ctrl+C to stop")
    
    # Create and start the MIDI listener
    midi_listener = MidiListener(sound_lib, port=args.port)
    
    try:
        # Keep the script running
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        # Clean up
        midi_listener.close()

if __name__ == "__main__":
    main()