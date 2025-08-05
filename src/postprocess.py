#! /usr/bin/python3

"""
Read entities, then aggregate them.

Update 09.03.:
We do not append full articles anymore, because we'd need to attach
too much information which bloats the file.
Instead, we only append the article-ID, so in the other steps like
aggregation, linking and prep_import we can simply use that id to get the
article information from the xml.
"""

import json
import glob
from multiprocessing import Pool
from lxml import etree
import os
from datetime import datetime
import logging
from utility.utils import save_data_intermediate

DATA2_MNT = "/mnt/data2/"


def initialize_found_entry() -> dict:
    """Returns an empty person entity dictionary."""
    entity = {
        "info": {
            "lastnames": [],
            "firstnames": [],
            "abbr_firstnames": [],
            "occupations": [],
            "titles": [],
            "address": [],
            "others": []
            },
        "pid": [],
        "pageNames": [],
        "pageNo": [],
        "sentenceNo": [],
        "positions": []
    }
    return entity


def initialize_found_place_entry() -> dict:
    """Returns an empty place entity dictionary."""
    entity = {
        "tokens": [],
        "type": "",
        "pid": [],
        "pageNames": [],
        "pageNo": [],
        "sentenceNo": [],
        "positions": []
    }
    return entity


def add_info_to_entity(entity: dict,
                       tag: str,
                       token: dict,
                       pageNo: str,
                       sentNo: str,
                       pageName: str,
                       articles: list,
                       pid: int) -> None:
    """
    Adds information to a person entity based on the provided token dictionary
    and metadata about the page.

    Args:
        entity (dict): The person entity dictionary to update.
        tag (str): The type of the entity information (e.g., "LN" for last
         name, "FN" for first name).
        token (dict): A dictionary containing token information, including
            - "token" (str): The token text.
            - "coord" (tuple): The coordinates of the token.
        pageNo (str): The page number where the entity is located.
        sentNo (str): The sentence number where the entity is located.
        pageName (str): The name of the page where the entity is located.
        articles (list): A list of articles associated with the page.
        pid (int): The physical ID of the page.

    Returns:
        None

    Notes:
        - Updates the `info` dictionary in the entity with the token text
        based on the tag.
        - Appends metadata such as `pid`, `pageNames`, `positions`, `pageNo`,
        and `sentenceNo` to the entity.
        - Sets the `type` of the entity to "PER" (person).
        - Processes and adds article information to the entity if not already
        present.
        - Logs a warning if an unknown tag is encountered.
    """
    if tag == "LN":
        entity["info"]["lastnames"].append(token["token"])
    elif tag == "FN" and token["token"][-1] != ".":
        entity["info"]["firstnames"].append(token["token"])
    elif tag == "FN":
        entity["info"]["abbr_firstnames"].append(token["token"])
    elif tag == "OC":
        entity["info"]["occupations"].append(token["token"])
    elif tag == "TL":
        entity["info"]["titles"].append(token["token"])
    elif tag == "AN":
        entity["info"]["address"].append(token["token"])
    elif tag == "OT":
        entity["info"]["others"].append(token["token"])
    elif tag == "COM":
        pass
    else:
        entity["info"]["others"].append(token["token"])
        logging.info("UNKNOWN TAG ENCOUNTERED: "+tag)
    entity["pageNames"].append(pageName)
    entity["pid"].append(pid)
    entity["positions"].append(token["coord"])
    entity["pageNo"].append(pageNo)
    entity["sentenceNo"].append(sentNo)
    entity["type"] = "PER"

    # Add information about structure, only needs to be done once
    if "articles" not in entity:
        articles = decide_articles(articles)
        entity["articles"] = articles


def add_info_to_place_entity(entity: dict,
                             tag: str,
                             token: dict,
                             pageNo: str,
                             sentNo: str,
                             pageName: str,
                             articles: list,
                             pid: int) -> None:
    """
    Adds information to a place entity based on the provided token dict and
    metadata about the page.

    Args:
        entity (dict): The place entity dictionary to update.
        tag (str): The type of the place entity (e.g., "LOC").
        token (dict): A dictionary containing token information, including
            - "token" (str): The token text.
            - "coord" (tuple): The coordinates of the token.
        pageNo (str): The page number where the entity is located.
        sentNo (str): The sentence number where the entity is located.
        pageName (str): The name of the page where the entity is located.
        articles (list): A list of articles associated with the page.
        pid (int): The physical ID of the page.

    Returns:
        None

    Notes:
        - Updates the `tokens` list in the entity with the token text.
        - Sets the `type` of the entity to the provided tag.
        - Appends metadata such as `pid`, `pageNames`, `positions`, `pageNo`,
        and `sentenceNo` to the entity.
        - Processes and adds article information to the entity if not already
        present.
    """

    entity["tokens"].append(token["token"])
    entity["type"] = tag
    entity["pid"].append(pid)
    entity["pageNames"].append(pageName)
    entity["positions"].append(token["coord"])
    entity["pageNo"].append(pageNo)
    entity["sentenceNo"].append(sentNo)
    # Add information about structure, only needs to be done once
    if "articles" not in entity:
        articles = decide_articles(articles)
        entity["articles"] = articles


