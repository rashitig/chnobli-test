import pytest
import os
from collections import Counter
from unittest.mock import patch, mock_open

from utility.evaluation_utils import (
   Paths,
   Scores,
   clean_raw,
   get_main_name,
   label_entity,
   label_and_match_to_key,
   eval_entity,
   eval_references,
   evaluate_person
)

gt_dict_with_gnd = {
    'lastname': 'z',
    'firstname': ['x y'],
    'abbr_firstname': [],
    'address': ["Frau"],
    'titles': [],
    'profession': [],
    'other': [],
    'references': {
        'aaa-001_2004_000_0012.txt': {
            'refs': [{'sent': 0, 'coords': ['a']}]}},
    'type': 'PER',
    'id': 0,
    'gt_gnd_id': 'a'}
gt_dict_without_gnd = {
    'lastname': 'z',
    'firstname': ['x y'],
    'abbr_firstname': [],
    'address': ["Frau"],
    'titles': [],
    'profession': [],
    'other': [],
    'references': {
        'aaa-001_2004_000_0012.txt': {
            'refs': [{'sent': 0, 'coords': ['a']}]}},
    'type': 'PER',
    'id': 0,
    'gt_gnd_id': ''}
entity_dict_without_gnd = {
    'lastname': 'z',
    'firstname': ['x y'],
    'abbr_firstname': [],
    'address': ["Frau"],
    'titles': [],
    'profession': [],
    'other': [],
    'references': {
        'aaa-001_2004_000_0012.txt': {
            'refs': [{'sent': 0, 'coords': ['a']}]}},
    'type': 'PER',
    'id': 0,
    'gnd_ids': []}
entity_dict_with_gnd = {
    'lastname': 'z',
    'firstname': ['x y'],
    'abbr_firstname': [],
    'address': ["Frau"],
    'titles': [],
    'profession': [],
    'other': [],
    'references': {
        'aaa-001_2004_000_0012.txt': {
            'refs': [{'sent': 0, 'coords': ['a']}]}},
    'type': 'PER',
    'id': 0,
    'gnd_ids': ["a", "b"]}
conf = {
    "PATH_TO_INPUT_FOLDERS": "./data/input/",
    "PATH_TO_NER_MODEL_1": "/home/adl/nla/models/ner-bio.pt",
    "PATH_TO_NER_MODEL_2": "/home/adl/nla/models/ner-det.pt",
    "PATH_TO_OUTFILE_FOLDER": "./data/output/",
    "PATH_TO_ABBREVIATION_FILE": "./src/preprocessing/abbrevs.txt",
    "BATCH_SIZE": 8,
    "PATH_TO_GROUND_TRUTH": "./data/ground_truth_linked/with_fuzzy_matching/"
    # which path to use as GT is set via command line option and based on the
    # config
    # "--fuzzy True" for instance sets
    # PATH_TO_GROUND_TRUTH = PATH_TO_GROUND_TRUTH_FUZZY
    # here i am skipping that part and simulating setting the GT path in main
}


# -------------------------------------------------
# 1. Test Paths Class functions
# -------------------------------------------------
def test_paths_init():
    paths = Paths(conf=conf)

    path_to_gt = conf.pop("PATH_TO_GROUND_TRUTH")
    paths = Paths(conf=conf)
    assert not paths.success

    conf["PATH_TO_GROUND_TRUTH"] = path_to_gt


