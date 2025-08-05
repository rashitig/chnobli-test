import pytest

from src.aggregation import (
    create_new_aggregated_unit,
    merge_to_existing_aggregated_unit,
    decide_candidates,
    full_firstname_match,
    aggregate_with,
    abbrev_firstname_match,
    only_lastname_match,
    only_firstname_match,
    only_abbrev_firstname_match,
    others_match,
    clean_up_aggregation,
    map_genitive_versions,
    map_genitive_places,
    find_place_match,
    aggregate_places,
    aggregate_place,
    create_new_aggregated_place,
    clean_up_aggregation_places,
    clean_lastname,
    aggregate_names,
    aggregate_and_save_data_timed,
    execute_aggregation
)


# -------------------------------------------------
# Test create_new_aggregated_unit
# -------------------------------------------------
def test_create_new_aggregated_unit_copilot():
    reference = {
        "info": {
            "lastnames": ["Doe"],
            "firstnames": "John",
            "abbr_firstnames": "J.",
            "address": ["123 Main St"],
            "titles": ["Dr."],
            "occupations": ["Engineer"],
            "others": ["AdditionalInfo"]
        },
        "pageNo": 1,
        "pageNames": "Page1",
        "pid": "pid1",
        "sentenceNo": 5,
        "positions": "pos1",
        "articles": "article1"
    }

    result = create_new_aggregated_unit(reference)

    assert result["lastname"] == ["Doe"]
    assert result["firstname"] == {("John",)}
    assert result["abbr_firstname"] == {("J.",)}
    assert result["address"] == {("123 Main St",)}
    assert result["titles"] == {("Dr.",)}
    assert result["profession"] == {("Engineer",)}
    assert result["other"] == {("AdditionalInfo",)}
    assert result["references"] == {
        (1, "Page1", "pid1"): [(5, "pos1", "article1")]
    }


# -------------------------------------------------
# Test merge_to_existing_aggregated_unit
# -------------------------------------------------
def test_merge_to_existing_aggregated_unit_copilot():
    match = {
        "firstname": {("John",)},
        "abbr_firstname": {("J.",)},
        "titles": {("Dr.",)},
        "other": {("OtherInfo",)},
        "address": {("123 Street",)},
        "profession": {("Engineer",)},
        "references": {
            (1, "Page1", "pid1"): [(1, "pos1", "article1")]
        }
    }
    reference = {
        "info": {
            "firstnames": "Jane",
            "abbr_firstnames": "J.",
            "titles": ["Prof."],
            "others": ["AdditionalInfo"],
            "address": ["456 Avenue"],
            "occupations": ["Scientist"]
        },
        "pageNo": 2,
        "pageNames": "Page2",
        "pid": "pid2",
        "sentenceNo": 5,
        "positions": "pos2",
        "articles": "article2"
    }

    merge_to_existing_aggregated_unit(match, reference)

    assert ("Jane",) in match["firstname"]
    assert ("J.",) in match["abbr_firstname"]
    assert ("Prof.",) in match["titles"]
    assert ("AdditionalInfo",) in match["other"]
    assert ("456 Avenue",) in match["address"]
    assert ("Scientist",) in match["profession"]
    assert (2, "Page2", "pid2") in match["references"]
    assert match["references"][(2, "Page2", "pid2")] == [
        (5, "pos2", "article2")
    ]
    assert len(match["references"]) == 2


