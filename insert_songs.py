#!/usr/bin/python
import os
import sys
import fingerprint as fingerprint

from file_decoder import Decoder
from db_sqlite import SqliteDatabase
from config import get_config

if __name__ == "__main__":
    config = get_config()

    db = SqliteDatabase()
    path = "mp3/"

    for filename in os.listdir(path):
        if filename.endswith(".mp3"):
            reader = Decoder(path + filename)
            audio = reader.parse_audio()

            song = db.get_song_by_filehash(audio["file_hash"])
            song_id = db.add_song(filename, audio["file_hash"])

            channel_amount = len(audio["channels"])
            print(f"\nsong_id: {song_id} | No. of channels: {channel_amount} | File name: {filename}\n")

            if song:
                hash_count = db.get_song_hashes_count(song_id)

                if hash_count > 0:
                    print(f"{song} already exists, skipping. Hahes count = {hash_count}")

                    continue
                print(f"Analysing new song: {song}")

            hashes = set()

            for channeln, channel in enumerate(audio["channels"]):
                print(f"Fingerprinting channel: {channeln+1}/{channel_amount}")

                channel_hashes = fingerprint.fingerprint(channel, Fs = audio["Fs"], plots = config["fingerprint.show_plots"])
                channel_hashes = set(channel_hashes)

                print(f"Finished channel {channeln+1}/{channel_amount}, total done: {len(channel_hashes)}\n")

                hashes |= channel_hashes
            
            values = []
            for hash, offset in hashes:
                values.append((song_id, hash, offset))
            
            db.store_fingerprints(values)
    
    print("Done.\n")