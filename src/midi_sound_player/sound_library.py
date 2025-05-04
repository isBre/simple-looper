import os
import json
from pathlib import Path

class SoundLibrary:
    def __init__(self, sounds_dir=None):
        """
        Initialize sound library.
        
        Args:
            sounds_dir: Directory containing sound files (default=None)
        """
        self.sounds_dir = sounds_dir
        self.channel_sounds = {}  # {channel: sound_file}
        self.available_sounds = {}  # {name: filepath}
        
        if sounds_dir:
            self.scan_sounds_directory(sounds_dir)
    
    def scan_sounds_directory(self, directory):
        """Scan directory for sound files."""
        directory = Path(directory)
        
        if not directory.exists() or not directory.is_dir():
            raise ValueError(f"Invalid sounds directory: {directory}")
        
        # Scan for WAV files
        for file_path in directory.glob("**/*.wav"):
            rel_path = file_path.relative_to(directory)
            name = str(rel_path.with_suffix(""))
            self.available_sounds[name] = str(file_path)
    
    def get_available_sounds(self):
        """Get list of available sounds."""
        return list(self.available_sounds.keys())
    
    def assign_sound_to_channel(self, channel, sound_name):
        """
        Assign a sound to a MIDI channel.
        
        Args:
            channel: MIDI channel (0-15)
            sound_name: Name of sound from available_sounds
        """
        if sound_name not in self.available_sounds:
            raise ValueError(f"Sound '{sound_name}' not found in library")
        
        self.channel_sounds[channel] = self.available_sounds[sound_name]
    
    def get_sound(self, channel):
        """Get sound assigned to channel."""
        return self.channel_sounds.get(channel)
    
    def save_configuration(self, config_file):
        """Save current configuration to file."""
        # Create a mapping of channel to sound name
        channel_sound_names = {}
        for channel, filepath in self.channel_sounds.items():
            # Find the sound name from filepath
            for name, path in self.available_sounds.items():
                if path == filepath:
                    channel_sound_names[channel] = name
                    break
        
        config = {
            "sounds_dir": str(self.sounds_dir) if self.sounds_dir else None,
            "channel_sounds": channel_sound_names
        }
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def load_configuration(self, config_file):
        """Load configuration from file."""
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Set sounds directory if provided
        if config.get("sounds_dir"):
            self.sounds_dir = config["sounds_dir"]
            self.scan_sounds_directory(self.sounds_dir)
        
        # Assign sounds to channels
        for channel_str, sound_name in config.get("channel_sounds", {}).items():
            channel = int(channel_str)
            if sound_name in self.available_sounds:
                self.channel_sounds[channel] = self.available_sounds[sound_name]