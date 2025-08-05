import os
import logging
from datetime import datetime
from utility.evaluation_utils import Paths, Scores, evaluate_person


def execute_evaluation(conf: dict, eval_level: str, fuzziness: bool) -> None:
    """
    Evaluates the F1-score of the data based on the given configuration,\
    evaluation level, and fuzziness.

    At eval_level "ent", this is done on entity level. At eval_level "ref",\
    this is done on reference level, which weighs the entities more that occur\
    more, thus should be linked correctly, since we have more context on them.

    Evaluation is done for all magazines in our ground-truth folder to make the\
    evaluations straightforward to compare. If you would like to evaluate only\
    one magazine, you need to create a new directory with only that magazine's\
    ground-truth in it, change that path in the config, and then run eval.

    Args:
        conf (dict): Configuration dictionary containing various settings and\
            paths.\n
        eval_level (str): Evaluation level to be used ("ent" or "ref").\n
        fuzzy (str): Whether to use fuzzy matching.

    Raises:
        NotImplementedError: _description_

    Returns:
        None. It creates several directories and json files in the output directory\
        specified in the config.
    """
    gt_fuzziness = "with_fuzzy" if fuzziness else "without_fuzzy"
    ref_level = True if (eval_level == "ref") else False
    paths = Paths(conf=conf)
    if paths.success:
        global_scores = Scores()
        for magazine in os.listdir(paths.get(type_="gt", key="")):
            paths.update(key="magazine", value=magazine)
            magazine_scores = Scores()
            for file in os.listdir(paths.get(type_="gt", key="magazine")):
                if file.endswith(".txt"):  # these are the notes
                    continue
                paths.update(key="file", value=file)
                gt_file = paths.get_json(type_="gt")
                eval_file = paths.get_json(type_="link")
                counts = evaluate_person(
                    gt=gt_file, linked=eval_file, ref_level=ref_level
                )
                # TODO implement treshold
                file_scores = Scores(counts_dict=counts)
                magazine_scores.update_counter(counts)
                global_scores.update_counter(counts)
                paths.save_json(
                    type_="eval",
                    key="file",
                    doc=file_scores.get_score(),
                    ref_level_name=eval_level,
                    fuzziness_name=gt_fuzziness,
                )
            paths.save_json(
                type_="eval",
                key="magazine",
                doc=magazine_scores.get_score(),
                ref_level_name=eval_level,
                fuzziness_name=gt_fuzziness,
            )
        paths.save_json(
            type_="eval",
            key="",
            doc=global_scores.get_score(),
            ref_level_name=eval_level,
            fuzziness_name=gt_fuzziness,
        )
    else:
        logging.info(conf)
        raise NotImplementedError("no path to ground truth was passed")


def execute_evaluation_timed(conf: dict, eval_level: str, fuzzy: bool) -> None:
    """
    Evaluates the data based on the given configuration, evaluation level, and\
    fuzziness, and logs the time it took for the evaluation.

    Args:
        conf (dict): Configuration dictionary containing various settings and\
            paths.\n
        eval_level (str): Evaluation level to be used.\n
        fuzzy (str): Whether to use fuzzy matching.

    Returns:
        None
    """
    start_time = datetime.now()
    logging.info("Starting Evaluation at %s:", start_time)
    execute_evaluation(conf, eval_level, fuzzy)
    logging.info("Evaluation took: %s", datetime.now() - start_time)
