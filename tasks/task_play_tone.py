import sys
from pydub import AudioSegment
from pydub.playback import play

if __name__ == '__main__':
    try:
        song = AudioSegment.from_wav("./wav/100Hz_to_20000Hz_mono.wav")
        play(song)
        print("Passed")
    except :
        print("Failed")