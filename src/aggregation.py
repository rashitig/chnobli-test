#! /usr/bin/python3

from collections import defaultdict
from germalemma import GermaLemma
import re
import pprint as pp
from datetime import datetime
import logging
from utility.utils import save_data
"""
TODO: Aggregate HANS FUCHS with Hans Fuchs.
TODO: Do not aggregate entities with each other where "other"-Info is given,
but no lastname
TODO: Check if entities with multiple candidates should also
check for candidates on previous pages and not only the same page.
TODO: Remove multiple mentions of jobs in "profession"-info
"""

PREPATTERN = re.compile(r"^[\W_]+", flags=re.UNICODE)
POSTPATTERN = re.compile(r"[\W_]+$", flags=re.UNICODE)
# TODO don't we want to remove these characters from within a word as well?


def create_new_aggregated_unit(reference: dict) -> dict:
    """
    Creates a new aggregated unit for a person entity based on the provided
    reference.

    Args:
        reference (dict): A dictionary containing information about the person
         entity and where the person appeared in the journal.

    Returns:
        dict: A dictionary representing the new aggregated unit where we
         changed the values to sets of tuples.
    """
    info = reference["info"]
    return {
        "lastname": info["lastnames"],
        "firstname": set([tuple(info["firstnames"].split())]),
        "abbr_firstname": set([tuple(info["abbr_firstnames"].split())]),
        "address": set([tuple(info["address"])]),
        "titles": set([tuple(info["titles"])]),
        "profession": set([tuple(info["occupations"])]),
        "other": set([tuple(info["others"])]),
        "references": {
                (reference["pageNo"], reference["pageNames"],
                 reference["pid"]): [(reference["sentenceNo"],
                                      reference["positions"],
                                      reference["articles"])]
            },
        "type": "PER"
        }


def merge_to_existing_aggregated_unit(match: dict, reference: dict) -> None:
    """Merges the information from a reference into an existing aggregated
    unit.

    Args:
        match (dict): The existing aggregated unit to which the reference
         will be merged.

        reference (dict): A dictionary containing information about the person
         entity and where the person appeared in the journal.

    Returns:
        None: The function modifies the `match` dictionary in place by adding
        the information from the `reference`.
    """
    # TODO making these tuples is quite inconvenient.
    # all of this should be rewritten.
    info = reference["info"]
    match["firstname"].add(tuple(info["firstnames"].split()))
    match["abbr_firstname"].add(tuple(info["abbr_firstnames"].split()))
    match["titles"].add(tuple(info["titles"]))
    match["other"].add(tuple(info["others"]))
    match["address"].add(tuple(info["address"]))
    match["profession"].add(tuple(info["occupations"]))
    if ((reference["pageNo"], reference["pageNames"], reference["pid"]) in
            match["references"]):
        match["references"][(reference["pageNo"], reference["pageNames"],
                             reference["pid"])].append(
                                 (reference["sentenceNo"],
                                  reference["positions"],
                                  reference["articles"]))
    else:
        match["references"][(reference["pageNo"], reference["pageNames"],
                             reference["pid"])] = [(reference["sentenceNo"],
                                                    reference["positions"],
                                                    reference["articles"])]


