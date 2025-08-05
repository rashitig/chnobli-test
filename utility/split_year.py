#!/usr/bin/env python3

"""
Splits a year folder in an intelligent way and names the parts after the
issues they're representing.

NOTE: At the moment, only issues are processed, this means that content
outside of issues, like table of contents or appendices,
are not processed. Discuss if this is wished for behavior.
"""

import glob
from lxml import etree
import os
import logging

DATA2_MNT = "/mnt/adl/"
LOG_PATH = "./data/logs/pipeline.log"
# LOG_PATH = "./test.log"
MISSING_PATH = "./data/logs/missing_content_list.txt"
# keep track of all years that had content ouside of issues,
# so we can process these later again if wanted.


def get_pagenumbers(xml):
    """Given an XML tree find all the issues in the journal and their pages.

    Args:
        xml (etree): XML-Tree with issue-information

    Returns:
        dict: Dictionary with information about all issues and the filenumbers
         that refer to the respective pagenumbers
    """
    returncode = 0

    issue_dict = {}  # Key: IssueNumber, Value: List of pagenumbers

    # 1. Get all issues with their ids
    issues = xml.findall(".//element[@type='Issue']")

    # Alternative plans if no issue informations are available
    if len(issues) == 0:
        print("WARNING: NO ISSUE INFORMATION WAS FOUND!")
        filenames = xml.findall(
            "./resource-list/resource/attr[@type='Agora:Path']"
            )
        issue_dict["1"] = []
        for filename in filenames:
            issue_dict["1"].append(os.path.basename(filename.text.lower())
                                   .replace(".gif", ".txt")
                                   .replace(".jpg", ".txt"))

    # 2. get info about first and last element of that issue
    for issue in issues:
        issue_number = issue.find("./attr[@type='IssueNumber']").text
        issue_dict[issue_number] = []

        additional_elements = issue.findall("./element")
        for elem in additional_elements + [issue]:
            idx = elem.get("ID")
            links = xml.findall(".//link[@from='{0}']".format(idx))

            # 3. get all those elements and only get pagenumbers
            for link in links:
                page_elem = xml.find(".//element[@ID='{0}']"
                                     .format(link.get("to")))

                # NOTE: Sometimes, the linked elements are regions. In the
                # cases I've checked, pages that the regions belong to are
                # also linked, so we could simply ignore regions but this
                # might lead to missing pages in cases I've not seen. Instead,
                # we append the page-resource-id and then we check for
                # duplicates before appending a filename

                if page_elem.get("type") == "Agora:Page":
                    resourceId = page_elem.find("./resource-id")
                else:
                    resourceId = page_elem.getparent().find("./resource-id")
                    # resourceId = None
                if resourceId is None:
                    # These print-Statements are used to debug
                    logging.warning(
                        "WARNING: No resource-id could be linked so a page might be missing later on.")
                    logging.warning(elem.get("ID"))
                    logging.warning(link.get("to"))
                    returncode = -1
                    continue
                else:
                    resourceId = resourceId.text
                # issue_dict[issue_number].append(physicalNo)
                filename = xml.find(
                    "./resource-list/resource[@ID='{0}']/attr[@type='Agora:Path']".format(resourceId)
                    ).text
                filename = os.path.basename(filename).replace(".jpg", ".txt")
                if filename not in issue_dict[issue_number]:
                    issue_dict[issue_number].append(filename)

    return returncode, issue_dict


def check_for_missing_pages(pagenos: dict):
    """Find duplicates in the pagenos dictionary.

    Args:
        pagenos (dict): Keys are issues, values are lists of pages.

    Returns:
        tuple (int, int): The first value is -1 if there were duplicates
         and 0 else. The second value is the number of pages in all the issues.
    """
    found_pages = [page for issue in pagenos.values() for page in issue]

    if len(found_pages) != len(set(found_pages)):
        logging.error("ERROR: DUPLICATES FOUND!")
        return -1, len(found_pages)

    return 0, len(found_pages)


def cut_pagenumbers(pagenos: dict,
                    max_len=500,
                    max_len_warning=1000):
    """Cut the issues into chunks small enough for the processing pipeline.
    Args:
        pagenos (dict): The keys are issues and the values are lists of pages.
        max_len (int, optional): Max number of pages in one chunk (regardless
         of whether it's from several issues or not). Defaults to 500.
        max_len_warning (int, optional): Max number of pages *per issue*.
         If it's more than that, we print a warning and split it within an
         issue. Defaults to 1000.
    Returns:
        list: List of Dictionaries of Lists of Pagenumbers
    """
    collected_issues = []

    current_chunk = {}
    collected_length = 0

    for issue, pagenumbers in pagenos.items():

        length = len(pagenumbers)
        if length > max_len_warning:
            # TODO: If a single issue is longer than the maximum length,
            # we need to split at article borders
            logging.warning(
                "WARNING: Issue is longer than set maximum length, will be split at set length interval."
            )
            if current_chunk:
                collected_issues.append(current_chunk)

            current_chunk = {}
            collected_length = 0
            chunks = [pagenumbers[i:i+max_len] for i in range(0,
                                                              len(pagenumbers),
                                                              max_len)]
            for i, chunk in enumerate(chunks):
                if len(chunk) < max_len:
                    current_chunk[issue + "-" + str(i)] = chunk
                    collected_length += len(chunk)
                else:
                    collected_issues.append({issue + "-" + str(i): chunk})

        elif length > max_len:
            logging.warning("WARNING: Single issue is larger than set length\
interval, but shorter than maximum length. Will be kept in one piece.")
            if current_chunk:
                collected_issues.append(current_chunk)
            collected_issues.append({issue: pagenumbers})
            current_chunk = {}
            collected_length = 0

        else:
            collected_length += length
            if collected_length > max_len:
                # this way we check first if with the new issue, it is higher
                # than max_len, so chunks always stay shorter than max_len
                collected_issues.append(current_chunk)
                current_chunk = {issue: pagenumbers}
                collected_length = length
            else:
                current_chunk[issue] = pagenumbers

    if current_chunk:
        collected_issues.append(current_chunk)

    return collected_issues


