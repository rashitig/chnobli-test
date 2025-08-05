import pytest
from unittest.mock import patch

from src.linking import (
    prep_word,
    remove_obsolete_abbrevs,
    get_candidates,
    prep_person_entry,
    prep_person_out,
    link_person,
    find_links,
    execute_linking
)


# -------------------------------------------------
# 1. Test prep_word
# -------------------------------------------------
@pytest.mark.parametrize(
    "word,expected",
    [
        ("Otmar M\u00e4der", 'Otmar Mäder'),
        ("P* Scha^mann", "P* Schamann"),
        ("URS CAVELTI", 'Urs Cavelti'),
        ("d'Estouilly", "dEstouilly")
    ],
)
def test_prep_word(word, expected):
    """
    """
    assert prep_word(word) == expected


# -------------------------------------------------
# 2. Test remove_obsolete_abbrevs
# -------------------------------------------------
@pytest.mark.parametrize(
    "fnames, abbr_firstnames, expected",
    [
        (["Richard"], ["R."], [[]]),
        (["Richard"], ["A.", "R."], [['A.'], []]),
        (["Richard"], ["A.", "R.", "B"], [['A.'], [], ['B.']]),
        (["Richard", "Albert"], ["A.", "R.", "B"], [[], [], ['B.']]),
        (["Albert", "Richard"], ["a.", "R.", "B"], [['a.'], [], ['B.']]),
        # names are highly case sensitive
        (["Richard"], [], []),
    ],
)
def test_remove_obsolete_abbrevs(fnames, abbr_firstnames, expected):
    """
    """
    assert remove_obsolete_abbrevs(fnames, abbr_firstnames) == expected


