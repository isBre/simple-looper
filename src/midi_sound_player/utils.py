import numpy as np
import scipy.signal as signal

def note_to_freq(note):
    """
    Convert MIDI note number to frequency.
    
    Args:
        note: MIDI note number (0-127)
        
    Returns:
        frequency in Hz
    """
    return 440.0 * (2.0 ** ((note - 69) / 12.0))

def freq_to_note(freq):
    """
    Convert frequency to closest MIDI note number.
    
    Args:
        freq: Frequency in Hz
        
    Returns:
        MIDI note number
    """
    if freq <= 0:
        return 0
    return int(round(69 + 12 * np.log2(freq / 440.0)))

def resample(data, original_sr, target_freq=None, target_note=None):
    """
    Resample audio data to match target frequency or note.
    
    Args:
        data: Audio data
        original_sr: Original sample rate
        target_freq: Target frequency (optional)
        target_note: Target MIDI note (optional)
        
    Returns:
        Resampled audio data
    """
    if target_freq is None and target_note is None:
        return data
    
    if target_note is not None:
        target_freq = note_to_freq(target_note)
    
    # Determine the original pitch
    # This is a simple implementation; for more accurate pitch detection,
    # consider using a dedicated pitch detection algorithm
    # Here we assume the sound's base frequency is A4 (440 Hz)
    base_freq = 440.0
    
    # Calculate the ratio between target and base frequency
    ratio = target_freq / base_freq
    
    # Adjust the length of the data
    new_length = int(len(data) / ratio)
    
    # Resample the data
    resampled = signal.resample(data, new_length)
    
    return resampled

def load_pipewire_device(device_id=8, in_channels=64, out_channels=64):
    """
    Helper function to setup PipeWire device.
    
    Args:
        device_id: PipeWire device ID
        in_channels: Number of input channels
        out_channels: Number of output channels
    
    Returns:
        Device configuration dict
    """
    return {
        'id': device_id,
        'name': f'pipewire ({in_channels}, {out_channels})',
        'in_channels': in_channels,
        'out_channels': out_channels
    }