def decide_articles(articles: list) -> list:
    """Given a list of lists, only keeps the entries that are exactly length 2.
    Or, if the input is only length one, keeps it unchanged.
    TODO why?

    Args:
        articles (list): List of articles

    Returns:
        list: Cleaned list of pages where we only keep the articles with
         exactly two pages.
    """
    if len(articles) == 1:
        return articles
    pages = [r for r in articles if len(r) == 2]

    return pages


def adjust_information(entitylist: list) -> None:
    """Adjusts page information in the given entity list.
    Only keeps first value in "pageNames", "pageNo", "sentenceNo", and "pid".
    Logs a warning if there are several values for these entries.
    If an entity has no "pid", this entry is removed.

    Args:
        entitylist (list): List of entity dictionaries, where each dict
         contains page information on where this entity appears.
    """
    for entity in entitylist:
        for key in ["pageNames", "pageNo", "sentenceNo", "pid"]:
            value = entity[key]
            set_value = set(value)
            if len(set_value) > 1:
                logging.info(
                 "WARNING: WHY DOES THIS REFERENCE CONTAIN MULTIPLE SENTENCES"
                )
            if len(set_value) > 0:
                entity[key] = list(set_value)[0]
            elif key == "pid":
                # if no pids were appended, we delete that entry as it's only
                # used for the frontend and Kai informed me not to write it if
                # not used
                logging.info("DELETE")
                del entity[key]


def get_structure_info(year: tuple, custom_path=None) -> dict:
    """
    Retrieves structural information for a given year from an XML file.

    Args:
        year (tuple): A tuple containing
            - short (str): The shortname of the journal (e.g., "bse").
            - year (str): The year of the journal (e.g., "2025").
        custom_path (str, optional): Path to a custom XML file for debugging.
         Defaults to None.

    Returns:
        dict: A dictionary where keys are page filenames (e.g., "page1.txt")
         and values are tuples
            - pid (str): The physical ID of the page (e.g., "doc123:page1").
            - articles (list): A list of article IDs associated with the page.
            - pagenum (str): The physical page number.

    Notes:
        - If `custom_path` is provided, it is used to parse the XML file.
        - If `custom_path` is not provided, the function constructs the path
        to the XML file based on the `year` tuple.
        - Handles cases where the XML file is missing or inaccessible by
        returning an empty dictionary.
        - Skips journal-level connections and focuses on article-level
        connections.
        - Extracts the filename for each page by replacing the `.jpg`
        extension with `.txt`.
    """
    short, year = year

    if custom_path is not None:
        # We can use this for local debugging
        root = etree.parse(custom_path).getroot()
    else:
        if short.startswith("bse"):
            xml_storage = os.path.join(
                DATA2_MNT,
                "xml.cache.prod01",
                short,
                "{0}-{1}.xml".format(short.upper(), year)
            )
        else:
            xml_storage = os.path.join(
                DATA2_MNT,
                "xml.cache.prod01",
                short,
                "{0}_{1}.xml".format(short, year)
            )

        try:
            root = etree.parse(xml_storage).getroot()
        except Exception:
            try:
                xml_storage = xml_storage.replace("prod01", "staging01")
                root = etree.parse(xml_storage).getroot()
            except Exception:
                return {}

    pages_to_articles = {}

    document_id = root.find("./element-list/element[@type='Agora:Document']/attr[@type='Agora:DocumentID']").text

    page_elems = root.findall("./element-list/element[@type='Agora:ImageSet']/element[@type='Agora:Page']")

    for page_elem in page_elems:
        articles = []
        idx = page_elem.get("ID")
        pagenum = page_elem.find("./attr[@type='Agora:PhysicalNo']").text
        links = root.findall("./link-list/link[@to='{0}']".format(idx))
        for link in links:
            article_idx = link.get("from")
            # NOTE: Journal-level connections should usually be uninteresting,
            # so we skip them specifically. For completeness sake, we might
            # take them in as well though.
            is_journal = root.find("./element-list/element[@type='Journal'][@ID='{0}']".format(article_idx))
            if is_journal is not None:
                continue
            article = root.find("./element-list/element[@type='Journal']//element[@ID='{0}']".format(article_idx))
            articles.append(article_idx)

            # if the first element found was not an article
            # we look for the first ancestor being one
            if article.get("type") == "Article":
                continue

            article_ancestor = article.xpath(
                "ancestor::element[@type='Article']"
            )
            if not article_ancestor:
                continue

            ancestor_idx = article_ancestor[0].get("ID")
            articles.append(ancestor_idx)

        resource_id = page_elem.find("./resource-id").text
        path = root.find("./resource-list/resource[@ID='{0}']/attr[@type='Agora:Path']".format(resource_id)).text
        filename = os.path.basename(path).replace(".jpg", ".txt").lower()
        pages_to_articles[filename] = (
            document_id + ":" + idx,
            articles,
            pagenum
        )

    return pages_to_articles


