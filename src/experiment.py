import logging

import dimod
import dwave.inspector
import neal
from dwave.system import DWaveSampler, EmbeddingComposite, LeapHybridSampler

from utils import *


def sim_anneal(qubo, nr, ns) -> dimod.sampleset.SampleSet:
    """Runs simulated annealing experiment
    :param qubo: QUBO formulation for the problem
    :type qubo: dictionary
    :param num_reads: Number of samples
    :type num_reads: int
    :param num_sweeps: Number of steps
    :type num_sweeps: int
    :return: sampleset
    :rtype: dimod.SampleSet
    """
    s = neal.SimulatedAnnealingSampler()
    return s.sample_qubo(qubo, num_sweeps=ns, num_reads=nr)


def real_anneal(
    qubo, num_reads, annealing_time, chain_strength, solver
) -> dimod.sampleset.SampleSet:
    """Runs quantum annealing experiment on D-Wave
    :param qubo: QUBO formulation for the problem
    :type qubo: dictionary
    :param num_reads: Number of samples
    :type num_reads: int
    :param annealing_time: Annealing time
    :type annealing_time: int
    :param chain_strength: Chain strength parameters
    :type chain_strength: float
    :param solver = DWave Solver name
    :type = string
    :return: sampleset
    :rtype: dimod.SampleSet
    """

    sampler = EmbeddingComposite(DWaveSampler(solver=solver))
    # annealing time in micro second, 20 is default.
    return sampler.sample_qubo(
        qubo,
        num_reads=num_reads,
        auto_scale="true",
        annealing_time=annealing_time,
        chain_strength=chain_strength,
    )


def hybrid_anneal(qubo) -> dimod.sampleset.SampleSet:
    """Runs experiment using hybrid solver
    :param qubo: QUBO formulation for the problem
    :type qubo: dictionary
    :return: sampleset
    :rtype: dimod.SampleSet
    """
    sampler = LeapHybridSampler()
    return sampler.sample_qubo(qubo)


def anneal(qubo, mode, a_dict, sample_p, solver=None):
    """Runs the annealing experiment

    :param qubo: QUBO formulation for the problem
    :type qubo: dictionary
    :param mode: Simulation mode
    :type mode: string
    :param a_dict: Dictionary containing annealing parameters
    :type a_dict: dictionary
    :return: sampleset
    :rtype: dimod.SampleSet
    """
    if mode == "sim":
        ns, nr = a_dict["ns"], a_dict["nr"]
        sampleset = sim_anneal(qubo, nr, ns)
        store_result(sample_p, sampleset)
    elif mode == "quantum":
        nr, t, rcs = a_dict["nr"], a_dict["t"], a_dict["rcs"]
        ch = max_chain_strength(qubo) * rcs
        print(max_chain_strength(qubo))
        sampleset = real_anneal(qubo, nr, t, ch, solver=solver)
        store_result(sample_p, sampleset)
    elif mode == "hyb":
        sampleset = hybrid_anneal(qubo)
        store_result(sample_p, sampleset)
    return sampleset


def analyze_solution(model, sample):
    """Uses pyqubo to analyze the sample

    :param model: Pyqubo model
    :type model: cpp_pyqubo.Model
    :param sample: Sample
    :type sample: dictionary
    :return: Broken constraints
    :rtype: dictionary
    """
    dec = model.decode_sample(sample, vartype="BINARY")
    return dec.constraints(only_broken=True)


def annealing_statistics(sampleset):
    """Logs the quantum annealing statistics

    :param sampleset: Sampleset to process
    :type sampleset: dimod.SampleSet
    """
    l = list(sampleset.info["embedding_context"]["embedding"].values())
    logging.info(f"Physical variables: {len(set.union(*[set(x) for x in l]))}")
    logging.info(f"Chain break: {list(sampleset.record.chain_break_fraction)}")


def max_chain_strength(qubo):
    """Finds the largest value appearing in qubo

    :param qubo: qubo to process
    :type qubo: dict
    :return: max value in qubo
    :rtype: float
    """
    return max([abs(x) for x in qubo.values()])
