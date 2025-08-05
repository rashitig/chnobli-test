import json
import requests

import unicodedata
import time
# from src import secrets  # for testing pipeline


with open("select_wikidata_value_dict.json", "r") as f:
    selected_wikidata_values_dict = json.load(f)


def prep_name_for_elasticsearch_query(name: str) -> str:
    """Specify allowed edit distance for each word of a name
    for the elasticsearch fuzzy search functionality.

    This is based on their fuzziness:auto implementation, and depends
    on the length of the word. We do not allow more than 2 edits per word.

    Args:
        name (str): Name to be searched.

    Returns:
        str: Name to be searched including allowed edit distances.
    """
    name = unicodedata.normalize("NFC", name)
    name = name.replace(".", "*")
    name_list = name.split(" ")
    name_list = [x for x in name_list if x != ""]
    # our own fuzziness:auto implementation
    for it, st in enumerate(name_list):
        if st[-1] == "*":
            continue
        else:
            if len(st) < 3:
                name_list[it] = name_list[it] + "~0"
            elif len(st) < 6:
                name_list[it] = name_list[it] + "~1"
            else:
                name_list[it] = name_list[it] + "~2"
    name = " ".join(name_list)
    return name


def convert_dates(wikidata_date_format: str) -> str:
    """Throws away time part of wikidata date format.

    Args:
        wikidata_date_format (str): Date in wikidata format.

    Returns:
        str: Date in YYYY-MM-DD format.

    Example:
        "+1796-10-16T00:00:00Z" => "1796-10-16"
    """
    date = wikidata_date_format.strip("+").split("T")[0]
    return date


def get_wikidata_value(wikidata_id: str) -> str:
    """Given a wikidata_id, returns the string associated with said id.
    The string is German, unless they don't have that language, then it's
    English, French, Italian, or "multiple languages", in that order.

    At the moment, it also reads in a dictionary containing mappings of
    select wikidata values for speed. If the wikidata_id this function
    is called with is not in that dictionary, it is added.

    Args:
        wikidata_id (str): String of a wikidata id.

    Returns:
        str: String of value associated with said wikidata id.

    TODO this is a huge bottleneck, we really need to add these strings
    to our database.
    """
    if wikidata_id in selected_wikidata_values_dict:
        return selected_wikidata_values_dict[wikidata_id]

    params = {
        "action": "wbgetentities",
        "ids": wikidata_id,
        "language": "de",
        "format": "json"
    }
    data = requests.get("https://www.wikidata.org/w/api.php", params=params)
    try:
        res = data.json()
    except ValueError:
        time.sleep(5)
        data = requests.get(
            "https://www.wikidata.org/w/api.php", params=params
        )
        try:
            res = data.json()
        except ValueError:
            with open("/home/adl/rashitig/nla/wiki_ids.txt", "a+") as f:
                print(wikidata_id, file=f)
            return None

    if "error" in res:
        return None

    if "labels" in res["entities"][wikidata_id]:
        labels_wikidata_id = res["entities"][wikidata_id]["labels"]
        value_as_str = ""
        if "de" in labels_wikidata_id:
            value_as_str = labels_wikidata_id["de"]["value"]
        elif "en" in labels_wikidata_id:
            value_as_str = labels_wikidata_id["en"]["value"]
        elif "fr" in labels_wikidata_id:
            value_as_str = labels_wikidata_id["fr"]["value"]
        elif "it" in labels_wikidata_id:
            value_as_str = labels_wikidata_id["it"]["value"]
        elif "mul" in labels_wikidata_id:
            value_as_str = labels_wikidata_id["mul"]["value"]
        else:
            return None

        #selected_wikidata_values_dict[wikidata_id] = value_as_str
        #with open("select_wikidata_value_dict.json", "w") as f:
        #    json.dump(selected_wikidata_values_dict, f)
        return value_as_str
    else:
        #selected_wikidata_values_dict[wikidata_id] = None
        #with open("select_wikidata_value_dict.json", "w") as f:
        #    json.dump(selected_wikidata_values_dict, f)
        return None


