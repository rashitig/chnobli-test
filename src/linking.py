#! /usr/bin/python3
import re
import unicodedata
from utility.linking_utils import search_person_wikidata, search_person_gnd
import logging
from datetime import datetime
from multiprocessing import Pool
from utility.utils import save_data_intermediate
"""
principles of this script:
The main point of connection is (obviously) the lastname.
The firstname is important as well, but can possibly be omitted.
Further criteria are the dates of birth and death.
Also Titles (if applicable, in the database, the field for biographical infos
sometimes contains that information.)
Ultimately, and maybe most importantly, we are interested in the occupations.
"""


def prep_word(word: str) -> str:
    """Normalizes and cleans up given string.

    Example:
        'OTMAR M\u00e4der' -> 'Otmar Mäder'
    """
    word = word.replace("^", "")
    word = unicodedata.normalize("NFC", word)
    word = word.title() if word.isupper() else word
    word = re.sub("""["']""", '', word)  # this removes ' within a word
    return word


def remove_obsolete_abbrevs(fnames: list, abbr_firstnames: list) -> list:
    """Removes abbreviated firstnames that are already covered by full
    firstnames.

    Args:
        fnames (list): List of firstnames
        abbr_firstnames (list): List of abbreviated firstnames

    Returns:
        list: List of firstnames where the obsolete abbreviated firstnames
        have been removed.

    Example:
        fnames = ["R.", "Richard"] => fnames = ["Richard"]
    """
    cleaned_abbr_fnames = []
    for abbr_group in abbr_firstnames:
        cleaned_abbr_group = []
        for abbr in abbr_group:
            is_obsolete = False
            abbr = abbr.rstrip(".")
            for fname in fnames:
                if fname.startswith(abbr):
                    is_obsolete = True
            if not is_obsolete:
                cleaned_abbr_group.append(abbr + ".")
        cleaned_abbr_fnames.append(cleaned_abbr_group)
    return cleaned_abbr_fnames


def get_candidates(person: dict, gnd_limit: int, wikidata_limit: int) -> dict:
    """Searches the GND and Wikidata index for candidates of a given person.

    Args:
        person (dict): A dictionary with various information on the given
            person entity.
        gnd_limit (int):
            The number of candidates to truncate our GND candidate list to.
        wikidata_limit (int):
            The number of candidates to truncate out wikidata
            candidate list to

    Returns:
        dict: Dictionary of candidates for the given person, containing
        information on the candidates themselves.
    """
    if (
        len(person["lastname"]) == 0
        or (len(" ".join(person["lastname"])) < 3)
        or (not person["firstname"] and not person["abbr_firstname"])
       ):
        return {}

    fnames = []
    fnames_flat = [x for y in person["firstname"] for x in y]
    for name in fnames_flat:
        if name not in fnames:
            fnames.append(name)

    abbr_fnames_trunc = remove_obsolete_abbrevs(
        fnames, person["abbr_firstname"]
    )
    abbr_fnames = []
    abbr_fnames_flat = [x for y in abbr_fnames_trunc for x in y]
    for name in abbr_fnames_flat:
        if name not in abbr_fnames:
            abbr_fnames.append(name)

    lastname = person["lastname"]
    if (len(lastname) > 1):
        lastname = " ".join(lastname)
    else:
        lastname = lastname[0]

    full_name = " ".join(fnames) + " " + lastname

    candidate_dict = dict()
    if abbr_fnames != []:
        full_name_abbr = " ".join(abbr_fnames) + " " + lastname
        candidate_dict.update(
            search_person_gnd(abbr_fnames, lastname, gnd_limit)
        )
        candidate_dict.update(
            search_person_wikidata(full_name_abbr, wikidata_limit)
        )
        candidate_dict = {
            k: v for k, v in sorted(
                candidate_dict.items(), key=lambda item: item[1]["score"],
                reverse=True
            )
        }

    res_dict_fullname = {}
    res_dict_fullname.update(search_person_gnd(fnames, lastname, gnd_limit))
    res_dict_fullname.update(search_person_wikidata(full_name, wikidata_limit))
    res_dict_fullname = {k: v for k, v in sorted(res_dict_fullname.items(),
                         key=lambda item: item[1]["score"], reverse=True)}
    candidate_dict.update(res_dict_fullname)

    return candidate_dict


def prep_person_entry(person: dict) -> None:
    """Normalizes and cleans up proper names in the given person dictionary.

    Args:
        person (dict): A person dictionary containing at least the keys
            "firstname", "abbr_firstname", "lastname", and "profession".
    """
    person["firstname"] = [
        [prep_word(y) for y in x.split()] for x in person["firstname"]
    ]
    person["abbr_firstname"] = [
        [prep_word(y) for y in x.split()] for x in person["abbr_firstname"]
    ]
    person["lastname"] = [prep_word(x) for x in person["lastname"].split()]
    person["profession"] = [prep_word(x) for x in person["profession"]]
    person["profession"].sort()


def prep_person_out(person: dict) -> None:
    """For a given dictionary, joins the fields "firstname", "abbr_firstname"
    and "lastname" repectively to make them strings.

    Args:
        person (dict): A person dictionary containing at least the keys
            "firstname", "abbr_firstname", and "lastname".
    """
    person["firstname"] = [" ".join(x) for x in person["firstname"]]
    person["abbr_firstname"] = [" ".join(x) for x in person["abbr_firstname"]]
    person["lastname"] = " ".join(person["lastname"])


