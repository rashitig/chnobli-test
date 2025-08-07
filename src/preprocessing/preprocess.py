#! /usr/bin/python3

"""
Includes all functions necessary to preprocess files.

TODO:
- Verbesserte Auflösung von Abkürzungen implementieren
    - "d.h.", "et al."

- Ordinalzahlen zusammenbehalten
    - XVII und so
"""

import json
import os
import pprint as pp
import re
import string
import sys
import logging
import glob
from datetime import datetime

from collections import defaultdict, OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import List
from multiprocessing import Pool
from utility import split_year


@dataclass
class PreprocessConfig:
    """Class for the preprocess configuration
    """

    ABBREVIATION_FILE: str = None
    ABBREVIATION_LIST: defaultdict = field(
        default_factory=lambda: defaultdict(list))
    KONJ: list = field(
        default_factory=lambda: [
            "und", "in", "oder", "&", "u.", "während", "auch"
        ]
    )
    PUNC: str = re.escape(string.punctuation + "«»„—¦¬")
    IN_WORD_SPLITTERS: str = re.escape("/")
    SENTENCE_ENDING: list = field(default_factory=lambda: [".", "!", "?"])

    def load_abbrevs(self) -> defaultdict:
        """
        Load the abbreviations from a file into a set for quick checking if a\
        word is included.

        Each abbreviation in the file should be on a separate line and will be\
        processed into a set where each abbreviation is associated with its\
        context (words before and after it).

        Args:
            infile (str): Path to the input file containing abbreviations.

        Returns:
            defaultdict: A dictionary where each key is an abbreviation and\
                the value is a list of dictionaries with 'before' and 'after'\
                keys indicating the context of the abbreviation.

        Example:
            If the input file contains:
                "Dr. John Smith"
                "Prof. Jane Doe"

            The returned dictionary will be:
                {
                    "dr.": [{"before": [], "after": ["john", "smith"]}],
                    "john": [{"before": ["dr."], "after": ["smith"]}],
                    "smith": [{"before": ["dr.", "john"], "after": []}],
                    "prof.": [{"before": [], "after": ["jane", "doe"]}],
                    "jane": [{"before": ["prof."], "after": ["doe"]}],
                    "doe": [{"before": ["prof.", "jane"], "after": []}]
                }
        Load the abbreviations into a set for quick checking if a word is
        included. Each abbrev looks like this:
        {"abbrev": [{"before": [], "after": []}]}

        TODO: Do some of the prep (like lowercasing) on the abbrev file itself.
        This will also prevent some duplicates.
        """
        with open(self.ABBREVIATION_FILE, encoding="utf8") as inf:
            for line in inf:
                line = line.rstrip().lower()
                line = line.split()
                words_in_abbrev = []
                for word in line:
                    word = re.sub(
                        r"([{}])".format(self.IN_WORD_SPLITTERS), r" \1 ", word
                    )
                    word = re.sub(r"(\.)[{}]*".format(self.PUNC), r"\1 ", word)
                    word = word.rstrip()
                    for w in word.split(" "):
                        words_in_abbrev.append(w)

                for pos, word in enumerate(words_in_abbrev):
                    self.ABBREVIATION_LIST[word].append(
                        {
                            "before": words_in_abbrev[:pos],
                            "after": words_in_abbrev[pos + 1:],
                        }
                    )


