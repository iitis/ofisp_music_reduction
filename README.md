<!-- [![DOI](https://zenodo.org/badge/376737392.svg)](https://zenodo.org/badge/latestdoi/376737392) -->

# Fixed interval scheduling problem with minimal idle time with an application to music arrangement problem

Person responsible for data: Ludmila Botelho (lbotelho[at]iitis.pl).

The scripts necessary for generating the results provided in the "Fixed interval scheduling problem with minimal idle time with
an application to music arrangement problem".

The code was tested under Windows and Ubuntu Linux. To set up the environment, please install the following packages: `music21`, `numpy`, `pyqubo`,  `dwave-ocean-sdk`, `pandas`.


## Generating sampleset and midi

To generate new a midi file, run the following command in the main directory:
```
python main.py bach-air-score.mid 
```

You can run simulated annealing, quantum annealing, and  hybrid solvers experiments using QUBO formulations. In order to use quantum annealing or the hybrid solver, you should have the necessary access to D-Wave.

The details of the optional keywords are described below:

```--measures```: Number of measures for the new composition. Default is-1.
```--tracks```: Number of tracks in the new composition. Default is 2.
```--mode```: Type of annealing algorithm . Choices are sim, quantum and hyb. Default is sim.
```--ns```: Number of sweeps. Default is 4000.
```--nr```: Number of readings. Default is 100.
```--rcs```: Chain strength value. Default is 0.2
```--t```: Annealing time. Default is 20
```--solver```: D-Wave quantum annealing solver. Default is Advantage_system4.1
```--load```: Load sampleset results, if available.
```--log```: Make log for the experiment.   

The generated outputs are stored in results folder corresponding to the mode selected. The files type are pickle (for the sampleset) and midi format. The name of the files are the original midi file name with the variables M (the number of tracks), nr (number of reads, for quantum and simulated), t (annealing time, for quantum), cr (chain strength, for quantum), ns (number of sweep, for simulated),  and solver (quantum).

### Experiment
We generated experiment data with the following script:

```
python benchmarking_exp.py 
```

On this script, we evaluated two compositions, varying the type of annealing, solvers and optimization parameters. Data used in the publication is located inside the results folder. 


## Publication

L. Botelho, Ö. Salehi, *Fixed interval scheduling problem with minimal idle time with an application to music arrangement problem*

