import os
import json
from collections import Counter
import logging


class Paths:
    def __init__(self, conf):
        if "PATH_TO_GROUND_TRUTH" in conf and "PATH_TO_OUTFILE_FOLDER" in conf:
            self.paths = {
                "gt": conf["PATH_TO_GROUND_TRUTH"],
                "link": os.path.join(conf["PATH_TO_OUTFILE_FOLDER"], "link"),
                "eval": os.path.join(conf["PATH_TO_OUTFILE_FOLDER"], "eval"),
                "input": conf["PATH_TO_INPUT_FOLDERS"],
            }
            self.state = {
                "magazine": "",
                "file": ""
            }
            self.success = True
        else:
            self.success = False

    def update(self, key, value):
        self.state[key] = value

    def get(self, type_, key, ref_level_name="", gt_fuzziness_name=""):
        _TYPES = ["gt", "link", "eval", "input"]
        KEY_TYPES = ["magazine", "file", ""]
        REF_LEVEL_TYPES = ["ent", "ref", ""]
        GT_FUZZINESS_TYPES = ["with_fuzzy", "without_fuzzy", ""]
        assert type_ in _TYPES, f"'{type_}' is not in {_TYPES}"
        assert key in KEY_TYPES, f"'{key}' is not in {KEY_TYPES}"
        assert ref_level_name in REF_LEVEL_TYPES, f"'{ref_level_name}' is not in {REF_LEVEL_TYPES}"
        assert gt_fuzziness_name in GT_FUZZINESS_TYPES, f"'{gt_fuzziness_name}' is not in {GT_FUZZINESS_TYPES}"

        if type_ == "input":
            if ref_level_name != "":
                logging.warning(
                    "Careful! You selected the input folder but also a reference level.\
                    There are no reference levels at input, this value is ignored."
                )
                ref_level_name = ""
            elif gt_fuzziness_name != "":
                logging.warning(
                    "Careful! You selected the input folder but also a gt fuzziness level.\
                    There are no fuziness levels at input, this value is ignored."
                )
                gt_fuzziness_name = ""

        if type_ == "gt" and gt_fuzziness_name != "":
            logging.warning(
                    "Careful! You selected the ground truth folder but also a gt fuzziness level.\
                    The folder already determines the fuzziness level, this value is ignored."
            )
            gt_fuzziness_name = ""

        if ref_level_name != "":
            ref_level_name = "_"+ref_level_name
        if gt_fuzziness_name != "":
            gt_fuzziness_name = "_"+gt_fuzziness_name

        if key == "magazine":
            return os.path.join(
                self.paths[type_] + ref_level_name + gt_fuzziness_name,
                self.state["magazine"])
        elif key == "file":
            return os.path.join(
                self.paths[type_] + ref_level_name + gt_fuzziness_name,
                self.state["magazine"],
                self.state["file"])
        else:
            return os.path.join(
                self.paths[type_] + ref_level_name + gt_fuzziness_name)

    def get_json(self, type_):
        path = self.get(type_=type_, key="file")
        with open(path, "r") as f:
            content = json.load(f)
        return content

    def check_and_create(self, type_, key, ref_level_name, gt_fuzziness_name):
        # TODO potentially clean this up!!!
        if type_ == "input":
            raise Exception("Cannot create input files")

        if key == "file":
            path = self.get(type_=type_,
                            key="file",
                            ref_level_name=ref_level_name,
                            gt_fuzziness_name=gt_fuzziness_name)
            if os.path.exists(os.path.dirname(path)):
                return path
            else:
                path = os.path.dirname(path)
        else:
            path = self.get(type_=type_,
                            key=key,
                            ref_level_name=ref_level_name,
                            gt_fuzziness_name=gt_fuzziness_name)
            if os.path.exists(path):
                return path
        split = path.split("/")
        curr_path = ""
        for i in range(len(split)):
            curr_path = os.path.join(curr_path, split[i])
            if os.path.isdir(curr_path):
                pass
            else:
                os.mkdir(curr_path)  # this creates the magazine directories

        if key == "file":  # we created the dict before, now we add the file to the path
            path = self.get(type_=type_,
                            key="file",
                            ref_level_name=ref_level_name,
                            gt_fuzziness_name=gt_fuzziness_name)
        return path

    def save_json(self, type_, key, doc, ref_level_name, fuzziness_name):
        if key == "file":
            with open(
                self.check_and_create(
                    type_=type_,
                    key=key,
                    ref_level_name=ref_level_name,
                    gt_fuzziness_name=fuzziness_name), "w") as f:
                json.dump(doc, f)
        else:
            with open(
                self.check_and_create(
                    type_=type_,
                    key=key,
                    ref_level_name=ref_level_name,
                    gt_fuzziness_name=fuzziness_name) + ".json", "w") as f:
                json.dump(doc, f)