def process_page(page: str,
                 sentences: list,
                 entitylist: list,
                 placeEntitylist: list,
                 structure_info: dict,
                 i: int) -> None:
    """
    Processes a single page of tagged sentences to extract entity information.

    Args:
        page (str): The name of the page being processed.
        sentences (list): A list of sentences, where each sentence is a list
            of tokens. Each token is a dictionary containing information such
            as "tag", "token", and "coord".
        entitylist (list): A list to store extracted person entities.
        placeEntitylist (list): A list to store extracted place entities.
        structure_info (dict): A dictionary containing structural information
            for the page. Keys are page names, and values are tuples of
            (pid, articles, pagenum).
        i (int): A fallback page number to use if no structural information is
            available.

    Returns:
        None

    Notes:
        - Extracts person entities (tagged with "PER") and place entities
        (tagged with other tags).
        - Uses BIO tagging format to identify the beginning ("B-") and
        continuation ("I-") of entities.
        - Updates the `entitylist` and `placeEntitylist` with extracted
        entities.
        - Handles cases where structural information is missing by using the
        fallback page number.
        - Logs warnings for unknown tags encountered during processing.
    """
    # In this new format, enumeration will not suffice. Use PhysicalID from
    # the structural information!
    # The reason for this is that for efficiency reasons, a page might be
    # split into multiple lines in the jsonl.

    # look up structure information for this page in the dictionary
    if page in structure_info:
        # We use the PhysicalNo of the page if it's available
        pid, articles, pagenum = structure_info[page]
        i = int(pagenum)
    else:
        articles = []
        pid = None

    for j, sentence in enumerate(sentences):
        entity = None
        current_tag = None
        for token in sentence:
            tag = token["tag"]
            if tag[2:5] == "PER":
                tagstart = tag[:6]
                tagend = tag[6:]
                if tagstart.startswith("B-"):
                    if entity:
                        if current_tag == "PER":
                            entitylist.append(entity)
                        else:
                            placeEntitylist.append(entity)
                    entity = initialize_found_entry()
                    add_info_to_entity(
                        entity, tagend, token, i, j, page, articles, pid
                    )
                elif tagstart.startswith("I-"):
                    if not entity:
                        # TODO: Write into a protocol that there is an error
                        # here
                        entity = initialize_found_entry()
                    elif current_tag != "PER":
                        placeEntitylist.append(entity)
                        entity = initialize_found_entry()
                    add_info_to_entity(
                        entity, tagend, token, i, j, page, articles, pid
                    )
                else:
                    logging.info("UNKNOWN TAG ENCOUNTERED: "+tag)
                current_tag = "PER"
            elif tag == "O" or tag.endswith("adj"):
                # ADJ tags will be ignored for the moment
                # Consider resetting BIO reset here
                # current_tag = "O"
                continue
            else:  # all place tags
                tagstart = tag[:2]
                tagend = tag[2:]
                if tagstart.startswith("B-"):
                    if entity:
                        if current_tag == "PER":
                            entitylist.append(entity)
                        else:
                            placeEntitylist.append(entity)
                    entity = initialize_found_place_entry()
                    add_info_to_place_entity(
                        entity, tagend, token, i, j, page, articles, pid
                    )
                elif tagstart.startswith("I-"):
                    if not entity:
                        # TODO: Write into a protocol that there is an error
                        # here
                        entity = initialize_found_place_entry()
                    elif current_tag != tagend:
                        placeEntitylist.append(entity)
                        entity = initialize_found_place_entry()
                    elif current_tag == "PER":
                        entitylist.append(entity)
                        entity = initialize_found_place_entry()
                    add_info_to_place_entity(
                        entity, tagend, token, i, j, page, articles, pid
                    )
                else:
                    logging.info("UNKNOWN TAG ENCOUNTERED: "+tag)
                current_tag = tagend
        if entity:
            if current_tag == "PER":
                entitylist.append(entity)
            else:
                placeEntitylist.append(entity)