def test_paths_update():
    paths = Paths(conf=conf)
    paths.update("magazine", "test_mag")
    paths.update("file", "test_file")

    # key can be gt, link, eval, input
    # state can be magazine, file or empty
    # ref level name can be ref, ent, or empty
    with pytest.raises(AssertionError) as excinfo:
        paths.get("input", "", "net", "")
        assert excinfo.value.args[0] == "'net' is not in ['ent', 'ref', '']"
    with pytest.raises(AssertionError) as excinfo:
        paths.get("input", "", "", "wirth_fuzzy")
    assert excinfo.value.args[0] == "'wirth_fuzzy' is not in ['with_fuzzy', 'without_fuzzy', '']"

    assert paths.get("input", "", "ent", "") == conf["PATH_TO_INPUT_FOLDERS"]
    assert paths.get(
        "input", "magazine", "", ""
    ) == conf["PATH_TO_INPUT_FOLDERS"] + "test_mag"
    assert paths.get(
        "input", "file", "", ""
    ) == conf["PATH_TO_INPUT_FOLDERS"] + "test_mag/test_file"
    assert paths.get(
        "input", "", "", "with_fuzzy"
    ) == conf["PATH_TO_INPUT_FOLDERS"]
    assert paths.get("input", "", "", "") == conf["PATH_TO_INPUT_FOLDERS"]

    for type_ in ["eval", "link"]:
        for ref_lvl in ["ent", "ref"]:
            for gt_fuzziness_name in ["with_fuzzy", "without_fuzzy"]:
                assert paths.get(
                    type_, "", ref_lvl, ""
                ) == conf["PATH_TO_OUTFILE_FOLDER"]+type_+"_"+ref_lvl
                assert paths.get(
                    type_, "magazine", "", ""
                ) == conf["PATH_TO_OUTFILE_FOLDER"]+type_+"/test_mag"
                assert paths.get(
                    type_, "file", "", ""
                ) == conf["PATH_TO_OUTFILE_FOLDER"]+type_+"/test_mag/test_file"
                assert paths.get(
                    type_, "", "", gt_fuzziness_name
                ) == conf["PATH_TO_OUTFILE_FOLDER"]+type_+"_"+gt_fuzziness_name
                assert paths.get(
                    type_, "", "", ""
                ) == conf["PATH_TO_OUTFILE_FOLDER"]+type_

    assert paths.get(
        "gt", "", "ent", ""
    ) == conf["PATH_TO_GROUND_TRUTH"]+"_ent"
    assert paths.get(
        "gt", "magazine", "", ""
    ) == conf["PATH_TO_GROUND_TRUTH"]+"test_mag"
    assert paths.get(
        "gt", "file", "", ""
    ) == conf["PATH_TO_GROUND_TRUTH"]+"test_mag/test_file"
    assert paths.get(
        "gt", "", "", "with_fuzzy"
    ) == conf["PATH_TO_GROUND_TRUTH"]
    assert paths.get("gt", "", "", "") == conf["PATH_TO_GROUND_TRUTH"]


@patch("builtins.open", new_callable=mock_open, read_data='{"key": "value"}')
@patch("utility.evaluation_utils.Paths.get")
def test_paths_get_json(mock_get, mock_open_file):
    conf = {
        "PATH_TO_INPUT_FOLDERS": "./data/input/",
        "PATH_TO_OUTFILE_FOLDER": "./data/output/",
        "PATH_TO_GROUND_TRUTH": "./data/ground_truth/"
    }
    paths = Paths(conf=conf)
    mock_get.return_value = "./data/input/test_file.json"

    result = paths.get_json("input")

    assert result == {"key": "value"}
    mock_get.assert_called_once_with(type_="input", key="file")
    mock_open_file.assert_called_once_with("./data/input/test_file.json", "r")


def test_paths_check_and_create():
    paths = Paths(conf=conf)
    paths.update("magazine", "test_mag")
    paths.update("file", "test_file")

    already_existed = os.path.isdir(conf["PATH_TO_OUTFILE_FOLDER"]+"link")
    path_linked = paths.check_and_create("link", "", "", "")
    assert path_linked == conf["PATH_TO_OUTFILE_FOLDER"]+"link"
    assert os.path.isdir(path_linked)
    if not already_existed:
        os.rmdir(path_linked)

    for type_ in ["eval", "link"]:
        path_with_type = conf["PATH_TO_OUTFILE_FOLDER"] + type_

        already_existed = os.path.isdir(path_with_type)
        path = paths.check_and_create(type_, "magazine", "", "")
        assert path == path_with_type+"/test_mag"
        assert os.path.isdir(path)
        os.rmdir(path)
        if not already_existed:
            os.rmdir(path_with_type)

        already_existed = os.path.isdir(path_with_type)
        path = paths.check_and_create(type_, "file", "", "")
        assert path == path_with_type+"/test_mag/test_file"
        assert os.path.exists("/".join(path.split("/")[:-1])), path
        os.rmdir(path_with_type+"/test_mag")
        if not already_existed:
            os.rmdir(path_with_type)

        for ref_lvl in ["ent", "ref"]:
            for gt_fuzziness_name in ["with_fuzzy", "without_fuzzy"]:
                if type_ == "eval":
                    path_gt = path_with_type+"_"+ref_lvl+"_"+gt_fuzziness_name
                    already_existed = os.path.isdir(path_gt)
                    path = paths.check_and_create(
                        type_,
                        "",
                        ref_lvl,
                        gt_fuzziness_name
                    )
                    assert path == path_gt
                    assert os.path.isdir(path)
                    if not already_existed:
                        os.rmdir(path)