def convert_wikidata_format_kibana(person_dict: dict) -> dict:
    """Convert the output dictionary we get from wikidata into
    the dictionary we use for the rest of the pipeline.

    Args:
        person_dict (dict): Dictionary containing various information
         on a person entity.

    Returns:
        dict: Dictionary containing various information on a person
         entity in our own format.
    """
    res_dict = {}

    if "description" in person_dict:
        res_dict["desc"] = set([person_dict["description"]])
        res_dict["desc"].discard(None)
    if "claims" in person_dict:
        if "P19" in person_dict["claims"].keys():  # "place_of_birth"
            res_dict["birthplaceLiteral"] = set(
                [get_wikidata_value(x) for x in person_dict["claims"]["P19"]]
            )
            res_dict["birthplaceLiteral"].discard(None)
        if "P1477" in person_dict["claims"].keys():  # "full_birthname":
            res_dict.setdefault("prefVarName", set()).update(
                person_dict["claims"]["P1477"]
            )
            # i have no idea why this one is already the actual name and
            # not just the wikipedia code
            res_dict["prefVarName"].discard(None)
        if "P735" in person_dict["claims"].keys():  # "firstname":
            res_dict.setdefault("prefForename", set()).update(
                [get_wikidata_value(x) for x in person_dict["claims"]["P735"]]
            )
            res_dict["prefForename"].discard(None)
        if "P734" in person_dict["claims"].keys():  # "lastname"
            res_dict.setdefault("prefSurname", set()).update(
                [get_wikidata_value(x) for x in person_dict["claims"]["P734"]]
            )
            res_dict["prefSurname"].discard(None)
        if "P1449" in person_dict["claims"].keys():  # "nicknames"
            res_dict["varForename"] = set(person_dict["claims"]["P1449"])
            res_dict["varForename"].discard(None)
        if "P106" in person_dict["claims"].keys():  # "occupation"
            res_dict["jobliteral"] = set(
                [get_wikidata_value(x) for x in person_dict["claims"]["P106"]]
            )
            res_dict["jobliteral"].discard(None)
        if "P569" in person_dict["claims"].keys():  # "date_of_birth"
            if len(person_dict["claims"]["P569"]) != 0:
                # TODO what if we get multiple birthdates?
                res_dict["birthdate"] = set(
                    [convert_dates(person_dict["claims"]["P569"][0])]
                )
                res_dict["birthdate"].discard(None)
        if "P570" in person_dict["claims"].keys():  # "date_of_death"
            if len(person_dict["claims"]["P570"]) != 0:
                res_dict["deathdate"] = set(
                    [convert_dates(person_dict["claims"]["P570"][0])]
                )
                res_dict["deathdate"].discard(None)
        if "P20" in person_dict["claims"].keys():  # "place_of_death"
            res_dict["deathplaceLiteral"] = set(
                [get_wikidata_value(x) for x in person_dict["claims"]["P20"]]
            )
            res_dict["deathplaceLiteral"].discard(None)
        if "P227" in person_dict["claims"].keys():  # gid
            res_dict.setdefault("gid", set())
            res_dict["gid"] = res_dict["gid"].union(
                set(person_dict["claims"]["P227"])
            )
            res_dict["gid"].discard(None)
        if "P7902" in person_dict["claims"].keys():  # gid
            res_dict.setdefault("gid", set())
            res_dict["gid"] = res_dict["gid"].union(
                set(person_dict["claims"]["P7902"])
            )
            res_dict["gid"].discard(None)

    if "label" in person_dict:
        res_dict["name"] = set([person_dict["label"]])
        res_dict["name"].discard(None)
        for fullname in res_dict["name"]:
            if "prefSurname" not in res_dict:
                res_dict["prefSurname"] = set([fullname.split(" ")[-1]])
            if "prefForename" not in res_dict:
                res_dict["prefForename"] = set(
                    [" ".join(fullname.split(" ")[:-1])]
                )

    return res_dict