def get_found_names(items: tuple) -> list:
    """
    Extracts and processes entity information (person and place names) from
    tagged files.

    Args:
        items (tuple): A tuple containing
            - year (tuple): A tuple of journal shortname and year as strings
            (e.g., ("abc", "2025")).
            - pages (dict): OrderedDict where the keys are filenames and the
            values are lists of sentences.

    Returns:
        tuple (list, tuple): The first entry is a list of all found entities
         (person and place names) with their associated metadata. The second
         is the year information (journal shortname and year).

    Notes:
        - Person names and place names are written in the same file but are
        sorted before printing (person names first).
        - When looking up the structure information for the pages, we use the
        information given by the raw data folder structure at the moment.
        This means that in rare cases two actually different volumes might have
        the same short-year combination and thus there will be problems
        when trying to link pages to structure elements. This will only change
        when using the structure files as initial information for the
        pipeline, but that requires a rework of a lot of stuff.
        So we will just be missing some information for the start.
        - Handles cases where tagged files are split into multiple lines for
        efficiency.
        - Adjusts entity information to remove duplicates and ensure
        consistency.
        - Missing structure information may result in incomplete metadata for
        some entities.
    """

    # TODO: Implement finding names even if they cross sentence and page
    # boundaries. (The tagger is not made for this, but there might still be
    # some cases to find left.)

    # UPDATE NOTE 02.03.2022: Due to the .jsonl efficiency update, the pages
    # variable now simply holds a list of paths
    # to the tagged files that belong to this year. These files should be
    # subsequently read and processed like they were a single file.
    year, pages = items
    # get structure information per page in dictionary form (key: pagenumber,
    # value: (information about the structure, pagenumber))
    structure_info = get_structure_info(year)

    entitylist = []
    placeEntitylist = []

    # handle old files
    if isinstance(pages, str):
        with open(pages, encoding="utf8") as inf:
            p = json.load(inf)
            for i, (page, sentences) in enumerate(p.items()):
                process_page(
                    page,
                    sentences,
                    entitylist,
                    placeEntitylist,
                    structure_info,
                    i
                )
    else:
        for path in pages:
            with open(path, encoding="utf8") as inf:
                for line in inf:
                    line = json.loads(line)
                    for i, (page, sentences) in enumerate(line.items()):
                        process_page(
                            page,
                            sentences,
                            entitylist,
                            placeEntitylist,
                            structure_info,
                            i
                        )

    adjust_information(entitylist)
    adjust_information(placeEntitylist)

    entitylist = entitylist + placeEntitylist

    return entitylist, year


def populate_year_dict(year_dict: dict, file_list: list) -> None:
    """
    Populates a dictionary with year-wise data paths for processing.

    Args:
        year_dict (dict): A dictionary to be populated. Keys are tuples of
            (magazine shortname, year), and values are file paths or lists of
            file paths.
        file_list (list): A list of file paths to be processed. The files can
            be in `.json` or `.jsonl` format.

    Notes:
        - For `.json` files, the file path is directly added to the dictionary.
        - For `.jsonl` files, all matching files are globbed and added as a
        list.
        - Unsupported file types are ignored.
    """
    for filename in file_list:
        filetype = "." + filename.split(".")[-1]
        if filetype == ".json":
            value = filename
        elif filetype == ".jsonl":
            value = sorted(glob.glob(filename.replace(".jsonl", "*.jsonl")))
        else:
            continue
        year_dict[
            (
                os.path.normpath(filename).split(os.sep)[-2],
                os.path.basename(filename).replace(filetype, ""),
            )
        ] = value