def test_paths_save_json():
    paths = Paths(conf=conf)
    paths.update("magazine", "test_mag")
    paths.update("file", "test_file")

    for type_ in ["eval", "link"]:
        path_with_type = conf["PATH_TO_OUTFILE_FOLDER"]+type_
        for ref_lvl in ["ent", "ref"]:
            for gt_fuzziness_name in ["with_fuzzy", "without_fuzzy"]:
                path_gt = path_with_type+"_"+ref_lvl+"_"+gt_fuzziness_name

                already_existed = os.path.isdir(path_gt)
                paths.save_json(
                    type_,
                    "magazine",
                    {"test1": "test2"},
                    ref_lvl,
                    gt_fuzziness_name
                )
                path_1 = paths.get(
                    type_,
                    "magazine",
                    ref_lvl,
                    gt_fuzziness_name
                )
                assert os.path.exists(path_1)
                os.rmdir(path_1)
                os.remove(path_gt+"/"+"test_mag.json")
                if not already_existed:
                    os.rmdir(path_gt)

                already_existed = os.path.isdir(path_gt)
                paths.save_json(
                    type_,
                    "file",
                    {"test1": "test2"},
                    ref_lvl,
                    gt_fuzziness_name
                )
                path_1 = paths.get(
                    type_,
                    "file",
                    ref_lvl,
                    gt_fuzziness_name
                )
                assert os.path.exists(path_1)
                os.remove(path_1)
                os.rmdir(path_gt+"/"+"test_mag")
                if not already_existed:
                    os.rmdir(path_gt)


# -------------------------------------------------
# 2. Test Scores Class functions
# -------------------------------------------------
def test_scores_init():
    scores = Scores({"tp": 161, "fp": 199, "fn": 74, "tn": 327})
    assert scores.precision == 0
    assert scores.recall == 0
    assert scores.f1 == 0
    assert Counter(
        {"tp": 161, "fp": 199, "fn": 74, "tn": 327}
    ) == scores.counter


def test_scores_compute_scores():
    counters = [{"tp": 161, "fp": 199, "fn": 74, "tn": 327},
                {"tp": 0, "fp": 3, "fn": 0, "tn": 93}]
    for i in counters:
        scores = Scores(i)
        scores.compute_scores()
        if scores.counter["tp"] + scores.counter["fp"] != 0:
            assert scores.precision == scores.counter["tp"] / (
                scores.counter["tp"] + scores.counter["fp"])
        else:
            assert scores.precision == 0
        if scores.counter["tp"] + scores.counter["fn"] != 0:
            assert scores.recall == scores.counter["tp"] / (
                scores.counter["tp"] + scores.counter["fn"])
        else:
            assert scores.recall == 0
        if (scores.counter["tp"] +
                scores.counter["tn"] +
                scores.counter["fp"] +
                scores.counter["fn"]) != 0:
            assert scores.accuracy == ((
                scores.counter["tn"] + scores.counter["tp"]) / (
                    scores.counter["tn"] +
                    scores.counter["tp"] +
                    scores.counter["fn"] +
                    scores.counter["fp"]))
        else:
            assert scores.accuracy == 0

        if ((scores.counter["tp"] + scores.counter["fp"] != 0) and
                (scores.counter["tp"] + scores.counter["fn"] != 0)):
            assert round(scores.f1, 10) == (
                round(2 * (
                    scores.counter["tp"] / (
                        scores.counter["tp"] + scores.counter["fp"]) *
                    scores.counter["tp"] / (
                        scores.counter["tp"] + scores.counter["fn"])) / (
                            scores.counter["tp"] / (
                                scores.counter["tp"] + scores.counter["fp"]) +
                            scores.counter["tp"] / (
                                scores.counter["tp"] + scores.counter["fn"])),
                      10)
            )
        else:
            assert scores.f1 == 0


