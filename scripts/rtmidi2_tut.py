from rtmidi2 import MidiIn, NOTEON, CC, splitchannel
midiin = MidiIn()
midiin.open_port(port = 1)    # will get messages from the default port

def callback(msg: list, timestamp: float):
    # msg is a list of 1-byte strings
    # timestamp is a float with the time elapsed since last midi event
    msgtype, channel = splitchannel(msg[0])
    if msgtype == NOTEON:
        note, velocity = msg[1], msg[2]
        print(f"Noteon, {channel=}, {note=}, {velocity=}")
    elif msgtype == CC:
        cc, value = msg[1:]
        print(f"Control Change {channel=}, {cc=}, {value=}")

midiin.callback = callback


print("Listening for MIDI messages. Press Ctrl+C to exit.")
try:
    # Keep the program running until Ctrl+C is pressed
    while True:
        pass
except KeyboardInterrupt:
    print("Exiting...")
finally:
    midiin.close_port()
    print("MIDI port closed and pygame shut down.")