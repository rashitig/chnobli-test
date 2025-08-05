#! /usr/bin/python3

"""
Includes functions to tag files using flairNLP.
Version 31.08.2020: Updated to use new tagging system which uses 2 models at
once.
TODO: Remove all debug information and make data as concise as possible for
save files.
"""

import json
from collections import defaultdict
from datetime import datetime
import logging
import os

import flair
from flair.data import Sentence, Token, Label
from flair.models import MultitaskModel
from flair.nn import Classifier
import torch


class CustomToken(Token):
    def __init__(self, text, coords, orig):
        super().__init__(text)
        self.coords = coords
        self.orig = orig


class CustomSentence(Sentence):
    def __init__(self, filename=None, text=None):
        super().__init__(text)
        self.filename = filename if filename is not None else ""


def decide_tag_no_tag_lower_prio(labels: list) -> Label:
    """Combining the tags of the two tagging models.
    If there is disagreement between the two models, "O" always loses.

    Args:
        labels (list): A list of tags for an entity with at most 2 entries.
            If there are two, the first entry corresponds to the bio label
            model and the second to the det label model.
            If there is only one entry, the model is detected based on the
            labeling scheme.

    Returns:
        Label: The Label object is the new combined label
        for this entity, the dictionary

    Raises:
        Exception: If the labels list is empty, an exception is raised.
    """
    # If there is disagreement between the two models, "O" always loses
    # TODO replace this by tag_dictionary directly from the models
    bio_tags = [
        '<unk>', 'O', 'B-PER', 'I-PER', 'B-CIT', 'B-CTR', 'I-CIT', 'B-CITadj',
        'B-CTRadj', 'I-CTRadj', 'I-CTR', 'B-GEOadj', 'B-GEO', 'I-GEO',
        'I-GEOadj', 'B-STR', 'I-STR', 'I-CITadj', 'B-EXT', 'I-OT', '<START>',
        '<STOP>'
    ]
    det_per_labels = ["AN", "OC", "FN", "LN", "COM", "OT"]
    if len(labels) == 2:
        bio_label = labels[0]
        det_label = labels[1]
    elif len(labels) == 1:
        if labels[0].value in bio_tags:  # bio
            bio_label = labels[0]
            det_label = Label(bio_label.data_point, value="O", score=0)
        else:  # det
            det_label = labels[0]
            bio_label = Label(det_label.data_point, value="O", score=0)
    else:
        raise Exception("Empty list of labels was passed.")
    # check if the labels agree
    if bio_label.value[2:] == "PER" and det_label.value[2:] in det_per_labels:
        new_label = bio_label.value + det_label.value[1:]
    elif bio_label.value[2:] == det_label.value[2:]:
        new_label = bio_label.value
    else:  # if they don't agree, O always loses
        if (
            det_label.value == "O"
            or
            (
                bio_label.score > det_label.score and bio_label.value != "O"
            )
        ):
            if bio_label.value[2:] == "PER":
                new_label = bio_label.value + "-OT"
            else:
                new_label = bio_label.value
        else:
            if det_label.value[2:] in det_per_labels:
                new_label = "B-PER" + det_label.value[1:]
            else:
                new_label = det_label.value

    return new_label


def add_sentences(new_data: dict, collected_sentences: list) -> None:
    """Given the sentences tagged with both models, combines their tags
    and updates the new_data dictionary with the new sentences.

    Args:
        new_data (dict): A dictionary where the keys are the filenames and
            the values are the tagged sentences in said file.
        collected_sentences (list): A list of sentences tagged by both models.
    """
    for sentence in collected_sentences:
        new_sentence = []
        for token in sentence:
            if token.labels == []:
                new_token = {
                    "token": token.orig,
                    "coord": token.coords,
                    "normalized": token.text,
                    "tag": "O"
                }
            else:
                tag = decide_tag_no_tag_lower_prio(token.labels)
                new_token = {
                    "token": token.orig,
                    "coord": token.coords,
                    "normalized": token.text,
                    "tag": tag,
                }
            new_sentence.append(new_token)
        new_data[sentence.filename].append(new_sentence)


def write_sentences_to_outfile(outfile, data: dict) -> None:
    """For each SENTENCE_BATCH_SIZE (set in the config file) batch of
    sentences, we write out the sentences into the outfile.
    This helps with our memory restrictions.

    This has the side-effect that the data dictionary is cleared with each time
    we call this function.

    Args:
        outfile (TextIOWrapper): Text stream we can write our
            intermediate results into.
        data (dict): Dictionary of filenames, tagged sentences.
    """
    for filename, sentences in data.items():
        out_dict = {filename: sentences}
        json_formatted = json.dumps(out_dict)
        outfile.write(json_formatted + "\n")
    data.clear()