def test_scores_update_counter():
    """
    This is a bit absurd but let's do it
    """
    counters = [{"tp": 161, "fp": 199, "fn": 74, "tn": 327},
                {"tp": 0, "fp": 3, "fn": 0, "tn": 93}]
    init_counter = {"tp": 1, "fp": 1, "fn": 1, "tn": 1}
    for i in counters:
        scores = Scores(init_counter)
        scores.update_counter(i)
        assert scores.counter["tp"] == i["tp"] + init_counter["tp"]
        assert scores.counter["fp"] == i["fp"] + init_counter["fp"]
        assert scores.counter["fn"] == i["fn"] + init_counter["fn"]
        assert scores.counter["tn"] == i["tn"] + init_counter["tn"]


def test_scores_get_score():
    """
    This is a bit absurd but let's do it
    """
    counters = [{"tp": 161, "fp": 199, "fn": 74, "tn": 327},
                {"tp": 0, "fp": 3, "fn": 0, "tn": 93}]
    roundings = [2, 3, 5]

    for i in counters:
        for r in roundings:
            scores = Scores(i)
            res = scores.get_score(round_to=r)
            assert res["tp"] == i["tp"]
            assert res["fp"] == i["fp"]
            assert res["tn"] == i["tn"]
            assert res["fn"] == i["fn"]
            if i["tp"] + i["fp"] != 0:
                assert res["Precision"] == round(
                    i["tp"] / (i["tp"] + i["fp"]),
                    r)
            else:
                assert res["Precision"] == 0
            if i["tp"] + i["fn"] != 0:
                assert res["Recall"] == round(i["tp"] / (i["tp"] + i["fn"]), r)
            else:
                assert res["Recall"] == 0
            if (i["tp"] + i["tn"] + i["fp"] + i["fn"]) != 0:
                assert res["Accuracy"] == round(((
                    i["tn"] + i["tp"]) / (
                        i["tn"] + i["tp"] + i["fn"] + i["fp"])), r)
            else:
                assert res["Accuracy"] == 0
            if i["tp"] + i["fp"] != 0 and i["tp"] + i["fn"] != 0:
                assert round(res["F1"], r) == (
                    round(2 * (
                        i["tp"] / (i["tp"] + i["fp"]) *
                        i["tp"] / (i["tp"] + i["fn"])) / (
                            i["tp"] / (i["tp"] + i["fp"]) +
                            i["tp"] / (i["tp"] + i["fn"])), r)
                )
            else:
                assert res["F1"] == 0


# -------------------------------------------------
# 3. Test clean_raw
# -------------------------------------------------
@pytest.mark.parametrize(
    "raw, is_gt, expected",
    [
     ([entity_dict_with_gnd,
       {"firstname": ["a b"],
        "lastname": "c",
        "abbr_firstname": [],
        "address": ["Frau"],
        "titles": [],
        "profession": [],
        "other": [],
        "references": {
            # old ref style
            "aaa-001_2004_000_0013.txt": [{"sent": "a", "coords": ["b:main"]}]
        },
        "type": "PER",
        "id": 1,
        "gnd_ids": ["y", "x"]}],
      False,
      [[{'lastname': 'z',
         'firstname': 'x y',
         'abbr_firstname': [],
         'other': [],
         'name': 'x y z',
         'profession': [],
         'places': [],
         'gnd_candidates': ["a", "b"],
         'page': 'aaa-001_2004_000_0012.txt',
         'year': '2004',
         'coord': 'a'}],
      [{'lastname': 'c',
        'firstname': 'a b',
        'abbr_firstname': [],
        'other': [],
        'name': 'a b c',
        'profession': [],
        'places': [],
        'gnd_candidates': ["y", "x"],
        'page': 'aaa-001_2004_000_0013.txt',
        'year': '2004',
        'coord': 'b'}]]),
     ([gt_dict_without_gnd,
       {"firstname": ["a b"],
        "lastname": "c",
        "abbr_firstname": [],
        "address": ["Frau"],
        "titles": [], "profession": [],
        "other": [],
        "references": {
            "aaa-001_2004_000_0013.txt": {
                "refs": [{"sent": "a", "coords": "b"}]}},
        "type": "PER",
        "id": 1}],
        True,
      [[{'lastname': 'z',
         'firstname': 'x y',
         'abbr_firstname': [],
         'other': [],
         'name': 'x y z',
         'profession': [],
         'places': [],
         'gt_gnd_id': "",
         'page': 'aaa-001_2004_000_0012.txt',
         'year': '2004',
         'coord': 'a'}],
      [{'lastname': 'c',
        'firstname': 'a b',
        'abbr_firstname': [],
        'other': [],
        'name': 'a b c',
        'profession': [],
        'places': [],
        'gt_gnd_id': [],
        'page': 'aaa-001_2004_000_0013.txt',
        'year': '2004',
        'coord': 'b'}]])
     ],
)
def test_clean_raw(raw, is_gt, expected):
    assert clean_raw(raw, is_gt) == expected


