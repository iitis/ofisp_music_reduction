import math
import pickle
from collections import defaultdict

from music21 import *

from toolbox import max_num_measures


def get_pitch_int(file):
    """Calculates and returns the pitch intervals

    :param file: File to process
    :type file: music21 Stream
    :return: A dictionary containing pitch intervals for each part
    :rtype: defaultdict
    """
    pitch_int = {i: [] for i in range(len(file.parts))}
    for i, part in enumerate(file.parts):
        pitches = [
            m.pitches[-1] for m in part.flat.getElementsByClass(["Note", "Chord"])
        ]
        for p1, p2 in zip(pitches, pitches[1:]):
            intvl = interval.Interval(p1, p2)
            pitch_int[i].append(abs(intvl.chromatic.semitones) + 1)
    return pitch_int


def get_ioi(file):
    """Calculates and returns the inter offset intervals

    :param file: File to process
    :type file: music21 Stream
    :return: A dictionary containing inter offset intervals for each part
    :rtype: defaultdict
    """
    ioi = {i: [] for i in range(len(file.parts))}
    for i, part in enumerate(file.parts):
        notes = part.flat.getElementsByClass(["Note", "Chord"])
        for n1, n2 in zip(notes, notes[1:]):
            ioi[i].append(n2.offset - n1.offset)
    return ioi


def get_rests(file):
    """Calculates and returns the rest intervals

    :param file: File to process
    :type file: music21 Stream
    :return: A dictionary containing rest intervals for each part
    :rtype: defaultdict
    """
    rests = {i: [] for i in range(len(file.parts))}
    for i, part in enumerate(file.parts):
        notes = part.flat.getElementsByClass(["Note", "Chord"])
        for n1, n2 in zip(notes, notes[1:]):
            rests[i].append(
                max(0, n2.offset - n1.offset + n1.duration.quarterLength) + 1
            )
    return rests


# TODO check the list is initalized with 0
def get_doc(intervals):
    """Calculates and returns the degree of change given intervals

    :param intervals: Dictionary containing intervals for each part
    :type intervals: defaultdict
    :return: A dictionary containing degree of change information for each part
    :rtype: defaultdict
    """
    no_parts = len(intervals)
    rdict = defaultdict(lambda: [0])
    for i in range(no_parts):
        rdict[i] += [
            abs(int2 - int1) / (int1 + int2)
            for int1, int2 in zip(intervals[i], intervals[i][1:])
        ]
    return rdict


def get_strength(intervals, doc):
    """Calculates boundary strength given the intervals and degree of change

    :param intervals: Dictionary containing intervals for each part
    :type intervals: defaultdict
    :param doc: Degree of change information for each part
    :type doc: defaultdict
    :return: Dictionary containing boundary strengths for each part
    :rtype: defaultdict
    """
    no_parts = len(intervals)
    sdict = defaultdict(list)
    for i in range(no_parts):
        slist = [
            intervals[i][j + 1] * (doc[i][j] + doc[i][j + 1])
            for j in range(len(intervals[i]) - 1)
        ]
        s = sum(slist)
        if s != 0:
            slist = [r / s for r in slist]
        sdict[i] = slist
    return sdict


def get_measures(file):
    """Gives information about which pitch belongs to which measure

    :param file: File to process
    :type file: music21 Stream
    :return: A dictionary of lists where each list is the list of measures corresponding to the pitches in each part
    :rtype: defaultdict
    """
    no_parts = len(file.parts)
    measures = defaultdict(list)
    for i in range(no_parts):
        for n in file.parts[i].flat.getElementsByClass(["Note", "Chord"]):
            measures[i].append(n.measureNumber)
    return measures


def find_peaks_t(bs, threshold):
    """Find the peaks in a list that are above a threshold value

    :param bs: The list to analyze consisting of boundary strength for each pitch
    :type bs: list
    :param threshold: The threshold value
    :type threshold: float
    :return: The list of indices that correspond to the peaks
    :rtype: list
    """

    return [
        i
        for i in range(1, len(bs) - 1)
        if bs[i] > bs[i + 1] and bs[i - 1] < bs[i] and bs[i] >= threshold
    ]


