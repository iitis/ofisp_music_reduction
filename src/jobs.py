import logging

import numpy as np

from toolbox import get_entropy


class Job:
    def __init__(self, start, end, weight, id, track=None):
        """Constructor  for the job class

        :param start: Start time
        :type start: int
        :param end: End time
        :type end: int
        :param weight: Weight of the job
        :type weight: float
        :param id: Id of the job
        :type id: int
        """
        self.start = start
        self.end = end
        self.weight = weight
        self.track = None
        self.id = id
        if track != None:
            self.track = track

    def __repr__(self):
        """Used for printing

        :return: String representation of the object
        :rtype: string
        """
        return f"Job id no: {self.id}, start: {self.start}, end: {self.end}, weight:{self.weight},  track:{self.track} \n"


class JobCollector:
    def __init__(self) -> None:
        """Constructor for the JobCollector class"""

        self.jobs = []
        self.counter = 0

    def new_job(self, start, end, weight, track=None) -> Job:
        """Creates a new job

        :param start: Start time
        :type start: int
        :param end: End time
        :type end: int
        :param weight: Weight of the job
        :type weight: float
        :param track: track information for music files
        :type track: int
        :return: Created job
        :rtype: Job
        """
        job = Job(start, end, weight, self.counter, track)
        self += job
        self.counter += 1
        return job

    def __add__(self, job: Job) -> "JobCollector":
        """Adds a job to the job list of the JobCollector

        :param job: Job to add
        :type job: Job
        :return: JobCollector object
        :rtype: JobCollector
        """
        if self[job.id] == None:
            self.jobs.append(job)
        else:
            print("Job id already exists")
        return self

    def __getitem__(self, id) -> Job:
        """Returns the job with the given id, None if it is not found

        :param id: Id of the job
        :type id: int
        :return: job with the given id
        :rtype:Job
        """
        return next((job for job in self.jobs if job.id == id), None)

    def __repr__(self):
        """Used for printing

        :return: String representation of the object
        :rtype: string
        """
        return self.jobs.__repr__()


def random_jobs(num_jobs, max_time, max_weight):
    """Creates a random job list

    :param num_jobs: Number of jobs
    :type num_jobs: int
    :param max_time: Maximum time
    :type max_time: int
    :param max_weight: Maximum weight
    :type max_weight: int
    :return: List of random jobs
    :rtype: list
    """
    np.random.seed(100)
    rdm_jobs_list = JobCollector()
    for i in range(num_jobs):
        start = np.random.randint(0, max_time)
        end = np.random.randint(start + 1, max_time + 1)
        weight = np.random.rand() * max_weight
        rdm_jobs_list.new_job(Job(start, end, weight))
    return rdm_jobs_list


def phrase_to_jobs(phrase_list, file):
    """Given the phrase list and the music file, create a list of jobs

    :param phrase_list: Dictionary containing the phrases
    :type phrase_list: dictionary
    :param file: Music file
    :type file: Music21 Stream
    :return: List of jobs
    :rtype: list
    """
    job_list = JobCollector()
    for track, value in phrase_list.items():
        for phrase in value:
            job_list.new_job(
                phrase[0] - 1,
                phrase[1],
                get_entropy(file, track, phrase[0], phrase[1]),
                track,
            )
    return job_list


def job_statistics(job_list):
    """Logs the job statistics

    :param job_list: list of jobs
    :type job_list: list
    """
    weights = [job.weight for job in job_list.jobs]
    lengths = [job.end - job.start for job in job_list.jobs]
    logging.info(
        f"Phrases min. weight: {-1 * min(weights)} max. weight: {-1 * max(weights)} avg. weight: {-1 * np.mean(weights)}"
    )
    logging.info(
        f"Phrases min. length: {min(lengths)} max. length: {max(lengths)} avg. length: {np.mean(lengths)}"
    )


def max_weight_phrase(job_list):
    """Finds the weight of the job with largest weight

    :param job_list: list of jobs
    :type job_list: list
    :return: max weight
    :rtype: float
    """
    return max([job.weight for job in job_list.jobs])
