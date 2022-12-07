
import math
from main import *
import pandas as pd

def get_exp_data(midi,mode,chains_str,annealing_times = [100, 500, 1000, 2000], num_reads=[1000],
                solver='Advantage_system4.1',num_sweeps=[1000],load=True, log = False):
                
    if mode == "quantum":
        df_entropy = pd.DataFrame(columns=chains_str, index=annealing_times)
        df_softv = pd.DataFrame(columns=chains_str, index=annealing_times)
        df_hardv = pd.DataFrame(columns=chains_str, index=annealing_times)
        print(f"Experiment for {mode} with {solver}")
        for rcs in chains_str:
            for i in range(len(annealing_times)):
                a_dict = {
                    "nr": num_reads[i],
                    "t": annealing_times[i],
                    "rcs": rcs,
                }  

                result,result_min = music_experiment(
                    midi, folder_dict, num_measures, M, mode, a_dict, solver, load, log
                )
                print(
                    f"done for number of reads: {num_reads[i]} and annealing time: {annealing_times[i]}"
                )
                if result != None:
                    print("got result without hard violation")
                    df_entropy.at[annealing_times[i], rcs] = result["entropy"]
                    df_softv.at[annealing_times[i], rcs] = result["M_violate"]
                    df_hardv.at[annealing_times[i], rcs] = 0
                else:
                    df_softv.at[annealing_times[i], rcs] = result_min["M_violate"]
                    df_hardv.at[annealing_times[i], rcs] = result_min["M_violate_hard"]

    elif mode == "sim":
        df_entropy = pd.DataFrame(columns=num_sweeps, index=num_reads)
        df_softv = pd.DataFrame(columns=num_sweeps, index=num_reads)
        df_hardv = pd.DataFrame(columns=num_sweeps, index=num_reads)
        print(f"Experiment for {mode}")
        for sweep in num_sweeps:
            for i in num_reads:
                a_dict = {
                    "nr": i,
                    "ns": sweep,
                }  

                result,result_min  = music_experiment(
                    midi, folder_dict, num_measures, M, mode, a_dict, solver, load, log
                )
                print(f"done for number of reads: {i} and number of sweeps: {sweep}")

                if result != None:
                    print("got result without hard violation")
                    df_entropy.at[i, sweep] = result["entropy"]
                    df_softv.at[i, sweep] = result["M_violate"]
                    df_hardv.at[i, sweep] = 0
                else:
                    df_entropy.at[i, sweep] = None
                    df_softv.at[i, sweep] = result_min["M_violate"]
                    df_hardv.at[i, sweep] = result_min["M_violate_hard"]
    elif mode == "hyb":
        df_entropy = pd.DataFrame()
        df_softv = pd.DataFrame()
        df_hardv = pd.DataFrame()
        print(f"Experiment for {mode}")
        a_dict = {}
        result,result_min= music_experiment(midi, folder_dict, num_measures, M, mode, a_dict, solver, load, log)
        if result!= None:
            print("got result without hard violation")
            df_entropy.at[1, 1] = result["energy"]
            df_softv.at[1, 1] = result["M_violate"]
            df_hardv.at[1, 1] = 0
        else:
            df_entropy.at[1, 1] = None
            df_softv.at[1, 1] = result_min["M_violate"]
            df_hardv.at[1, 1] = result_min["M_violate_hard"]
    
    return df_entropy,df_softv,df_hardv

if __name__ == "__main__":
    num_measures = -1
    M = 2

    midis = ["bach-air-score.mid","Symphony_No._7_2nd_Movement.mid"]
    modes = ["quantum","sim","hyb"]
    solvers = ['Advantage_system4.1','Advantage2_prototype1.1']

    folder_dict = {
        "midi_folder": "midi",
        "phrase_folder": "phrases",
        "results_folder": "results",
    }

    load = True
    load = not True
    logging.basicConfig(
        filename=get_file_path("results", "results_benchmarking.log"),
        level=logging.INFO)

    for midi in midis:
        for mode in modes:
            if mode == "quantum":
                for solver in solvers:
                    df_entropy,df_softv,df_hardv = get_exp_data(midi,mode,solver= solver, load = load)
            else:
                df_entropy,df_softv,df_hardv = get_exp_data(midi,mode, load = load)
        print(df_entropy,df_softv,df_hardv)