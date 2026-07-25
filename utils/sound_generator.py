import math
import os
import struct
import wave

def generate_sine_wave(frequency_func, duration, volume=0.3, sample_rate=22050):
    """Generates sound samples using a frequency modulation function."""
    num_samples = int(sample_rate * duration)
    samples = []
    current_phase = 0.0

    for i in range(num_samples):
        t = i / sample_rate
        freq = frequency_func(t, duration)
        
        # Calculate amplitude envelope
        # Fade in/out slightly to prevent clicks
        envelope = 1.0
        if t < 0.02:
            envelope = t / 0.02
        elif t > duration - 0.02:
            envelope = (duration - t) / 0.02
            
        # Specific fade-out envelopes
        current_phase += 2 * math.pi * freq / sample_rate
        sample = math.sin(current_phase) * volume * envelope
        
        # Convert to 16-bit PCM integer
        sample_int = int(max(-32768, min(32767, sample * 32767)))
        samples.append(struct.pack('<h', sample_int))
        
    return b"".join(samples)

def write_wav(filepath, data, sample_rate=22050):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with wave.open(filepath, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)   # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(data)

def generate_all_sounds(sound_dir):
    """Generates all the buddy sound effects."""
    os.makedirs(sound_dir, exist_ok=True)
    
    # 1. Boing sound (Jumping)
    def boing_freq(t, dur):
        # Sweeps up rapidly from 150 to 550 Hz
        return 150 + (t / dur) ** 2 * 400
    boing_data = generate_sine_wave(boing_freq, 0.25, volume=0.25)
    write_wav(os.path.join(sound_dir, "boing.wav"), boing_data)

    # 2. Whoosh sound (Running/escaping)
    def whoosh_freq(t, dur):
        # Sweeps down from 800 to 200 Hz
        return 800 - (t / dur) * 600
    whoosh_data = generate_sine_wave(whoosh_freq, 0.2, volume=0.15)
    write_wav(os.path.join(sound_dir, "whoosh.wav"), whoosh_data)

    # 3. Yawn sound (Sleeping)
    def yawn_freq(t, dur):
        # Sweeps down from 350 to 180 Hz, volume fades out
        return 350 - (t / dur) * 170
    # Custom yawn generator with steep volume fade out
    yawn_samples = []
    sample_rate = 22050
    duration = 0.8
    current_phase = 0.0
    for i in range(int(sample_rate * duration)):
        t = i / sample_rate
        freq = yawn_freq(t, duration)
        # Slow fade out envelope
        envelope = math.cos((t / duration) * (math.pi / 2)) * 0.2
        if t < 0.05:
            envelope *= (t / 0.05)
        current_phase += 2 * math.pi * freq / sample_rate
        sample = math.sin(current_phase) * envelope
        sample_int = int(max(-32768, min(32767, sample * 32767)))
        yawn_samples.append(struct.pack('<h', sample_int))
    write_wav(os.path.join(sound_dir, "yawn.wav"), b"".join(yawn_samples))

    # 4. Hehe sound (Laughing/giggling)
    # Composed of two short chuckles
    chuckle_duration = 0.07
    pause_duration = 0.05
    def chuckle_freq(t, dur):
        return 500 + t * 100
    chuckle_data = generate_sine_wave(chuckle_freq, chuckle_duration, volume=0.2)
    pause_data = b"\x00" * int(22050 * pause_duration * 2)  # 2 bytes per sample (16-bit)
    hehe_data = chuckle_data + pause_data + chuckle_data
    write_wav(os.path.join(sound_dir, "hehe.wav"), hehe_data)

    # 5. Greet sound (Waving/saying Hello)
    # A quick C major arpeggio
    greet_samples = []
    # Note 1: E5 (659 Hz) for 0.08s
    # Note 2: G5 (784 Hz) for 0.12s
    def note1_freq(t, dur): return 659.0
    def note2_freq(t, dur): return 784.0
    note1_data = generate_sine_wave(note1_freq, 0.08, volume=0.2)
    note2_data = generate_sine_wave(note2_freq, 0.14, volume=0.2)
    greet_data = note1_data + note2_data
    write_wav(os.path.join(sound_dir, "greet.wav"), greet_data)

    # 6. Caught sound (Sigh/cry)
    def cry_freq(t, dur):
        # Vibrato effect around 300 Hz
        return 300 + math.sin(t * 40) * 40
    cry_data = generate_sine_wave(cry_freq, 0.35, volume=0.25)
    write_wav(os.path.join(sound_dir, "caught.wav"), cry_data)

if __name__ == "__main__":
    import sys
    # Generate sounds in assets/sounds/
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "../assets/sounds"
    generate_all_sounds(target_dir)
    print("Sound effects generated successfully.")