def decide_candidates(reference: dict,
                      candidates: list,
                      aggregated_names: list,
                      verbose=False) -> None:
    """
    Determines the best candidate from a list of candidates to merge with the
    given reference. If no suitable candidate is found, creates a new
    aggregated unit for the reference.

    Args:
        reference (dict): A dictionary containing information about the person
         entity and where the person appeared in the journal.

        candidates (list): A list of dictionaries representing existing
         aggregated units that are potential matches for the reference.

        aggregated_names (list): A list of all aggregated units.
         If no suitable candidate is found, a new aggregated unit will be
         added to this list.

        verbose (bool, optional): If True, prints detailed information about
         the reference and the selected candidate. Defaults to False.

    Returns:
        None: The function modifies the `aggregated_names` list in place by
         either merging the reference into an existing aggregated unit or
         creating a new one.
    """
    if verbose:
        pp.pprint(reference)
    best_candidate = None
    for c in candidates:
        # get page and sentence number
        c_pos_list = [(page[0], entry[0]) for page, pagelist in
                      c["references"].items() for entry in pagelist]
        diff = [
            (
                reference["pageNo"] - c_pos[0],
                reference["sentenceNo"] - c_pos[1]
            )
            for c_pos in c_pos_list if reference["pageNo"] - c_pos[0] > 0 or (
                (
                    reference["pageNo"] - c_pos[0] == 0
                )
                and
                (
                    reference["sentenceNo"] - c_pos[1] >= 0
                )
            )
        ]
        if diff:
            diff = min(diff)
        else:
            continue
        if best_candidate is None:
            best_candidate = (c, diff[0], diff[1])
        else:
            if best_candidate[1] > diff[0]:
                best_candidate = (c, diff[0], diff[1])
            elif best_candidate[1] == diff[0]:
                if best_candidate[2] > diff[1]:
                    best_candidate = (c, diff[0], diff[1])
    if best_candidate is None:
        aggregated_names.append(create_new_aggregated_unit(reference))
    else:
        match = best_candidate[0]
        merge_to_existing_aggregated_unit(match, reference)
        if verbose:
            pp.pprint(match)


def full_firstname_match(ref: dict, aggregated_names: list) -> dict:
    """
    Finds a match in the aggregated names for a reference based on the
    full firstname and lastname.

    Args:
        ref (dict): A dictionary containing information about the reference.

        aggregated_names (list): A list of dictionaries representing existing
         aggregated units.

    Returns:
        dict: The matching aggregated unit if a match is found,
         otherwise `None`.
    """
    for entry in aggregated_names:
        if ref["info"]["lastnames"] == entry["lastname"]:
            if set(
                [
                    x for x in ref["info"]["firstnames"].split() if x != ""
                ]
            ).isdisjoint([y for x in entry["firstname"] for y in x]):
                continue
            return entry
    return None


def aggregate_with(namepart_dict: dict,
                   aggregated_names: list,
                   namepart: str) -> None:
    """
    Aggregates references from a dictionary into existing aggregated units
    or creates new aggregated units based on the specified name part.

    Args:
        namepart_dict (dict): A dictionary where keys are name parts
         (e.g., last names) and values are lists of references (dictionaries)
         containing information about person entities.

        aggregated_names (list): A list of dictionaries representing existing
         aggregated units. This list will be updated with new or merged
         aggregated units.

        namepart (str): Specifies the type of name part to use for aggregation.

    Raises:
        Exception: If the provided `namepart` is not recognized.

    Returns:
        None: The function modifies the `aggregated_names` list in place by
         either merging references into existing aggregated units or creating
         new ones.
    """
    for key, value in namepart_dict.items():
        for reference in value:
            if namepart == "fullfirstnames":
                # Aggregate all persons that have a matching lastname and at
                # least one matching firstname.
                # "Hans Mueller" <=> "Hans Friedrich Mueller"
                # Also check for matching gender (or no gender info)
                match = full_firstname_match(reference, aggregated_names)
                if not match:
                    candidates = []
                else:
                    candidates = [match]
            elif namepart == "abbrevs":
                # Aggregate all persons that have a matching lastname and at
                # least one matching firstname.
                # "H. Mueller" <=> "Hans Friedrich Mueller"
                # Also check for matching gender (or no gender info)
                # This time, we need to collect candidates, then take the one
                # that appeared the closest last time.
                candidates = abbrev_firstname_match(reference,
                                                    aggregated_names)
            elif namepart == "onlylastnames":
                # Aggregate with matching lastnames, if multiple candidates
                # choose last seen.
                candidates = only_lastname_match(reference, aggregated_names)
            elif namepart == "onlyfirstnames":
                candidates = only_firstname_match(reference, aggregated_names)
            elif namepart == "onlyabbrevfirstnames":
                candidates = only_abbrev_firstname_match(reference,
                                                         aggregated_names)
            elif namepart == "others":
                candidates = others_match(reference, aggregated_names)
            else:
                raise Exception(f"This namepart: {namepart} is unknown.")

            if len(candidates) == 0:
                aggregated_names.append(create_new_aggregated_unit(reference))
            elif len(candidates) == 1:
                match = candidates[0]
                merge_to_existing_aggregated_unit(match, reference)
            else:
                decide_candidates(reference, candidates, aggregated_names)