def link_person(data_in) -> None:
    """Searches GND and Wikidata for candidates, sets a field "gnd_ids" in the
    person dictionary with at most `linked_persons_limit` candidates.

    Args
        data_in: This is a 4 tuple containing:
            - person (dict): A dictionary with keys "lastname", "firstname",
                "abbr_firstname", "address", "titles", "profession", "other",
                "references", "type" and "id".
                -- fields up until "references" are lists, except for lastname
                which is a string
                -- references is a defaultdict(list), a list of page_names
                where each page_name has coords and sentences associated with
                it where the candidate was mentioned
                -- type is a string denoting the entity type
                -- id is an internal id
            - gnd_limit (int):
                The number of candidates to truncate our GND candidate list to.
                Defaults to 15.
            - wikidata_limit (int):
                The number of candidates to truncate out wikidata
                candidate list to. Defaults to 5.
            - linked_persons_limit (int, optional):
                The number of candidates to truncate our combined gnd and
                wikidata candidates list to. Defaults to 10.
    Notes:
        - If the list of candidates is longer than `linked_persons_limit`,
          we check if the first letters of the firstnames match the abbreviated
          firstnames. If not, those candidates are deleted first, before we
          truncate to `linked_persons_limit`.
    Returns:
        dict: The changed person dictionary, now containing the gnd_ids.
    """
    person, gnd_limit, wikidata_limit, linked_persons_limit = data_in
    prep_person_entry(person)
    candidates = get_candidates(person, gnd_limit, wikidata_limit)

    abbr_firstname = [
        x.split(".") for y in person["abbr_firstname"] for x in y
        ]
    abbr_firstname = [x for y in abbr_firstname for x in y]
    gnds_to_remove = []

    len_candidates = len(candidates)
    if len_candidates > 10 and abbr_firstname != []:
        for gndid, value in candidates.items():
            notfound = True
            for prefforename in value["prefForename"]:
                if prefforename != "" and prefforename[0] in abbr_firstname:
                    notfound = False
                    break
            if notfound:
                gnds_to_remove.append(gndid)

    for gndid in gnds_to_remove:
        candidates.pop(gndid)

    person["gnd_ids"] = list(candidates.keys())[:linked_persons_limit]
    # keys are ordered by insertion so technically ordered by "_score" already
    prep_person_out(person)
    return person


def find_links(data_in) -> list:
    """Links all the people in the given data

    Args
        data_in (3-tuple)
            - mag_year (tuple): A tuple contaning the magazine shortname and
                year of the journal we're currently processing in that order.
            - data (list): The list of dictionaries created through
                aggregating PER entities in our magazine-year tuple.
            - conf (dict): configurations

    Returns:
        list: An ordered list of person entity dictionaries containing a
        "gnd_ids"
        key with the candidates list.
    """
    mag_year, data, conf = data_in

    magazine = mag_year[0]
    year = re.match(r"\d{4}", mag_year[1])
    if year is None:
        year = 0
    else:
        year = int(year.group(0))

    person_list = [
        (
            x,
            conf["GND_LIMIT"],
            conf["WIKIDATA_LIMIT"],
            conf["LINKED_PERSONS_LIMIT"]
        ) for x in data if x["type"] == "PER"]

    person_list = [link_person(x) for x in person_list]

    logging.info("Finished {} {}".format(magazine, str(year)))
    #print("Finished {} {}".format(magazine, str(year)))
    save_data_intermediate(mag_year, person_list, conf, "link")
    return person_list


def execute_linking_timed(aggregated_data: list,
                          conf: dict,
                          tasks: list) -> None:
    """
    Links the aggregated data based on the given configuration and tasks,
    and logs the time it took to run the linking.

    Args:
        aggregated_data (list): The data that has been aggregated and is ready
            for linking.
        conf (dict): Configuration dictionary containing various settings
            and paths.
        tasks (list): List of tasks to be performed during linking.

    Raises:
        Exception: If the tasks list doesn't include 'finish' or if 'agg' and
                   'post' is not included in the tasks list, an exception is
                   raised indicating that 'post,agg,link' or 'finish' must be
                   called together.

    Returns:
        None
    """
    start_time = datetime.now()
    logging.info("Starting Linking at", start_time, ":")
    #print("Starting Linking at", start_time, ":")
    execute_linking(aggregated_data, conf, tasks)
    logging.info("Linking took: ", datetime.now() - start_time)
    #print("Linking took: ", datetime.now() - start_time)


def execute_linking(data: dict, conf: dict, tasks: list) -> None:
    """
    Links the aggregated data based on the given configuration and tasks.

    Args:
        data (dict): The data that has been aggregated and is ready for
            linking. The keys are the magazine-year shortnames, the values
            are the aggregated entities.
        conf (dict): Configuration dictionary containing various settings and
            paths.
        tasks (list): List of tasks to be performed during linking.

    Raises:
        Exception: If the tasks list doesn't include 'finish' or if 'agg' and
                   'post' is not included in the tasks list, an exception is
                   raised indicating that 'post,agg,link' or 'finish' must be
                   called together.

    Returns:
        None
    """
    if (
        ("finish" not in tasks)
        or
        ("link" in tasks and ("agg" not in tasks or "post" not in tasks))
       ):
        raise Exception(
            "'post,agg,link' must be called together, or call 'finish' instead."
        )
    else:
        # NOTE this cannot be called seperately after the aggregation step,
        # "post,agg,link" need to be called together after "tag",
        # or you could just call "finish"
        logging.info("executeLinking reached")
        logging.info(
            "Linking now: " + ", ".join(["-".join(x) for x in data.keys()])
        )

        links = [
            (
                k,  # tuple of (mag, year) like ("cmt", "1998_076")
                v,  # list of person dictionaries
                conf
            ) for (k, v) in data.items()
        ]

        with Pool(len(links)) as p:
            links = p.map(find_links, links)
