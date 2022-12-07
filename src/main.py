import argparse
import os
import pickle

from music21 import converter

from experiment import anneal, annealing_statistics
from jobs import job_statistics, max_weight_phrase, phrase_to_jobs
from phrase_identification import generate_phrase_list
from postprocess import *
from qubo import get_qubo
from toolbox import max_num_measures
from utils import get_file_path, load_result
import datetime


def get_out_paths(folder_dict, out_file_name, mode, a_dict, solver=None):
    """Given the folder dictionary, it returns necessary path for storing out files

    :param folder_dict: Dictionary containing names of the folders
    :type folder_dict: dictionary
    :param out_file_name: Name of the out file
    :type out_file_name: string
    :param mode: Mode of the simulation
    :type string
    :param a_dict: Dictionary of annealing parameters
    :type a_dict: dict
    :return: Names of the paths to the files
    :rtype: tuple(string, string, string)
    """
    midi_p = get_file_path(folder_dict["midi_folder"], out_file_name)
    temp = get_file_path(folder_dict["phrase_folder"], out_file_name)
    index = temp.rindex("_")
    phrase_p = temp[:index]
    results_p = get_file_path(
        get_file_path(folder_dict["results_folder"], mode), out_file_name
    )
    if mode == "sim":
        ns, nr = a_dict["ns"], a_dict["nr"]
        results_p = f"{results_p}_{nr}_{ns}"
    elif mode == "quantum":
        nr, t, rcs = a_dict["nr"], a_dict["t"], a_dict["rcs"]
        results_p = f"{results_p}_{nr}_{t}_{rcs}_{solver}"
    elif mode == "hyb":
        results_p = f"{results_p}_hyb"
    return midi_p, phrase_p, results_p


def get_phrases(file, phrase_path):
    """If the phrases already exist, it loads it. Otherwise, it generates and saves.

    :param file: Music file
    :type file: music21 Stream
    :param phrase_path: Path to the phrases
    :type phrase_path: string
    :return: List of phrases
    :rtype: list
    """
    if os.path.isfile(phrase_path):
        phrase_list = pickle.load(open(phrase_path, "rb"))
    else:
        phrase_list = generate_phrase_list(file, phrase_path)
    return phrase_list


def log_experiment(
    midi_file,
    num_measures,
    M,
    p_dict,
    mode,
    solver,
    a_dict,
    phrase_list,
    job_list,
    model,
    offset,
    result_e,
    result_n,
    results,
    sampleset,
):
    logging.info(
        "--------------------------------------New Run-----------------------------------"
    )
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logging.info(f"Date: {date}")
    logging.info(f"File: {midi_file}")
    logging.info(f"Measures: {num_measures}")
    logging.info(f"Tracks: {M}")
    logging.info(f"Penalties: {p_dict}")
    logging.info(f"Solver: {mode}")
    if mode == "quantum":
        logging.info(f"Machine: {solver}")
    logging.info(f"Annealing params: {a_dict}")
    logging.info(f"Phrase list: {phrase_list}")
    logging.info(f"Job list: {job_list}")
    job_statistics(job_list)
    logging.info(f"QUBO num variables: {len(model.variables)}\n offset: {offset}")
    logging.info(f"Best entropy result: {result_e}")
    logging.info(f"Best non-violating result: {result_n}")
    logging.info(f"First 10 samples sorted based on entropy:")
    for d in results[:10]:
        logging.info(d)
    if mode == "quantum":
        annealing_statistics(sampleset)


def music_experiment(
    midi_file, folder_dict, num_measures, M, mode, a_dict, solver, load, log
):
    """Runs the music experiment

    :param folder_dict: Dictionary containing folder names
    :type folder_dict: dictionary
    :param num_measures: Number of measures to parse, if -1, then whole song is considered
    :type num_measures: int
    :param M: Number of tracks
    :type M: int
    :param p_dict: Dictionary for QUBO penalties
    :type p_dict: dictionary
    :param mode: Simulation mode
    :type mode: string
    :param a_dict: Dictionary containing annealing parameters
    :type a_dict: dictionary
    """

    input_p = get_file_path(folder_dict["midi_folder"], midi_file)
    if not os.path.isfile(input_p):
        print("Midi file does not exist.")
        exit(1)

    file_name = midi_file[:-4]
    if num_measures == -1:
        out_file_name = f"{file_name}_{M}"
        file = converter.parse(input_p).stripTies()
        num_measures = max_num_measures(file)
    else:
        out_file_name = f"{file_name}_{num_measures}_{M}"
        file = converter.parse(input_p).measures(0, num_measures).stripTies()

    midi_p, phrase_p, results_p = get_out_paths(
        folder_dict, out_file_name, mode, a_dict, solver
    )
    phrase_list = get_phrases(file, phrase_p)

    job_list = phrase_to_jobs(phrase_list, file)
    p = max_weight_phrase(job_list)
    p_dict = {"exact": 2 * p, "less": 2 * 2 * p}

    qubo, offset, model = get_qubo(job_list, M, num_measures, p_dict)

    if load:
        print(results_p)
        if os.path.exists(results_p):
            sampleset = load_result(results_p)
        else:
            print("Solution does not exist")
            exit(1)
    else:
        if os.path.exists(results_p):
            print("Overwriting old results")

        sampleset = anneal(qubo, mode, a_dict, results_p, solver=solver)
    
    results = sampleset_to_result(sampleset, M, num_measures, job_list)
    result_e = get_best_entropy_result(results)
    result_n = get_best_nonviolating_result(results)
    results_min = sorted(results, key=lambda d: d["M_violate"])[0]
    if result_e:
        sample_to_midi(file, result_e["sample"], M, job_list, results_p, "e")
    if result_n:
        sample_to_midi(file, result_n["sample"], M, job_list, results_p, "n")

    if log:
        log_experiment(
            midi_file,
            num_measures,
            M,
            p_dict,
            mode,
            solver,
            a_dict,
            phrase_list,
            job_list,
            model,
            offset,
            result_e,
            result_n,
            results,
            sampleset,
        )

    return result_n,results_min


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("midi", type=str)
    parser.add_argument("--measures", type=int, required=False, default=-1)
    parser.add_argument("--tracks", type=int, required=False, default=2)
    parser.add_argument(
        "--mode",
        type=str,
        required=False,
        default="sim",
        choices=["sim", "quantum", "hyb"],
    )
    parser.add_argument("--ns", type=int, required=False, default=4000)
    parser.add_argument("--nr", type=int, required=False, default=100)
    parser.add_argument("--rcs", type=float, required=False, default=0.2)
    parser.add_argument("--t", type=int, required=False, default=20)
    parser.add_argument(
        "--solver", type=str, required=False, default="Advantage_system4.1"
    )
    parser.add_argument("--load", action="store_true")
    parser.add_argument("--log", action="store_true")

    args = parser.parse_args()

    folder_dict = {
        "midi_folder": "midi",
        "phrase_folder": "phrases",
        "results_folder": "results",
    }
    try:
        os.mkdir("phrases")
    except OSError as error:
        pass
    try:
        os.mkdir("results")
    except OSError as error:
        pass

    a_dict = {
        "ns": args.ns,
        "nr": args.nr,
        "t": args.t,
        "rcs": args.rcs,
    }  # ns = number of sweaps, nr = number of reads

    logging.basicConfig(
        filename=get_file_path("results", "results.log"), level=logging.INFO
    )

    music_experiment(
        args.midi,
        folder_dict,
        args.measures,
        args.tracks,
        args.mode,
        a_dict,
        args.solver,
        args.load,
        args.log,
    )
