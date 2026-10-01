import sounddevice as sd

print("=== INPUT DEVICES (Microphones) ===")
for i, d in enumerate(sd.query_devices()):
    if d['max_input_channels'] > 0:
        print(f"[{i}] {d['name']} (channels={d['max_input_channels']})")

print("\n=== OUTPUT DEVICES (Speakers / Virtual Lines) ===")
for i, d in enumerate(sd.query_devices()):
    if d['max_output_channels'] > 0:
        print(f"[{i}] {d['name']} (channels={d['max_output_channels']})")
