from rtmidi2 import MidiIn, NOTEON, NOTEOFF, CC, splitchannel
from .sound_player import SoundPlayer
from .utils import note_to_freq

class MidiListener:
    def __init__(self, sound_library, port=1):
        """
        Initialize MIDI listener.
        
        Args:
            sound_library: SoundLibrary instance
            port: MIDI input port (default=1)
        """
        self.sound_library = sound_library
        self.sound_player = SoundPlayer()
        self.active_notes = {}  # {note: sound_instance}
        
        self.midiin = MidiIn()
        self.midiin.open_port(port=port)
        self.midiin.callback = self._midi_callback
        
    def _midi_callback(self, msg, timestamp):
        """Process incoming MIDI messages."""
        msgtype, channel = splitchannel(msg[0])
        
        if msgtype == NOTEON:
            note, velocity = msg[1], msg[2]
            if velocity > 0:
                self._handle_note_on(channel, note, velocity)
            else:
                # Note-on with velocity 0 is equivalent to note-off
                self._handle_note_off(channel, note)
                
        elif msgtype == NOTEOFF:
            note, velocity = msg[1], msg[2]
            self._handle_note_off(channel, note)
            
        elif msgtype == CC:
            cc, value = msg[1], msg[2]
            self._handle_cc(channel, cc, value)
    
    def _handle_note_on(self, channel, note, velocity):
        """Handle note-on events."""
        # Get the configured sound for this channel
        sound_path = self.sound_library.get_sound(channel)
        if not sound_path:
            return
            
        # Calculate frequency from note
        freq = note_to_freq(note)
        
        # Start sound playback
        sound_instance = self.sound_player.play_sound(
            sound_path, 
            freq=freq, 
            volume=velocity/127.0, 
            loop=True
        )
        
        # Store the sound instance so we can stop it later
        self.active_notes[(channel, note)] = sound_instance
    
    def _handle_note_off(self, channel, note):
        """Handle note-off events."""
        # Find and stop the corresponding note
        key = (channel, note)
        if key in self.active_notes:
            self.sound_player.stop_sound(self.active_notes[key])
            del self.active_notes[key]
    
    def _handle_cc(self, channel, cc, value):
        """Handle control change events."""
        # Implement control change handling (e.g., volume, modulation)
        # This is a basic implementation that can be expanded
        if cc == 7:  # Volume
            self._set_channel_volume(channel, value/127.0)
    
    def _set_channel_volume(self, channel, volume):
        """Set volume for all active notes on channel."""
        for (ch, note), sound_instance in self.active_notes.items():
            if ch == channel:
                self.sound_player.set_volume(sound_instance, volume)
    
    def close(self):
        """Clean up resources."""
        # Stop all active sounds
        for sound_instance in self.active_notes.values():
            self.sound_player.stop_sound(sound_instance)
        self.active_notes.clear()
        
        # Close MIDI port
        self.midiin.close_port()