import os
import sys

from matplotlib.pyplot import fill
import fingerprint
import argparse

from argparse import RawDescriptionHelpFormatter
from itertools import zip_longest
from config import get_config
from reader_microphone import MicrophoneReader
from visualiser_console import VisualiserConsole as visual_peak
from visualiser_plot import VisualiserPlot as visual_plot
from db_sqlite import SqliteDatabase
from collections import Counter

from recommendation import recommend_song

if __name__ == "__main__":
    config = get_config()

    db = SqliteDatabase()

    parser = argparse.ArgumentParser(formatter_class= RawDescriptionHelpFormatter)
    parser.add_argument("-s", "--seconds", nargs="?")
    args = parser.parse_args()

    if not args.seconds:
        parser.print_help()
        sys.exit(0)
    
    seconds = int(args.seconds)

    chunksize = 2**12
    channels = 2

    record_forever = False
    visualise_console = bool(config["mic.visualise_console"])
    visualise_plot = bool(config["mic.visualise_plot"])

    reader = MicrophoneReader(None)

    print("Started recording...")
    reader.start_recording(seconds = seconds, chunksize = chunksize, channels = channels)

    while True:
        bufferSize = int(reader.rate / reader.chunksize * seconds)
        for i in range(0, bufferSize):
            nums = reader.process_recording()

            if visualise_console:
                print(f"    {visual_peak.calc(nums)}")
            else:
                print(f"    processing {i} of {bufferSize}")
            
        if not record_forever: break
    
    if visualise_plot:
        data = reader.get_recorded_data()[0]
        visual_plot.show(data)
    
    reader.stop_recording()

    print("Recording stopped.")

    def grouper(iterable, n, fillvalue = None):
        args = [iter(iterable)] * n
        #filter_return = list(filter(None, values) for values in zip_longest(*args, fillvalue = fillvalue))
        filter_return = [x for x in zip_longest(fillvalue = fillvalue, *args) if x is not None]
        return filter_return
    
    data = reader.get_recorded_data()

    print(f"Recorded {len(data[0])} samples.")
    Fs = fingerprint.DEFAULT_FS
    channel_amount = len(data)

    result = set()
    matches = []

    def find_matches(samples, Fs = fingerprint.DEFAULT_FS):
        hashes = fingerprint.fingerprint(samples, Fs = Fs)
        return return_matches(hashes)
    
    def return_matches(hashes):
        mapper = {}
        for hash, offset in hashes:
            mapper[hash.upper()] = offset
        values = mapper.keys()

        for split_values in grouper(values, len(values)):
            query_add = ', '.join('?' * len(list(split_values)))
            query = f"""
                SELECT upper(hash), song_fk, offset
                FROM fingerprints
                WHERE upper(hash) in ({query_add})
            """
            x = db.executeAll(query, list(split_values))
            # print("hereeeee" ,x)
            matches_found = len(x)

            if matches_found > 0:
                print(f"    found {matches_found} hash matches (step {len(split_values)}/{len(values)}")
            else:
                print(f"    No matches found (step {len(split_values)}/{values})")

            for hash, sid, offset in x:
                offset = int.from_bytes(offset, "big")
                # print(mapper[hash])
                # print(offset)
                # print(sid)
                yield (sid, offset - mapper[hash])
    
    for channeln, channel in enumerate(data):
        print(f"    Fingerprinting channel {channeln+1}/{channel_amount}")
        matches.extend(find_matches(channel))

        print(f"    Finished channel {channeln+1}/{channel_amount}, got {len(matches)} hashes.")
    
    def align_matches(matches):
        # diff_counter = {}
        # largest = 0
        # largest_count = 0
        # song_id = -1

        # for tup in matches:
        #     sid, diff = tup
        
        #     if diff not in diff_counter:
        #         diff_counter[diff] = {}
            
        #     if sid not in diff_counter:
        #         diff_counter[diff][sid] = 0
            
        #     diff_counter[diff][sid] += 1

        #     if diff_counter[diff][sid] > largest_count:
        #         largest = diff
        #         largest_count = diff_counter[diff][sid]
        #         song_id = sid

        diff_counter = []
        confidence = 0
        song_id = -1

        for tup in matches:
            sid, diff = tup
            if [sid, diff] not in diff_counter:
                diff_counter.append((sid, diff))
        
        def return_2nd_element(tuple1):
            return tuple1[1]

        counts = dict(Counter(x[0] for x in diff_counter))
        song_id = max(counts, key = lambda x: counts[x])
        offset_list = [x for x in diff_counter if x[0] == song_id]
        offset = min(offset_list, key = return_2nd_element)[1]
        confidence = counts[song_id]/ sum(counts.values()) * 100
        
        songM = db.get_song_by_id(song_id)

        nseconds = round(float(offset) / fingerprint.DEFAULT_FS * fingerprint.DEFAULT_WINDOW_SIZE * fingerprint.DEFAULT_OVERLAP_RATIO, 5)

        return {
            "SONG_ID": song_id,
            "SONG_NAME": songM[0],
            "CONFIDENCE": confidence,
            "OFFSET": int(offset),
            "OFFSET_SECS": nseconds
        }
    
    total_matches_found = len(matches)

    print()

    if total_matches_found > 0:
        print(f"    Found {total_matches_found} total matches")
        song = align_matches(matches)
        print(f"""\n        =>Song: {song["SONG_NAME"][1][:-4]} (id= {song["SONG_ID"]})\n        Confidence: {song["CONFIDENCE"]}""")
        # Offset: {song["OFFSET"]} ({song["OFFSET_SECS"]} seconds)\n        

        artist_name, track_title = song["SONG_NAME"][1].split(" - ")
        track_title = track_title[:-4]
        recommendation = recommend_song(artist_name, track_title)
        print("\n    Recommended songs:\n",recommendation, "\n")
    
    else:
        print("No matches found.")