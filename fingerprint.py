import hashlib
from operator import itemgetter
import numpy as np
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt

from scipy.ndimage.filters import maximum_filter
from scipy.ndimage.morphology import (generate_binary_structure, iterate_structure, binary_erosion)

IDX_FREQ_I = 0
IDX_TIME_J = 1
DEFAULT_FS = 44100
DEFAULT_WINDOW_SIZE = 4096
DEFAULT_OVERLAP_RATIO = 0.5
DEFAULT_FAN_VALUE = 15
DEFAULT_AMP_MIN = 10
PEAK_NEIGHBORHOOD_SIZE = 20
MIN_HASH_TIME_DELTA = 0
MAX_HASH_TIME_DELTA = 200
PEAK_SORT = True
FINGERPRINT_REDUCTION = 20

def fingerprint(channel_samples, Fs = DEFAULT_FS, wsize = DEFAULT_WINDOW_SIZE, wratio = DEFAULT_OVERLAP_RATIO, fan_value = DEFAULT_FAN_VALUE, amp_min = DEFAULT_AMP_MIN, plots = False):
    # if plots:
    #     plt.plot(channel_samples)
    #     plt.title('%d samples' % len(channel_samples))
    #     plt.xlabel('time (s)')
    #     plt.ylabel('amplitude (A)')
    #     plt.show()
    #     plt.gca().invert_yaxis()
    
    arr2D = mlab.specgram(channel_samples, NFFT = wsize, Fs = Fs, window = mlab.window_hanning, noverlap = int(wsize * wratio))[0]

    # if plots:
    #     plt.plot(arr2D)
    #     plt.title('FFT')
    #     plt.show()
    
    arr2D = 10 * np.log10(arr2D)
    arr2D[arr2D == -np.inf] = 0

    local_maxima = get_2D_peaks(arr2D, plot = plots, amp_min = amp_min)
    #print(f"local_maxima: {local_maxima} of frequency and time pairs.")

    return generate_hashes(local_maxima, fan_value = fan_value)

def get_2D_peaks(arr2D, plot = False, amp_min = DEFAULT_AMP_MIN):
    struct = generate_binary_structure(2, 1)
    neighbourhood = iterate_structure(struct, PEAK_NEIGHBORHOOD_SIZE)

    local_max = maximum_filter(arr2D, footprint= neighbourhood) == arr2D
    background = (arr2D == 0)
    eroded_background = binary_erosion(background, structure = neighbourhood, border_value= 1)

    detected_peaks = local_max ^ eroded_background

    amps = arr2D[detected_peaks]
    j, i = np.where(detected_peaks)

    amps = amps.flatten()
    peaks = zip(i, j, amps)
    peaks_filtered = [x for x in peaks if x[2] > amp_min]

    frequency_idx = [x[1] for x in peaks_filtered]
    time_idx = [x[0] for x in peaks_filtered]

    if plot:
        fig, ax = plt.subplots()
        ax.imshow(arr2D)
        ax.scatter(time_idx, frequency_idx)
        ax.set_xlabel('Time')
        ax.set_ylabel('Frequency')
        ax.set_title("Spectrogram")
        plt.gca().invert_yaxis()
        plt.show()

    return list(zip(frequency_idx, time_idx))

def generate_hashes(peaks, fan_value = DEFAULT_FAN_VALUE):
    if PEAK_SORT:
        peaks.sort(key = itemgetter(1))
    
    for i in range(len(peaks)):
        for j in range(1, fan_value):
            if (i + j) < len(peaks):
                freq1 = peaks[i][IDX_FREQ_I]
                freq2 = peaks[i + j][IDX_FREQ_I]

                t1 = peaks[i][IDX_TIME_J]
                t2 = peaks[i + j][IDX_TIME_J]

                t_delta = t2 - t1

                if t_delta >= MIN_HASH_TIME_DELTA and t_delta <= MAX_HASH_TIME_DELTA:
                    h = hashlib.sha1(f"{str(freq1)}|{str(freq2)}|{str(t_delta)}".encode("utf-8"))
                    yield(h.hexdigest()[0:FINGERPRINT_REDUCTION], t1)