import logging

from music21 import stream

from jobs import JobCollector
from qubo import running_jobs


def sample_to_jobs(sample, job_list):
    """Given a sample, converts it back into a job_list

    :param sample: Sample obtained as a result of the annealing
    :type sample: dictionary
    :param job_list: List of all the jobs
    :type job_list: list
    :return: List of selected jobs
    :rtype: list
    """
    new_list = JobCollector()
    for job in job_list.jobs:
        if sample[f"x_{job.id}"] == 1:
            new_list += job
    return new_list


def sort_jobs(jobs_list):
    """Sorts the jobs according to their start times

    :param jobs_list: List of jobs
    :type jobs_list: list
    :return: Sorted jobs
    :rtype: list
    """
    return sorted(jobs_list.jobs, key=lambda x: x.start, reverse=False)


def greedy_machines(M, job_list):
    """This is the earliest starting time first greedy algorithm

    :param M: Numver of machines
    :type M: int
    :param jobs: list of jobs
    :type jobs: list
    :return: Assignment of jobs to machines
    :rtype: dictionary
    """
    jobs = sort_jobs(job_list)
    machines_dict = {i: [] for i in range(M)}
    for job in jobs:
        for m in range(M):
            try:
                if job.start >= machines_dict[m][-1].end:
                    machines_dict[m].append(job)
                    break
            except IndexError:
                machines_dict[m].append(job)
                break
    return machines_dict


def store_midi(new_arrange, results_p):
    """Given the music stream, stores the midi file

    :param new_arrange: New music file
    :type new_arrange: Music21 Stream
    :param results_p: Path to store the results
    :type results_p: string
    """
    new_arrange.write("midi", f"{results_p}.mid")


def machines_to_stream(machine_dict, file):
    """Given the machine and file, creates the new stream

    :param machine_dict: Dictionary containing machine job assignment
    :type machine_dict: dictionary
    :param file: Music file
    :type file: Music21 Stream
    :return: New music file
    :rtype: Music21 Stream
    """
    new_arrange = stream.Score()
    stream_parts = [stream.Part(id=f"part{i}") for i in range(len(machine_dict))]
    for machine, jobs in machine_dict.items():
        for job in jobs:
            for jobin in range(job.start + 1, job.end + 1):
                stream_parts[machine].append(file.parts[job.track].measure(jobin))
    for i in range(len(machine_dict)):
        new_arrange.insert(0, stream_parts[i])
    return new_arrange


def countM(sample, M, max_time, job_list):
    """Counts the number of time points for which there are not M jobs assigned

    :param sample: Dictionary of samples
    :type sample: dict
    :param max_time: Maximum time
    :type max_time: int
    :param job_list: list of jobs
    :type job_list: list
    :return: number of time points that violate the rule
    :rtype: int
    """
    x = 0
    for j in range(1, max_time + 1):
        run_jobs = running_jobs(job_list, j)
        if len(run_jobs) < 1:
            continue
        if M != sum(sample[f"x_{i}"] for i in run_jobs):
            x += 1
    return x


def countM_hard(sample, M, max_time, job_list):
    """Counts the number of time points for which there are not M jobs assigned

    :param sample: Dictionary of samples
    :type sample: dict
    :param max_time: Maximum time
    :type max_time: int
    :param job_list: list of jobs
    :type job_list: list
    :return: number of time points that violate the rule
    :rtype: int
    """
    x = 0
    for j in range(1, max_time + 1):
        run_jobs = running_jobs(job_list, j)
        if len(run_jobs) < 1:
            continue
        if M < sum(sample[f"x_{i}"] for i in run_jobs):
            x += 1
    return x

def is_sample_feasible(sample, M, max_time, job_list):
    """Checks whether a given sample satisfies no more than M track at each time point constraint

    :param sample: sample to process
    :type sample:  dict
    :param M: Number of tracks
    :type M: int
    :param max_time: Maximum time/number of measures
    :type max_time: int
    :param job_list: list of jobs
    :type job_list: list
    :return: Feasibility of the sample
    :rtype: boolean
    """

    for j in range(1, max_time + 1):
        run_jobs = running_jobs(job_list, j)
        if len(run_jobs) < 1:
            continue
        if sum(sample[f"x_{i}"] for i in run_jobs) > M:
            return False
    return True


def get_total_entropy(sample, job_list):
    """Given a sample calculates its entropy

    :param sample: sample to process
    :type sample: dict
    :param job_list: list of jobs
    :type job_list: list
    :return: total entropy of the sample
    :rtype: float
    """
    return sum(-1 * job.weight for job in job_list.jobs if sample[f"x_{job.id}"] == 1)


def get_best_entropy_result(results):
    """Returns the feasible solution with the lowest entropy

    :param results: dictionary containing annealing results
    :type results: dict
    :return: result dictionary corresponding to a single sample
    :rtype: dict
    """
    sresults = sorted(results, key=lambda d: d["entropy"])
    return next((l for l in sresults if l["feasible"]), None)


def get_best_nonviolating_result(results):
    """Returns the feasible solution with the lowest entropy that does not violate any constraints

    :param results: dictionary containing annealing results
    :type results: dict
    :return: result dictionary corresponding to a single sample
    :rtype: dict
    """
    sresults = sorted(results, key=lambda d: d["M_violate"])
    return next((l for l in sresults if l["feasible"]), None)


def sampleset_to_result(sampleset, M, max_time, job_list):
    """Check samples one by one, and computes it statistics.
    Statistics includes energy (as provided by D'Wave), total entropy of the selected phrases, feasibility analysis, the samples itself. Samples are sorted
    according to the entropy

    :param sampleset: analyzed samples
    :type sampleset: analyzed samples
    :param M: number of machines
    :type M: int
    :param max_time: maximum time
    :type max_time: int
    :param job_list: list of jobs
    :type job_list: list
    :return: dictionary containing samples
    :rtype: dict
    """
    dict_list = []
    for data in sampleset.data():
        rdict = {}
        sample = data.sample
        rdict["energy"] = data.energy
        rdict["entropy"] = get_total_entropy(sample, job_list)
        rdict["feasible"] = is_sample_feasible(sample, M, max_time, job_list)
        rdict["M_violate"] = countM(sample, M, max_time, job_list)
        rdict["M_violate_hard"] = countM_hard(sample, M, max_time, job_list)
        rdict["sample"] = sample
        dict_list.append(rdict)
    return sorted(dict_list, key=lambda d: d["entropy"])


def sample_to_midi(file, sample, M, job_list, results_p, sample_type):
    """Given a sample generates the midi file

    :param file: file to process
    :type file: music21 file
    :param sample: sample to process
    :type sample: dict
    :param M: number of tracks
    :type M: int
    :param job_list: list of jobs
    :type job_list: list
    :param results_p: path to save midi
    :type results_p: string
    :param sample_type: whether it is best entropy or best non-violating solution
    :type sample_type: string
    """
    new_jobs = sample_to_jobs(sample, job_list)
    machine_jobs = greedy_machines(M, new_jobs)
    new_music = machines_to_stream(machine_jobs, file)
    store_midi(new_music, f"{results_p}_{sample_type}")

    return new_jobs,machine_jobs

