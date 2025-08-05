import argparse
import subprocess
import os
import json
import logging


def set_default(obj):
    """
    Helper function to translate all sets in the aggregated dictionaries into
    lists when dumping them to files.
    """
    if isinstance(obj, set):
        return list(obj)
    raise TypeError


def str2bool(value: str) -> bool:
    """Casts a string to a boolean value

    Args:
        value (str): String input to be cast.

    Raises:
        argparse.ArgumentTypeError: If the string value cannot be cast
         to a boolean, this error is raised.

    Returns:
        bool: Boolean value of the given string.
    """
    value = str(value)
    if value.lower() in {"true", "1"}:
        return True
    elif value.lower() in {"false", "0"}:
        return False
    else:
        raise argparse.ArgumentTypeError(
            "Boolean value expected (true/false, 1/0)"
        )


def positive_int(value: str) -> int:
    """Custom type function for argparse that ensures a positive integer."""
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError(f"{value} is not a positive integer")
    return ivalue


def parse_arguments() -> argparse.Namespace:
    """
    Parses command-line arguments for the script.
    Returns:
        argparse.Namespace: An object containing the parsed command-line
         arguments.
    Command-line Arguments:
        --tasks (str): Comma-separated list of tasks to perform.\
        Default is "prep,tag,finish".
        --gpu (str): GPU identifier to use. Default is "0".
        --magazine_year_paths (str): Paths to magazine year data.
        --config_file (str): Path to the configuration file.\
        Default is "./configs/configurations.json".
        --eval_level (str): Evaluation level. Default is "ref".
        --fuzzy (str): Whether to use fuzzy matching. Default is True.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", type=str, default="finish")
    parser.add_argument("--gpu", type=positive_int, default=0)
    parser.add_argument("--magazine_year_paths", type=str)
    parser.add_argument(
        "--config_file", type=str, default="./configs/configurations.json"
    )
    parser.add_argument(
        "--eval_level", type=str, default="ref", choices=["ref", "ent"]
    )
    parser.add_argument(
        "--fuzzy",
        type=str2bool,
        default="True",
        choices=[
            True, False, "True", "False", "true", "false", "1", "0", 1, 0
        ],
    )

    args = parser.parse_args()
    return args


def check_gpu(args: argparse.Namespace) -> int:
    """
    Checks if an Nvidia GPU is available and sets the GPU number accordingly.

    Args:
        args: An object containing the GPU argument. It should have an
        attribute 'gpu' which is a string representing the GPU number.

    Returns:
        int: The GPU number to be used. If no Nvidia GPU is detected,
        it returns 0 indicating that the code will run on CPU.
    """
    if args.gpu != 0:
        try:
            subprocess.check_output("nvidia-smi")
        except Exception:
            logging.info("No Nvidia GPU detected, the code will run on CPU.")
            return 0
    return args.gpu


def save_data_intermediate(year: list, files: dict, conf: dict, taskname: str):
    """Saves the data given in a "taskname" folder in the oufile folder
    specified in the configurations. If the "taskname" folder doesn't exist,
    one is created. As opposed to "save_data", this function combines all the
    years for a magazine instead of saving each year individually into a file.

    Args:
        year (list): A list [mag, year, ..-] where the first entry is
         the magazine shortname and the following entry (or entries) is the
         year (or the years) we processed.
        files (dict): A dictionary containing the intermediate results of
         the given taskname.
        conf (dict): A dictionary describing various paths and settings.
        taskname (str): The task at hand, for example "link" or "tag".
    """
    outfolder = conf["PATH_TO_OUTFILE_FOLDER"]
    magfolder = os.path.join(outfolder, taskname, year[0])
    if not os.path.exists(magfolder):
        os.makedirs(magfolder)
    with open(
        os.path.join(
            magfolder, "".join(year[1:]) + ".json"
        ), encoding="utf8", mode="w"
    ) as out:
        json.dump(files, out, default=set_default)


def save_data(data: dict, conf: dict, taskname: str):
    """Saves the data given in a "taskname" folder in the oufile folder
    specified in the configurations. If the "taskname" folder doesn't exist,
    one is created.

    Args:
        data (dict): The keys are magazine-year tuples, the values are given
         by the task.
        conf (dict): A dictionary describing various paths and settings.
        taskname (str): The task at hand, for example "link" or "tag".
    """
    logging.info("Reached saveData")
    outfolder = conf["PATH_TO_OUTFILE_FOLDER"]
    prepfolder = os.path.join(outfolder, taskname)
    if not os.path.exists(prepfolder):
        os.makedirs(prepfolder)
    for batch in data:
        for year, d in batch.items():
            yearfolder = os.path.join(prepfolder, year[0])
            if not os.path.exists(yearfolder):
                os.makedirs(yearfolder)
            with open(
                os.path.join(yearfolder, year[1] + ".json"),
                encoding="utf8",
                mode="w"
            ) as out:
                json.dump(d, out, default=set_default)