def abbrev_firstname_match(reference: dict, aggregated_names: list) -> list:
    """
    Finds matches in the aggregated names for a reference based on the
    abbreviated first and lastname.

    Args:
        reference (dict): A dictionary containing information about the
         reference.

        aggregated_names (list): A list of dictionaries representing existing
         aggregated units.

    Returns:
        list: A list of matching aggregated units where the abbreviated first-
         and lastname match the reference.
    """
    matches = []
    for entry in aggregated_names:
        if reference["info"]["lastnames"] == entry["lastname"]:
            set_abbr_fnames = set(
                [
                    x[0]+"." for x in reference["info"]["abbr_firstnames"].split() if x != ""
                ]
            )
            if (
                set_abbr_fnames.isdisjoint(
                    [
                        y[0]+"." for x in entry["firstname"] for y in x
                    ]
                ) and set_abbr_fnames.isdisjoint(
                    [
                        y[0]+"." for x in entry["abbr_firstname"] for y in x
                    ]
                )
            ):
                continue
            matches.append(entry)
    return matches


def only_lastname_match(reference: dict, aggregated_names: list) -> list:
    """
    Finds matches in the aggregated names for a reference based on the
     lastname only.

    Args:
        reference (dict): A dictionary containing information about the
         reference.

        aggregated_names (list): A list of dictionaries representing existing
         aggregated units.

    Returns:
        list: A list of matching aggregated units where the lastname matches
         the reference.
    """
    matches = []
    for entry in aggregated_names:
        if reference["info"]["lastnames"] == entry["lastname"]:
            matches.append(entry)
    return matches


def only_firstname_match(reference: dict, aggregated_names: list) -> list:
    """
    Finds matches in the aggregated names for a reference based on the
     firstname only.

    Args:
        reference (dict): A dictionary containing information about the
         reference.

        aggregated_names (list): A list of dictionaries representing existing
         aggregated units.

    Returns:
        list: A list of matching aggregated units where the firstname matches
         the reference.
    """
    matches = []
    for entry in aggregated_names:
        if (
            reference["info"]["firstnames"] in [
                y for x in entry["firstname"] for y in x
            ]
        ):
            matches.append(entry)
    return matches


def only_abbrev_firstname_match(reference: dict,
                                aggregated_names: list) -> list:
    """
    Finds matches in the aggregated names for a reference based on the
     abbreviated firstname only.

    Args:
        reference (dict): A dictionary containing information about the
         reference.

        aggregated_names (list): A list of dictionaries representing existing
         aggregated units.

    Returns:
        list: A list of matching aggregated units where the abbreviated
         firstname matches the reference.
    """
    matches = []
    for entry in aggregated_names:
        if (
            reference["info"]["abbr_firstnames"] in [
                y for x in entry["abbr_firstname"] for y in x
            ]
        ):
            matches.append(entry)
    return matches


def others_match(reference: dict, aggregated_names: list) -> list:
    """
    Finds matches in the aggregated names for a reference based on the
     others field only.

    Args:
        reference (dict): A dictionary containing information about the
         reference.

        aggregated_names (list): A list of dictionaries representing existing
         aggregated units.

    Returns:
        list: A list of matching aggregated units where the others field
         matches the reference.
    """
    matches = []
    for entry in aggregated_names:
        for other in reference["info"]["others"]:
            if other in [y for x in entry["other"] for y in x]:
                matches.append(entry)
    return matches


