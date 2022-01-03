import pandas as pd
import numpy as np

from sklearn.cluster import KMeans
from sklearn.utils import shuffle
import pickle

def fit(df, algo, flag = 0):
    if flag:
        algo.fit(df)
    else:
        algo.partial_fit(df)
    df["label"] = algo.labels_
    return (df, algo)

def predict(t, Y):
    y_pred = t[1].predict(Y)
    mode = pd.Series(y_pred).mode()
    return t[0][t[0]["label"] == mode.loc[0]]

def recommend(recommendations, meta, Y):
    dat = []
    for i in Y["track_id"]:
        dat.append(i)
    genre_mode = meta.loc[dat]["genre"].mode()
    artist_mode = meta.loc[dat]["artist_name"].mode()
    #return meta[meta["genre"] == genre_mode.iloc[0], meta["artist_name"] == artist_mode.iloc[0], meta.loc[recommendations['track_id']]]
    # return meta[meta.loc[recommendations['track_id']]]
    pass

def recommend_song(artist_name, track_name):
    with open("model.pkl", "rb") as f:
        t = pickle.load(f)
        f.close()
    
    meta = pd.read_csv(r"D:\AUDIOFINGERPRINTING_FINAL\datasets\final\metadata.csv")
    final = pd.read_csv(r"D:\AUDIOFINGERPRINTING_FINAL\datasets\final\final.csv")
    data = meta.loc[meta["track_title"] == track_name]
    data = data.loc[data["artist_name"] == artist_name]
    Y = final.loc[final["track_id"] == data.iloc[0,0]].iloc[:,1:]
    prediction = predict(t, Y)
    # metaOne = meta.reindex(["track_id", "album_title", "artist_name", "genre", "track_title"])
    # print(prediction["track_id"])
    # output = metaOne.loc[prediction["track_id"]]
    # print(meta.loc[prediction.iloc[0:5,0]])
    # output = pd.DataFrame( columns = ["track_id", "album_title", "artist_name", "genre", "track_title"])
    # output = pd.DataFrame(meta.loc[meta["track_id"] == 10062])
    # print("here", output)
    # for x in prediction.iloc[0:5,0]:
    #     # print(meta.loc[meta["track_id"] == x])
    #     pd.concat([output, meta.loc[meta["track_id"] == x]])
    # print("final", output)
    songs_artists = []
    songs_titles = []
    for x in prediction.iloc[0:5,0]:
        song_details = meta.loc[meta["track_id"] == x]
        songs_artists.extend(list(song_details["artist_name"]))
        songs_titles.extend(list(song_details["track_title"]))
    
    output = pd.DataFrame({"track_title": songs_titles, "artist_name": songs_artists})
    return output