# -------------------------------------------------
# 3. Test get_candidates
# -------------------------------------------------
@patch("src.linking.search_person_gnd")
@patch("src.linking.search_person_wikidata")
@pytest.mark.parametrize(
    "person, gnd_limit, wikidata_limit, gnd_return, wikidata_return, expected",
    [
     ({"lastname": ["Cavelti"],
       "firstname": [["Urs"], ["Josef"]],
       "abbr_firstname": ["U."]},
      15,
      5,
      {'1066273278': {
         'desc': {'(1927-2003)'},
         'birthplaceLiteral': {'Gossau'},
         'prefForename': {'Urs'},
         'jobliteral': {'Jurist'},
         'birthdate': {'1927-09-03'},
         'deathdate': {'2003-11-04'},
         'deathplaceLiteral': {'St. Gallen'},
         'gid': {'1066273278'},
         'name': {'Urs Josef Cavelti'},
         'prefSurname': {'Cavelti'},
         'score': 23.719946
         }
       },
      {},
      {'1066273278': {
          'desc': {'(1927-2003)'},
          'birthplaceLiteral': {'Gossau'},
          'prefForename': {'Urs'},
          'jobliteral': {'Jurist'},
          'birthdate': {'1927-09-03'},
          'deathdate': {'2003-11-04'},
          'deathplaceLiteral': {'St. Gallen'},
          'gid': {'1066273278'},
          'name': {'Urs Josef Cavelti'},
          'prefSurname': {'Cavelti'},
          'score': 23.719946
        }
       }),
     ({"lastname": ["Chatterjee"],
       "firstname": [],
       "abbr_firstname": ["S."]},
      15,
      5,
      {'104124474': {'gid': {'104124474'},
                     'prefForename': {'Suhas'},
                     'prefSurname': {'Chatterjee'},
                     'varForename': {'S.'},
                     'varSurname': {'Chatterjee'},
                     'birthdate': {'1935'},
                     'score': 11.123201},
       '104274638': {'gid': {'104274638'},
                     'prefForename': {'Shiba P.'},
                     'prefSurname': {'Chatterjee'},
                     'academic': {'Prof.'},
                     'birthdate': {'1903'},
                     'deathdate': {'1989'},
                     'score': 11.123201},
       '143232991': {'gid': {'143232991'},
                     'prefForename': {'Samir'},
                     'prefSurname': {'Chatterjee'},
                     'varForename': {'S.'},
                     'varSurname': {'Chatterjee'},
                     'academic': {'Ph.D.'},
                     'score': 11.123201},
       '170184749': {'gid': {'170184749'},
                     'prefForename': {'Salil K.'},
                     'prefSurname': {'Chatterjee'},
                     'varForename': {'Salil Kumar'},
                     'varSurname': {'Chatterjee'},
                     'birthdate': {'1938'},
                     'score': 11.123201},
       '170050564': {'gid': {'170050564'},
                     'prefForename': {'Sangit'},
                     'prefSurname': {'Chatterjee'},
                     'score': 11.123201},
       '170446042': {'gid': {'170446042'},
                     'prefForename': {'Srikanta'},
                     'prefSurname': {'Chatterjee'},
                     'varForename': {'S.'},
                     'varSurname': {'Chatterjee'},
                     'academic': {'Prof.'},
                     'score': 11.123201},
       '170721930': {'gid': {'170721930'},
                     'prefForename': {'Sris'},
                     'prefSurname': {'Chatterjee'},
                     'varForename': {'S.'},
                     'varSurname': {'Chatterjee'},
                     'score': 11.123201},
       '170724727': {'gid': {'170724727'},
                     'prefForename': {'S. K.'},
                     'prefSurname': {'Chatterjee'},
                     'score': 11.123201},
       '170726045': {'gid': {'170726045'},
                     'prefForename': {'Shiladitya'},
                     'prefSurname': {'Chatterjee'},
                     'score': 11.123201},
       '170681866': {'gid': {'170681866'},
                     'prefForename': {'Sayan'},
                     'prefSurname': {'Chatterjee'},
                     'academic': {'Prof. of Policy'},
                     'score': 11.123201},
       '171016556': {'gid': {'171016556'},
                     'prefForename': {'Surendra N.'},
                     'prefSurname': {'Chatterjee'},
                     'varForename': {'Surendra Nath'},
                     'varSurname': {'Chatterjee'},
                     'birthdate': {'1944'},
                     'score': 11.123201},
       '171011252': {'gid': {'171011252'},
                     'prefForename': {'Shri G.'},
                     'prefSurname': {'Chatterjee'},
                     'score': 11.123201},
       '17147967X': {'gid': {'17147967X'},
                     'prefForename': {'S.'},
                     'prefSurname': {'Chatterjee'},
                     'score': 11.123201},
       '171610288': {'gid': {'171610288'},
                     'prefForename': {'Samir'},
                     'prefSurname': {'Chatterjee'},
                     'varForename': {'S. R.', 'Sam', 'Samir Ranjan'},
                     'varSurname': {'Chatterjee'},
                     'academic': {'Prof.', 'Prof. Dr.'},
                     'birthdate': {'1945'},
                     'score': 11.123201},
       '171620682': {'gid': {'171620682'},
                     'prefForename': {'Sandip'},
                     'prefSurname': {'Chatterjee'},
                     'score': 11.123201}},
      {'1253876894': {'desc': {'researcher'},
                      'jobliteral': {'Forscher'},
                      'gid': {'1253876894'},
                      'name': {'Swarn Chatterjee'},
                      'prefSurname': {'Chatterjee'},
                      'prefForename': {'Swarn'},
                      'score': 11.362046},
       '172018978': {'desc': {'Ph.D. Harvard University 1967'},
                     'birthdate': {'1938-01-01'},
                     'gid': {'172018978'},
                     'name': {'Samprit Chatterjee'},
                     'prefSurname': {'Chatterjee'},
                     'prefForename': {'Samprit'},
                     'score': 11.362046},
       '124061795X': {'prefSurname': {'Chatterjee'},
                      'jobliteral': {'Hochschullehrer', 'Informatiker'},
                      'birthdate': {'1963-00-00'},
                      'gid': {'124061795X'},
                      'name': {'Siddhartha Chatterjee'},
                      'prefForename': {'Siddhartha'},
                      'score': 11.362046},
       '1199154059': {'desc': {'researcher'},
                      'jobliteral': {'Forscher'},
                      'gid': {'1199154059'},
                      'name': {'Sangam Chatterjee'},
                      'prefSurname': {'Chatterjee'},
                      'prefForename': {'Sangam'},
                      'score': 11.362046},
       '1060392003': {'desc': {
           'Indian politician and former Speaker of the Lok Sabha (1929-2018)'
                      },
                      'birthplaceLiteral': {'Tezpur'},
                      'prefForename': {'Somnath'},
                      'prefSurname': {'Chatterjee'},
                      'jobliteral': {'Barrister', 'Politiker'},
                      'birthdate': {'1929-07-25'},
                      'deathdate': {'2018-08-13'},
                      'deathplaceLiteral': {'Kolkata'},
                      'gid': {'1060392003'},
                      'name': {'Somnath Chatterjee'},
                      'score': 11.362046}},
      {'104124474': {'birthdate': {'1935'},
                     'gid': {'104124474'},
                     'prefForename': {'Suhas'},
                     'prefSurname': {'Chatterjee'},
                     'score': 11.123201,
                     'varForename': {'S.'},
                     'varSurname': {'Chatterjee'}},
       '104274638': {'academic': {'Prof.'},
                     'birthdate': {'1903'},
                     'deathdate': {'1989'},
                     'gid': {'104274638'},
                     'prefForename': {'Shiba P.'},
                     'prefSurname': {'Chatterjee'},
                     'score': 11.123201},
       '1060392003': {'birthdate': {'1929-07-25'},
                      'birthplaceLiteral': {'Tezpur'},
                      'deathdate': {'2018-08-13'},
                      'deathplaceLiteral': {'Kolkata'},
                      'desc': {
                          'Indian politician and former Speaker of the Lok \
Sabha (1929-2018)'
                      },
                      'gid': {'1060392003'},
                      'jobliteral': {'Barrister', 'Politiker'},
                      'name': {'Somnath Chatterjee'},
                      'prefForename': {'Somnath'},
                      'prefSurname': {'Chatterjee'},
                      'score': 11.362046},
       '1199154059': {'desc': {'researcher'},
                      'gid': {'1199154059'},
                      'jobliteral': {'Forscher'},
                      'name': {'Sangam Chatterjee'},
                      'prefForename': {'Sangam'},
                      'prefSurname': {'Chatterjee'},
                      'score': 11.362046},
       '124061795X': {'birthdate': {'1963-00-00'},
                      'gid': {'124061795X'},
                      'jobliteral': {'Hochschullehrer', 'Informatiker'},
                      'name': {'Siddhartha Chatterjee'},
                      'prefForename': {'Siddhartha'},
                      'prefSurname': {'Chatterjee'},
                      'score': 11.362046},
       '1253876894': {'desc': {'researcher'},
                      'gid': {'1253876894'},
                      'jobliteral': {'Forscher'},
                      'name': {'Swarn Chatterjee'},
                      'prefForename': {'Swarn'},
                      'prefSurname': {'Chatterjee'},
                      'score': 11.362046},
       '143232991': {'academic': {'Ph.D.'},
                     'gid': {'143232991'},
                     'prefForename': {'Samir'},
                     'prefSurname': {'Chatterjee'},
                     'score': 11.123201,
                     'varForename': {'S.'},
                     'varSurname': {'Chatterjee'}},
       '170050564': {'gid': {'170050564'},
                     'prefForename': {'Sangit'},
                     'prefSurname': {'Chatterjee'},
                     'score': 11.123201},
       '170184749': {'birthdate': {'1938'},
                     'gid': {'170184749'},
                     'prefForename': {'Salil K.'},
                     'prefSurname': {'Chatterjee'},
                     'score': 11.123201,
                     'varForename': {'Salil Kumar'},
                     'varSurname': {'Chatterjee'}},
       '170446042': {'academic': {'Prof.'},
                     'gid': {'170446042'},
                     'prefForename': {'Srikanta'},
                     'prefSurname': {'Chatterjee'},
                     'score': 11.123201,
                     'varForename': {'S.'},
                     'varSurname': {'Chatterjee'}},
       '170681866': {'academic': {'Prof. of Policy'},
                     'gid': {'170681866'},
                     'prefForename': {'Sayan'},
                     'prefSurname': {'Chatterjee'},
                     'score': 11.123201},
       '170721930': {'gid': {'170721930'},
                     'prefForename': {'Sris'},
                     'prefSurname': {'Chatterjee'},
                     'score': 11.123201,
                     'varForename': {'S.'},
                     'varSurname': {'Chatterjee'}},
       '170724727': {'gid': {'170724727'},
                     'prefForename': {'S. K.'},
                     'prefSurname': {'Chatterjee'},
                     'score': 11.123201},
       '170726045': {'gid': {'170726045'},
                     'prefForename': {'Shiladitya'},
                     'prefSurname': {'Chatterjee'},
                     'score': 11.123201},
       '171011252': {'gid': {'171011252'},
                     'prefForename': {'Shri G.'},
                     'prefSurname': {'Chatterjee'},
                     'score': 11.123201},
       '171016556': {'birthdate': {'1944'},
                     'gid': {'171016556'},
                     'prefForename': {'Surendra N.'},
                     'prefSurname': {'Chatterjee'},
                     'score': 11.123201,
                     'varForename': {'Surendra Nath'},
                     'varSurname': {'Chatterjee'}},
       '17147967X': {'gid': {'17147967X'},
                     'prefForename': {'S.'},
                     'prefSurname': {'Chatterjee'},
                     'score': 11.123201},
       '171610288': {'academic': {'Prof.', 'Prof. Dr.'},
                     'birthdate': {'1945'},
                     'gid': {'171610288'},
                     'prefForename': {'Samir'},
                     'prefSurname': {'Chatterjee'},
                     'score': 11.123201,
                     'varForename': {'S. R.', 'Sam', 'Samir Ranjan'},
                     'varSurname': {'Chatterjee'}},
       '171620682': {'gid': {'171620682'},
                     'prefForename': {'Sandip'},
                     'prefSurname': {'Chatterjee'},
                     'score': 11.123201},
       '172018978': {'birthdate': {'1938-01-01'},
                     'desc': {'Ph.D. Harvard University 1967'},
                     'gid': {'172018978'},
                     'name': {'Samprit Chatterjee'},
                     'prefForename': {'Samprit'},
                     'prefSurname': {'Chatterjee'},
                     'score': 11.362046},
       })
     ],
)
def test_get_candidates(mock_search_person_gnd,
                        mock_search_person_wikidata,
                        person,
                        gnd_limit,
                        wikidata_limit,
                        expected,
                        gnd_return,
                        wikidata_return):
    # Mock GND and Wikidata search results
    mock_search_person_gnd.return_value = gnd_return
    mock_search_person_wikidata.return_value = wikidata_return

    assert get_candidates(person, gnd_limit, wikidata_limit) == expected