# -------------------------------------------------
# 4. Test get_main_name
# -------------------------------------------------
@pytest.mark.parametrize(
    "dictionary, expected",
    [({"firstname": "x y",
       "lastname": "z",
       "abbr_firstname": [],
       "other": []},
      'x y z'),
     ({"firstname": "x y",
       "lastname": "z",
       "abbr_firstname": ["b"],
       "other": []},
      'x y z'),
     ({"firstname": "",
       "lastname": "z",
       "abbr_firstname": ["b"],
       "other": []},
      'b z'),
     ({"firstname": "x y",
       "lastname": "",
       "abbr_firstname": ["b"],
       "other": []},
      'x y b'),
     ({"firstname": "",
       "lastname": "",
       "abbr_firstname": ["b"],
       "other": []},
      'b'),
     ({"firstname": "",
       "lastname": "",
       "abbr_firstname": [],
       "other": ["d"]},
      'd'),
     ({"firstname": "",
       "lastname": "",
       "abbr_firstname": [],
       "other": []},
      None),
     ({}, "--"),
     ],
)
def test_get_main_name(dictionary, expected):
    assert get_main_name(dictionary) == expected


# -------------------------------------------------
# 5. Test label_entity
# -------------------------------------------------
@pytest.mark.parametrize(
    "ent, gt, expected",
    [({'page': 'aaa-001_2004_000_0012.txt',
       'year': '2004',
       'coord': 'b'},
      [[{'page': 'aaa-001_2004_000_0012.txt',
         'year': '2004',
         'coord': 'b',
         "gt_gnd_id": "a"}]],
      "a"),
     ({'page': 'aaa-001_2004_000_0012.txt',
       'year': '2004',
       'coord': 'b'},
      [[{'page': 'aaa-001_2004_000_0012.txt',
         'year': '2004',
         'coord': 'c',
         "gt_gnd_id": "a"}]],
      "")
     ],
)
def test_label_entity(ent, gt, expected):
    assert label_entity(ent, gt) == expected


# -------------------------------------------------
# 6. Test label_and_match_to_key
# -------------------------------------------------
@pytest.mark.parametrize(
    "gt_label, match, expected",
    [("", True, "tn"),
     ("a", True, "tp"),
     ("", False, "fp"),
     ("a", False, "fn"),
     ],
)
def test_label_and_match_to_key(gt_label, match, expected):
    assert label_and_match_to_key(gt_label, match) == expected


# -------------------------------------------------
# 7. Test eval_entity
# -------------------------------------------------
@pytest.mark.parametrize(
    "entity, expected",
    [({"candidates": [[]],
       "label": "a"},
      {"tp": 0, "fp": 0, "tn": 0, "fn": 1}),
     ({"candidates": ["a", "b"],
       "label": "a"},
      {"tp": 1, "fp": 0, "tn": 0, "fn": 0}),
     ({"candidates": ["a"],
       "label": ""},
      {"tp": 0, "fp": 1, "tn": 0, "fn": 0}),
     ({"candidates": [[]],
       "label": ""},
      {"tp": 0, "fp": 0, "tn": 1, "fn": 0})
     ],
)
def test_eval_entity(entity, expected):
    assert eval_entity(entity) == expected


# -------------------------------------------------
# 8. Test eval_references
# -------------------------------------------------
@pytest.mark.parametrize(
    "entity, expected",
    [({"candidates": [[], []],
       "labels": ["a", "b"]},
      {"tp": 0, "fp": 0, "tn": 0, "fn": 2}),
     ({"candidates": [["a"], ["b"]],
       "labels": ["a", "b"]},
      {"tp": 2, "fp": 0, "tn": 0, "fn": 0}),
     ({"candidates": [["a"], ["b"]],
       "labels": ["", ""]},
      {"tp": 0, "fp": 2, "tn": 0, "fn": 0}),
     ({"candidates": [[], []],
       "labels": ["", ""]},
      {"tp": 0, "fp": 0, "tn": 2, "fn": 0})
     ],
)
def test_eval_references(entity, expected):
    assert eval_references(entity) == expected