# -------------------------------------------------
# Test aggregate_with
# -------------------------------------------------
@pytest.mark.parametrize(
  "namepart_dict, aggregated_names, namepart, expected",
  [
   ({"x": [
         {
          "info": {
              "lastnames": "Müller",
              "firstnames": "Maria",
              "abbr_firstnames": "",
              "titles": ["match_titles"],
              "address": ["match_address"],
              "occupations": ["match_occupations"],
              "others": ["match_others"]
          },
          "pageNo": 44,
          "sentenceNo": 55,
          "pageNames": "",
          "pid": "",
          "positions": "",
          "articles": "",
          'type': 'PER'
          }
        ]
     },
    [{'firstname': {('Anna', 'Maria')},
      "lastname": "Müller",
      "abbr_firstname": set(),
      "titles": {("Frau", "Dr.")},
      "address": {("a", "b")},
      "profession": {("c", "d")},
      "other": {("e")},
      "references": {
               (4, "abc", 2): [(5, "123", "123"), (6, "456", "456")]
           }
      },
    {"firstname": {("Kat", "Man")},
     "lastname": "Bil",
     "abbr_firstname": set(),
     "titles": {("Herr", "Prof")},
     "address": {("a", "b")},
     "profession": {("c", "d")},
     "other": {},
     "references": {
              (4, "abc", 2): [(5, "123", "123"), (6, "456", "456")]
          }
     }],
    "fullfirstnames",
    [{'firstname': {('Anna', 'Maria'), ('Maria',)},
      'lastname': 'Müller',
      'abbr_firstname': {()},
      'titles': {('match_titles',), ('Frau', 'Dr.')},
      'address': {('match_address',), ('a', 'b')},
      'profession': {('match_occupations',), ('c', 'd')},
      'other': {'e', ('match_others',)},
      'references': {
          (4, 'abc', 2): [(5, '123', '123'), (6, '456', '456')],
          (44, '', ''): [(55, '', '')]}},
     {'firstname': {('Kat', 'Man')},
      'lastname': 'Bil',
      'abbr_firstname': set(),
      'titles': {('Herr', 'Prof')},
      'address': {('a', 'b')},
      'profession': {('c', 'd')},
      'other': {},
      'references': {
          (4, 'abc', 2): [(5, '123', '123'), (6, '456', '456')]}
      }]
    ),
   ({"x": [
        {
            "info": {
                "lastnames": "Müller",
                "firstnames": "",
                "abbr_firstnames": "M",
                "titles": "",
                "address": "",
                "occupations": "",
                "others": "e"
             },
            "pageNo": 44,
            "sentenceNo": 55,
            "pageNames": "",
            "pid": "",
            "positions": "",
            "articles": "",
            'type': 'PER'
         }
       ]
     },
    [{'firstname': {('Anna', 'Maria')},
      "lastname": "Müller",
      "abbr_firstname": set(),
      "titles": {("Frau", "Dr.")},
      "address": {("a", "b")},
      "profession": {("c", "d")},
      "other": {("e")},
      "references": {
               (4, "abc", 2): [(5, "123", "123"), (6, "456", "456")]
           }
      },
     {"firstname": {("Kat", "Man")},
      "lastname": "Bil",
      "abbr_firstname": set(),
      "titles": {("Herr", "Prof")},
      "address": {("a", "b")},
      "profession": {("c", "d")},
      "other": {},
      "references": {
                (4, "abc", 2): [(5, "123", "123"), (6, "456", "456")]
            }
      }],
       "fullfirstnames",
       [{'firstname': {('Anna', 'Maria')},
         'lastname': 'Müller',
         'abbr_firstname': set(),
         'titles': {('Frau', 'Dr.')},
         'address': {('a', 'b')},
         'profession': {('c', 'd')},
         'other': {'e'},
         'references': {
            (4, 'abc', 2): [(5, '123', '123'), (6, '456', '456')]}},
        {'firstname': {('Kat', 'Man')},
         'lastname': 'Bil',
         'abbr_firstname': set(),
         'titles': {('Herr', 'Prof')},
         'address': {('a', 'b')},
         'profession': {('c', 'd')},
         'other': {},
         'references': {
             (4, 'abc', 2): [(5, '123', '123'), (6, '456', '456')]}},
        {'lastname': 'Müller',
         'firstname': {()},
         'abbr_firstname': {('M',)},
         'address': {()},
         'titles': {()},
         'profession': {()},
         'other': {('e',)},
         'references': {
             (44, '', ''): [(55, '', '')]},
         'type': 'PER'}]
    ),
   ({"x": [
         {
          "info": {
              "lastnames": "Müller",
              "firstnames": "",
              "abbr_firstnames": "M",
              "titles": ["match_titles"],
              "address": ["match_address"],
              "occupations": ["match_occupations"],
              "others": ["match_others"]
          },
          "pageNo": 44,
          "sentenceNo": 55,
          "pageNames": "",
          "pid": "",
          "positions": "",
          "articles": "",
          'type': 'PER'
          }
        ]
     },
    [{'firstname': {('Anna', 'Maria')},
      "lastname": "Müller",
      "abbr_firstname": set(),
      "titles": {("Frau", "Dr.")},
      "address": {("a", "b")},
      "profession": {("c", "d")},
      "other": {("e")},
      "references": {
               (4, "abc", 2): [(5, "123", "123"), (6, "456", "456")]
           }
      },
    {"firstname": {("Kat", "Man")},
     "lastname": "Bil",
     "abbr_firstname": set(),
     "titles": {("Herr", "Prof")},
     "address": {("a", "b")},
     "profession": {("c", "d")},
     "other": {},
     "references": {
              (4, "abc", 2): [(5, "123", "123"), (6, "456", "456")]
          }
     }],
    "abbrevs",
    [{'firstname': {(), ('Anna', 'Maria')},
      'lastname': 'Müller',
      'abbr_firstname': {('M',)},
      'titles': {('match_titles',), ('Frau', 'Dr.')},
      'address': {('a', 'b'), ('match_address',)},
      'profession': {('match_occupations',), ('c', 'd')},
      'other': {'e', ('match_others',)},
      'references': {
          (4, 'abc', 2): [(5, '123', '123'), (6, '456', '456')],
          (44, '', ''): [(55, '', '')]}},
     {'firstname': {('Kat', 'Man')},
      'lastname': 'Bil',
      'abbr_firstname': set(),
      'titles': {('Herr', 'Prof')},
      'address': {('a', 'b')},
      'profession': {('c', 'd')},
      'other': {},
      'references': {
          (4, 'abc', 2): [(5, '123', '123'), (6, '456', '456')]}
      }]
    ),
   ({"x": [
        {
            "info": {
                "lastnames": "Müller",
                "firstnames": "",
                "abbr_firstnames": "D",
                "titles": "",
                "address": "",
                "occupations": "",
                "others": "e"
             },
            "pageNo": 44,
            "sentenceNo": 55,
            "pageNames": "",
            "pid": "",
            "positions": "",
            "articles": "",
            'type': 'PER'
         }
       ]
     },
    [{'firstname': {('Anna', 'Maria')},
      "lastname": "Müller",
      "abbr_firstname": set(),
      "titles": {("Frau", "Dr.")},
      "address": {("a", "b")},
      "profession": {("c", "d")},
      "other": {("e")},
      "references": {
               (4, "abc", 2): [(5, "123", "123"), (6, "456", "456")]
           }
      },
     {"firstname": {("Kat", "Man")},
      "lastname": "Bil",
      "abbr_firstname": set(),
      "titles": {("Herr", "Prof")},
      "address": {("a", "b")},
      "profession": {("c", "d")},
      "other": {},
      "references": {
                (4, "abc", 2): [(5, "123", "123"), (6, "456", "456")]
            }
      }],
    "abbrevs",
    [{'firstname': {('Anna', 'Maria')},
      'lastname': 'Müller',
      'abbr_firstname': set(),
      'titles': {('Frau', 'Dr.')},
      'address': {('a', 'b')},
      'profession': {('c', 'd')},
      'other': {'e'},
      'references': {
          (4, 'abc', 2): [(5, '123', '123'), (6, '456', '456')]}},
     {'firstname': {('Kat', 'Man')},
      'lastname': 'Bil',
      'abbr_firstname': set(),
      'titles': {('Herr', 'Prof')},
      'address': {('a', 'b')},
      'profession': {('c', 'd')},
      'other': {},
      'references': {
          (4, 'abc', 2): [(5, '123', '123'), (6, '456', '456')]}},
     {'lastname': 'Müller',
      'firstname': {()},
      'abbr_firstname': {('D',)},
      'address': {()},
      'titles': {()},
      'profession': {()},
      'other': {('e',)},
      'references': {
          (44, '', ''): [(55, '', '')]},
      'type': 'PER'}]
    ),
   ({"x": [
         {
          "info": {
              "lastnames": "Müller",
              "firstnames": "",
              "abbr_firstnames": "M",
              "titles": ["match_titles"],
              "address": ["match_address"],
              "occupations": ["match_occupations"],
              "others": ["match_others"]
          },
          "pageNo": 44,
          "sentenceNo": 55,
          "pageNames": "",
          "pid": "",
          "positions": "",
          "articles": "",
          'type': 'PER'
          }
        ]
     },
    [{'firstname': {('Anna', 'Maria')},
      "lastname": "Müller",
      "abbr_firstname": set(),
      "titles": {("Frau", "Dr.")},
      "address": {("a", "b")},
      "profession": {("c", "d")},
      "other": {("e")},
      "references": {
               (4, "abc", 2): [(5, "123", "123"), (6, "456", "456")]
           }
      },
    {"firstname": {("Kat", "Man")},
     "lastname": "Bil",
     "abbr_firstname": set(),
     "titles": {("Herr", "Prof")},
     "address": {("a", "b")},
     "profession": {("c", "d")},
     "other": {},
     "references": {
              (4, "abc", 2): [(5, "123", "123"), (6, "456", "456")]
          }
     }],
    "onlylastnames",
    [{'firstname': {(), ('Anna', 'Maria')},
      'lastname': 'Müller',
      'abbr_firstname': {('M',)},
      'titles': {('match_titles',), ('Frau', 'Dr.')},
      'address': {('a', 'b'), ('match_address',)},
      'profession': {('match_occupations',), ('c', 'd')},
      'other': {'e', ('match_others',)},
      'references': {
          (4, 'abc', 2): [(5, '123', '123'), (6, '456', '456')],
          (44, '', ''): [(55, '', '')]}},
     {'firstname': {('Kat', 'Man')},
      'lastname': 'Bil',
      'abbr_firstname': set(),
      'titles': {('Herr', 'Prof')},
      'address': {('a', 'b')},
      'profession': {('c', 'd')},
      'other': {},
      'references': {
          (4, 'abc', 2): [(5, '123', '123'), (6, '456', '456')]}
      }]
    ),
   ({"x": [
         {
             "info": {
                 "lastnames": "Müller",
                 "firstnames": "x",
                 "abbr_firstnames": "",
                 "titles": ["match_titles"],
                 "address": ["match_address"],
                 "occupations": ["match_occupations"],
                 "others": ["match_others"]
              },
             "pageNo": 44,
             "sentenceNo": 55,
             "pageNames": "",
             "pid": "",
             "positions": "",
             "articles": "",
             'type': 'PER'
          }
        ]
     },
    [{'firstname': {('Anna', 'Maria')},
      "lastname": "Müller",
      "abbr_firstname": set(),
      "titles": {("Frau", "Dr.")},
      "address": {("a", "b")},
      "profession": {("c", "d")},
      "other": {("e")},
      "references": {
               (4, "abc", 2): [(5, "123", "123"), (6, "456", "456")]
           }
      },
    {"firstname": {("Kat", "Man")},
     "lastname": "Bil",
     "abbr_firstname": set(),
     "titles": {("Herr", "Prof")},
     "address": {("a", "b")},
     "profession": {("c", "d")},
     "other": {},
     "references": {
              (4, "abc", 2): [(5, "123", "123"), (6, "456", "456")]
          }
     }],
    "onlylastnames",
    [{'firstname': {('x',), ('Anna', 'Maria')},
        'lastname': 'Müller',
        'abbr_firstname': {()},
        'titles': {('Frau', 'Dr.'), ('match_titles',)},
        'address': {('match_address',), ('a', 'b')},
        'profession': {('c', 'd'), ('match_occupations',)},
        'other': {('match_others',), 'e'},
        'references': {
            (4, 'abc', 2): [(5, '123', '123'), (6, '456', '456')],
            (44, '', ''): [(55, '', '')]}},
       {'firstname': {('Kat', 'Man')},
        'lastname': 'Bil',
        'abbr_firstname': set(),
        'titles': {('Herr', 'Prof')},
        'address': {('a', 'b')},
        'profession': {('c', 'd')},
        'other': {},
        'references': {
            (4, 'abc', 2): [(5, '123', '123'), (6, '456', '456')]}
        }]),
   ({"x": [
         {
             "info": {
                 "lastnames": "z",
                 "firstnames": "Anna",
                 "abbr_firstnames": "",
                 "titles": "",
                 "address": "",
                 "occupations": "",
                 "others": "e"
              },
             "pageNo": 44,
             "sentenceNo": 55,
             "pageNames": "",
             "pid": "",
             "positions": "",
             "articles": "",
             'type': 'PER'
          }
        ]
     },
    [{'firstname': {('Anna', 'Maria')},
      "lastname": "Müller",
      "abbr_firstname": set(),
      "titles": {("Frau", "Dr.")},
      "address": {("a", "b")},
      "profession": {("c", "d")},
      "other": {("e")},
      "references": {
               (4, "abc", 2): [(5, "123", "123"), (6, "456", "456")]
           }
      },
    {"firstname": {("Kat", "Man")},
     "lastname": "Bil",
     "abbr_firstname": set(),
     "titles": {("Herr", "Prof")},
     "address": {("a", "b")},
     "profession": {("c", "d")},
     "other": {},
     "references": {
              (4, "abc", 2): [(5, "123", "123"), (6, "456", "456")]
          }
     }],
    "onlyfirstnames",
    [
     {'firstname': {('Anna',), ('Anna', 'Maria')},
      'lastname': 'Müller',
      'abbr_firstname': {()},
      'titles': {(), ('Frau', 'Dr.')},
      'address': {(), ('a', 'b')},
      'profession': {(), ('c', 'd')},
      'other': {('e',), 'e'},
      'references': {
          (4, 'abc', 2): [(5, '123', '123'),
                          (6, '456', '456')],
          (44, '', ''): [(55, '', '')]}},
     {'firstname': {('Kat', 'Man')},
      'lastname': 'Bil',
      'abbr_firstname': set(),
      'titles': {('Herr', 'Prof')},
      'address': {('a', 'b')},
      'profession': {('c', 'd')},
      'other': {},
      'references': {
          (4, 'abc', 2): [(5, '123', '123'),
                          (6, '456', '456')]}}]
    ),
   ({"x": [
       {"info": {"lastnames": "z", "firstnames": "x",
                 "abbr_firstnames": "A",
                 "titles": ["titles_newmatch"],
                 "address": ["address_newmatch"],
                 "occupations": ["occupation_newmatch"],
                 "others": ["others_newmatch"]},
        "pageNo": 44, "sentenceNo": 55, "pageNames": "", "pid": "",
        "positions": "", "articles": "", 'type': 'PER'
        }]
     },
    [{'firstname': {('Anna', 'Maria')},
      "lastname": "Müller",
      "abbr_firstname": {"A"},
      "titles": {("Frau", "Dr.")},
      "address": {("a", "b")},
      "profession": {("c", "d")},
      "other": {("e")},
      "references": {
               (4, "abc", 2): [(5, "123", "123"), (6, "456", "456")]
           }
      },
    {"firstname": {("Kat", "Man")},
     "lastname": "Bil",
     "abbr_firstname": set(),
     "titles": {("Herr", "Prof")},
     "address": {("a", "b")},
     "profession": {("c", "d")},
     "other": {},
     "references": {
              (4, "abc", 2): [(5, "123", "123"), (6, "456", "456")]
          }
     }],
    "onlyabbrevfirstnames",
    [{'firstname': {('x',), ('Anna', 'Maria')},
      'lastname': 'Müller',
      'abbr_firstname': {('A',), 'A'},
      'titles': {('Frau', 'Dr.'), ('titles_newmatch',)},
      'address': {('a', 'b'), ('address_newmatch',)},
      'profession': {('c', 'd'), ('occupation_newmatch',)},
      'other': {('others_newmatch',), 'e'},
      'references': {
          (4, 'abc', 2): [(5, '123', '123'), (6, '456', '456')],
          (44, '', ''): [(55, '', '')]}},
     {'firstname': {('Kat', 'Man')},
      'lastname': 'Bil',
      'abbr_firstname': set(),
      'titles': {('Herr', 'Prof')},
      'address': {('a', 'b')},
      'profession': {('c', 'd')},
      'other': {},
      'references': {
          (4, 'abc', 2): [(5, '123', '123'), (6, '456', '456')]}}]
    ),
   ({("e",): [
      {"info": {"lastnames": "z",
                "firstnames": "x",
                "abbr_firstnames": "y",
                "titles": "",
                "address": "",
                "occupations": "",
                "others": "e"},
       "pageNo": 4,
       "sentenceNo": 5,
       "pageNames": "",
       "pid": "",
       "positions": "",
       "articles": "",
       'type': 'PER'}],
     ("b",): [
      {"info": {"lastnames": "",
                "firstnames": "",
                "abbr_firstnames": "",
                "titles": "",
                "address": "",
                "occupations": "",
                "others": "f"},
       "pageNo": 0,
       "sentenceNo": 11,
       "pageNames": "",
       "pid": "",
       "positions": "",
       "articles": ""}]},
    [{'firstname': {('Anna', 'Maria')},
      "lastname": "Müller",
      "abbr_firstname": set(),
      "titles": {("Frau", "Dr.")},
      "address": {("a", "b")},
      "profession": {("c", "d")},
      "other": {("e")},
      "references": {
               (4, "abc", 2): [(5, "123", "123"), (6, "456", "456")]
           }
      },
    {"firstname": {("Kat", "Man")},
     "lastname": "Bil",
     "abbr_firstname": set(()),
     "titles": {("Herr", "Prof")},
     "address": {("a", "b")},
     "profession": {("c", "d")},
     "other": {},
     "references": {
              (4, "abc", 2): [(5, "123", "123"), (6, "456", "456")]
          }
     }],
    "others",
    # # # # sol # # # #
    [{'abbr_firstname': {('y',)},
      'address': {(), ('a', 'b')},
      'firstname': {('Anna', 'Maria'), ('x',)},
      'lastname': 'Müller',
      'other': {'e', ('e',)},
      'profession': {(), ('c', 'd')},
      'references': {(4, '', ''): [(5, '', '')],
                     (4, 'abc', 2): [(5, '123', '123'), (6, '456', '456')]},
      'titles': {(), ('Frau', 'Dr.')}},
     {'abbr_firstname': set(),
      'address': {('a', 'b')},
      'firstname': {('Kat', 'Man')},
      'lastname': 'Bil',
      'other': {},
      'profession': {('c', 'd')},
      'references': {(4, 'abc', 2): [(5, '123', '123'), (6, '456', '456')]},
      'titles': {('Herr', 'Prof')}
      },
     {'abbr_firstname': {()},
      'address': {()},
      'firstname': {()},
      'lastname': '',
      'other': {('f',)},
      'profession': {()},
      'references': {(0, '', ''): [(11, '', '')]},
      'titles': {()},
      'type': 'PER'}]
    )
   ]
)
def test_aggregate_with(namepart_dict,
                        aggregated_names,
                        namepart,
                        expected):
    aggregate_with(namepart_dict, aggregated_names, namepart)
    assert aggregated_names == expected, aggregated_names


