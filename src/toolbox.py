import numpy as np


def get_pitches(phrase):
    """Given phrases, it returns list of notes pitches

    :param phrase: list of phrases (music21 file)
    :type phrase: list
    :return: list of pitches
    :rtype: list
    """
    pitches_list = []
    for nt in phrase.flat.getElementsByClass(["Note", "Chord"]):
        pitches_list.append(nt.pitches[-1].ps)
    return pitches_list


def get_ioi_list(phrase):
    """Given phrase, it returns list of Interonset interval (ioi)

    :param phrase: list of phrases (music21 file)
    :type phrase: list
    :return: list of ioi
    :rtype: list
    """
    ioi_list = []
    notes = phrase.flat.getElementsByClass(["Note", "Chord"])
    for n1, n2 in zip(notes, notes[1:]):
        ioi_list.append(n2.offset - n1.offset)
    return ioi_list


def get_list_entropy(a_list):
    """Retuns the entropy of elements of a list

    :param a_list: list
    :type a_list: list
    :return: entropy of list elements
    :rtype: float
    """
    unique, counts = np.unique(a_list, return_counts=True)
    # dict(zip(unique, counts/num_pitches))
    list_entropy = sum([-p * np.log(p) for p in counts / len(a_list)])
    return list_entropy


def get_entropy(file, track, meas_start, meas_end):
    """Given a measure, calculates its entropy

    :param file: Music file
    :type file: Music21 File
    :param track: Track number
    :type track: int
    :param meas_start: First measure
    :type meas_start: int
    :param meas_end: Last measure
    :type meas_end: int
    :return: entropy
    :rtype: float
    """
    # file = file.stripTies()
    E_p = get_pitches(file.parts[track].measures(meas_start, meas_end).flat)
    E_ioi = get_ioi_list(file.parts[track].measures(meas_start, meas_end).flat)
    return get_list_entropy(E_p) + get_list_entropy(E_ioi)


def max_num_measures(file):
    """Returns the number of measures in the file

    :param file: Music file
    :type file: Music21 Stream
    :return: Number of measures in the file
    :rtype: int
    """
    return max([len(p) for p in file.parts])