def fuse_hyphens(content: str, preprocess_data: PreprocessConfig) -> list:
    """
    Fuse words that were split by hyphens or line breaks in OCR outputs.

    Args:
        content (str): The raw text containing words and their coordinate\
            metadata.

    Returns:
        list: A list of dictionaries, where each dictionary has a "word" (str)\
              and a "coord" (list) key, representing the fused token and its\
              associated coordinates.

    Example:
        >>> sample_text = "Hel¬ 001122\\nlo 12345\\nWorld 67890"
        >>> fuse_hyphens(sample_text)
        [{'word': 'Hello', 'coord': ['001122', '12345']},
         {'word': 'World', 'coord': ['67890']}]

    Explanation:
        1. Lines with fewer than two tokens are skipped.
        2. If a word ends with a special marker (like a trailing hyphen), the\
           following token may be fused, preserving coordinate metadata.
        3. Returns the fully assembled words and their combined coordinates.
    """
    output = []
    lastword = None  # There might be multiple ones possible
    maybe_lastword = None
    lastcoord = []
    KONJ = preprocess_data.KONJ
    for line in content.split("\n"):
        line = line.split()
        if len(line) < 2:
            continue
        word = line[0]
        coord = [line[1]]
        if lastword is not None:
            word = lastword + word
            coord = lastcoord + coord
            lastword = None
            lastcoord = []
        elif maybe_lastword is not None:
            if word not in KONJ and word[0].islower():
                word = maybe_lastword + word
                coord = lastcoord + coord
            elif word not in KONJ and word[0].isupper():
                # this indicates a concatenated word like "Fischli-Boson",
                # "Greig-Gould" etc.
                word = maybe_lastword + "-" + word
                coord = lastcoord + coord
            else:
                output.append({"word": maybe_lastword + "-",
                               "coord": lastcoord})
            maybe_lastword = None
            lastcoord = []
        if word[-1] == "¬":
            lastword = word[:-1]
            lastcoord = coord
        elif word[-1] == "-" and len(word) > 1:
            maybe_lastword = word[:-1]
            lastcoord = coord
        else:
            output.append({"word": word, "coord": coord})
    if lastword is not None:
        output.append({"word": lastword, "coord": lastcoord})
    elif maybe_lastword is not None:
        output.append({"word": maybe_lastword, "coord": lastcoord})
    return output


def check_for_abbrev(pos: int,
                     text,
                     preprocess_data: PreprocessConfig) -> bool:
    """
    Check if the token at the specified position is recognized as an
    abbreviation.

    This function verifies if the token at the given index is listed in a
    predefined set of abbreviations and whether the surrounding context
    matches the expected "before" and "after" patterns defined for that
    abbreviation.

    Args:
        pos (int): The position of the token within the text list.
        text (list of tuple): The tokenized text, where each token is
            represented as a tuple containing the word (and possibly other
            metadata).

    Returns:
        bool: True if the token at the specified position is identified as an
        abbreviation (matching the required context), otherwise False.
    """
    ABBREVIATION_LIST = preprocess_data.ABBREVIATION_LIST
    word = text[pos][0].lower()
    if word not in ABBREVIATION_LIST:
        return False
    for option in ABBREVIATION_LIST[word]:
        before_is_valid = True
        for i, token in enumerate(reversed(option["before"])):
            before_position = pos - i - 1
            if before_position < 0:
                before_is_valid = False
                break
            relevant_word = text[before_position][0]
            if relevant_word.lower() != token:
                before_is_valid = False
                break
        if not before_is_valid:
            continue
        after_is_valid = True
        for i, token in enumerate(option["after"]):
            after_position = pos + i + 1
            if after_position >= len(text):
                after_is_valid = False
                break
            relevant_word = text[after_position][0]
            if relevant_word.lower() != token:
                after_is_valid = False
                break
        if not after_is_valid:
            continue

        return True

    return False


def check_roman_numeral(word: str) -> bool:
    """
    Checks whether a given word matches a specific format for Roman numerals.

    Args:
        word (str): The input string to check.

    Returns:
        bool: True if the word ends with a period and the preceding characters
        consist only of the lowercase Roman numerals 'i', 'v', or 'x'.
        Otherwise, returns False.
    """
    word = word.lower()
    if word[-1] == "." and all(
        [True if x in ["x", "v", "i"] else False for x in word[:-1]]
    ):
        return True
    else:
        return False