def compare_pagenames(pagenos: dict,
                      year_pages: list,
                      page_count: int,
                      directory: str):
    """Checks if files are missing and which are missing.

    Args:
        pagenos (dict): Keys are ssues, the values are lists of pages.
        year_pages (list): List of paths to pages.
        page_count (int): How many pages there should be.
        directory (str): Path to the directory where the pages should be.

    Returns:
        int: -1 if there were files missing, and we write the missing
         filepaths into a file, else 0.

    Note:
        Ismail: Common missing files are the ones at the end of a file that are not
        part of any issue. I've decided that these files don't provide any value,
        so it's fine to ignore them.
        check again if the split went correctly
    """
    if len(year_pages) != page_count:
        logging.warning(
            "WARNING: Page count in data directory doesnt equal page count calculated by year splitter!"
        )
        flattened_pages = sorted([page for issue in pagenos.values()
                                 for page in issue])
        sorted_pages = sorted([os.path.basename(x) for x in year_pages])
        longer_list = flattened_pages if (
            len(flattened_pages) >= len(sorted_pages)) else sorted_pages
        shorter_list = flattened_pages if (
            len(flattened_pages) < len(sorted_pages)) else sorted_pages
        parallelized_pages = []
        i = 0
        j = 0
        while i < len(longer_list):
            page_a = longer_list[i]
            if page_a in shorter_list[j:]:
                for k, p in enumerate(shorter_list[j:]):
                    if p != page_a:
                        parallelized_pages.append((None, p))
                    else:
                        parallelized_pages.append((page_a, p))
                        j = j + k + 1
                        break
                if j > len(shorter_list):
                    for p in longer_list[i+1:]:
                        parallelized_pages.append((p, None))
                    break
            else:
                parallelized_pages.append((page_a, None))
            i += 1
        logging.info(parallelized_pages)

        # get the indices of all elements that could not be parallelized
        # this helps for manual check if this is simply the index missing
        # (which would be fine)
        indices = ", ".join([str(i) for i, p in enumerate(parallelized_pages)
                            if None in p])
        with open(LOG_PATH, mode="a", encoding="utf8") as log:
            log.write("WARNING: Splitting {} pagecount is suspicious.\
                      Pages at positions {} are missing.\
                      Max index is {}.\n".format(directory,
                                                 indices,
                                                 str(len(longer_list))))
        with open(MISSING_PATH, mode="a", encoding="utf8") as mss:
            mss.write(directory + "\n")

        return -1

    return 0


def split_directory(directory: str, custom_xml_path=None):
    """Splits the given directory into chunks of pages.

    Args:
        directory (str): Path to the directory
        custom_xml_path (str, optional): _description_. Defaults to None.

    Yields:
        dict: Dictionary with chunknames as key and list of pages as pathfiles as values
    """

    if custom_xml_path is not None:
        xml = etree.parse(custom_xml_path).getroot()
    else:
        split_path = directory.split("/")
        short = split_path[-2]
        year = split_path[-1]
        if short.startswith("bse"):
            xml_storage = os.path.join(DATA2_MNT, "xml.cache.prod01", short,
                                       "{0}-{1}.xml".format(
                                        short.upper(), year))
        else:
            xml_storage = os.path.join(DATA2_MNT, "xml.cache.prod01", short,
                                       "{0}_{1}.xml".format(
                                        short, year))

        try:
            xml = etree.parse(xml_storage).getroot()
        except Exception:
            xml_storage = xml_storage.replace("prod01", "staging01")
            xml = etree.parse(xml_storage).getroot()

    returncode, pagenos = get_pagenumbers(xml)
    if returncode != 0:
        with open(LOG_PATH, mode="a", encoding="utf8") as log:
            log.write(
                "WARNING: Splitting {} some resource ids could not be linked.\n".format(directory)
            )
    returncode, page_count = check_for_missing_pages(pagenos)
    if returncode != 0:
        with open(LOG_PATH, mode="a", encoding="utf8") as log:
            log.write(
                "WARNING: Splitting {} duplicates were found.\n".format(directory)
            )
    # NOTE: Aborting in case of error is a possibility, but it would mean,
    # that when part of the pipeline, we always get stuck at this point.
    # NOTE: It's smarter to just let it pass with an error, but note the error
    # in the log, so it can be fixed and processed again at a later point.
    chunks = cut_pagenumbers(pagenos)

    year_pages = glob.glob(directory+"/*.txt")

    returncode = compare_pagenames(pagenos, year_pages, page_count, directory)

    for i, chunk in enumerate(chunks):
        chunk_pagepaths = []
        for issue, pages in chunk.items():
            for page in pages:
                found = False
                for path in year_pages:
                    if path.endswith(page):
                        chunk_pagepaths.append(path)
                        found = True
                        break
                if not found:
                    print("ERROR: No path found for page {0}!".format(page))

        yield i, chunk_pagepaths


if __name__ == "__main__":
    for chunk, pages in split_directory("smh/1979_059",
                                        "smh/smh_1979_059.xml"):
        pass