# -------------------------------------------------
# Test decide_candidates
# -------------------------------------------------
def test_decide_candidates_no_candidates_copilot():
    reference = {
        "pageNo": 1,
        "sentenceNo": 5,
        "info": {
            "lastnames": "Doe",
            "firstnames": "John",
            "abbr_firstnames": "J.",
            "address": [],
            "titles": [],
            "occupations": [],
            "others": []
        },
        "pageNames": "Page1",
        "pid": "123",
        "positions": [10, 20],
        "articles": ["Article1"]
    }
    candidates = []
    aggregated_names = []

    decide_candidates(reference, candidates, aggregated_names)

    assert len(aggregated_names) == 1
    assert aggregated_names[0]["lastname"] == "Doe"
    assert ("John",) in aggregated_names[0]["firstname"]


def test_decide_candidates_single_best_candidate_copilot():
    reference = {
        "pageNo": 2,
        "sentenceNo": 10,
        "info": {
            "lastnames": "Smith",
            "firstnames": "Alice",
            "abbr_firstnames": "A.",
            "address": [],
            "titles": [],
            "occupations": [],
            "others": []
        },
        "pageNames": "Page2",
        "pid": "456",
        "positions": [30, 40],
        "articles": ["Article2"]
    }
    candidates = [
        {
            "lastname": "Smith",
            "firstname": {("Alice",)},
            "titles": {()},
            "address": {()},
            "profession": {()},
            "other": {()},
            "abbr_firstname": {("A.",)},
            "references": {
                (1, "Page1", "123"): [(5, [10, 20], ["Article1"])]
            }
        }
    ]
    aggregated_names = []

    decide_candidates(reference, candidates, aggregated_names)

    assert len(aggregated_names) == 0
    assert len(candidates[0]["references"]) == 2
    assert (2, "Page2", "456") in candidates[0]["references"]


def test_decide_candidates_multiple_candidates_copilot():
    reference = {
        "pageNo": 3,
        "sentenceNo": 15,
        "info": {
            "lastnames": "Brown",
            "firstnames": "Charlie",
            "abbr_firstnames": "C.",
            "address": [],
            "titles": [],
            "occupations": [],
            "others": []
        },
        "pageNames": "Page3",
        "pid": "789",
        "positions": [50, 60],
        "articles": ["Article3"]
    }
    candidates = [
        {
            "lastname": "Brown",
            "firstname": {("Charlie",)},
            "abbr_firstname": {("C.",)},
            "titles": {()},
            "address": {()},
            "profession": {()},
            "other": {()},
            "references": {
                (2, "Page2", "456"): [(10, [30, 40], ["Article2"])]
            }
        },
        {
            "lastname": "Brown",
            "firstname": {("Charlie",)},
            "abbr_firstname": {("C.",)},
            "titles": {()},
            "address": {()},
            "profession": {()},
            "other": {()},
            "references": {
                (1, "Page1", "123"): [(5, [10, 20], ["Article1"])]
            }
        }
    ]
    aggregated_names = []

    decide_candidates(reference, candidates, aggregated_names)

    assert len(aggregated_names) == 0
    assert len(candidates[0]["references"]) == 2
    assert (3, "Page3", "789") in candidates[0]["references"]
    assert len(candidates[1]["references"]) == 1