def test_get_candidates_no_lastname():
    assert get_candidates({"lastname": []}, 15, 5) == {}


def test_get_candidates_no_firstname_or_abbr():
    assert get_candidates(
        {"lastname": ["A", "B"], "firstname": [], "abbr_firstname": []}, 15, 5
    ) == {}


def test_get_candidates_short_lastname():
    assert get_candidates(
        {
            "lastname": ["B"],
            "firstname": [["Alice"]],
            "abbr_firstname": ["A."]
        },
        15,
        5) == {}


# -------------------------------------------------
# 4. Test prep_person_entry
# -------------------------------------------------
@pytest.mark.parametrize(
    "person, expected",
    [
        ({"firstname": ["ALLIE Marie"],
          "lastname": "K^ann MEIÉR",
          "abbr_firstname": "",
          "profession": ["Schauspielerin", "Musikerin"]},
         {'firstname': [['Allie', 'Marie']],
          'lastname': ['Kann', 'Meiér'],
          'abbr_firstname': [],
          'profession': ['Musikerin', 'Schauspielerin']})
    ],
)
def test_prep_person_entry(person, expected):
    """
    """
    prep_person_entry(person)
    assert person == expected


# -------------------------------------------------
# 5. Test prep_person_out
# -------------------------------------------------
@pytest.mark.parametrize(
    "person,expected",
    [
        ({'firstname': [['Allie', 'Marie']],
            'lastname': ['Kann', 'Meiér'],
            'abbr_firstname': [],
            'profession': ['Musikerin', 'Schauspielerin']},
         {'firstname': ['Allie Marie'],
            'lastname': 'Kann Meiér',
            'abbr_firstname': [],
            'profession': ['Musikerin', 'Schauspielerin']}),
    ],
)
def test_prep_person_out(person, expected):
    """
    """
    prep_person_out(person)
    assert person == expected