def tokenize(content: list, preprocess_data: PreprocessConfig) -> list:
    """Tokenize the provided list of dictionaries containing words and their
    coordinates.

    This function processes each dictionary in the form:
        [
            {"word": "ExampleWord", "coord": "ExampleCoordinate"},
            ...
        ]

    <b>Tokenization Details</b>
        1. Separates punctuation that appears at the beginning or end of a
           word, preserving periods used in abbreviations.
        2. Splits certain in-word punctuation (e.g., semicolons, dashes) into
           separate tokens.
        3. Normalizes fully uppercase tokens by converting them to title case
           (e.g., "HANS" → "Hans").
        4. Treats tokens ending with a period as potential abbreviations or
           separates the period as an individual token if it is not part of
           an abbreviation.

    <b>Arguments</b>:
        content (list of dict) Each dict must have:
            1. "word" (string): The raw text token.
            2. "coord": The coordinate or reference string associated with the
            token.

    <b>Returns</b>
        list of dict, A new list in which each dict includes
            1. "token": The processed token string.\n
            2. "coord": The coordinate or reference string with informative
            suffixes to indicate type (e.g., ':main', ':lpunc', ':rpunc').\n
            3. "normalized": An optional key with the title-cased version of
            the token if it was originally uppercase.\n

    <b>Example</b>
        Input
            [{"word": "Hello", "coord": "1209745"}, {"word": "v.a.",
            "coord": "1908234"}]
        Output
            [
            {"token": "Hello", "coord": "1;2;0;9;7;4;5:main",
            "normalized": "Hello"},
            {"token": "v.", "coord": "1;9;0;8;2;3;4:main"},
            {"token": "a.", "coord": "1;9;0;8;2;3;4:main"}
            ]\n
    Tokenize the text.
    \n
    Input: List of dicts: [{"word": "Hello", "coord": "1209745"},
                           {"word": "World", "coord": "1908234"}]
    Output: Tokenized list of dicts.

    What tokenizing means in this case:
    - "v.a." => "v. a." => Two separate tokens (This will also help to tag
    names later on)
    - Remove punctuations left and right of the word (except periods on
    abbreviations) and add them as seperate tokens.
    - Not really tokenizing, but add a modified word element to do this:
    "HANS" => "Hans" (TODO: Test if this actually improves accuracy)
    """
    output = []
    temp_word_list = []
    PUNC = preprocess_data.PUNC
    IN_WORD_SPLITTERS = preprocess_data.IN_WORD_SPLITTERS
    for element in content:
        word = element["word"]
        coord = element["coord"]
        rp = re.match(
            r"([{}]*)(.+?\.?)([{}]*)$".format(
                PUNC, PUNC.replace("-", "")
            ), word
        )
        lpunc = ""
        if len(rp.group(1)) > 0:
            lpunc = rp.group(1)
        rpunc = ""
        if len(rp.group(3)) > 0:
            rpunc = rpunc + rp.group(3)
        word = rp.group(2)

        # splits = re.split(r"({}+)".format(PUNC.replace(".", "")), word)
        # if len(splits) > 1:
        #     pp.pprint(splits)
        #     word = " ".join([x for x in splits if len(x) > 0])
        word = re.sub(r"([{}])".format(IN_WORD_SPLITTERS), r" \1 ", word)
        word = re.sub(r"(\.)[{}]*".format(PUNC), r"\1 ", word)

        word = word.rstrip()
        words = word.split(" ")
        words = [x for x in words if x]
        for i, word in enumerate(words):
            if i == 0 and i + 1 == len(words):
                temp_word_list.append((word, coord, rpunc, lpunc))
            elif i == 0:
                temp_word_list.append((word, coord, "", lpunc))
            elif i + 1 == len(words):
                temp_word_list.append((word, coord, rpunc, ""))
            else:
                temp_word_list.append((word, coord, "", ""))

    for pos, (word, coord, rpunc, lpunc) in enumerate(temp_word_list):
        if lpunc:
            output.append({"token": lpunc, "coord": ";".join(coord)+":lpunc"})
        # word is abbreviated
        if (
            check_for_abbrev(pos, temp_word_list, preprocess_data)
            or check_roman_numeral(word.lower())
            or (len(word) < 5 and word.istitle() and word[-1] == ".")
            or re.match(r"\d{1,2}\.", word)
        ):
            word_dict = {"token": word, "coord": ";".join(coord) + ":main"}
            if word.isupper():
                word_dict["normalized"] = word.title()
            output.append(word_dict)
        # word is not abbreviated, but had period
        elif word[-1] == ".":
            word = word[:-1]
            word_dict = {"token": word, "coord": ";".join(coord) + ":main"}
            if word.isupper():
                word_dict["normalized"] = word.title()
            output.append(word_dict)
            output.append({"token": ".", "coord": ";".join(coord) + ":rpunc"})
        # no period
        else:
            word_dict = {"token": word, "coord": ";".join(coord) + ":main"}
            if word.isupper():
                word_dict["normalized"] = word.title()
            output.append(word_dict)

        if len(rpunc) > 0:
            output.append({"token": rpunc, "coord": ";".join(coord)+":rpunc"})

    return output


