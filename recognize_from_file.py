import os
import sys
from pydub import AudioSegment
from pydub.utils import audioop
import numpy as np
from db_sqlite import SqliteDatabase
import fingerprint
from itertools import count, zip_longest
from collections import Counter
from recommendation import recommend_song

path = "test_mp3/"


db = SqliteDatabase()

def Recognize(path):
    matches = []
    for filename in os.listdir(path):
        if filename.endswith(".mp3"):
            channels = parse_audio(path, filename)
        
        for samples in channels:
            matches.append(find_matches(samples))
    
    total_matches_found = len(matches)
    # print("matches[0]",matches[0])
    if total_matches_found > 0:
        print(f"    Found {total_matches_found} total matches.")
        song = align_matches(matches[0])
        print(f"""\n        => Song: {song["SONG_NAME"][1][:-4]} (id= {song["SONG_ID"]})\n           Confidence: {song["CONFIDENCE"]}""")
        # Offset: {song["OFFSET"]} ({song["OFFSET_SECS"]} seconds)\n
    
    else:
        print("No matches found.")
    
    artist_name, track_title = song["SONG_NAME"][1].split(" - ")
    track_title = track_title[:-4]
    recommendation = recommend_song(artist_name, track_title)
    print("\n    Recommended songs:\n",recommendation, "\n")

def parse_audio(path, filename):
    try:
        audiofile = AudioSegment.from_file(path + filename)

        data = np.frombuffer(audiofile._data, np.int16)

        channels = []
        for chn in range(audiofile.channels):
            channels.append(data[chn::audiofile.channels])
    
    except audioop.error:
        print("audioop.error")
        pass

    return channels

def find_matches(samples, Fs = fingerprint.DEFAULT_FS):
    hashes = fingerprint.fingerprint(samples, Fs = Fs)
    return return_matches(hashes)

def grouper(iterable, n, fillvalue = None):
    args = [iter(iterable)] * n
    #filter_return = list(filter(None, values) for values in zip_longest(*args, fillvalue = fillvalue))
    filter_return = [x for x in zip_longest(fillvalue = fillvalue, *args) if x is not None]
    return filter_return

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
        # print(x)
        matches_found = len(x)

        if matches_found >0:
            print(f"    Found {matches_found} hash matches (step {len(split_values)}/{len(values)})")
        else:
            print(f"    No matches found (step {len(split_values)}/{values})")
    
        for hash, sid, offset in x:
            offset = int.from_bytes(offset, "big")
            yield(sid, offset - mapper[hash])

def align_matches(matches):
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
        
    #     if diff not in diff_counter:
    #         diff_counter[diff] = {}
        
    #     if sid not in diff_counter:
    #         diff_counter[diff][sid] = 0
    #     diff_counter[diff][sid] += 1

    # if diff_counter[diff][sid] > largest_count:
    #     largest = diff
    #     largest_count = diff_counter[diff][sid]
    #     song_id = sid
            
    
        # print("LMAO", diff_counter)
    
    # print(type(offset))
    songM = db.get_song_by_id(song_id)

    nseconds = round(float(offset / fingerprint.DEFAULT_FS * fingerprint.DEFAULT_WINDOW_SIZE * fingerprint.DEFAULT_OVERLAP_RATIO))

    return {
        "SONG_ID": song_id,
        "SONG_NAME": songM[0],
        "CONFIDENCE": confidence,
        "OFFSET": offset,
        "OFFSET_SECS": nseconds
    }

Recognize(path)