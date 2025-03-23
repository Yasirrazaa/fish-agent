import pyaudio
import wave
import time
import sys

def record_audio(filename="test_audio.wav", duration=15, sample_rate=16000):
    """
    Record audio for testing voice cloning
    Duration: default 15 seconds
    """
    chunk = 1024
    format = pyaudio.paInt16
    channels = 1
    
    # Initialize PyAudio
    p = pyaudio.PyAudio()
    
    print(f"Starting recording for {duration} seconds...")
    print("Please speak clearly into your microphone")
    
    # Open stream
    stream = p.open(format=format,
                   channels=channels,
                   rate=sample_rate,
                   input=True,
                   frames_per_buffer=chunk)
    
    frames = []
    
    # Record audio
    for i in range(0, int(sample_rate / chunk * duration)):
        sys.stdout.write(f"\rRecording: {i * chunk / sample_rate:.1f}s / {duration}s")
        sys.stdout.flush()
        data = stream.read(chunk)
        frames.append(data)
    
    print("\nFinished recording!")
    
    # Stop and close stream
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    # Save the recorded audio
    wf = wave.open(filename, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(format))
    wf.setframerate(sample_rate)
    wf.writeframes(b''.join(frames))
    wf.close()
    
    print(f"Audio saved to {filename}")

if __name__ == "__main__":
    try:
        record_audio()
    except KeyboardInterrupt:
        print("\nRecording cancelled.")
    except Exception as e:
        print(f"Error: {str(e)}")