def clean_up_aggregation(aggregated_names: list) -> list:
    """Cleans up the given aggregated person list by sorting and re-writing
    the datastructure of the references.

    Args:
        aggregated_names (list): List of dictionaries of people.

    Returns:
        list: Cleaned up aggregated names list.
    """
    aggregated_names = sorted(
        aggregated_names, key=lambda k: (k["lastname"], k["firstname"])
    )
    for i, entry in enumerate(aggregated_names):
        # sort functions may be deleted for performance improvements, only
        # added for test reasons (easier to compare files when they are the
        # same each run)
        entry["id"] = i
        entry["firstname"] = sorted(
            [" ".join(fname) for fname in entry["firstname"] if fname]
        )
        entry["abbr_firstname"] = sorted(
            [" ".join(fname) for fname in entry["abbr_firstname"] if fname]
        )
        entry["titles"] = [" ".join(reversed(x)) for x in entry["titles"] if x]
        entry["address"] = [y for x in entry["address"] if x for y in x if y]
        entry["profession"] = [
            y for x in entry["profession"] if x for y in x if y
        ]
        entry["other"] = [x for x in entry["other"] if x]
        new_references = defaultdict(list)

        for k, v in sorted(entry["references"].items()):
            elements = set()
            for x in v:
                for el in x[2]:
                    elements.add(el)
            elements = list(elements)
            elements = sorted(elements)
            new_references[k[1]] = {
                "pid": k[2],
                "refs": [{"sent": x[0], "coords": x[1]} for x in v],
                "elements": elements
            }
        entry["references"] = new_references
    return aggregated_names


def map_genitive_versions(all_names: list,
                          lastname_dict: dict,
                          key: str) -> None:
    """Maps the person names to a non-genitive version by removing the last "s"
    from their lastnames in certain cases.

    Args:
        all_names (list): A list of person names mentioned in the journal.
        lastname_dict (dict): A dict of lastnames to map the genitive to.
        key (str): What namepart to map.

    Returns:
        None: The lastname_dict is changed by mapping away the genitive.
    """
    for lastname in lastname_dict:
        if (
            lastname.endswith("s")
            and len(lastname) > 1
            and lastname[-2] != 's'
            and lastname[:-1] in all_names
        ):
            for entry in lastname_dict[lastname]:
                entry["info"][key] = entry["info"][key][:-1]


def map_genitive_places(all_names: list, place_list: list) -> None:
    """Maps the place names to a non-genitive version by removing the last "s"
    in certain cases.

    Args:
        all_names (list): A list of place names mentioned in the journal.
        place_list (list): A list of places to map the genitive to.

    Returns:
        None: Maps away the genitive in the places in the place_list.
    """

    MINIMUMGENITIVELENGTH = 4

    for place in place_list:
        for i in range(len(place["tokens"])):
            if (
                place["tokens"][i].lower().endswith("s")
                and len(place["tokens"][i]) > MINIMUMGENITIVELENGTH
                and place["tokens"][i][-2].lower() != "s"
                and place["tokens"][i][:-1].lower() in all_names
            ):
                # pp.pprint(place["tokens"][i])
                place["tokens"][i] = place["tokens"][i][:-1]
                # pp.pprint(place["tokens"][i])


def find_place_match(place_name: str,
                     place_type: str,
                     aggregated_places: list) -> dict:
    """
    Finds matches in the aggregated placenames for the given placename based on
     full matches only.

    Args:
        place_name (str): The placename as a string.

        place_type (str): The type value of the place entity (GPE, LOC, etc.)

        aggregated_places(list): A list of dictionaries representing existing
         aggregated units.

    Returns:
        dict: A dict of a matching aggregated unit where the placenames
         match.
    """
    for entry in aggregated_places:
        if (
            " ".join(entry["tokens"]).lower() == place_name
            and entry["type"] == place_type
        ):
            return entry
    return False


def aggregate_places(all_places: list, aggregated_places: list):
    """Merges the information from a reference list into an existing aggregated
    unit in a list of aggregated places.

    Args:
        all_places (list): A list of dictionaries containing information about
         the place entities and where they appeared in the journal.

        aggregated_places (list):  A list of dictionaries of existing
         aggregated units to which the reference will be merged.

    Returns:
        None: The function modifies the `match` dictionary in place by adding
        the information from the `reference`.
    """
    for place in all_places:
        place_name = " ".join(place["tokens"]).lower()
        found_place = find_place_match(
            place_name, place["type"], aggregated_places
        )
        if found_place:
            aggregate_place(found_place, place)
        else:
            aggregated_places.append(create_new_aggregated_place(place))