def split_sentences(content: list, preprocess_data: PreprocessConfig) -> list:
    """
    Splits a list of tokens into sentences based on sentence-ending
    punctuation.

    Args:
        content (list): A list of tokens, where each token is a dictionary
            containing token information.
        preprocess_data (PreprocessConfig): Configuration object containing
            preprocessing settings, including sentence-ending punctuation.

    Returns:
        list: A list of lists, where each inner list contains tokens that form
            a sentence.
    """
    sentences = []
    sentence = []
    SENTENCE_ENDING = preprocess_data.SENTENCE_ENDING
    for token in content:
        if token["coord"].endswith("rpunc") and \
                token["token"][-1] in SENTENCE_ENDING:
            sentence.append(token)
            sentences.append(sentence)
            sentence = []
        else:
            sentence.append(token)
    if sentence:
        sentences.append(sentence)

    return sentences


def preprocess_file(infile: str, conf: dict) -> list:
    """
    Preprocesses a file output by OCR and returns a list of sentences.

    Args:
        infile (str): Path to the input file to be preprocessed.\n
        conf (dict): Configuration dictionary containing the path to the\
            abbreviation file.

    Returns:
        list: A list of sentences, where each sentence is a list of tokens,\
            and each token is a dictionary.

    Raises:
        FileNotFoundError: If the input file does not exist.\n
        KeyError: If the configuration dictionary does not contain the\
            required keys.

    Example:
        conf = {"PATH_TO_ABBREVIATION_FILE": "/path/to/abbreviation/file"}\n
        sentences = preprocess_file("/path/to/input/file", conf)
    """
    preprocess_data = PreprocessConfig(
        ABBREVIATION_FILE=conf["PATH_TO_ABBREVIATION_FILE"]
    )
    preprocess_data.load_abbrevs()
    with open(infile, encoding="utf8") as inf:
        content = inf.read()
    content = fuse_hyphens(content, preprocess_data)
    content = tokenize(content, preprocess_data)
    sentences = split_sentences(content, preprocess_data)

    return sentences


def get_year_chunk_paths(year: str) -> list:
    """Chunks the pages of the given year path.

    Args:
        year (str): Path to the year folder.

    Returns:
        list: Chunked files per year as list of lists.
    """
    infiles = sorted(glob.glob(year + "/*.txt"))
    MAX_INFILES_SIZE = 1000
    if len(infiles) > MAX_INFILES_SIZE:
        chunk_list = split_year.split_directory(year)
        return [
            (
                tuple(
                    os.path.normpath(year).split(os.sep)[-2:]
                    + ["-", str(chunk_name).zfill(2)]
                ),
                pagepaths,
            )
            for chunk_name, pagepaths in chunk_list
        ]
    else:
        return [(tuple(os.path.normpath(year).split(os.sep)[-2:]), infiles)]


def prep_year_data_for_tagging(data: tuple) -> tuple:
    """Prepare the year data for tagging.
    TODO this is the fourth function that just "starts" the preprocessing.
    Surely we can do better.

    Args:
        data (tuple): The first entry is the year, the second entry is the
         list of paths to infiles and the third entry is the config dict.

    Returns:
        tuple: The first entry is a dictionary where the keys are years and
         the values is prepared data for tagging. The second entry is the year.
    """
    year, infiles, conf = data
    logging.info("Prepping %s", year)
    od = OrderedDict()
    for infile in infiles:
        od[os.path.basename(infile)] = preprocess_file(infile, conf)
    return od, year


