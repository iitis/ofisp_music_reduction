import os
import pickle

import dimod


def get_file_path(folder, file_name):
    """Returns the path to the file

    :param folder: Name of the folder
    :type folder: string
    :param file_name: Name of the file
    :type file_name: string
    :return: Path to the file
    :rtype: string
    """
    return os.path.join(folder, file_name)


def store_result(file_name: str, sampleset: dimod.SampleSet):
    """Save samples to the file

    :param file_name: name of the file
    :type file_name: str
    :param sampleset: samples
    :type sampleset: dimod.SampleSet
    """
    sdf = sampleset.to_serializable()
    with open(file_name, "wb") as handle:
        pickle.dump(sdf, handle)


def load_result(file_name: str) -> dimod.SampleSet:
    """Load samples from the file

    :param file_name: name of the file
    :type file_name: str
    :return: loaded samples
    :rtype: dimod.SampleSet
    """
    file = pickle.load(open(file_name, "rb"))
    return dimod.SampleSet.from_serializable(file)
