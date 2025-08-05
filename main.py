#! /usr/bin/python3

"""
NER pipeline.
"""
import json
import logging
from datetime import datetime

from src.preprocessing.preprocess import execute_preprocessing
from src.aggregation import aggregate_and_save_data_timed, execute_aggregation
from src.postprocess import postprocess_data, get_data_paths_iterative, \
    execute_postprocessing

from src.linking import execute_linking
from src.evaluation import execute_evaluation
from utility.utils import parse_arguments, check_gpu, save_data_intermediate


def setup_logging():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )


def finish_data(conf: dict, tasks: list) -> None:
    """
    Executes the final steps of the pipeline, including postprocessing,
    aggregation, and linking.

    Args:
        conf (dict): Configuration dictionary containing various settings
            and paths.

    Returns:
        None
    """
    start_time = datetime.now()
    logging.info("Starting Finish at", start_time, ":")
    if "CUSTOM_PATHS" not in conf:
        conf["PATH_TO_INPUT_FOLDERS"] = conf["PATH_TO_OUTFILE_FOLDER"] + "tag/"

    magazines = get_data_paths_iterative(conf)
    # post
    postprocessed_data = execute_postprocessing(magazines, conf["BATCH_SIZE"])
    # agg
    aggregated_data = execute_aggregation(postprocessed_data)
    # link
    execute_linking(aggregated_data, conf, tasks)
    logging.info("Finish took: ", datetime.now() - start_time)


def main():
    # Parse command-line arguments
    args = parse_arguments()

    tasks = args.tasks.split(",")
    paths = args.magazine_year_paths
    config_file = args.config_file
    eval_level = args.eval_level
    fuzzy = args.fuzzy
    gpu_num = check_gpu(args)
    with open(config_file, encoding="utf8") as conf:
        conf = json.load(conf)

    if "eval" in tasks:
        if fuzzy:
            conf["PATH_TO_GROUND_TRUTH"] = conf["PATH_TO_GROUND_TRUTH_FUZZY"]
        else:
            conf["PATH_TO_GROUND_TRUTH"] = conf["PATH_TO_GROUND_TRUTH_NOTFUZZY"]

    if paths:
        paths = paths.split(",")
        for path in paths:
            if path[0] == "/":
                path = path[1:]
        conf["CUSTOM_PATHS"] = paths
        if tasks == "eval":
            logging.warning(
                "Careful! You have selected the task 'eval' as well as\
                    giving a custom path. Evaluation is always done on\
                    all the magazines we have ground-truth data for."
            )

    if "prep" in tasks:
        preprocessed_data = execute_preprocessing(conf)
        # If we are not going to tag, we save the preprocessed data
        if "tag" not in tasks:
            for year, files in preprocessed_data:
                save_data_intermediate(year, files, conf, "prep")

    if "tag" in tasks:
        from src.tag_flair import execute_tagging
        # DO NOT MOVE THIS IMPORT!!! It makes the code extremely slow
        # because torch and flair is imported there.
        execute_tagging(preprocessed_data, conf, tasks, gpu_num)

    if "post" in tasks:
        postprocessed_data = postprocess_data(conf, tasks)

    if "agg" in tasks:
        aggregated_data = aggregate_and_save_data_timed(
            postprocessed_data, conf, tasks)

    if "link" in tasks:
        execute_linking(aggregated_data, conf, tasks)

    if "eval" in tasks:
        execute_evaluation(conf, eval_level, fuzzy)

    if "finish" in tasks:
        finish_data(conf, tasks)


if __name__ == "__main__":
    main()
