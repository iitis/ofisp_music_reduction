import argparse
import sys

# import os
# import pprint


def experiment_handle(argv):

    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--midi", type=str, required=True)
    parser.add_argument("--n-measures", type=int, required=False, default=30)
    parser.add_argument("--instruments", type=int, required=False, default=1)
    parser.add_argument("--path", type=str, required=False, default=None)
    parser.add_argument("--solver", type=str, required=False, default="sim")
    args = parser.parse_args()

    p_dict = {"exact": 1, "less": 2}
    a_dict = {"ns": 4000, "nr": 1000, "t": 200, "ch": 1}
    file_name = "Symphony_No._7_2nd_Movement"
    folder_dict = {
        "midi_folder": "midi",
        "phrase_folder": "phrases",
        "results_folder": "results",
    }
    # music_experiment(folder_dict, args.instruments, M, p_dict, args.solver, a_dict)

    print(args)


if __name__ == "__main__":
    main(sys.argv[1:])