def aggregate_place(found: dict, place: dict) -> None:
    """Merges the information from a reference into an existing aggregated
    unit.

    Args:
        found (dict): The existing aggregated unit to which the reference
         will be merged.

        place (dict): A dictionary containing information about the place
         entity and where the place appeared in the journal.

    Returns:
        None: The function modifies the `found` dictionary in place by adding
        the information from the `place` reference.
    """

    # type needs no aggregation
    if (
        place["pageNo"], place["pageNames"], place["pid"]
       ) in found["references"]:
        found["references"][(place["pageNo"],
                             place["pageNames"],
                             place["pid"])].append(
                                 (
                                     place["sentenceNo"],
                                     place["positions"],
                                     place["articles"]
                                 )
                            )
    else:
        found["references"][(place["pageNo"],
                             place["pageNames"],
                             place["pid"])] = [
                                 (
                                     place["sentenceNo"],
                                     place["positions"],
                                     place["articles"]
                                 )
                            ]


def create_new_aggregated_place(reference: dict) -> dict:
    """
    Creates a new aggregated place for a place entity based on the provided
    reference.

    Args:
        reference (dict): A dictionary containing information about the place
         entity and where the place appeared in the journal.

    Returns:
        dict: A dictionary representing the new aggregated place unit where we
         changed the values to sets of tuples.
    """
    return {
        "name": " ".join([x.title() if x.isupper else x for x in
                         reference["tokens"]]),
        "tokens": reference["tokens"],
        "type": reference["type"],
        "references": {
                (reference["pageNo"],
                 reference["pageNames"],
                 reference["pid"]): [(reference["sentenceNo"],
                                      reference["positions"],
                                      reference["articles"])]
            }
        }


def clean_up_aggregation_places(aggregated_places: list,
                                last_index: int) -> list:
    """Cleans up the given aggregated places list by sorting and re-writing
    the datastructure of the references.

    Args:
        aggregated_places (list): List of dictionaries of places.
        last_index (int): Index of the last places entity we processed.

    Returns:
        list: Cleaned up aggregated places list.
    """
    aggregated_places = sorted(aggregated_places, key=lambda k: k["name"])
    for i, entry in enumerate(aggregated_places):
        entry["id"] = i + last_index + 1
        new_references = defaultdict(list)
        # for k, v in entry["references"].items():
        #    new_references[k[1]].extend([{"sent": x[0], "coords":x[1],
        #                                  "articles":x[2]} for x in v])
        for k, v in sorted(entry["references"].items()):
            elements = set()
            for x in v:
                for el in x[2]:
                    elements.add(el)
            elements = list(elements)
            elements = sorted(elements)
            new_references[k[1]] = {
                "pid": k[2],
                "refs": [{"sent": x[0], "coords": x[1]} for x in v],
                "elements": elements
            }
        entry["references"] = new_references
    return aggregated_places


def clean_lastname(word: str) -> str:
    """Cleans given word with the global PRE and POSTPATTERN."""
    word = PREPATTERN.sub("", word)
    word = POSTPATTERN.sub("", word)
    return word