# -------------------------------------------------
# Test full_firstname_match
# -------------------------------------------------
@pytest.mark.parametrize(
  "reference, aggregated_names, expected",
  [({"info": {"lastnames": "Müller",
              "firstnames": "Maria",
              "abbr_firstnames": "",
              "titles": ["match_titles"],
              "address": ["match_address"],
              "occupations": ["match_occupations"],
              "others": ["match_others"]},
     "pageNo": 44,
     "sentenceNo": 55,
     "pageNames": "",
     "pid": "",
     "positions": "",
     "articles": "",
     'type': 'PER'
     },
    [{'firstname': {('Anna', 'Maria')},
      "lastname": "Müller",
      "abbr_firstname": set(),
      "titles": {("Frau", "Dr.")},
      "address": {("a", "b")},
      "profession": {("c", "d")},
      "other": {("e")},
      "references": {
               (4, "abc", 2): [(5, "123", "123"), (6, "456", "456")]
           }
      },
    {"firstname": {("Kat", "Man")},
     "lastname": "Bil",
     "abbr_firstname": set(),
     "titles": {("Herr", "Prof")},
     "address": {("a", "b")},
     "profession": {("c", "d")},
     "other": {},
     "references": {
              (4, "abc", 2): [(5, "123", "123"), (6, "456", "456")]
          }
     }],
      {'firstname': {('Anna', 'Maria')},
       'lastname': 'Müller',
       'abbr_firstname': set(),
       'titles': {('Frau', 'Dr.')},
       'address': {('a', 'b')},
       'profession': {('c', 'd')},
       'other': {'e'},
       'references': {(4, 'abc', 2): [(5, '123', '123'), (6, '456', '456')]}}
    ),
   ({"info": {"lastnames": "x",
              "firstnames": "Maria",
              "abbr_firstnames": "",
              "titles": ["match_titles"],
              "address": ["match_address"],
              "occupations": ["match_occupations"],
              "others": ["match_others"]},
     "pageNo": 44,
     "sentenceNo": 55,
     "pageNames": "",
     "pid": "",
     "positions": "",
     "articles": "",
     'type': 'PER'
     },
    [{'firstname': {('Anna', 'Maria')},
      "lastname": "Müller",
      "abbr_firstname": set(),
      "titles": {("Frau", "Dr.")},
      "address": {("a", "b")},
      "profession": {("c", "d")},
      "other": {("e")},
      "references": {
               (4, "abc", 2): [(5, "123", "123"), (6, "456", "456")]
           }
      },
    {"firstname": {("Kat", "Man")},
     "lastname": "Bil",
     "abbr_firstname": set(),
     "titles": {("Herr", "Prof")},
     "address": {("a", "b")},
     "profession": {("c", "d")},
     "other": {},
     "references": {
              (4, "abc", 2): [(5, "123", "123"), (6, "456", "456")]
          }
     }],
      None)
   ]
)
def test_full_firstname_match(reference,
                              aggregated_names,
                              expected):
    assert full_firstname_match(reference, aggregated_names) == expected


# -------------------------------------------------
# Test abbrev_firstname_match
# -------------------------------------------------
@pytest.mark.parametrize(
  "reference, aggregated_names, expected",
  [({"info": {"lastnames": "Müller",
              "firstnames": "",
              "abbr_firstnames": "M",
              "titles": ["match_titles"],
              "address": ["match_address"],
              "occupations": ["match_occupations"],
              "others": ["match_others"]},
     "pageNo": 44,
     "sentenceNo": 55,
     "pageNames": "",
     "pid": "",
     "positions": "",
     "articles": "",
     'type': 'PER'
     },
    [{'firstname': {('Anna', 'Maria')},
      "lastname": "Müller",
      "abbr_firstname": set(),
      "titles": {("Frau", "Dr.")},
      "address": {("a", "b")},
      "profession": {("c", "d")},
      "other": {("e")},
      "references": {
               (4, "abc", 2): [(5, "123", "123"), (6, "456", "456")]
           }
      },
    {"firstname": {("Kat", "Man")},
     "lastname": "Bil",
     "abbr_firstname": set(),
     "titles": {("Herr", "Prof")},
     "address": {("a", "b")},
     "profession": {("c", "d")},
     "other": {},
     "references": {
              (4, "abc", 2): [(5, "123", "123"), (6, "456", "456")]
          }
     }],
      [{'firstname': {('Anna', 'Maria')},
        'lastname': 'Müller',
        'abbr_firstname': set(),
        'titles': {('Frau', 'Dr.')},
        'address': {('a', 'b')},
        'profession': {('c', 'd')},
        'other': {'e'},
        'references': {
            (4, 'abc', 2): [(5, '123', '123'), (6, '456', '456')]}}]
    )]
)
def test_abbrev_firstname_match(reference,
                                aggregated_names,
                                expected):
    assert abbrev_firstname_match(reference, aggregated_names) == expected


# -------------------------------------------------
# Test only_lastname_match
# -------------------------------------------------
@pytest.mark.parametrize(
  "reference, aggregated_names, expected",
  [({"info": {"lastnames": "Müller", "firstnames": "x",
              "abbr_firstnames": "",
              "titles": "", "address": "", "occupations": "",
              "others": "e"},
     "pageNo": 4, "sentenceNo": 5, "pageNames": "", "pid": "",
     "positions": "", "articles": "", 'type': 'PER'
     },
    [{'firstname': {('Anna', 'Maria')},
      "lastname": "Müller",
      "abbr_firstname": set(),
      "titles": {("Frau", "Dr.")},
      "address": {("a", "b")},
      "profession": {("c", "d")},
      "other": {("e")},
      "references": {
               (4, "abc", 2): [(5, "123", "123"), (6, "456", "456")]
           }
      },
    {"firstname": {("Kat", "Man")},
     "lastname": "Bil",
     "abbr_firstname": set(),
     "titles": {("Herr", "Prof")},
     "address": {("a", "b")},
     "profession": {("c", "d")},
     "other": {},
     "references": {
              (4, "abc", 2): [(5, "123", "123"), (6, "456", "456")]
          }
     }],
      [{'firstname': {('Anna', 'Maria')},
        "lastname": "Müller",
        "abbr_firstname": set(),
        "titles": {("Frau", "Dr.")},
        "address": {("a", "b")},
        "profession": {("c", "d")},
        "other": {("e")},
        "references": {
                 (4, "abc", 2): [(5, "123", "123"), (6, "456", "456")]
             }
        }]
    )]
)
def test_only_lastname_match(reference,
                             aggregated_names,
                             expected):
    assert only_lastname_match(reference, aggregated_names) == expected


# -------------------------------------------------
# Test only_firstname_match
# -------------------------------------------------
@pytest.mark.parametrize(
  "reference, aggregated_names, expected",
  [({"info": {"lastnames": "z", "firstnames": "Anna",
              "abbr_firstnames": "",
              "titles": "", "address": "", "occupations": "",
              "others": "e"},
     "pageNo": 4, "sentenceNo": 5, "pageNames": "", "pid": "",
     "positions": "", "articles": "", 'type': 'PER'
     },
    [{'firstname': {('Anna', 'Maria')},
      "lastname": "Müller",
      "abbr_firstname": {("A")},
      "titles": {("Frau", "Dr.")},
      "address": {("a", "b")},
      "profession": {("c", "d")},
      "other": {("e")},
      "references": {
               (4, "abc", 2): [(5, "123", "123"), (6, "456", "456")]
           }
      },
    {"firstname": {("Kat", "Man")},
     "lastname": "Bil",
     "abbr_firstname": set(),
     "titles": {("Herr", "Prof")},
     "address": {("a", "b")},
     "profession": {("c", "d")},
     "other": {},
     "references": {
              (4, "abc", 2): [(5, "123", "123"), (6, "456", "456")]
          }
     }],
      [{'firstname': {('Anna', 'Maria')},
        "lastname": "Müller",
        "abbr_firstname": {("A")},
        "titles": {("Frau", "Dr.")},
        "address": {("a", "b")},
        "profession": {("c", "d")},
        "other": {("e")},
        "references": {
                 (4, "abc", 2): [(5, "123", "123"), (6, "456", "456")]
             }
        }]
    )]
)
def test_only_firstname_match(reference,
                              aggregated_names,
                              expected):
    assert only_firstname_match(reference, aggregated_names) == expected


