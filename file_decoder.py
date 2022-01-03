#!/usr/bin/python
import os
from pydub import AudioSegment
from pydub.utils import audioop
import numpy as np
from hashlib import sha1

from reader import BaseReader

class Decoder(BaseReader):
    def __init__(self, filename):
        self.filename = filename
    
    def parse_audio(self):
        limit = None

        song_name, extension = os.path.splitext(os.path.basename(self.filename))
        try:
            audiofile = AudioSegment.from_file(self.filename)

            if limit:
                audiofile = audiofile[ : limit * 1000]
            
            data = np.fromstring(audiofile._data, np.int16)

            channels = []
            for chn in range(audiofile.channels):
                channels.append(data[chn::audiofile.channels])
            
            fs = audiofile.frame_rate
        
        except audioop.error:
            print("audioop.error")
            pass

        return {
            "songname": song_name,
            "extension": extension,
            "channels": channels,
            "Fs": audiofile.frame_rate,
            "file_hash": self.unique_hash()
        }
    
    def unique_hash(self, blocksize = 2**20):
        s = sha1()

        with open(self.filename, "rb") as f:
            while True:
                buf = f.read(blocksize)
                if not buf:
                    break
                s.update(buf)
        
        return s.hexdigest().upper()