class Scores:
    def __init__(self, counts_dict={"tp": 0, "fp": 0, "fn": 0, "tn": 0}):
        self.counter = Counter(counts_dict)
        self.precision = 0
        self.recall = 0
        self.f1 = 0

    def compute_scores(self):
        self.precision = self.counter["tp"]/(
            self.counter["tp"] + self.counter["fp"]
        ) if self.counter["tp"] + self.counter["fp"] != 0 else 0
        self.recall = self.counter["tp"]/(
            self.counter["tp"] + self.counter["fn"]
        ) if self.counter["tp"] + self.counter["fn"] != 0 else 0
        self.f1 = 2 * self.counter["tp"]/(
            2*self.counter["tp"] + self.counter["fp"] + self.counter["fn"]
        ) if self.counter["tp"] + self.counter["fp"] + self.counter["fn"] != 0 else 0
        self.accuracy = ((self.counter["tp"]+self.counter["tn"]) / (
            self.counter["tp"]+self.counter["tn"] + self.counter["fp"]+self.counter["fn"]
        ) if (self.counter["tp"]+self.counter["tn"] + self.counter["fp"]+self.counter["fn"]) != 0 else 0)

    def update_counter(self, counts_dict):
        self.counter.update(counts_dict)

    def get_score(self, round_to=3):
        self.compute_scores()
        result = {
            "tp": self.counter["tp"],
            "fp": self.counter["fp"],
            "fn": self.counter["fn"],
            "tn": self.counter["tn"],
            "Precision": round(self.precision, round_to),
            "Recall": round(self.recall, round_to),
            "F1": round(self.f1, round_to),
            "Accuracy": round(self.accuracy, round_to)
        }
        return result


def clean_raw(raw: list, is_gt=False) -> list:
    """Given a list of entity dictionaries cleans up said dictionaries
    by unifying the references to make comparisons easier.

    Args:
        raw (list): List of entity dictionaries.
        is_gt (bool, optional): Whether the entity dictionaries are from a
         GT file. Defaults to False.

    Returns:
        list: List of entity dictionaries, cleaned up to make comparisons
        easier, especially between the coordinates.
    """
    result = []
    for ent in raw:
        if "type" in ent and ent["type"] == "PER":
            ent_mentions = []
            dictionary = {}
            if "lastname" in ent:
                dictionary["lastname"] = ent["lastname"]
            else:
                dictionary["lastname"] = ""
            if "firstname" in ent and ent["firstname"]:
                dictionary["firstname"] = " ".join(ent["firstname"])
            else:
                dictionary["firstname"] = ""
            if "abbr_firstname" in ent:
                dictionary["abbr_firstname"] = ent["abbr_firstname"]
            else:
                dictionary["abbr_firstname"] = []
            if "other" in ent:
                dictionary["other"] = ent["other"]
            else:
                dictionary["other"] = []
            dictionary["name"] = get_main_name(dictionary=dictionary)
            if "profession" in ent:
                dictionary["profession"] = ent["profession"]
            else:
                dictionary["profession"] = []
            places = []
            if "places" in ent:
                for place in ent["places"]:
                    if "name" in place:
                        places.append(place["name"])
            else:
                dictionary["places"] = []
            dictionary["places"] = places

            if is_gt:
                dictionary["gt_gnd_id"] = []
                if "gt_gnd_id" in ent:
                    dictionary["gt_gnd_id"] = ent["gt_gnd_id"]
            else:
                dictionary["gnd_candidates"] = []
                if "gnd_ids" in ent:
                    dictionary["gnd_candidates"] = ent["gnd_ids"]

            if "references" in ent:
                for page, refs in ent["references"].items():
                    dictionary.update({
                        "page": page,
                        "year": page.split("_")[1]
                    })
                    if "refs" in refs:
                        # old linking files are set up slightly differently.
                        curr_list = refs["refs"]
                    else:
                        curr_list = refs
                    for ref in curr_list:
                        if "coords" in ref:
                            normalized_coords = set()
                            for coord in ref["coords"]:

                                coord_clean = str(coord).split(":")[0]
                                coord_clean = str(coord_clean).split(";")
                                for i in coord_clean:
                                    normalized_coords.add(i)

                            for coord in normalized_coords:
                                aux = dictionary.copy()
                                aux.update({"coord": coord})
                                ent_mentions.append(aux)

            result.append(ent_mentions)
    return result