def start_preprocessing(year_directories: List[str], conf: dict):
    """Preprocess the files in the year directories in chunks.
    TODO this is the third function that just "starts" the preprocessing.
    Surely we can do better.

    Args:
        year_directories (List[str]): List of years.
        conf (dict): Dictionary with various paths and settings.

    Yields:
        tuple: The first entry is the year (from list of years),
         the second entry is the dictionary of preprocessed data.
    """
    chunked_years = []
    BATCH_SIZE = conf["BATCH_SIZE"]
    for year in year_directories:
        logging.info("Chunking %s", year)
        chunked_years.extend(get_year_chunk_paths(year))

    for i in range(0, len(chunked_years), BATCH_SIZE):
        year_chunk = chunked_years[i: i + BATCH_SIZE]
        packaged = [(y[0], y[1], conf) for y in year_chunk]
        with Pool(BATCH_SIZE) as p:
            # removing imap can improve ram requirements again
            for files, year in p.imap(prep_year_data_for_tagging, packaged):
                yield year, files


def execute_preprocessing(conf: dict):
    """
    Executes the preprocessing on the files given in the conf dict.

    Args:
        conf (dict): Dictionary containing various paths and settings.

    Yields:
        tuple: The first entry is the year, the second entry is the dictionary\
            of preprocessed data.
    
    Example:
        bliblablub

    Explanation:
        bliblablub
    """
    if "CUSTOM_PATHS" in conf:
        # If custom paths are set (this is default pipeline behavior), we get
        # year directories, not magazine directories
        year_directories = conf["CUSTOM_PATHS"]
        for year, files in start_preprocessing(year_directories, conf):
            yield year, files
    else:
        magazine_folder = sorted(
            glob.glob(conf["PATH_TO_INPUT_FOLDERS"] + "/*"))
        for magazine in magazine_folder:
            # If RAM is still not enough, consider cutting this further down,
            # e.g. processing chunks of 20 year at the same time
            year_directories = sorted(glob.glob(magazine + "/*"))
            # put all year_folder in a worker pool
            for year, files in start_preprocessing(year_directories, conf):
                yield year, files


def timed_execute_preprocessing(conf: dict) -> dict:
    """Runs execute preprocessing but also logs the time it took to run."""
    start_time = datetime.now()
    logging.info("Starting Preprocessing at", start_time, ":")
    preprocessed_data = execute_preprocessing(conf)
    logging.info("Preprocessing took:", datetime.now() - start_time)
    return preprocessed_data


def main():
    # NOTE this is for debugging purposes
    preprocess_data = PreprocessConfig()
    preprocess_data.load_abbrevs()
    infolder = sorted(glob.glob("{}/*/*/*.txt".format(sys.argv[1])))

    filelist = []
    for infile in infolder:
        pp.pprint(infile)
        sentences = preprocess_file(infile)
        if not sentences:
            continue
        text = " <EOS>\n".join(
            [
                " ".join(
                    [
                        x["normalized"] if "normalized" in x else x["token"]
                        for x in sentence
                    ]
                )
                for sentence in sentences
            ]
        )
        filedict = {}
        filedict["text"] = text
        filedict["labels"] = []
        path = Path(infile)
        filedict["meta"] = {
            "collection": str(path.parent).split("\\")[-1],
            "filename": os.path.basename(infile),
        }
        filelist.append(json.dumps(filedict))

    with open(sys.argv[2], mode="w", encoding="utf8") as outf:
        for entry in filelist:
            outf.write(entry + "\n")

    """
    outfile = open("vertical.txt", mode="w", encoding="utf8")
    for infile in infolder:
        sentences = preprocess_file(infile)
        for sentence in sentences:
            for token in sentence:
                if "normalized" in token.keys():
                    outfile.write(token["normalized"]+"\n")
                else:
                    outfile.write(token["token"]+"\n")
            outfile.write("\n")

    outfile.close()
    """


if __name__ == "__main__":
    main()