# -------------------------------------------------
# 9. Test evaluate_person
# -------------------------------------------------
linked_dict_without_gnd = {
    'lastname': 'z',
    'firstname': ['x y'],
    'abbr_firstname': [],
    'address': ["Frau"],
    'titles': [],
    'profession': [],
    'other': [],
    'references': {
        'aaa-001_2004_000_0012.txt': {
            'refs': [{'sent': 0, 'coords': ['a']}]}
    },
    'type': 'PER',
    'id': 0,
    'gnd_ids': []
}
gt_dict_with_multiple_refs = {
    'lastname': 'z',
    'firstname': ['x y'],
    'abbr_firstname': [],
    'address': ["Frau"],
    'titles': [],
    'profession': [],
    'other': [],
    'references': {
        'aaa-001_2004_000_0012.txt': {
            'refs': [
                {'sent': 0, 'coords': ['a']}, {'sent': 1, 'coords': ['b']}
            ]
        }
    },
    'type': 'PER',
    'id': 0,
    'gt_gnd_id': 'a'
}
linked_dict_with_partial_refs = {
    'lastname': 'z',
    'firstname': ['x y'],
    'abbr_firstname': [],
    'address': ["Frau"],
    'titles': [],
    'profession': [],
    'other': [],
    'references': {
        'aaa-001_2004_000_0012.txt': {
            'refs': [{'sent': 0, 'coords': ['a']}]}
    },
    'type': 'PER',
    'id': 0,
    'gnd_ids': ["a"]
}
linked_dict_with_extra_refs = {
    'lastname': 'z',
    'firstname': ['x y'],
    'abbr_firstname': [],
    'address': ["Frau"],
    'titles': [],
    'profession': [],
    'other': [],
    'references': {
        'aaa-001_2004_000_0012.txt': {
            'refs': [
                {'sent': 0, 'coords': ['a']}, {'sent': 2, 'coords': ['c']}
            ]
        }
    },
    'type': 'PER',
    'id': 0,
    'gnd_ids': ['a']
}


@pytest.mark.parametrize(
    "gt, linked, ref_level, expected",
    [([gt_dict_with_gnd],
      [entity_dict_with_gnd],
      True,
      {'tp': 1, 'fp': 0, 'fn': 0, 'tn': 0}),
     ([gt_dict_without_gnd],
      [entity_dict_with_gnd],
      True,
      {'tp': 0, 'fp': 1, 'fn': 0, 'tn': 0}),
     ([gt_dict_with_gnd],
      [entity_dict_without_gnd],
      True,
      {'tp': 0, 'fp': 0, 'fn': 1, 'tn': 0}),
     ([gt_dict_without_gnd],
      [entity_dict_without_gnd],
      True,
      {'tp': 0, 'fp': 0, 'fn': 0, 'tn': 1}),
     # Ground truth has multiple references, linked has partial matches
     # This case covers differences in aggregation for instance
     ([gt_dict_with_multiple_refs],
      [linked_dict_with_partial_refs],
      True,
      {'tp': 1, 'fp': 0, 'fn': 0, 'tn': 0}),
     # Ground truth has multiple references, linked has extra references
     ([gt_dict_with_multiple_refs],
      [linked_dict_with_extra_refs],
      True,
      {'tp': 1, 'fp': 0, 'fn': 0, 'tn': 0}),
     # Ground truth and linked entity match with GND ID
     ([gt_dict_with_gnd],
      [linked_dict_with_partial_refs],
      False,
      {'tp': 1, 'fp': 0, 'fn': 0, 'tn': 0}),
     # Ground truth has no GND ID, but linked entity has GND ID
     ([gt_dict_without_gnd],
      [linked_dict_with_partial_refs],
      False,
      {'tp': 0, 'fp': 1, 'fn': 0, 'tn': 0}),
     # Ground truth has GND ID, but linked entity has no GND ID
     ([gt_dict_with_gnd],
      [linked_dict_without_gnd],
      False,
      {'tp': 0, 'fp': 0, 'fn': 1, 'tn': 0}),
     # Neither ground truth nor linked entity has GND ID
     ([gt_dict_without_gnd],
      [linked_dict_without_gnd],
      False,
      {'tp': 0, 'fp': 0, 'fn': 0, 'tn': 1}),
     ],
)
def test_evaluate_person(gt, linked, ref_level, expected):
    assert evaluate_person(gt, linked, ref_level) == expected
