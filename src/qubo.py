from pyqubo.integer.log_encoded_integer import LogEncInteger

from cpp_pyqubo import Binary, Constraint


def get_objective(job_list):
    """Implements the objective part of the QUBO

    :param file: File to process
    :type file: music21 Stream
    :param phrase_list: List of start and end measures of phrases
    :type phrase_list: defaultdict
    :param bias: Bias for each instrument
    :type bias: list
    :return: pyqubo object corresponding to the objective function
    :rtype: cpp_pyqubo.Add
    """
    o = 0
    for job in job_list.jobs:
        o += -job.weight * Binary(f"x_{job.id}")
    return o


def running_jobs(job_list, t):
    """Returns the list of jobs where t is between the start and end times

    :param job_list: List of jobs
    :type job_list: list
    :param t: Time
    :type t: int
    :return: List of jobs active at time t
    :rtype: list
    """
    run_jobs = []
    for job in job_list.jobs:
        if t > job.start and t <= job.end:
            run_jobs.append(job.id)
    return run_jobs


def num_machine_cons(M, job_list, max_time, p):
    """Implements the number of tracks constraint, which ensures that there are exactly M tracks after the reduction

    :param M: Number of tracks after reduction
    :type M: int
    :param job_list: List of jobs
    :type job_list: list
    :param max_time: Maximum time
    :type max_time: int
    :param p: Penalty value
    :type p: float
    :return: pyqubo object corresponding to the objective function
    :rtype: cpp_pyqubo.Add
    """
    c = 0
    for j in range(1, max_time + 1):
        run_jobs = running_jobs(job_list, j)
        if len(run_jobs) < 1:
            continue
        c += Constraint(
            p * (M - sum(Binary(f"x_{i}") for i in run_jobs)) ** 2,
            f"exactly_M_{j}",
        )
    return c


def min_idle_time_cons(M, job_list, max_time, p):
    """Implements the constraint, which ensures that there are less than M tracks after the reduction

    :param M: Number of tracks after reduction
    :type M: int
    :param job_list: List of jobs
    :type job_list: list
    :param max_time: Maximum time
    :type max_time: int
    :param p: Penalty value
    :type p: float
    :return: pyqubo object corresponding to the objective function
    :rtype: cpp_pyqubo.Add
    """

    c = 0
    for j in range(1, max_time + 1):
        run_jobs = running_jobs(job_list, j)
        if len(run_jobs) < 1:
            continue
        slack_var = LogEncInteger(f"slack{j}", (0, M))
        c += Constraint(
            p * (M - sum(Binary(f"x_{i}") for i in run_jobs) - slack_var) ** 2,
            f"less_M_{j}",
        )
    return c


def get_qubo(job_list, M, max_time, p_dict):
    """Constructs the qubo for the problem

    :param file: File to process
    :type file: music21 Stream
    :param phrase_list: List of start and end measures of phrases
    :type phrase_list: defaultdict
    :param M: Number of tracks to reduce
    :type M: int
    :param bias:Bias for the instruments
    :type bias: dict
    :param conf_list:
    :type conf_list:
    :param p_dict:
    :type p_dict:
    :return: QUBO formulation, the offset and the model
    :rtype: dict, float, cpp_pyqubo.Model
    """
    H = get_objective(job_list)
    H += num_machine_cons(M, job_list, max_time, p_dict["exact"])
    H += min_idle_time_cons(M, job_list, max_time, p_dict["less"])

    model = H.compile()
    qubo, offset = model.to_qubo()
    return qubo, offset, model