# -------------------------------------------------
# Test only_abbrev_firstname_match
# -------------------------------------------------
@pytest.mark.parametrize(
  "reference, aggregated_names, expected",
  [({"info": {"lastnames": "z", "firstnames": "x",
              "abbr_firstnames": "A",
              "titles": "", "address": "", "occupations": "",
              "others": "e"},
     "pageNo": 4, "sentenceNo": 5, "pageNames": "", "pid": "",
     "positions": "", "articles": "", 'type': 'PER'
     },
    [{'firstname': {('Anna', 'Maria')},
      "lastname": "Müller",
      "abbr_firstname": {("A")},
      "titles": {("Frau", "Dr.")},
      "address": {("a", "b")},
      "profession": {("c", "d")},
      "other": {("e")},
      "references": {
               (4, "abc", 2): [(5, "123", "123"), (6, "456", "456")]
           }
      },
    {"firstname": {("Kat", "Man")},
     "lastname": "Bil",
     "abbr_firstname": set(),
     "titles": {("Herr", "Prof")},
     "address": {("a", "b")},
     "profession": {("c", "d")},
     "other": {},
     "references": {
              (4, "abc", 2): [(5, "123", "123"), (6, "456", "456")]
          }
     }],
      [{'firstname': {('Anna', 'Maria')},
        "lastname": "Müller",
        "abbr_firstname": {("A")},
        "titles": {("Frau", "Dr.")},
        "address": {("a", "b")},
        "profession": {("c", "d")},
        "other": {("e")},
        "references": {
                 (4, "abc", 2): [(5, "123", "123"), (6, "456", "456")]
             }
        }]
    )]
)
def test_only_abbrev_firstname_match(reference,
                                     aggregated_names,
                                     expected):
    assert only_abbrev_firstname_match(reference, aggregated_names) == expected


# -------------------------------------------------
# Test others_match
# -------------------------------------------------
@pytest.mark.parametrize(
  "reference, aggregated_names, expected",
  [({"info": {"lastnames": "z", "firstnames": "x",
              "abbr_firstnames": "y",
              "titles": "", "address": "", "occupations": "",
              "others": "e"},
     "pageNo": 4, "sentenceNo": 5, "pageNames": "", "pid": "",
     "positions": "", "articles": "", 'type': 'PER'},
    [{'firstname': {('Anna', 'Maria')},
      "lastname": "Müller",
      "abbr_firstname": set(),
      "titles": {("Frau", "Dr.")},
      "address": {("a", "b")},
      "profession": {("c", "d")},
      "other": {("e")},
      "references": {
               (4, "abc", 2): [(5, "123", "123"), (6, "456", "456")]
           }
      },
    {"firstname": {("Kat", "Man")},
     "lastname": "Bil",
     "abbr_firstname": set(()),
     "titles": {("Herr", "Prof")},
     "address": {("a", "b")},
     "profession": {("c", "d")},
     "other": {},
     "references": {
              (4, "abc", 2): [(5, "123", "123"), (6, "456", "456")]
          }
     }],
    [{'abbr_firstname': set(),
      'address': {('a', 'b')},
      'firstname': {('Anna', 'Maria')},
      'lastname': 'Müller',
      'other': {'e'},
      'profession': {('c', 'd')},
      'references': {(4, 'abc', 2): [(5, '123', '123'), (6, '456', '456')]},
      'titles': {('Frau', 'Dr.')}}])]
)
def test_others_match(reference, aggregated_names, expected):
    assert others_match(reference, aggregated_names) == expected


# -------------------------------------------------
# Test clean_up_aggregation
# -------------------------------------------------
@pytest.mark.parametrize(
  "aggregated_names, expected",
  [([{"firstname": {("Anna", "Maria"), ()},
      "lastname": "Müller",
      "abbr_firstname": {()},
      "titles": {("Dr.", "Frau")},
      "address": {("a", "b")},
      "profession": {("c", "d")},
      "other": {("e", None)},
      "references": {
               (4, "abc", 2): [(5, "123", "123"), (6, "456", "456")]
           }
      },
    {"firstname": {("Kat", "Man")},
      "lastname": "Bil",
      "abbr_firstname": "",
      "titles": {("Prof.", "Herr"), ()},
      "address": {("a", "b")},
      "profession": {("c", "d")},
      "other": {("e", None)},
      "references": {
               (4, "abc", 2): [(5, "123", "123"), (6, "456", "456")]
           }
     }],
    [{'abbr_firstname': [], 'address': ['a', 'b'],
      'firstname': ['Kat Man'], 'id': 0, 'lastname': 'Bil',
      'other': [('e', None)], 'profession': ['c', 'd'],
      'references': {
          'abc': {
              'elements': ['1', '2', '3', '4', '5', '6'],
              'pid': 2,
              'refs': [{'coords': '123', 'sent': 5},
                       {'coords': '456', 'sent': 6}]}},
      'titles': ['Herr Prof.']
      },
     {'abbr_firstname': [], 'address': ['a', 'b'],
      'firstname': ['Anna Maria'], 'id': 1, 'lastname': 'Müller',
      'other': [('e', None)], 'profession': ['c', 'd'],
      'references': {
        'abc': {
          'elements': ['1', '2', '3', '4', '5', '6'],
          'pid': 2,
          'refs': [{'coords': '123', 'sent': 5}, {'coords': '456', 'sent': 6}]
        }},
      'titles': ['Frau Dr.']
      }
     ])]
)
def test_clean_up_aggregation(aggregated_names, expected):
    res = clean_up_aggregation(aggregated_names)
    assert (res == expected)


# -------------------------------------------------
# Test map_genitive_versions
# -------------------------------------------------
@pytest.mark.parametrize(
  "all_names, lastname_dict, key, expected",
  [(["wyss", "müller", "krasniqi"],
    {"krasniqis": [{"info": {"lastnames": "krasniqis"}}],
     "müllers": [{"info": {"lastnames": "müllers"}}],
     "wyss": [{"info": {"lastnames": "wyss"}}]},
    "lastnames",
    {"krasniqis": [{"info": {"lastnames": "krasniqi"}}],
     "müllers": [{"info": {"lastnames": "müller"}}],
     "wyss": [{"info": {"lastnames": "wyss"}}]}
    )]
)
def test_map_genitive_versions(all_names, lastname_dict, key, expected):
    map_genitive_versions(all_names, lastname_dict, key)
    assert lastname_dict == expected


# -------------------------------------------------
# Test map_genitive_places
# -------------------------------------------------
@pytest.mark.parametrize(
  "all_names, place_list, expected",
  [
    (["zürich", "basel"],
     [{
      "tokens": ["ZÜRICHS"],
      "type": "LOC",
      "references": {
              (4, "abc", 2): [(5, "123", "123"), (6, "456", "456")]
          }
      },
      {
       "tokens": ["BASELS"],
       "type": "LOC",
       "references": {
               (7, "mnl", 8): [(10, "159", "159"), (11, "753", "753")]
           }
       }],
     [{
      'references': {
          (4, 'abc', 2): [(5, '123', '123'), (6, '456', '456')],
        },
      'tokens': ['ZÜRICH'],
      'type': 'LOC',
      },
      {
      'references': {
          (7, 'mnl', 8): [(10, '159', '159'), (11, '753', '753')],
        },
      'tokens': ['BASEL'],
      'type': 'LOC',
      }]),
    (["zürich", "basel"],
     [{
      "tokens": ["URIS"],
      "type": "LOC",
      "references": {
              (4, "abc", 2): [(5, "123", "123"), (6, "456", "456")]
          }
      }],
     [{
      "tokens": ["URIS"],
      "type": "LOC",
      "references": {
              (4, "abc", 2): [(5, "123", "123"), (6, "456", "456")]
          }
      }])
  ]
)
def test_map_genitive_places(all_names, place_list, expected):
    map_genitive_places(all_names, place_list)
    assert place_list == expected


# -------------------------------------------------
# Test find_place_match
# -------------------------------------------------
@pytest.mark.parametrize(
  "place_name, place_type, aggregated_places, expc",
  [
    ("zürich", "LOC",
     [{"tokens": ["ZÜRICH"],
       "type": "LOC",
       "references": {
               (4, "abc", 2): [(5, "123", "123"), (6, "456", "456")]
           }
       }],
     {
      'references': {
          (4, 'abc', 2): [(5, '123', '123'), (6, '456', '456')],
      },
      'tokens': ['ZÜRICH'],
      'type': 'LOC',
      }),
    ("basel", "LOC",
     [{"tokens": ["ZÜRICH"],
       "type": "LOC",
       "references": {
               (4, "abc", 2): [(5, "123", "123"), (6, "456", "456")]
           }
       }],
     False)
  ]
)
def test_find_place_match(place_name, place_type, aggregated_places,
                          expc):
    assert find_place_match(place_name, place_type, aggregated_places) == expc