# -------------------------------------------------
# 6. Test link_person
# -------------------------------------------------
@patch("src.linking.get_candidates")
def test_link_person_with_valid_data(mock_get_candidates):
    person = {
        "lastname": "Doe",
        "firstname": ["John"],
        "abbr_firstname": ["J."],
        "address": ["123 Main St"],
        "titles": ["Dr."],
        "profession": ["Engineer"],
        "other": [],
        "references": {
            "1": {"refs": [{"sent": "Example sentence", "coords": "0,0"}]}
        },
        "type": "PER",
        "id": 1,
    }

    mock_get_candidates.return_value = {
        "1111": {"prefForename": {"John"}, "score": 15},
        "2222": {"prefForename": {"John"}, "score": 25},
        "3333": {"prefForename": {"J."}, "score": 30},
    }

    result = link_person((person, 15, 5, 10))

    assert "gnd_ids" in result
    # the results from get gnd/wikidata values are assumed to be
    # sorted by score, so we do not sort them again.
    assert result["gnd_ids"] == ["1111", "2222", "3333"]
    assert result["firstname"] == ["John"]
    assert result["lastname"] == "Doe"
    assert mock_get_candidates.called


def test_link_person_with_no_candidates_copilot():
    person = {
        "lastname": "Doe",
        "firstname": ["John"],
        "abbr_firstname": ["J."],
        "address": ["123 Main St"],
        "titles": ["Dr."],
        "profession": ["Engineer"],
        "other": [],
        "references": {
            "1": {"refs": [{"sent": "Example sentence", "coords": "0,0"}]}
        },
        "type": "PER",
        "id": 1,
    }

    # Mock candidates returned by get_candidates
    mock_get_candidates = patch("src.linking.get_candidates").start()
    mock_get_candidates.return_value = {}

    result = link_person((person, 15, 5, 10))

    assert "gnd_ids" in result
    assert result["gnd_ids"] == []  # No candidates found
    assert result["firstname"] == ["John"]
    assert result["lastname"] == "Doe"
    mock_get_candidates.stop()