def tag_year_data_and_save(collection: dict,
                           tagger: MultitaskModel,
                           outfile_path: str,
                           sentence_batch_size: int) -> None:
    """Runs tagging on the collection and saves the result
    into the outfile_path.

    Args:
        collection (dict): A dictionary where the keys are the filenames and
            the values are the sentences in said file.
        tagger (MultitaskModel): The MultitaskModel containing both
            tagging models (ner-det and ner-bio).
        outfile (str): String of the outfile path where the tagged file
            will be saved.
        sentence_batch_size (int): Number of sentences, after which we start
            writing the intermediate results into the outfile.
    """

    # open outfile
    outfile = open(outfile_path, mode="w", encoding="utf8")

    new_data = defaultdict(list)
    # all_collected_sentences = []
    collected_sentences = []
    # TODO: instead of reading from a dictionary,
    # just iterate the given year directly
    for filename, sentences in collection.items():
        for sentence in sentences:
            new_sentence = CustomSentence(filename, "")
            for i, token in enumerate(sentence):
                new_sentence._add_token(
                    CustomToken(
                        (
                            token["normalized"]
                            if "normalized" in token
                            else token["token"]
                        ),
                        token["coord"],
                        token["token"],
                    )
                )
                if i + 1 % 250 == 0:
                    collected_sentences.append(new_sentence)
                    new_sentence = CustomSentence(filename, "")
            collected_sentences.append(new_sentence)
            if len(collected_sentences) == sentence_batch_size:
                tagger.predict(
                    collected_sentences,
                    verbose=False,
                    mini_batch_size=4,
                    force_token_predictions=True
                )
                add_sentences(new_data, collected_sentences)
                # all_collected_sentences.extend(collected_sentences)
                collected_sentences = []

                # TODO: whenever a file has been processed, write all
                # information for that file to the output-file in json-coding
                # If this doesnt improve performance enough, it might be
                # necessary to write a sentence per line.
                write_sentences_to_outfile(outfile, new_data)

    if collected_sentences:
        tagger.predict(
            collected_sentences,
            verbose=False,
            mini_batch_size=4,
            force_token_predictions=True
        )
        add_sentences(new_data, collected_sentences)
        # all_collected_sentences.extend(collected_sentences)

        write_sentences_to_outfile(outfile, new_data)

    outfile.close()


def setup_flair_tagger(conf: dict,
                       gpu_num: int) -> flair.models.MultitaskModel:
    """
    Sets up and returns a Flair MultitaskModel for two NER models.

    Args:
        conf (dict): Configuration dict containing paths to the NER models.
            Expected keys:
                - "PATH_TO_NER_MODEL_1": Path to the first NER model.
                - "PATH_TO_NER_MODEL_2": Path to the second NER model.
        gpu_num (int): GPU number to use. If set to "0", the CPU will be used.

    Returns:
        flair.models.MultitaskModel: An instance of Flair's MultitaskModel
        loaded with the specified NER models.
    """
    flair.device = torch.device(int(gpu_num) if gpu_num != 0 else "cpu")

    ner_tagger_1 = Classifier.load(conf["PATH_TO_NER_MODEL_1"])
    ner_tagger_2 = Classifier.load(conf["PATH_TO_NER_MODEL_2"])
    flairTagger = MultitaskModel([ner_tagger_1, ner_tagger_2])
    return flairTagger


def package_generator_output_paths(generator, batch_size):
    """
    Packages the output from a generator into batches of a specified size.

    Args:
        generator (iterable): An iterable that yields tuples, where the first
                              element is a year and the second element is a
                              list of files.
        batch_size (int): The number of items to include in each batch.

    Yields:
        dict: A dictionary where the keys are years and the values are lists
              of files, with the number of items in the dictionary not
              exceeding the batch size.

    Example:
        generator = [(2020, ['file1', 'file2']), (2021, ['file3', 'file4'])]
        batch_size = 1
        for batch in packageGeneratorOutput(generator, batch_size):
            print(batch)
        # Output:
        # {2020: ['file1', 'file2']}
        # {2021: ['file3', 'file4']}
    """
    year_dict = {}
    for year, files in generator:
        year_dict[year] = files
        if len(year_dict) >= batch_size:
            yield year_dict
            year_dict = {}

    if year_dict != {}:
        yield year_dict


def execute_tagging(preprocessed_data,
                    conf: dict,
                    tasks: list,
                    gpu_num: int) -> None:
    """
    Tags the preprocessed data using the provided flair tagger and
    configuration.

    Args:
        preprocessed_data : The data that has been preprocessed and is ready
            for tagging.
        flairTagger: The flair tagger model used for tagging the data.
        conf (dict): Configuration dictionary containing various settings
            and paths.
        tasks (list): List of tasks to be performed. Must include 'prep' for
            this function to execute.

    Raises:
        Exception: If 'prep' is not included in the tasks list, an exception
            is raised indicating that 'prep,tag' must be called together.

    Returns:
        None
    """
    flairTagger = setup_flair_tagger(conf, gpu_num)
    start_time = datetime.now()
    logging.info("Starting Tagging at", datetime.now(), ":")
    if "prep" not in tasks:  # TODO this cannot be called seperately
        raise Exception("'prep,tag' must be called together.")
        # this is supposed to make prep,tag independent, does not work yet
        # conf["PATH_TO_INPUT_FOLDERS"] += "/tag/"
        # preprocessed_data = loadDataIterative(conf)
    else:
        # TODO: instead of packaging the output into batches,
        # just read give a year file to the tag_flair script
        # and process one year after the other
        # this is probably not the bottleneck atm, but i still should
        # change this at some point
        preprocessed_data = package_generator_output_paths(
            preprocessed_data, conf["BATCH_SIZE"]
        )
    for magazine in preprocessed_data:
        for year, data in magazine.items():
            logging.info("Tagging %s", year)
            outfolder = conf["PATH_TO_OUTFILE_FOLDER"]
            yearfolder = os.path.join(outfolder, "tag", year[0])
            if not os.path.exists(yearfolder):
                os.makedirs(yearfolder)
            outfile_path = os.path.join(yearfolder,
                                        "".join(year[1:]) + ".jsonl")
            tag_year_data_and_save(
                data,
                flairTagger,
                outfile_path,
                int(conf["SENTENCE_BATCH_SIZE"])
            )
            logging.info(f"Finished tagging {year}.")
    logging.info("Tagging took: ", datetime.now() - start_time)