# -------------------------------------------------
# Test aggregate_places
# -------------------------------------------------
@pytest.mark.parametrize(
  "all_places, aggregated_places, expected_all, expected_agg",
  [
    (
     [{"tokens": ["ZÜRICH"],
       "type": "LOC",
       "pageNo": 7,
       "pageNames": "efg",
       "pid": 8,
       "sentenceNo": 6,
       "positions": "456",
       "articles": "456"
       },
      {"tokens": ["BASEL"],
       "type": "LOC",
       "pageNo": 4,
       "pageNames": "abc",
       "pid": 5,
       "sentenceNo": 7,
       "positions": "123",
       "articles": "123"}],
     [{"tokens": ["ZÜRICH"],
       "type": "LOC",
       "references": {
               (4, "abc", 2): [(5, "123", "123"), (6, "456", "456")]
           }
       }],
     [{
      'articles': '456',
      'pageNames': 'efg',
      'pageNo': 7,
      'pid': 8,
      'positions': '456',
      'sentenceNo': 6,
      'tokens': ['ZÜRICH'],
      'type': 'LOC',
      },
      {
      'articles': '123',
      'pageNames': 'abc',
      'pageNo': 4,
      'pid': 5,
      'positions': '123',
      'sentenceNo': 7,
      'tokens': ['BASEL'],
      'type': 'LOC',
      }],
     [{
      'references': {
          (4, 'abc', 2): [(5, '123', '123'), (6, '456', '456')],
          (7, 'efg', 8): [(6, '456', '456')],
       },
      'tokens': ['ZÜRICH'],
      'type': 'LOC',
      },
      {'name': "Basel",
       'references': {
         (4, 'abc', 5): [(7, '123', '123')],
        },
       'tokens': ['BASEL'],
       'type': 'LOC',
       }]
    ),
  ]
)
def test_aggregate_places(all_places, aggregated_places,
                          expected_all, expected_agg):
    aggregate_places(all_places, aggregated_places)
    assert all_places == expected_all
    assert aggregated_places == expected_agg


# -------------------------------------------------
# Test aggregate_place
# -------------------------------------------------
@pytest.mark.parametrize(
  "found, place, expected",
  [
    (
     {"name": "Zürich",
      "tokens": ["ZÜRICH"],
      "type": "LOC",
      "references": {
              (4, "abc", 2): [(5, "123", "123")]  # (pageNo, pageNames, pid)
          }
      },
     {"name": "Zürich",
      "tokens": ["ZÜRICH"],
      "type": "LOC",
      "pageNo": 4,
      "pageNames": "abc",
      "pid": 2,
      "sentenceNo": 6,
      "positions": "456",
      "articles": "456"
      },
     {"name": "Zürich",
      "tokens": ["ZÜRICH"],
      "type": "LOC",
      "references": {
              (4, "abc", 2): [(5, "123", "123"), (6, "456", "456")]
          }
      }
    ),
    (
     {"name": "Zürich",
      "tokens": ["ZÜRICH"],
      "type": "LOC",
      "references": {
              (4, "abc", 2): [(5, "123", "123")]  # (pageNo, pageNames, pid)
          }
      },
     {"name": "Zürich",
      "tokens": ["ZÜRICH"],
      "type": "LOC",
      "pageNo": 7,
      "pageNames": "efg",
      "pid": 8,
      "sentenceNo": 6,
      "positions": "456",
      "articles": "456"
      },
     {"name": "Zürich",
      "tokens": ["ZÜRICH"],
      "type": "LOC",
      "references": {
              (4, "abc", 2): [(5, "123", "123")],
              (7, "efg", 8): [(6, "456", "456")]
          }
      }
    )
  ]
)
def test_aggregate_place(found, place, expected):
    aggregate_place(found, place)
    assert found == expected


# -------------------------------------------------
# Test create_new_aggregated_place
# -------------------------------------------------
@pytest.mark.parametrize(
  "reference, expected",
  [
    (
     {"tokens": ["ZÜRICH"],
      "type": "LOC",
      "pageNo": 4,
      "pageNames": "abc",
      "pid": 2,
      "sentenceNo": 5,
      "positions": "123",
      "articles": "123"
      },
     {"name": "Zürich",
      "tokens": ["ZÜRICH"],
      "type": "LOC",
      "references": {
              (4, "abc", 2): [(5, "123", "123")]
          }
      }
    )
  ]
)
def test_create_new_aggregated_place(reference, expected):
    assert create_new_aggregated_place(reference) == expected


# -------------------------------------------------
# Test clean_up_aggregation_places
# -------------------------------------------------
@pytest.mark.parametrize(
  "aggregated_places, last_index, expc",
  [
   (
    [{"name": "zurich", "references": {}},
     {"name": "basel", "references": {}}], 0,
    [{'name': 'basel', 'references': {}, 'id': 1},
     {'name': 'zurich', 'references': {}, 'id': 2}]
   ), (
    [{"name": "zurich", "references":
        {
          "ab1":
          [(0, "123", ["elem1", "elem2"]), (1, "456", ["elem1", "elem2"])]
        }
      },
     {"name": "zurich", "references":
        {
          "cd2":
          [(3, "789", ["elem1", "elem2"]), (4, "000", ["elem1", "elem2"])]
        }
      }], 5,
    [{'name': 'zurich', 'references':
      {
          'b':
          {
              'pid': '1', 'refs':
              [
                  {
                      'sent': 0, 'coords': '123'
                  }, {
                      'sent': 1, 'coords': '456'
                  }
              ],
              'elements':
              [
                  'elem1', 'elem2'
              ]
          }
      },
      'id': 6},
     {'name': 'zurich', 'references':
      {
          'd':
          {
              'pid': '2', 'refs':
              [
                  {
                      'sent': 3, 'coords': '789'
                  }, {
                      'sent': 4, 'coords': '000'
                  }
               ],
              'elements':
              [
                  'elem1', 'elem2'
              ]
           }
       },
      'id': 7}]
   ),
  ]
)
def test_clean_up_aggregation_places(aggregated_places, last_index, expc):
    assert clean_up_aggregation_places(aggregated_places, last_index) == expc


# -------------------------------------------------
# Test clean_lastname
# -------------------------------------------------
@pytest.mark.parametrize(
  "word, expected",
  [
    ("müller<---", "müller"),
    ("mülle<---r", "mülle<---r"),
    ("-----müller<   ---", "müller"),
    ("-----müller<   -r--", "müller<   -r"),
  ]
)
def test_clean_lastname(word, expected):
    assert clean_lastname(word) == expected