def test_link_person_with_abbr_firstname_filtering():
    person = {
        "lastname": "Doe",
        "firstname": ["John"],
        "abbr_firstname": ["J."],
        "address": ["123 Main St"],
        "titles": ["Dr."],
        "profession": ["Engineer"],
        "other": [],
        "references": {
            "1": {"refs": [{"sent": "Example sentence", "coords": "0,0"}]}
        },
        "type": "PER",
        "id": 1,
    }

    # Mock candidates returned by get_candidates
    mock_get_candidates = patch("src.linking.get_candidates").start()
    mock_get_candidates.return_value = {
        "12345": {"prefForename": {"John"}, "score": 20},
        "67890": {"prefForename": {"Kane"}, "score": 15},
    }

    result = link_person((person, 15, 5, 1))

    assert "gnd_ids" in result
    # Filtered by matching abbr_firstname
    assert result["gnd_ids"] == ["12345"]
    assert result["firstname"] == ["John"]
    assert result["lastname"] == "Doe"
    mock_get_candidates.stop()


# -------------------------------------------------
# 6. Test find_links
# -------------------------------------------------
@patch("src.linking.link_person")
@patch("src.linking.save_data_intermediate")
def test_find_links(mock_save_data_intermediate, mock_link_person):
    mag_year = ("abc", "2023")
    data = [
        {
            "lastname": "Doe",
            "firstname": ["John"],
            "abbr_firstname": ["J."],
            "address": ["123 Main St"],
            "titles": ["Dr."],
            "profession": ["Engineer"],
            "other": [],
            "references": {
                "1": {"refs": [{"sent": "Example sentence", "coords": "0,0"}]}
            },
            "type": "PER",
            "id": 1,
        },
        {
            "lastname": "Smith",
            "firstname": ["Alice"],
            "abbr_firstname": ["A."],
            "address": ["456 Elm St"],
            "titles": ["Prof."],
            "profession": ["Scientist"],
            "other": [],
            "references": {
                "2": {"refs": [{"sent": "Another example", "coords": "1,1"}]}
            },
            "type": "PER",
            "id": 2,
        },
    ]
    conf = {
        "GND_LIMIT": 5,
        "WIKIDATA_LIMIT": 10,
        "LINKED_PERSONS_LIMIT": 3,
        "PATH_TO_OUTFILE_FOLDER": "./tests/test_data/output/",
    }

    mock_link_person.side_effect = lambda x: {
        **x[0], "gnd_ids": ["12345", "67890"]
    }

    result = find_links((mag_year, data, conf))

    assert len(result) == 2
    assert result[0]["gnd_ids"] == ["12345", "67890"]
    assert result[1]["gnd_ids"] == ["12345", "67890"]

    # Verify that link_person was called for each person
    assert mock_link_person.call_count == 2

    # Verify that save_data_intermediate was called with the correct arguments
    mock_save_data_intermediate.assert_called_once_with(
        mag_year, result, conf, "link"
    )


# -------------------------------------------------
# 7. Test execute_linking
# -------------------------------------------------
def test_execute_linking():
    """
    All this function does is call find links (tested above)
    and save the intermediate data (tested in test_utils)
    """
    with pytest.raises(Exception) as excinfo:
        execute_linking(None, None, ["post", "link"])
    assert str(excinfo.value) == "'post,agg,link' must be called together, \
or call 'finish' instead."