def get_data_paths_iterative(conf: dict):
    """Generates year-wise data paths for processing based on the given
    configuration.

    Args:
        conf (dict): Configuration dictionary containing various paths and
         settings.


    Raises:
        Exception: If no valid data paths are found in the configuration.
        Exception: If an input path generated with the configuration is
         neither a valid directory nor a valid file. This means the data paths
         are valid, but nothing useful is in there.

    Yields:
        dict: A dictionary where keys are tuples of (magazine shortname, year)
         and values are file paths or lists of file paths.
    """
    if "CUSTOM_PATHS" in conf:
        inputs = conf["CUSTOM_PATHS"]
    else:
        # in this case instead of using custom paths we use paths to infile
        # and thus get magazine directories instead of magazine-year dirs

        LEN_MAGAZINE_SHORTNAME = 3
        inconsistent_magazine_names = [
            "bse-cr",
            "bse-me",
            "bse-pe",
            "bse-re",
            "aan-normal.zip",
            "aan-speichern.zip",
            "aan-ultra.zip",
            "grs.zip",
            'szg.zip"',
        ]
        inputs_magazine_year_level = []

        magazine_folder = sorted(glob.glob(conf["PATH_TO_INPUT_FOLDERS"]+"/*"))
        for magazine in magazine_folder:
            if (
                len(os.path.basename(magazine)) == LEN_MAGAZINE_SHORTNAME
                or os.path.basename(magazine) in inconsistent_magazine_names
            ):
                # it's a magazine directory.
                year_directories = sorted(glob.glob(magazine + "/*"))
                inputs_magazine_year_level += year_directories
        inputs = inputs_magazine_year_level

    year_dict = {}

    if (
        isinstance(inputs, str)
        and (
            inputs.split("/")[-1] == "tag"
            or (inputs.split("/")[-1] == ""
                and inputs.split("/")[-2] == "tag")
        )
    ):
        # process everything in the tag folder
        inputs = glob.glob(inputs + "/*")

    if inputs == []:
        raise Exception(f"No valid data paths found in {conf}")

    for mag_year_path in inputs:
        if os.path.isdir(mag_year_path):
            populate_year_dict(year_dict, glob.glob(mag_year_path + "/*"))
        elif os.path.isfile(mag_year_path):
            populate_year_dict(year_dict, [mag_year_path])
        else:
            raise Exception(f'The given input: {inputs} is neither a valid directory, nor a valid file.')
        if len(year_dict) >= conf["BATCH_SIZE"]:
            yield year_dict
            year_dict = {}
    yield year_dict


# TODO these shouldn't be two functions, that's silly
def postprocess_data(conf: dict, tasks: list) -> None:
    """
    Postprocesses data based on the given configuration and tasks.

    Args:
        conf (dict): Configuration dictionary containing various settings and
            paths.
        tasks (list): List of tasks to be performed during postprocessing.

    Returns:
        None

    Notes:
        - Logs the start and end time of the postprocessing.
        - If "CUSTOM_PATH" is not in the configuration, sets the input folder \
            path to the output folder path with "tag" appended.
        - Loads data iteratively based on the configuration.
        - Executes postprocessing on the loaded data.
        - Saves intermediate data if "agg" is not in the tasks list.
    """
    start_time = datetime.now()
    logging.info("Starting Postprocessing at", start_time, ":")
    if "CUSTOM_PATH" not in conf:
        conf["PATH_TO_INPUT_FOLDERS"] = conf["PATH_TO_OUTFILE_FOLDER"] + "tag"
    magazines = get_data_paths_iterative(conf)
    postprocessed_data = execute_postprocessing(magazines, conf["BATCH_SIZE"])
    if "agg" not in tasks:
        for year, data in postprocessed_data:
            save_data_intermediate(year, data, conf, "post")
    logging.info("Postprocessing took: ", datetime.now() - start_time)
    return postprocessed_data


def execute_postprocessing(magazines: dict, batch_size: int):
    """Postprocess the magazines given.

    Args:
        magazines (dict): Keys are years, values is the data after
         tagging / aggregation.
        batch_size (int): Batch size for years to process together.

    Yields:
        tuple ((year,magazine), dict): The first value of the tuple is another
         tuple, consisting of the year of the magazine and the shortname of
         the magazine. The second value of the tuple is a dictionary
         describing the data.
    """
    for data in magazines:
        with Pool(batch_size) as p:
            postprocessed_years = p.map(get_found_names, data.items())
        for data, year in postprocessed_years:
            logging.info("Postprocessed: %s", year)
            yield year, data
            # saveDataIntermediate(year, data, conf, "post")