def convert_gnd_format_kibana(person_dict: dict) -> dict:
    """Convert the output dictionary we get from gnd into
    the dictionary we use for the rest of the pipeline.

    Args:
        person_dict (dict): Dictionary containing various information
         on a person entity.

    Returns:
        dict: Dictionary containing various information on a person
         entity in our own format.
    """
    res_dict = {}
    for attri in person_dict.keys():
        fullname = ""
        if attri == "Forenames":
            res_dict.setdefault("prefForename", set()).update(
                person_dict[attri]
            )
            fullname = fullname + person_dict[attri][0]
        elif attri == "Surnames":
            res_dict.setdefault("prefSurname", set()).update(
                person_dict[attri]
            )
            fullname = fullname + person_dict[attri][0]
            # i combine the first two, if there are more firstnames /
            # lastnames (there shouldn't be because of the definition of
            # preferred fname/lname) then only the first is considered
        elif attri == "Descriptions":
            res_dict["desc"] = set(person_dict[attri])
            res_dict["desc"].discard(None)
        elif attri == "Birthplaces":
            res_dict["birthplaceLiteral"] = set(person_dict[attri])
            res_dict["birthplaceLiteral"].discard(None)
        elif attri == "VariantForenames":
            res_dict["varForename"] = set(person_dict[attri])
            res_dict["varForename"].discard(None)
        elif attri == "VariantSurnames":
            res_dict["varSurname"] = set(person_dict[attri])
            res_dict["varSurname"].discard(None)
        elif attri == "Jobs":
            res_dict["jobliteral"] = set(person_dict[attri])
            res_dict["jobliteral"].discard(None)
        elif attri == "Academics":
            res_dict["academic"] = set(person_dict[attri])
        elif attri == "Birthdate":
            res_dict["birthdate"] = set([person_dict[attri][0]])
            # NOTE if we have multiple birthdates, only the first is considered
            res_dict["birthdate"].discard(None)
        elif attri == "Deathdate":
            res_dict["deathdate"] = set([person_dict[attri][0]])
            res_dict["deathdate"].discard(None)
        elif attri == "Deathplaces":
            res_dict["deathplaceLiteral"] = set(person_dict[attri])
            res_dict["deathplaceLiteral"].discard(None)
        elif attri == "Activeperiods":
            res_dict["activeperiod"] = set(person_dict[attri])
        elif attri == "Affiliations":
            res_dict["affiliationLiteral"] = set(person_dict[attri])
        elif attri == "GND_ID":
            res_dict["gid"] = set(person_dict[attri])
            res_dict["gid"].discard(None)
    return res_dict


def search_person_gnd(fnames: list, lastname: str, gnd_limit=15) -> dict:
    """We search for this firstnames lastname in our elasticsearch GND index.
    We return at most `gnd_limit` results.

    Args:
        fnames (list): List of firstnames of the person to search
        lastname (str): Lastname of the person to search
        gnd_limit (int, optional): Number of results. Defaults to 15.

    Returns:
        dict: Dictionary of each viable candidate where the keys are the
         gnd ids.
    """
    if gnd_limit == 0:
        return {}

    if isinstance(fnames, list):
        # should even throw an exception, but I'll be nice
        fnames = " ".join(fnames)

    fnames = prep_name_for_elasticsearch_query(fnames)
    if fnames == "":
        fnames = "*"
    lastname = prep_name_for_elasticsearch_query(lastname)

    headers = {"Content-Type": "application/json"}

    json_data = {
        "from": 0,
        "size": gnd_limit,
        "query": {
            "bool": {
                "must": [
                    {"query_string": {
                        "default_field": "Forenames",
                        "query": fnames,
                        "default_operator": "and",
                        "analyze_wildcard": "true"
                        }},
                    {"query_string": {
                        "default_field": "Surnames",
                        "query": lastname,
                        "default_operator": "and",
                        "analyze_wildcard": "true"
                    }}
                ]
            }
        }
    }

    try:
        data = requests.get(
            "https://plessur.ethz.ch:9200/gnd/_search?pretty",
            headers=headers,
            json=json_data,
            # verify=secrets.filepath_certificate,  # for the testing pipeline
            # auth=(secrets.username, secrets.password),  # for the testing pipeline
            timeout=0.5)
    except requests.exceptions.Timeout:
        try:
            data = requests.get(
                "https://plessur.ethz.ch:9200/gnd/_search?pretty",
                headers=headers,
                json=json_data,
                # verify=secrets.filepath_certificate,  # for the testing pipeline
                # auth=(secrets.username, secrets.password),  # for the testing pipeline
                timeout=5)
        except requests.exceptions.Timeout:
            pass

    result_json = data.json()
    res_candidates = {}
    # max score would be at result_json["hits"]["max_score"]
    if "error" in result_json:
        return []

    for hit in result_json["hits"]["hits"]:
        # score is at hit["_score"]
        person_info = convert_gnd_format_kibana(hit["_source"])
        if "gid" in person_info and len(person_info["gid"]) != 0:
            gid = person_info["gid"].pop()
            person_info["gid"] = {gid}
            person_info["score"] = hit["_score"]
            res_candidates[gid] = person_info
    return res_candidates