def get_main_name(dictionary: dict) -> str:
    """Given a person dictionary returns the persons name as a string.

    Args:
        dictionary (dict): Person entity dictionary.

    Returns:
        str: Name of the person.

    Example:
        {"lastname":"Müller", "firstname": "Otto"} => "Otto Müller"\n
        {"lastname":"Müller", "abbr_firstname": "O."} => "O. Müller"
    """
    if "lastname" in dictionary and dictionary["lastname"]:
        if "firstname" in dictionary and dictionary["firstname"]:
            return dictionary["firstname"] + " " + dictionary["lastname"]
        elif "abbr_firstname" in dictionary and dictionary["abbr_firstname"]:
            return " ".join(
                dictionary["abbr_firstname"]
            ) + " " + dictionary["lastname"]
    elif "firstname" in dictionary and dictionary["firstname"]:
        if "abbr_firstname" in dictionary and dictionary["abbr_firstname"]:
            return dictionary["firstname"] + " " + " ".join(
                dictionary["abbr_firstname"]
            )
    elif "abbr_firstname" in dictionary and dictionary["abbr_firstname"]:
        return " ".join(dictionary["abbr_firstname"])
    elif "other" in dictionary:
        for other_elem in dictionary["other"]:
            return " ".join(other_elem)
    else:
        return "--"


def label_entity(ent: dict, gt: list) -> str:
    """Given an entity and a list of ground-truth entities,
    checks if they refer to the same person and returns what
    the ground truth gndid would be.

    Args:
        ent (dict): Person dictionary.
        gt (list): List of person dictionaries in the ground-truth files.

    Returns:
        str: Ground-truth gnd_id, or "" if none exists.
    """
    for g in gt:
        for f in g:
            if ent["page"] == f["page"] and ent["coord"] == f["coord"]:
                return f["gt_gnd_id"]
    return ""


def label_and_match_to_key(gt_label: str, match: bool) -> str:
    """Return the fitting case ("tp", "tn", "fp", "fn") given the ground truth
    label and whether the entities matched or not."""
    if match:
        if gt_label == "":
            return "tn"
        else:
            return "tp"
    else:
        if gt_label == "":
            return "fp"
        else:
            return "fn"


def eval_entity(entity: dict) -> dict:
    """Get evaluation dictionary for given entity and its candidates.

    Args:
        entity (dict): Person entity dictionary.

    Returns:
        dict: Dictionary of "tp", "fp", "tn", "fn" counts.
    """
    counts = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}

    gnd_candidates = []
    for x in entity["candidates"]:
        if x == []:
            gnd_candidates.append("")
        else:
            gnd_candidates += x
    if entity["label"] in gnd_candidates:
        key = label_and_match_to_key(gt_label=entity["label"], match=True)
    else:
        key = label_and_match_to_key(gt_label=entity["label"], match=False)
    counts[key] += 1

    return counts


def eval_references(entity: dict) -> dict:
    """Get evaluation dictionary for given entity and its candidates.
    Count not just the entities but the references, in order to give more
    weight to entities which occur often.

    Args:
        entity (dict): Person entity dictionary.

    Returns:
        dict: Dictionary of "tp", "fp", "tn", "fn" counts.
    """
    counts = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}

    gnd_candidates = []
    for x in entity["candidates"]:
        if x == []:
            gnd_candidates.append([""])
        else:
            gnd_candidates.append(x)
    for i, label in enumerate(entity["labels"]):
        if label in gnd_candidates[i]:
            key = label_and_match_to_key(gt_label=label, match=True)
        else:
            key = label_and_match_to_key(gt_label=label, match=False)
        counts[key] += 1

    return counts


