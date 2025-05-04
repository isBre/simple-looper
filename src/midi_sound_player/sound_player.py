import sounddevice as sd
import soundfile as sf
import numpy as np
from .utils import resample

class SoundPlayer:
    def __init__(self, sample_rate=44100, blocksize=1024, device=None):
        """
        Initialize sound player.
        
        Args:
            sample_rate: Output sample rate (default=44100)
            blocksize: Output buffer size (default=1024)
            device: Output device (default=None, uses system default)
        """
        self.sample_rate = sample_rate
        self.blocksize = blocksize
        self.device = device
        self.sounds = {}  # Cache for loaded sounds
        self.instances = {}  # Active sound instances
        self.next_id = 0
    
    def load_sound(self, filepath):
        """Load sound file into memory."""
        if filepath in self.sounds:
            return self.sounds[filepath]
            
        data, sr = sf.read(filepath, dtype='float32')
        
        # Convert stereo to mono if needed
        if len(data.shape) > 1 and data.shape[1] > 1:
            data = np.mean(data, axis=1)
        
        # Cache the sound data and its sample rate
        self.sounds[filepath] = (data, sr)
        return data, sr
    
    def play_sound(self, filepath, freq=None, volume=1.0, loop=False):
        """
        Start playing a sound.
        
        Args:
            filepath: Path to sound file
            freq: Target frequency (for pitch shifting)
            volume: Playback volume (0.0-1.0)
            loop: Whether to loop the sound
            
        Returns:
            sound_id: ID of the sound instance
        """
        # Load the sound file
        data, sr = self.load_sound(filepath)
        
        # Resample if frequency is specified
        if freq is not None:
            data = resample(data, sr, freq)
        
        # Apply volume
        data = data * volume
        
        # Create a streaming instance
        instance_id = self._get_next_id()
        self.instances[instance_id] = {
            'data': data,
            'position': 0,
            'volume': volume,
            'loop': loop,
            'active': True,
            'stream': None
        }
        
        # Start the audio stream
        stream = sd.OutputStream(
            samplerate=self.sample_rate,
            blocksize=self.blocksize,
            channels=1,
            callback=lambda outdata, frames, time, status: 
                self._audio_callback(outdata, frames, time, status, instance_id),
            device=self.device
        )
        
        self.instances[instance_id]['stream'] = stream
        stream.start()
        
        return instance_id
    
    def _audio_callback(self, outdata, frames, time, status, instance_id):
        """Audio callback for continuous playback."""
        if status:
            print(f"Status: {status}")
            
        if instance_id not in self.instances or not self.instances[instance_id]['active']:
            outdata.fill(0)
            return
            
        instance = self.instances[instance_id]
        
        # Calculate how much data we need
        remaining = len(instance['data']) - instance['position']
        
        if remaining >= frames:
            # We have enough data
            outdata[:] = instance['data'][instance['position']:instance['position']+frames].reshape(-1, 1)
            instance['position'] += frames
        elif instance['loop']:
            # We need to loop
            # First, copy what's left
            outdata[:remaining] = instance['data'][instance['position']:].reshape(-1, 1)
            
            # Then fill the rest with the beginning of the file, looping as needed
            to_fill = frames - remaining
            loops_needed = to_fill // len(instance['data']) + 1
            
            for i in range(loops_needed):
                start = 0
                end = min(len(instance['data']), to_fill - i * len(instance['data']))
                if end <= 0:
                    break
                    
                dest_start = remaining + i * len(instance['data'])
                dest_end = dest_start + (end - start)
                
                if dest_end <= len(outdata):
                    outdata[dest_start:dest_end] = instance['data'][start:end].reshape(-1, 1)
            
            instance['position'] = (instance['position'] + frames) % len(instance['data'])
        else:
            # Not enough data and not looping, so fill with zeros after the remaining data
            outdata[:remaining] = instance['data'][instance['position']:].reshape(-1, 1)
            outdata[remaining:].fill(0)
            
            # Mark instance as inactive
            instance['active'] = False
            instance['stream'].stop()
    
    def stop_sound(self, instance_id):
        """Stop a sound instance."""
        if instance_id in self.instances:
            if self.instances[instance_id]['stream']:
                self.instances[instance_id]['stream'].stop()
                self.instances[instance_id]['stream'].close()
            self.instances[instance_id]['active'] = False
            del self.instances[instance_id]
    
    def set_volume(self, instance_id, volume):
        """Set volume for a sound instance."""
        if instance_id in self.instances:
            # Scale the data by the ratio of new volume to old volume
            old_volume = self.instances[instance_id]['volume']
            if old_volume > 0:  # Avoid division by zero
                scale = volume / old_volume
                self.instances[instance_id]['data'] *= scale
            self.instances[instance_id]['volume'] = volume
    
    def _get_next_id(self):
        """Generate a unique ID for sound instances."""
        self.next_id += 1
        return self.next_id
    
    def cleanup(self):
        """Clean up all resources."""
        for instance_id in list(self.instances.keys()):
            self.stop_sound(instance_id)
        self.sounds.clear()