# -------------------------------------------------
# Test aggregate_names
# -------------------------------------------------
@pytest.mark.parametrize(
    "data, expected",
    [
     # If one of the firstnames matches, we match
     ([{'info': {
         'lastnames': ['Müller'], 'firstnames': ['Anne'],
         'abbr_firstnames': [], 'occupations': [], 'titles': [],
         'address': [], 'others': []}, 'pid': 1,
         'pageNames': 'abc-001_1234_123_0001.txt',
         'pageNo': 1, 'sentenceNo': 29,
         'positions': ['865,1781,49,22:main', '924,1780,100,23:main'],
         'type': 'PER', 'articles': []},
       {'info': {
         'lastnames': ['Müller'], 'firstnames': ['Anne', 'Marie'],
         'abbr_firstnames': [], 'occupations': [], 'titles': [],
         'address': [], 'others': []}, 'pid': 1,
         'pageNames': 'abc-001_1234_123_0001.txt', 'pageNo': 1,
         'sentenceNo': 30,
         'positions': [
            '789,2016,48,22:main',
            '847,2013,65,30:main',
            '920,2014,101,24:main'],
         'type': 'PER', 'articles': []}
       ],
      [{'lastname': 'Müller', 'firstname': ['Anne', 'Anne Marie'],
        'abbr_firstname': [], 'address': [], 'titles': [], 'profession': [],
        'other': [],
        'references': {
            'abc-001_1234_123_0001.txt': {
                'pid': 1,
                'refs': [
                   {'sent': 29,
                    'coords': ['865,1781,49,22:main', '924,1780,100,23:main']},
                   {'sent': 30,
                    'coords': ['789,2016,48,22:main', '847,2013,65,30:main',
                               '920,2014,101,24:main']}],
                'elements': []}},
        'type': 'PER', 'id': 0}]),
     # if we have the genetiv version, we clean it up and still match
     ([{'info': {
         'lastnames': ['Müller'], 'firstnames': ['Maria'],
         'abbr_firstnames': [], 'occupations': [], 'titles': [],
         'address': [], 'others': []}, 'pid': 1,
         'pageNames': 'abc-001_1234_123_0001.txt',
         'pageNo': 1, 'sentenceNo': 29,
         'positions': ['865,1781,49,22:main', '924,1780,100,23:main'],
         'type': 'PER', 'articles': []},
       {'info': {
         'lastnames': ['Müllers'], 'firstnames': ['Maria'],
         'abbr_firstnames': [], 'occupations': [], 'titles': [],
         'address': [], 'others': []}, 'pid': 1,
         'pageNames': 'abc-001_1234_123_0001.txt',
         'pageNo': 1, 'sentenceNo': 30,
         'positions': ['789,2016,48,22:main', '847,2013,65,30:main',
                       '920,2014,101,24:main'],
         'type': 'PER', 'articles': []}
       ],
      [{'lastname': 'Müller', 'firstname': ['Maria'], 'abbr_firstname': [],
        'address': [], 'titles': [], 'profession': [], 'other': [],
        'references': {
            'abc-001_1234_123_0001.txt': {
               'pid': 1,
               'refs': [
                   {'sent': 29,
                    'coords': ['865,1781,49,22:main', '924,1780,100,23:main']},
                   {'sent': 30,
                    'coords': ['789,2016,48,22:main', '847,2013,65,30:main',
                               '920,2014,101,24:main']}],
               'elements': []}},
        'type': 'PER',
        'id': 0}]),
     # page number, page name, pid do not matter if both firstname
     # and lastname match, we match all mentions within a magazine-year
     ([{'info': {
         'lastnames': ['Müller'], 'firstnames': ['Maria'],
         'abbr_firstnames': [], 'occupations': [], 'titles': [],
         'address': [], 'others': []}, 'pid': 1,
         'pageNames': 'abc-001_1234_123_0001.txt', 'pageNo': 1,
         'sentenceNo': 29, 'positions': ['865,1781,49,22:main',
                                         '924,1780,100,23:main'],
         'type': 'PER', 'articles': []},
       {'info': {
           'lastnames': ['Müllers'], 'firstnames': ['Maria'],
           'abbr_firstnames': [], 'occupations': [], 'titles': [],
           'address': [], 'others': []}, 'pid': 100,
           'pageNames': 'abc-001_1234_123_0100.txt', 'pageNo': 100,
           'sentenceNo': 30,
           'positions': ['789,2016,48,22:main', '847,2013,65,30:main',
                         '920,2014,101,24:main'],
           'type': 'PER', 'articles': []}
       ],
      [{'lastname': 'Müller', 'firstname': ['Maria'], 'abbr_firstname': [],
        'address': [], 'titles': [], 'profession': [], 'other': [],
        'references': {
           'abc-001_1234_123_0001.txt': {
              'pid': 1,
              'refs': [
                  {'sent': 29,
                   'coords': ['865,1781,49,22:main', '924,1780,100,23:main']}],
              'elements': []},
           'abc-001_1234_123_0100.txt': {
              'pid': 100,
              'refs': [
                  {'sent': 30,
                   'coords': ['789,2016,48,22:main', '847,2013,65,30:main',
                              '920,2014,101,24:main']}],
              'elements': []}},
        'type': 'PER', 'id': 0}]),
     # even if the names are close, we do not match if the names don't match
     ([{'info': {
         'lastnames': ['Müller'], 'firstnames': ['Maria'],
         'abbr_firstnames': [], 'occupations': [], 'titles': [],
         'address': [], 'others': []}, 'pid': 1,
         'pageNames': 'abc-001_1234_123_0001.txt', 'pageNo': 1,
         'sentenceNo': 29, 'positions': ['865,1781,49,22:main',
                                         '924,1780,100,23:main'],
        'type': 'PER', 'articles': []},
      {'info': {
          'lastnames': ['Müller'], 'firstnames': ['Meria'],
          'abbr_firstnames': [], 'occupations': [], 'titles': [],
          'address': [], 'others': []}, 'pid': 1,
          'pageNames': 'abc-001_1234_123_0001.txt',
          'pageNo': 1, 'sentenceNo': 30,
          'positions': ['789,2016,48,22:main', '847,2013,65,30:main',
                        '920,2014,101,24:main'],
          'type': 'PER', 'articles': []}
       ],
      [{'lastname': 'Müller', 'firstname': ['Maria'], 'abbr_firstname': [],
        'address': [], 'titles': [], 'profession': [], 'other': [],
        'references': {
            'abc-001_1234_123_0001.txt': {
              'pid': 1,
              'refs': [
                  {'sent': 29,
                   'coords': ['865,1781,49,22:main', '924,1780,100,23:main']}],
              'elements': []}},
        'type': 'PER', 'id': 0},
       {'lastname': 'Müller', 'firstname': ['Meria'], 'abbr_firstname': [],
        'address': [], 'titles': [], 'profession': [], 'other': [],
        'references': {
            'abc-001_1234_123_0001.txt': {
                'pid': 1,
                'refs': [
                    {'sent': 30,
                     'coords': ['789,2016,48,22:main', '847,2013,65,30:main',
                                '920,2014,101,24:main']}],
                'elements': []}},
        'type': 'PER', 'id': 1}]),
     # if the lastname matches the firstnames don't contradict each other,
     # and we're closer than to any other person, we match.
     ([{'info': {
         'lastnames': ['Müller'], 'firstnames': ['Maria'],
         'abbr_firstnames': [], 'occupations': [], 'titles': [],
         'address': [], 'others': []}, 'pid': 1,
         'pageNames': 'abc-001_1234_123_0001.txt', 'pageNo': 1,
         'sentenceNo': 29, 'positions': ['865,1781,49,22:main',
                                         '924,1780,100,23:main'],
         'type': 'PER', 'articles': []},
      {'info': {
          'lastnames': ['Müller'], 'firstnames': [''], 'abbr_firstnames': [],
          'occupations': [], 'titles': [], 'address': [], 'others': []},
          'pid': 1, 'pageNames': 'abc-001_1234_123_0001.txt', 'pageNo': 1,
          'sentenceNo': 30,
          'positions': ['789,2016,48,22:main', '847,2013,65,30:main',
                        '920,2014,101,24:main'],
          'type': 'PER', 'articles': []}
       ],
      [{'lastname': 'Müller', 'firstname': ['Maria'], 'abbr_firstname': [],
        'address': [], 'titles': [], 'profession': [], 'other': [],
        'references': {
           'abc-001_1234_123_0001.txt': {
               'pid': 1,
               'refs': [
                   {'sent': 29,
                    'coords': ['865,1781,49,22:main', '924,1780,100,23:main']},
                   {'sent': 30,
                    'coords': ['789,2016,48,22:main', '847,2013,65,30:main',
                               '920,2014,101,24:main']}],
               'elements': []}},
        'type': 'PER', 'id': 0}]),
     # the second occurrence of Müller is matched to martin instead of maria
     # because we go through the people and ONLY match with previous
     # occurrences, never with future ones.
     # this is intended behavior, but should it be? TODO
     ([{'info': {
         'lastnames': ['Müller'], 'firstnames': ['Martin'],
         'abbr_firstnames': [], 'occupations': [], 'titles': [],
         'address': [], 'others': []}, 'pid': 9,
         'pageNames': 'abc-001_1234_123_0009.txt', 'pageNo': 9,
         'sentenceNo': 27, 'positions': ['865,1781,49,22:main',
                                         '924,1780,100,23:main'],
         'type': 'PER', 'articles': []},
       {'info': {
           'lastnames': ['Müller'], 'firstnames': [''], 'abbr_firstnames': [],
           'occupations': [], 'titles': [], 'address': [], 'others': []},
           'pid': 10, 'pageNames': 'abc-001_1234_123_0010.txt', 'pageNo': 10,
           'sentenceNo': 28,
           'positions': ['789,2016,48,22:main', '847,2013,65,30:main',
                         '920,2014,101,24:main'],
           'type': 'PER', 'articles': []},
       {'info': {
           'lastnames': ['Müller'], 'firstnames': ['Maria'],
           'abbr_firstnames': [], 'occupations': [], 'titles': [],
           'address': [], 'others': []}, 'pid': 11,
           'pageNames': 'abc-001_1234_123_0011.txt', 'pageNo': 11,
           'sentenceNo': 29,
           'positions': ['865,1781,49,22:main', '924,1780,100,23:main'],
           'type': 'PER', 'articles': []}
       ],
      [{'lastname': 'Müller', 'firstname': ['Maria'], 'abbr_firstname': [],
        'address': [], 'titles': [], 'profession': [], 'other': [],
        'references': {
            'abc-001_1234_123_0011.txt': {
              'pid': 11,
              'refs': [
                  {'sent': 29,
                   'coords': ['865,1781,49,22:main', '924,1780,100,23:main']}],
              'elements': []}},
        'type': 'PER', 'id': 0},
       {'lastname': 'Müller', 'firstname': ['Martin'], 'abbr_firstname': [],
        'address': [], 'titles': [], 'profession': [], 'other': [],
        'references': {
            'abc-001_1234_123_0009.txt': {
              'pid': 9,
              'refs': [
                  {'sent': 27,
                   'coords': ['865,1781,49,22:main', '924,1780,100,23:main']}],
              'elements': []},
            'abc-001_1234_123_0010.txt': {
                'pid': 10,
                'refs': [
                    {'sent': 28,
                     'coords': ['789,2016,48,22:main', '847,2013,65,30:main',
                                '920,2014,101,24:main']}],
                'elements': []}},
        'type': 'PER', 'id': 1}]),
     # abbreviated firstnames and same lastnames are matched.
     ([{'info': {
         'lastnames': ['Müller'], 'firstnames': ['Maria'],
         'abbr_firstnames': [], 'occupations': [], 'titles': [],
         'address': [], 'others': []}, 'pid': 1,
         'pageNames': 'abc-001_1234_123_0001.txt', 'pageNo': 1,
         'sentenceNo': 29, 'positions': ['865,1781,49,22:main',
                                         '924,1780,100,23:main'],
         'type': 'PER', 'articles': []},
      {'info': {
          'lastnames': ['Müller'], 'firstnames': [], 'abbr_firstnames': ["M."],
          'occupations': [], 'titles': [], 'address': [], 'others': []},
          'pid': 1, 'pageNames': 'abc-001_1234_123_0001.txt', 'pageNo': 1,
          'sentenceNo': 30,
          'positions': ['789,2016,48,22:main', '847,2013,65,30:main',
                        '920,2014,101,24:main'],
          'type': 'PER', 'articles': []}
       ],
      [{'lastname': 'Müller', 'firstname': ['Maria'], 'abbr_firstname': ['M.'],
        'address': [], 'titles': [], 'profession': [], 'other': [],
        'references': {
            'abc-001_1234_123_0001.txt': {
                'pid': 1, 'refs': [
                   {'sent': 29,
                    'coords': ['865,1781,49,22:main', '924,1780,100,23:main']},
                   {'sent': 30,
                    'coords': ['789,2016,48,22:main', '847,2013,65,30:main',
                               '920,2014,101,24:main']}],
                'elements': []}},
        'type': 'PER', 'id': 0}]),
     # same firstnames and not conflicing lastnames are matched.
     ([{'info': {
         'lastnames': [], 'firstnames': ['Maria'],
         'abbr_firstnames': [], 'occupations': [], 'titles': [],
         'address': [], 'others': []}, 'pid': 1,
         'pageNames': 'abc-001_1234_123_0001.txt', 'pageNo': 1,
         'sentenceNo': 29, 'positions': ['865,1781,49,22:main',
                                         '924,1780,100,23:main'],
         'type': 'PER', 'articles': []},
       {'info': {
           'lastnames': [], 'firstnames': ["Maria"], 'abbr_firstnames': [],
           'occupations': [], 'titles': [], 'address': [], 'others': []},
           'pid': 100, 'pageNames': 'abc-001_1234_123_0100.txt', 'pageNo': 100,
           'sentenceNo': 30,
           'positions': ['789,2016,48,22:main', '847,2013,65,30:main',
                         '920,2014,101,24:main'],
           'type': 'PER', 'articles': []}
       ],
      [{'lastname': '', 'firstname': ['Maria'], 'abbr_firstname': [],
        'address': [], 'titles': [], 'profession': [], 'other': [],
        'references': {
            'abc-001_1234_123_0001.txt': {
              'pid': 1, 'refs': [
                  {'sent': 29,
                   'coords': ['865,1781,49,22:main', '924,1780,100,23:main']}],
              'elements': []},
            'abc-001_1234_123_0100.txt': {
              'pid': 100, 'refs': [
                  {'sent': 30,
                   'coords': ['789,2016,48,22:main', '847,2013,65,30:main',
                              '920,2014,101,24:main']}],
              'elements': []}},
        'type': 'PER', 'id': 0}]),
     # same abbreviated firstnames and not conflicing lastnames are matched.
     # even if the firstnames do not match, which is intended behavior
     # but should it be? TODO
     ([{'info': {
         'lastnames': [], 'firstnames': ['Maria'],
         'abbr_firstnames': ["A."], 'occupations': [], 'titles': [],
         'address': [], 'others': []}, 'pid': 1,
         'pageNames': 'abc-001_1234_123_0001.txt', 'pageNo': 1,
         'sentenceNo': 29, 'positions': ['865,1781,49,22:main',
                                         '924,1780,100,23:main'],
         'type': 'PER', 'articles': []},
       {'info': {
           'lastnames': [], 'firstnames': [], 'abbr_firstnames': ["A."],
           'occupations': [], 'titles': [], 'address': [], 'others': []},
           'pid': 100, 'pageNames': 'abc-001_1234_123_0100.txt', 'pageNo': 100,
           'sentenceNo': 30,
           'positions': ['789,2016,48,22:main', '847,2013,65,30:main',
                         '920,2014,101,24:main'],
           'type': 'PER', 'articles': []}
       ],
      [{'lastname': '', 'firstname': ['Maria'], 'abbr_firstname': ["A."],
        'address': [], 'titles': [], 'profession': [], 'other': [],
        'references': {
            'abc-001_1234_123_0001.txt': {
              'pid': 1, 'refs': [
                  {'sent': 29,
                   'coords': ['865,1781,49,22:main', '924,1780,100,23:main']}],
              'elements': []},
            'abc-001_1234_123_0100.txt': {
               'pid': 100, 'refs': [
                  {'sent': 30,
                   'coords': ['789,2016,48,22:main', '847,2013,65,30:main',
                              '920,2014,101,24:main']}],
               'elements': []}},
        'type': 'PER', 'id': 0}]),
     # same other and non-conflicting names are matched
     ([{'info': {
         'lastnames': [], 'firstnames': [], 'abbr_firstnames': [],
         'occupations': [], 'titles': [], 'address': [], 'others': ["B"]},
         'pid': 1, 'pageNames': 'abc-001_1234_123_0001.txt', 'pageNo': 1,
         'sentenceNo': 29, 'positions': ['865,1781,49,22:main',
                                         '924,1780,100,23:main'],
         'type': 'PER', 'articles': []},
       {'info': {
           'lastnames': [], 'firstnames': [], 'abbr_firstnames': [],
           'occupations': [], 'titles': [], 'address': [], 'others': ["B"]},
           'pid': 100, 'pageNames': 'abc-001_1234_123_0100.txt', 'pageNo': 100,
           'sentenceNo': 30,
           'positions': ['789,2016,48,22:main', '847,2013,65,30:main',
                         '920,2014,101,24:main'],
           'type': 'PER', 'articles': []}
       ],
      [{'lastname': '', 'firstname': [], 'abbr_firstname': [], 'address': [],
        'titles': [], 'profession': [], 'other': [('B',)],
        'references': {
            'abc-001_1234_123_0001.txt': {
              'pid': 1, 'refs': [
                  {'sent': 29,
                   'coords': ['865,1781,49,22:main', '924,1780,100,23:main']}],
              'elements': []},
            'abc-001_1234_123_0100.txt': {
              'pid': 100, 'refs': [
                  {'sent': 30,
                   'coords': ['789,2016,48,22:main', '847,2013,65,30:main',
                              '920,2014,101,24:main']}],
              'elements': []}},
        'type': 'PER', 'id': 0}]),
    ]
)
def test_aggregate_names(data, expected):
    """
    """
    res = aggregate_names(data)

    for entry in res:
        entry.pop("id")  # id depends on the order

    for entry in expected:  # the order is not deterministic
        entry.pop("id")
        assert entry in res


