from recommendation import fit, predict, recommend

import pandas as pd
import numpy as np
import pickle

from sklearn.cluster import KMeans
from sklearn.utils import shuffle

final = pd.read_csv("datasets/final/final.csv")
final.drop("delete", axis = 1, inplace = True)
final.set_index("track_id")
final = shuffle(final)

X = final.loc[[i for i in range(0, 6000)]]
Y = final.loc[[i for i in range(6000, final.shape[0])]]
X = shuffle(X)
Y = shuffle(Y)

metadata = pd.read_csv("datasets/final/metadata.csv")
metadata = metadata.set_index("track_id")

kmeans = KMeans(n_clusters = 6)

t = fit(X, kmeans, 1)

with open("model.pkl", "wb") as f:
    pickle.dump(t, f)