def evaluate_person(gt: list, linked: list, ref_level=True) -> dict:
    """This function returns the true and false positives, as well as the true
    and false negatives of the linked file based on the ground-truth file.

    The evaluation can be done on reference level (every time a person
    is mentioned) and on entity level (every person counts only once).

    Special care has to be taken for entities with several ground-truth ids,
    which can happen when aggregation changed and now what used to be two
    person entities became one.

    Args:
        gt (list): List of ground-truth entities.
        linked (list): List of linked entities.
        ref_level (bool, optional): If the evaluation should be done on
         reference-level. If False, it is done on entity level.
         Defaults to True.

    Returns:
        dict: Dictionary describing the true and false positives, and true
        and false negatives of this particular magazine-year.
    """
    references_counter = Counter({"tp": 0, "fp": 0, "fn": 0, "tn": 0})
    entities_counter = Counter({"tp": 0, "fp": 0, "fn": 0, "tn": 0})

    # clean up data
    gt_data = []
    linked_data = []

    input_linked = linked
    gt = clean_raw(gt, is_gt=True)
    gt_data += gt
    input_linked = clean_raw(input_linked)

    # due to non-determinism in the flair NER:
    all_refs_gt = [
        ent["page"]+ent["coord"] for gt_elems in gt for ent in gt_elems
    ]
    all_refs_linked = [
        ent["page"]+ent["coord"] for li_el in input_linked for ent in li_el
    ]
    all_valid_refs = set(all_refs_gt).intersection(set(all_refs_linked))

    for ent_variations in input_linked:
        ent_instances = []
        for ent in ent_variations:
            if (ent["page"]+ent["coord"]) in all_valid_refs:
                ent_instances.append({
                    "ent": ent, "label": label_entity(ent, gt)
                })
        if ent_instances:
            linked_data.append(ent_instances)

    # but now linked_data is on reference level, we want to aggregate them:
    ent_cand_label = []
    for entity_list in linked_data:
        coord_list = []
        label_list = []
        candidates_list = []
        # now i need the candidates, in the rulebased case we only have access
        # to the gnd_ids
        for ent_dict in entity_list:
            ent = ent_dict["ent"]
            coord_list.append({
                "page": ent.pop("page", ""),
                "coords": ent.pop("coord", "")
            })
            label_list.append(ent_dict["label"])
            candidates_list.append(ent["gnd_candidates"])
        ent_cand_label.append({
            "entity": ent,
            "candidates": candidates_list,
            "occurences": coord_list,
            "labels": label_list
        })

    list_of_good_entities = []
    list_of_problematic_entities = []
    for ent_dict in ent_cand_label:
        if len(set(ent_dict["labels"])) > 1:
            for label in set(ent_dict["labels"]):
                ent_dict["label"] = label
                list_of_problematic_entities.append(ent_dict.copy())
        else:
            ent_dict["label"] = set(ent_dict["labels"]).pop()
            list_of_good_entities.append(ent_dict)

    list_of_all_entities = (list_of_good_entities+list_of_problematic_entities)

    if ref_level:
        scores_mention = Scores()

        for entity in list_of_all_entities:
            scores_mention.update_counter(counts_dict=eval_references(entity))

        references_counter["tp"] = scores_mention.get_score()["tp"]
        references_counter["fp"] = scores_mention.get_score()["fp"]
        references_counter["tn"] = scores_mention.get_score()["tn"]
        references_counter["fn"] = scores_mention.get_score()["fn"]

        return references_counter
    else:
        scores_entity = Scores()
        for entity in list_of_all_entities:
            scores_entity.update_counter(counts_dict=eval_entity(entity))

        entities_counter["tp"] = scores_entity.get_score()["tp"]
        entities_counter["fp"] = scores_entity.get_score()["fp"]
        entities_counter["tn"] = scores_entity.get_score()["tn"]
        entities_counter["fn"] = scores_entity.get_score()["fn"]

        return entities_counter