def aggregate_names(data: list) -> list:
    """Given a list of person entities, aggregate the mentions depending on
    the person information and where they appear in the journal.

    Args:
        data (list): List of person entities.

    Returns:
        list: Aggregated list of person entities.
    """
    lemmatizer = GermaLemma()
    # restrict data to persons only, aggregate places in a separate block of
    # code (as it's much less complicated)
    place_data = [x for x in data if "info" not in x]
    data = [x for x in data if "info" in x]

    # do persons first
    all_last_names = set([y for x in data for y in x["info"]["lastnames"]])
    all_first_names = set([y for x in data for y in x["info"]["firstnames"]])
    lastnames_with_firstnames = defaultdict(list)
    lastnames_with_abbrev = defaultdict(list)
    lastnames_only = defaultdict(list)
    firstnames_only = defaultdict(list)
    abbrev_firstnames_only = defaultdict(list)
    others_only = defaultdict(list)
    debug_list = []  # just collect all remaining entities
    for entry in data:
        info = entry["info"]
        lastname = " ".join([clean_lastname(x) for x in info["lastnames"]])
        info["lastnames"] = lastname
        info["firstnames"] = " ".join(info["firstnames"])
        info["abbr_firstnames"] = " ".join(info["abbr_firstnames"])

        # lemmatize descriptors
        # We assume all occupations are nouns
        info["occupations"] = [
            lemmatizer.find_lemma(x, "N") for x in info["occupations"]
        ]
        # We assume all titles are nouns
        info["titles"] = [
            lemmatizer.find_lemma(x, "N") for x in info["titles"]
        ]
        # We assume all address are nouns
        info["address"] = [
            lemmatizer.find_lemma(x, "N") for x in info["address"]
        ]

        if len(lastname) == 0:
            if len(info["firstnames"]) > 0:
                firstnames_only[info["firstnames"]].append(entry)
            elif len(info["abbr_firstnames"]) > 0:
                abbrev_firstnames_only[info["abbr_firstnames"]].append(entry)
            elif len(info["others"]) > 0:
                others_only[tuple(info["others"])].append(entry)
            else:
                debug_list.append(entry)
        else:
            if len(info["firstnames"]) > 0:
                lastnames_with_firstnames[lastname].append(entry)
            # these lines were commented out, but why?
            elif len(info["abbr_firstnames"]) > 0:
                lastnames_with_abbrev[lastname].append(entry)
            else:
                lastnames_only[lastname].append(entry)

    map_genitive_versions(
        all_last_names, lastnames_with_firstnames, "lastnames"
    )
    map_genitive_versions(all_last_names, lastnames_with_abbrev, "lastnames")
    map_genitive_versions(all_last_names, lastnames_only, "lastnames")
    map_genitive_versions(all_first_names, firstnames_only, "firstnames")

    aggregated_names = []
    aggregate_with(
        lastnames_with_firstnames, aggregated_names, "fullfirstnames"
    )
    aggregate_with(lastnames_with_abbrev, aggregated_names, "abbrevs")
    aggregate_with(lastnames_only, aggregated_names, "onlylastnames")
    aggregate_with(
        firstnames_only, aggregated_names, "onlyfirstnames"
    )
    # this below might do more damage than good
    aggregate_with(
        abbrev_firstnames_only, aggregated_names, "onlyabbrevfirstnames"
    )
    aggregate_with(others_only, aggregated_names, "others")

    aggregated_names = clean_up_aggregation(aggregated_names)

    # do places second
    all_place_names = set([y.lower() for x in place_data for y in x["tokens"]])
    map_genitive_places(all_place_names, place_data)
    aggregated_places = []
    aggregate_places(place_data, aggregated_places)
    aggregated_places = clean_up_aggregation_places(
        aggregated_places, len(aggregated_names)
    )

    aggregated_names = aggregated_names + aggregated_places

    return aggregated_names


# TODO these shouldn't be two functions, that's silly
def aggregate_and_save_data_timed(postprocessed_data,
                                  conf: dict,
                                  tasks: list):
    """
    Aggregates the postprocessed data based on the given configuration and
    tasks and logs the time it took to execute.

    Args:
        postprocessed_data : The data that has been postprocessed and is ready
            for aggregation.
        conf (dict): Configuration dictionary containing various settings
            and paths.
        tasks (list): List of tasks to be performed during aggregation.

    Raises:
        Exception: If 'post' is not included in the tasks list, an exception
                   is raised indicating that 'post,agg,link' must be called
                   together.

    Returns:
        Generator object containing the aggregated data as a list of
        dictionaries. Each dict contains the tagged people (and places)
    """
    start_time = datetime.now()
    logging.info("Starting Aggregation at", start_time, ":")
    if "post" not in tasks:
        raise Exception("'post,agg,link' must be called together")
    aggregated_data = execute_aggregation(postprocessed_data)
    logging.info("Aggregation took: ", datetime.now() - start_time)
    if "link" not in tasks:
        save_data(aggregated_data, conf, "agg")
    return aggregated_data


def execute_aggregation(data) -> dict:
    """Given the data we agggregate the person and place entities in said data
    based on their names and positions in the journal.

    Args:
        data: Tagged data of the magazine to be aggregated.

    Returns:
        dict: Dictionary of aggregated entities where each key is the mag-year
         and the values are the entities.
    """
    aggDict = {}
    for year, d in data:
        logging.info("Aggregating: %s", year)
        aggregated = aggregate_names(d)
        aggDict[year] = aggregated
    return aggDict