def find_peaks(file, bs, measures, longest_phrase):
    """Finds the peaks in in array, based on the condition that the longest phrase should not exceed a limit. If no solution is found, then the limit in increased. To guide the process, a threshold value is used, which is decreased at each iteration.

    :param file: File to process
    :type file: music21 Stream
    :param bs: The list to analyze consisting of boundary strength for each pitch
    :type bs: list
    :param measures: The list of measures corresponding to each pitch
    :type measures: list
    :param longest_phrase: The upper bound on the longest phrase length
    :type longest_phrase: int
    :return: A list of measures indicating phrase beginning and endings
    :rtype: list
    """
    if len(bs) != 0:
        min_bs = min(x for x in bs if x != 0)
        threshold = max(bs)
        flag = True
        while flag:
            flag = False
            plist = find_peaks_t(bs, threshold)
            if not plist:
                threshold -= 2 * min_bs
                flag = True
                continue
            phrase_start_end = find_peak_measures(file, measures, plist)
            for pair in phrase_start_end:
                if pair[1] - pair[0] + 1 > longest_phrase:
                    flag = True
                    threshold -= 2 * min_bs
                    if threshold < 0:
                        threshold = max(bs)
                        longest_phrase += 1
                        # print("is this happening?")
                    break
        return phrase_start_end
    else:
        return []


def is_longest_satified(phrase_start_end, longest_phrase):
    """Check if longest phrase condition is satisfied

    :param phrase_start_end: A list of measures indicating phrase beginning and endings
    :type phrase_start_end: list
    :param longest_phrase: The maximal number of measures in the phrase
    :type longest_phrase: Int
    :return: True if is satisfied, False if is not satisfied
    :rtype: boolean
    """
    for pair in phrase_start_end:
        if pair[1] - pair[0] + 1 > longest_phrase:
            return False
    return True


def find_peaks_v2(file, bs, measures, longest_phrase):
    """Finds the peaks in in array, based on the condition that the longest phrase should not exceed a limit. If no solution is found, then the limit in increased. To guide the process, a threshold value is used, which is decreased at each iteration.

    :param file: File to process
    :type file: music21 Stream
    :param bs: The list to analyze consisting of boundary strength for each pitch
    :type bs: list
    :param measures: The list of measures corresponding to each pitch
    :type measures: list
    :param longest_phrase: The upper bound on the longest phrase length
    :type longest_phrase: int
    :return: A list of measures indicating phrase beginning and endings
    :rtype: list
    """
    if len(bs) != 0:
        min_bs = min(x for x in bs if x != 0)
        max_bs = max(bs)
        threshold = (min_bs + max_bs) / 2
        flag = True
        found_threshold = None
        while flag:
            plist = find_peaks_t(bs, threshold)
            if not plist:
                flag = True
                max_bs = threshold
                threshold = (min_bs + max_bs) / 2
                if math.isclose(min_bs, max_bs):
                    phrase_start_end = find_peak_measures(file, measures, plist)
                    flag = False
                continue
            phrase_start_end = find_peak_measures(file, measures, plist)
            if not is_longest_satified(
                phrase_start_end, longest_phrase
            ):  # if longest phrasee condition is not satisfied
                flag = True
                max_bs = threshold
                threshold = (min_bs + max_bs) / 2  # decrease the threshold
                if threshold - min_bs < 0.00001:  # stopping condition
                    if (
                        found_threshold != None
                    ):  # if there was a found threshold and we were looking for better
                        plist = find_peaks_t(bs, found_threshold)
                        phrase_start_end = find_peak_measures(file, measures, plist)
                        return phrase_start_end
                    else:
                        max_bs = max(
                            bs
                        )  # reset to the initial conditions, increase longest allowed phrase
                        min_bs = min(x for x in bs if x != 0)
                        threshold = (min_bs + max_bs) / 2
                        longest_phrase += 1
            else:  # if longest phrasee condition is satisfied
                found_threshold = threshold
                min_bs = threshold
                threshold = (min_bs + max_bs) / 2  # increase the threshold
                if max_bs - threshold < 0.00001:  # stopping condition
                    flag = False
        return phrase_start_end
    else:
        return []