def search_person_wikidata(search_term: str, wikidata_limit=5) -> dict:
    """We search for this firstnames lastname in our elasticsearch
    Wikidata index. We return at most `gnd_limit` results.

    Args:
        search_term (str): first- and lastname of the person to search.
        wikidata_limit (int, optional): Number of results. Defaults to 5.

    Returns:
        dict: Dictionary of each viable candidate where the keys are the
         gnd ids.
    """
    if wikidata_limit == 0:
        return {}

    search_term = prep_name_for_elasticsearch_query(search_term)

    headers = {"Content-Type": "application/json"}

    json_data = {
        "from": 0,
        "size": wikidata_limit,
        "query": {
            "bool": {
                "must": {
                    "query_string": {
                        "default_field": "labels",
                        "query": search_term,
                        "default_operator": "and",
                        "analyze_wildcard": "true"
                    },
                },
                "filter": [{
                    "bool": {
                        "should": [
                            {"exists": {"field": "claims.P227"}},
                            {"exists": {"field": "claims.P7902"}}
                        ]
                    }
                }],
            }
        }
    }

    try:
        data = requests.get(
            "https://plessur.ethz.ch:9200/wikidata/_search?pretty",
            headers=headers,
            json=json_data,
            # verify=secrets.filepath_certificate,  # for the testing pipeline
            # auth=(secrets.username, secrets.password),  # for the testing pipeline
            timeout=0.5)
    except requests.exceptions.Timeout:
        try:
            data = requests.get(
                "https://plessur.ethz.ch:9200/wikidata/_search?pretty",
                headers=headers,
                json=json_data,
                # verify=secrets.filepath_certificate,  # for the testing pipeline
                # auth=(secrets.username, secrets.password),  # for the testing pipeline
                timeout=5)
        except requests.exceptions.Timeout:
            pass

    result_json = data.json()

    res_candidates = {}
    # max score would be at result_json["hits"]["max_score"]
    if "error" in result_json:
        return []

    for hit in result_json["hits"]["hits"]:
        # score is at hit["_score"]
        info = {}
        info["label"] = hit["_source"]["labels"]
        if "descriptions" in hit["_source"]:
            info["description"] = hit["_source"]["descriptions"]
        info["claims"] = hit["_source"]["claims"]
        if "P227" in info["claims"] or "P7902" in info["claims"]:
            person_info = convert_wikidata_format_kibana(info)

            if "gid" in person_info and len(person_info["gid"]) != 0:
                person_info["score"] = hit["_score"]
                for gid in person_info["gid"]:
                    # sometimes one entity is assigned several gids.
                    # this unfortunately breaks a lot of what we did logically
                    # but this cannot be fixed on our end.
                    res_candidates[gid] = person_info

    return res_candidates