# -------------------------------------------------
# Test execute_aggregation
# -------------------------------------------------
def test_execute_aggregation():
    data = [
        (2025, [
            {
                "info": {
                    "lastnames": ["Doe"],
                    "firstnames": ["John"],
                    "abbr_firstnames": ["J."],
                    "address": ["123 Main St"],
                    "titles": ["Dr."],
                    "occupations": ["Engineer"],
                    "others": ["AdditionalInfo"]
                },
                "pageNo": 1,
                "pageNames": "Page1",
                "pid": "pid1",
                "sentenceNo": 5,
                "positions": "pos1",
                "articles": ["article1"]
            },
            {
                "info": {
                    "lastnames": ["Doe"],
                    "firstnames": [""],
                    "abbr_firstnames": ["J."],
                    "address": [""],
                    "titles": [""],
                    "occupations": [""],
                    "others": [""]
                },
                "pageNo": 3,
                "pageNames": "Page3",
                "pid": "pid3",
                "sentenceNo": 20,
                "positions": "pos5",
                "articles": ["article4"]
            }
        ])
    ]

    result = execute_aggregation(data)

    assert 2025 in result
    assert len(result[2025]) == 1
    aggregated_unit = result[2025][0]
    assert aggregated_unit["lastname"] == "Doe"
    assert aggregated_unit["firstname"] == ["John"]
    assert aggregated_unit["abbr_firstname"] == ["J."]
    assert aggregated_unit["address"] == ["123 Main St"]
    assert set(aggregated_unit["titles"]) == set(["", "Dr."])
    assert aggregated_unit["profession"] == ["Engineer"]
    assert set(aggregated_unit["other"]) == set([("AdditionalInfo",), ("",)])
    assert aggregated_unit["references"] == {
        "Page1": {
            "pid": "pid1",
            "refs": [{"sent": 5, "coords": "pos1"}],
            "elements": ["article1"]
        },
        "Page3": {
            "pid": "pid3",
            "refs": [{"sent": 20, "coords": "pos5"}],
            "elements": ["article4"]
        }
    }


# -------------------------------------------------
# Test aggregate_and_save_data_timed
# -------------------------------------------------
def test_aggregate_and_save_data_timed():
    with pytest.raises(Exception) as excinfo:
        aggregate_and_save_data_timed([], {}, "agg,link")
    assert str(excinfo.value) == "'post,agg,link' must be called together"