def find_peak_measures(file, measures, plist):
    """Given a list of pitches that correspond to peaks, it returns the corresponding measures. If same measure is selected more than once, then it is taken only once

    :param file: File to process
    :type file: music21 Stream
    :param measures: The list of measures corresponding to each pitch
    :type measures:list
    :param plist: The list of indices that correspond to the peaks
    :type plist: list
    :return: The list of measures corresponding to the peaks
    :rtype: list
    """
    if not plist:
        phrase_start_end = []
        measure_list = sorted(list(set(measures)))
        temp = measure_list[0]
        for m, n in zip(measure_list, measure_list[1:]):
            if n - m != 1:
                phrase_start_end.append([temp, m])
                temp = n
        phrase_start_end.append([temp, measure_list[-1]])

    else:
        meas_list = [measures[m] for m in plist]

        measure_list = sorted(list(set(meas_list)))
        phrase_start_end = [[measures[0], measure_list[0]]]

        for i in range(len(measure_list) - 1):
            x = find_next_non_empty(measures, measure_list[i] + 1)
            phrase_start_end.append([x, measure_list[i + 1]])
        if measure_list[-1] != max_num_measures(file):
            x = find_next_non_empty(measures, measure_list[-1] + 1)
            phrase_start_end.append([x, measures[-1]])
    return phrase_start_end


def find_next_non_empty(measures, meas_num):
    for measure in measures:
        if measure >= meas_num:
            return measure


def calculate_lbsp(file, ldict):
    """Given a file and a dictionary containing the weights, returns the lbsp

    :param file: File to process
    :type file: music21 Stream
    :param ldict: Dictionary containing weights for pitch, ioi and rests
    :type ldict: dict
    :return: lbsp for each part
    :rtype: defaultdict
    """
    pitch_int = get_pitch_int(file)
    rpitch = get_doc(pitch_int)
    spitch = get_strength(pitch_int, rpitch)

    ioi = get_ioi(file)
    rioi = get_doc(ioi)
    sioi = get_strength(ioi, rioi)

    rests = get_rests(file)
    rrests = get_doc(rests)
    srests = get_strength(rests, rrests)

    no_parts = len(file.parts)
    lbsp = defaultdict(list)

    for i in range(no_parts):
        lbsp[i] = [
            ldict["p"] * pitch + ldict["i"] * ioi + ldict["r"] * rest
            for pitch, ioi, rest in zip(spitch[i], sioi[i], srests[i])
        ]

    return lbsp


def get_phrase_list(file, longest_phrase, ldict):
    """Given the upper bound for the longest phrase and the weights, returns the measures corresponding to the beginning and ending of the phrases

    :param file: File to process
    :type file: music21 Stream
    :param longest_phrase: Upper bound on the longest phrase
    :type longest_phrase: int
    :param ldict: Dictionary containing weights for pitch, ioi and rests
    :type ldict: dict
    :return: Measures indicating beginning and the end of the phrases for e ach part
    :rtype: defaultdict
    """
    phrase_measures = defaultdict(list)
    measures = get_measures(file)
    lbsp = calculate_lbsp(file, ldict)
    for i in range(len(file.parts)):
        phrase_measures[i] = find_peaks_v2(file, lbsp[i], measures[i], longest_phrase)
    return phrase_measures


def is_all_silence(part, meas_start, meas_ends):
    """Checks whether the given measure is silent

    :param part: Part of the file
    :type part: Music21 Part
    :param meas_start: First measure
    :type meas_start: int
    :param meas_ends: Last measure
    :type meas_ends: int
    :return: True if it is all silent, False otherwise
    :rtype: Boolean
    """
    return (
        len(
            part.measures(meas_start, meas_ends).flat.getElementsByClass(
                ["Note", "Chord"]
            )
        )
        == 0
    )


def modify_phrase_list(phrase_measures, file):
    """Updates the phrase list so that all silent measures are removed

    :param phrase_measures: Dictionary containing the measures list for each track
    :type phrase_measures: dictionary
    :param file: Music file
    :type file: Music21 Stream
    :return: Dictionary containing the measure list for each track after the slient measures are removed
    :rtype: dictionary
    """
    for track in phrase_measures:
        phrase_measures[track] = [
            p in phrase_measures[track]
            for p in phrase_measures[track]
            if not is_all_silence(file.parts[track], p[0], p[1])
        ]
    return phrase_measures


def generate_phrase_list(
    file, phrase_path, longest_phrase=4, weights={"p": 0.25, "i": 0.5, "r": 0.25}
):
    """Generate the phrase list given the file

    :param file: Music file
    :type file: Music21 Stream
    :param phrase_path: Path to save the phrases
    :type phrase_path: string
    :param longest_phrase: Longest phrase length in terms of measures
    :type longest_phrase: 4
    :param weights: Dictionary containing the weights for the phrase generation
    :type weights: dictionary
    :return: The list of phrases
    :rtype: dictionary
    """

    phrase_list = get_phrase_list(file, longest_phrase, weights)
    filehandler = open(phrase_path, "wb")
    pickle.dump(phrase_list, filehandler)

    return phrase_list
