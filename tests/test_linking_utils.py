import pytest
from unittest.mock import patch, MagicMock

from utility.linking_utils import (
    prep_name_for_elasticsearch_query,
    search_person_gnd,
    convert_dates,
    get_wikidata_value,
    convert_wikidata_format_kibana,
    convert_gnd_format_kibana,
    search_person_wikidata
)


# -------------------------------------------------
# 1. Test prep_name_for_elasticsearch_query
# -------------------------------------------------
@pytest.mark.parametrize(
    "name,expected",
    [
        ("D. Birchall", 'D* Birchall~2'),
        ("J.F. Bitschnau", 'J*F* Bitschnau~2'),
        ("Viktor Amadeus", 'Viktor~2 Amadeus~2'),
        (" Hiilimann", 'Hiilimann~2'),
        ("Urs fosef Cavelti", 'Urs~1 fosef~1 Cavelti~2'),
        # his name is actually Urs Josef Cavelti
        ("David", "David~1")
    ],
)
def test_prep_name_for_elasticsearch_query(name, expected):
    """
    This is just a function to prepare the search terms for the
    elasticsearch queries.
    """
    assert prep_name_for_elasticsearch_query(name) == expected


# -------------------------------------------------
# 2. Test search_person_gnd
# -------------------------------------------------
@pytest.mark.parametrize(
    "fnames, lastname, gnd_limit, expected, get_res",
    [(["Albert"], "Einstein", 0, {}, {}),
     (["D."], "Birchall", 15,
      {'171726375': {'gid': {'171726375'},
                     'prefForename': {'David'},
                     'prefSurname': {'Birchall'},
                     'varForename': {'D.', 'D. W.', 'David W.'},
                     'varSurname': {'Birchall'},
                     'academic': {'Prof. em.'},
                     'desc': {
                         'Henley Management College, \
Henley Business School, Univ. of Reading'
                      },
                     'score': 13.893601},
       '1089259662': {'gid': {'1089259662'},
                      'prefForename': {'J. D.'},
                      'prefSurname': {'Birchall'},
                      'desc': {'Chemiker, USA'},
                      'score': 13.893601},
       '171776313': {'gid': {'171776313'},
                     'prefForename': {'Sérgio de Oliveira'},
                     'prefSurname': {'Birchal'},
                     'varForename': {'Sérgio'},
                     'varSurname': {'Oliveira Birchal'},
                     'birthdate': {'1959'},
                     'desc': {'UNA School of Business, \
Belo Horizonte, Brazil (1999)'},
                     'score': 12.051659},
       '1016708696': {'gid': {'1016708696'},
                      'prefForename': {'Alice de Souza'},
                      'prefSurname': {'Birchal'},
                      'varForename': {'Alice', 'Alice de'},
                      'varSurname': {'De Souza Birchal', 'Souza Birchal'},
                      'desc': {'Brasilian. Juristin, \
Spez. Familien- u. Erbrecht'},
                      'score': 12.051659},
       '129263265': {'gid': {'129263265'},
                     'prefForename': {'Derek'},
                     'prefSurname': {'Birdsall'},
                     'birthdate': {'1934'},
                     'score': 10.670202},
       '1020064781': {'gid': {'1020064781'},
                      'prefForename': {'Dean R.'},
                      'prefSurname': {'Brimhall'},
                      'birthdate': {'1886'},
                      'score': 10.670202},
       '1089356234': {'gid': {'1089356234'},
                      'prefForename': {'Derek'},
                      'prefSurname': {'Birdsall'},
                      'desc': {'Graphiker'},
                      'score': 10.670202},
       '1102224219': {'gid': {'1102224219'},
                      'prefForename': {'David'},
                      'prefSurname': {'Burchell'},
                      'score': 10.670202},
       '1119113008': {'gid': {'1119113008'},
                      'prefForename': {'Douglas'},
                      'prefSurname': {'Birdsall'},
                      'activeperiod': {'ca. 21. Jh.'},
                      'desc': {'Chairman of the Third Lausanne Congress, \
Cape Town 2010'},
                      'score': 10.670202},
       '1158133847': {'gid': {'1158133847'},
                      'prefForename': {'David Lyn'},
                      'prefSurname': {'Birdsall'},
                      'varForename': {'David', 'David L.'},
                      'varSurname': {'Birdsall'},
                      'score': 10.670202}},
      {'hits': {
             'hits': [
                 {'_index': 'gnd',
                  '_id': '171726375',
                  '_score': 13.893601,
                  '_source': {
                      'GND_ID': ['171726375'],
                      'Forenames': ['David'],
                      'Surnames': ['Birchall'],
                      'VariantForenames': ['D. W.', 'David W.', 'D.'],
                      'VariantSurnames': ['Birchall'],
                      'Academics': ['Prof. em.'],
                      'Descriptions': [
                          'Henley Management College, \
Henley Business School, Univ. of Reading'
                      ]}
                  },
                 {'_index': 'gnd',
                  '_id': '1089259662',
                  '_score': 13.893601,
                  '_source': {
                      'GND_ID': ['1089259662'],
                      'Forenames': ['J. D.'],
                      'Surnames': ['Birchall'],
                      'Descriptions': ['Chemiker, USA']}
                  },
                 {'_index': 'gnd',
                  '_id': '171776313',
                  '_score': 12.051659,
                  '_source': {
                      'GND_ID': ['171776313'],
                      'Forenames': ['Sérgio de Oliveira'],
                      'Surnames': ['Birchal'],
                      'VariantForenames': ['Sérgio'],
                      'VariantPrefixes': ['de'],
                      'VariantSurnames': ['Oliveira Birchal'],
                      'Descriptions': [
                          'UNA School of Business, \
Belo Horizonte, Brazil (1999)'
                      ],
                      'Birthdate': ['1959']}
                  },
                 {'_index': 'gnd',
                  '_id': '1016708696',
                  '_score': 12.051659,
                  '_source': {
                      'GND_ID': ['1016708696'],
                      'Forenames': ['Alice de Souza'],
                      'Surnames': ['Birchal'],
                      'VariantForenames': ['Alice de', 'Alice'],
                      'VariantSurnames': ['Souza Birchal', 'De Souza Birchal'],
                      'Descriptions': [
                          'Brasilian. Juristin, Spez. Familien- u. Erbrecht'
                      ]}
                  },
                 {'_index': 'gnd',
                  '_id': '129263265',
                  '_score': 10.670202,
                  '_source': {
                      'GND_ID': ['129263265'],
                      'Forenames': ['Derek'],
                      'Surnames': ['Birdsall'],
                      'Birthdate': ['1934']}
                  },
                 {'_index': 'gnd',
                  '_id': '1020064781',
                  '_score': 10.670202,
                  '_source': {
                      'GND_ID': ['1020064781'],
                      'Forenames': ['Dean R.'],
                      'Surnames': ['Brimhall'],
                      'Birthdate': ['1886']}
                  },
                 {'_index': 'gnd',
                  '_id': '1089356234',
                  '_score': 10.670202,
                  '_source': {
                      'GND_ID': ['1089356234'],
                      'Forenames': ['Derek'],
                      'Surnames': ['Birdsall'],
                      'Descriptions': ['Graphiker']}
                  },
                 {'_index': 'gnd',
                  '_id': '1102224219',
                  '_score': 10.670202,
                  '_source': {
                      'GND_ID': ['1102224219'],
                      'Forenames': ['David'],
                      'Surnames': ['Burchell']}
                  },
                 {'_index': 'gnd',
                  '_id': '1119113008',
                  '_score': 10.670202,
                  '_source': {
                      'GND_ID': ['1119113008'],
                      'Forenames': ['Douglas'],
                      'Surnames': ['Birdsall'],
                      'Activeperiods': ['ca. 21. Jh.'],
                      'Descriptions': [
                          'Chairman of the Third Lausanne Congress, \
Cape Town 2010'
                      ]}
                  },
                 {'_index': 'gnd',
                  '_id': '1158133847',
                  '_score': 10.670202,
                  '_source': {
                      'GND_ID': ['1158133847'],
                      'Forenames': ['David Lyn'],
                      'Surnames': ['Birdsall'],
                      'VariantForenames': ['David', 'David L.'],
                      'VariantSurnames': ['Birdsall']}
                  }
             ]
         }
       }
      ),
     (["J.F."], "Bitschnau", 15,
      {'1033767735': {'gid': {'1033767735'},
                      'prefForename': {'Josef'},
                      'prefSurname': {'Bitschnau'},
                      'birthdate': {'1925-10-10'},
                      'score': 13.787728},
       '1065067526': {'gid': {'1065067526'},
                      'prefForename': {'Johann Josef'},
                      'prefSurname': {'Bitschnau'},
                      'academic': {'Dr.jur.et med.'},
                      'birthdate': {'1776'},
                      'deathdate': {'1819'},
                      'score': 13.787728}},
      {'hits': {
          'hits': [
              {'_index': 'gnd',
               '_id': '1033767735',
               '_score': 13.787728,
               '_source': {
                   'GND_ID': ['1033767735'],
                   'Forenames': ['Josef'],
                   'Surnames': ['Bitschnau'],
                   'Birthdate': ['1925-10-10']}
               },
              {'_index': 'gnd',
               '_id': '1065067526',
               '_score': 13.787728,
               '_source': {
                   'GND_ID': ['1065067526'],
                   'Forenames': ['Johann Josef'],
                   'Surnames': ['Bitschnau'],
                   'Academics': ['Dr.jur.et med.'],
                   'Birthdate': ['1776'],
                   'Deathdate': ['1819']}
               }
            ]
      }}
      ),
     (["Viktor"], "Amadeus", 15,
      {'1056411104': {'gid': {'1056411104'},
                      'prefForename': {'Victor Oliveira'},
                      'prefSurname': {'Mateus'},
                      'varForename': {'Victor'},
                      'varSurname': {'Oliveira Mateus'},
                      'desc': {'geb. in Lissabon', ' Philosoph u. Dichter'},
                      'score': 12.636148}},
      {'hits': {
          'hits': [
              {'_index': 'gnd',
               '_id': '1056411104',
               '_score': 12.636148,
               '_source': {
                   'GND_ID': ['1056411104'],
                   'Forenames': ['Victor Oliveira'],
                   'Surnames': ['Mateus'],
                   'VariantForenames': ['Victor'],
                   'VariantSurnames': ['Oliveira Mateus'],
                   'Descriptions': [
                       'geb. in Lissabon', ' Philosoph u. Dichter'
                    ]
                }
               }
          ]
        }
       }
      ),
     ([""], " Hiilimann", 15,
      {'1147518866': {'gid': {'1147518866'},
                      'prefForename': {'Charles'},
                      'prefSurname': {'Hirlimann'},
                      'birthdate': {'1947'},
                      'score': 9.743573},
       '105795291': {'gid': {'105795291'},
                     'prefForename': {'Felix'},
                     'prefSurname': {'Heinimann'},
                     'varForename': {'Felix'},
                     'varSurname': {'Heinimann-Lienhard'},
                     'academic': {'Prof. Dr.'},
                     'birthdate': {'1915-07-13'},
                     'deathdate': {'2006-01-23'},
                     'desc': {'Schweiz. Klassischer Philologe und Lehrer an \
diversen Schulen in Basel, Aarau, Solothurn, Biel'},
                     'score': 8.650627},
       '109865308': {'gid': {'109865308'},
                     'prefForename': {'Ullrich'},
                     'prefSurname': {'Heilemann'},
                     'varForename': {'Ulrich'},
                     'varSurname': {'Heilemann'},
                     'academic': {'Prof. Dr. rer. pol. em.'},
                     'affiliationLiteral': {
                         'Institut für Empirische Wirtschaftsforschung Leipzig'
                      },
                     'birthdate': {'1944'},
                     'score': 8.650627},
       '110821734': {'gid': {'110821734'},
                     'prefForename': {'Michael'},
                     'prefSurname': {'Heilemann'},
                     'birthdate': {'1953'},
                     'desc': {'Promovierter Psychologischer Psychotherapeut'},
                     'score': 8.650627},
       '115824839': {'gid': {'115824839'},
                     'prefForename': {'Christoph'},
                     'prefSurname': {'Hürlimann'},
                     'birthdate': {'1938'},
                     'desc': {'Theologe', ' Schriftsteller'},
                     'score': 8.650627},
       '11665144X': {'gid': {'11665144X'},
                     'prefForename': {'Ernst'},
                     'prefSurname': {'Heilemann'},
                     'varForename': {'E.'},
                     'varSurname': {'Heilemann'},
                     'deathplaceLiteral': {'Kitchener (Ontario)'},
                     'birthdate': {'1870-08-08'},
                     'deathdate': {'1936-04-09'},
                     'score': 8.650627},
       '117050873': {'gid': {'117050873'},
                     'prefForename': {'Heinrich Otto'},
                     'prefSurname': {'Hürlimann'},
                     'birthdate': {'1900-06-16'},
                     'deathdate': {'1964-01-13'},
                     'score': 8.650627},
       '118554425': {'gid': {'118554425'},
                     'prefForename': {'Hans'},
                     'prefSurname': {'Hürlimann'},
                     'birthdate': {'1918-04-06'},
                     'deathdate': {'1994-02-22'},
                     'desc': {
                         'Bundesrat 1973-1982 (Innenminister, Bildungs- und \
Forschungsminister',
                         ' Bundespräsident 1979'
                     },
                     'score': 8.650627},
       '118554417': {'gid': {'118554417'},
                     'prefForename': {'Bettina'},
                     'prefSurname': {'Hürlimann'},
                     'varForename': {
                         'Bettina',
                         'Bettina Hürlimann-',
                         'Bettīna',
                         'ベッティーナ'},
                     'varSurname': {
                         'Hyūriman',
                         'Hyūrīman',
                         'Hürlimann Kiepenheuer',
                         'Hürlimann-Kiepenheuer',
                         'Kiepenheuer',
                         'ヒューリマン', 'ヒューリーマン'},
                     'birthdate': {'1909-06-19'},
                     'deathdate': {'1983-07-09'},
                     'desc': {
                         'Tochter des Verlegers Gustav Kiepenheuer und Gattin \
des Verlegers Martin Hürlimann',
                         ' Kinderbuchsammlerin, Schriftstellerin u. \
Übersetzerin',
                         ' Dt.-schweiz. Verlegerin u. Journalistin'
                     },
                     'score': 8.650627},
       '11919967X': {'gid': {'11919967X'},
                     'prefForename': {'Thomas'},
                     'prefSurname': {'Hürlimann'},
                     'birthdate': {'1950-12-21'},
                     'score': 8.650627},
       '118139681': {'gid': {'118139681'},
                     'prefForename': {'Annemarie'},
                     'prefSurname': {'Hürlimann'},
                     'birthdate': {'1949'},
                     'desc': {
                         'Studium der Anglistik, Kunstgeschichte und dt. \
Literatur',
                         ' Katalogbeiträge und Rezensionen in den Bereichen \
Kunst, Photographie und Kulturgeschichte',
                         ' Schweizerische Ausstellungskuratorin, Publizistin, \
Übersetzerin'
                     },
                     'score': 8.650627},
       '118554433': {'gid': {'118554433'},
                     'prefForename': {'Martin'},
                     'prefSurname': {'Hürlimann'},
                     'varForename': {'Martin'},
                     'varSurname': {
                         'Huerlimann',
                         'Hurlimann',
                         'Hürlimann-Kiepenheuer'},
                     'academic': {'Dr.'},
                     'birthdate': {'1897-11-12'},
                     'deathdate': {'1984-03-04'},
                     'desc': {'Schweizer. Verleger, Fotograf, Schriftsteller'},
                     'score': 8.650627},
       '118707809': {'gid': {'118707809'},
                     'prefForename': {'Ernst'},
                     'prefSurname': {'Hürlimann'},
                     'birthdate': {'1921-11-15'},
                     'deathdate': {'2001-02-24'},
                     'desc': {'Dt. Architekt, Grafiker u. Karikaturist'},
                     'score': 8.650627},
       '118839225': {'gid': {'118839225'},
                     'prefForename': {'Siegfried'},
                     'prefSurname': {'Heinimann'},
                     'academic': {'Prof. Dr.'},
                     'birthdate': {'1917-04-13'},
                     'deathdate': {'1996-06-15'},
                     'score': 8.650627},
       '141983582': {'gid': {'141983582'},
                     'prefForename': {'Stefan'},
                     'prefSurname': {'Heilemann'},
                     'birthdate': {'1974'},
                     'score': 8.650627}},
      {'hits': {
          'hits': [
              {'_index': 'gnd',
               '_id': '1147518866',
               '_score': 9.743573,
               '_source': {
                   'GND_ID': ['1147518866'],
                   'Forenames': ['Charles'],
                   'Surnames': ['Hirlimann'],
                   'Birthdate': ['1947']}
               },
              {'_index': 'gnd',
               '_id': '105795291',
               '_score': 8.650627,
               '_source': {
                   'GND_ID': ['105795291'],
                   'Forenames': ['Felix'],
                   'Surnames': ['Heinimann'],
                   'VariantForenames': ['Felix'],
                   'VariantSurnames': ['Heinimann-Lienhard'],
                   'Academics': ['Prof. Dr.'],
                   'Descriptions': [
                       'Schweiz. Klassischer Philologe und Lehrer an diversen \
Schulen in Basel, Aarau, Solothurn, Biel'
                    ],
                   'Birthdate': ['1915-07-13'],
                   'Deathdate': ['2006-01-23']}
               },
              {'_index': 'gnd',
               '_id': '109865308',
               '_score': 8.650627,
               '_source': {
                   'GND_ID': ['109865308'],
                   'Forenames': ['Ullrich'],
                   'Surnames': ['Heilemann'],
                   'VariantForenames': ['Ulrich'],
                   'VariantSurnames': ['Heilemann'],
                   'Academics': ['Prof. Dr. rer. pol. em.'],
                   'Affiliations': [
                       'Institut für Empirische Wirtschaftsforschung Leipzig'
                    ],
                   'Birthdate': ['1944']}
               },
              {'_index': 'gnd',
               '_id': '110821734',
               '_score': 8.650627,
               '_source': {
                   'GND_ID': ['110821734'],
                   'Forenames': ['Michael'],
                   'Surnames': ['Heilemann'],
                   'Descriptions': [
                       'Promovierter Psychologischer Psychotherapeut'
                    ],
                   'Birthdate': ['1953']}
               },
              {'_index': 'gnd',
               '_id': '115824839',
               '_score': 8.650627,
               '_source': {
                   'GND_ID': ['115824839'],
                   'Forenames': ['Christoph'],
                   'Surnames': ['Hürlimann'],
                   'Descriptions': ['Theologe', ' Schriftsteller'],
                   'Birthdate': ['1938']}
               },
              {'_index': 'gnd',
               '_id': '11665144X',
               '_score': 8.650627,
               '_source': {
                   'GND_ID': ['11665144X'],
                   'Forenames': ['Ernst'],
                   'Surnames': ['Heilemann'],
                   'VariantForenames': ['E.'],
                   'VariantSurnames': ['Heilemann'],
                   'Deathplaces': ['Kitchener (Ontario)'],
                   'Birthdate': ['1870-08-08'],
                   'Deathdate': ['1936-04-09']}
               },
              {'_index': 'gnd',
               '_id': '117050873',
               '_score': 8.650627,
               '_source': {
                   'GND_ID': ['117050873'],
                   'Forenames': ['Heinrich Otto'],
                   'Surnames': ['Hürlimann'],
                   'Birthdate': ['1900-06-16'],
                   'Deathdate': ['1964-01-13']}
               },
              {'_index': 'gnd',
               '_id': '118554425',
               '_score': 8.650627,
               '_source': {
                   'GND_ID': ['118554425'],
                   'Forenames': ['Hans'],
                   'Surnames': ['Hürlimann'],
                   'Descriptions': [
                       'Bundesrat 1973-1982 (Innenminister, Bildungs- und \
Forschungsminister',
                       ' Bundespräsident 1979'
                    ],
                   'Birthdate': ['1918-04-06'],
                   'Deathdate': ['1994-02-22']}
               },
              {'_index': 'gnd',
               '_id': '118554417',
               '_score': 8.650627,
               '_source': {
                   'GND_ID': ['118554417'],
                   'Forenames': ['Bettina'],
                   'Surnames': ['Hürlimann'],
                   'VariantForenames': [
                       'Bettina',
                       'Bettina Hürlimann-',
                       'Bettīna',
                       'ベッティーナ'
                    ],
                   'VariantSurnames': [
                       'Kiepenheuer',
                       'Hürlimann-Kiepenheuer',
                       'Hürlimann Kiepenheuer',
                       'Hyūriman',
                       'Hyūrīman',
                       'ヒューリマン',
                       'ヒューリーマン'
                    ],
                   'Descriptions': [
                       'Tochter des Verlegers Gustav Kiepenheuer und Gattin \
des Verlegers Martin Hürlimann',
                       ' Kinderbuchsammlerin, Schriftstellerin u. \
Übersetzerin',
                       ' Dt.-schweiz. Verlegerin u. Journalistin'
                    ],
                   'Birthdate': ['1909-06-19'],
                   'Deathdate': ['1983-07-09']}
               },
              {'_index': 'gnd',
               '_id': '11919967X',
               '_score': 8.650627,
               '_source': {
                   'GND_ID': ['11919967X'],
                   'Forenames': ['Thomas'],
                   'Surnames': ['Hürlimann'],
                   'Birthdate': ['1950-12-21']}
               },
              {'_index': 'gnd',
               '_id': '118139681',
               '_score': 8.650627,
               '_source': {
                   'GND_ID': ['118139681'],
                   'Forenames': ['Annemarie'],
                   'Surnames': ['Hürlimann'],
                   'Descriptions': [
                       'Studium der Anglistik, Kunstgeschichte und dt. \
Literatur',
                       ' Katalogbeiträge und Rezensionen in den Bereichen \
Kunst, Photographie und Kulturgeschichte',
                       ' Schweizerische Ausstellungskuratorin, Publizistin, \
Übersetzerin'
                   ],
                   'Birthdate': ['1949']}
               },
              {'_index': 'gnd',
               '_id': '118554433',
               '_score': 8.650627,
               '_source': {
                   'GND_ID': ['118554433'],
                   'Forenames': ['Martin'],
                   'Surnames': ['Hürlimann'],
                   'VariantForenames': ['Martin'],
                   'VariantSurnames': [
                       'Huerlimann', 'Hurlimann', 'Hürlimann-Kiepenheuer'
                    ],
                   'Academics': ['Dr.'],
                   'Descriptions': [
                       'Schweizer. Verleger, Fotograf, Schriftsteller'
                    ],
                   'Birthdate': ['1897-11-12'],
                   'Deathdate': ['1984-03-04']}
               },
              {'_index': 'gnd',
               '_id': '118707809',
               '_score': 8.650627,
               '_source': {
                   'GND_ID': ['118707809'],
                   'Forenames': ['Ernst'],
                   'Surnames': ['Hürlimann'],
                   'Descriptions': ['Dt. Architekt, Grafiker u. Karikaturist'],
                   'Birthdate': ['1921-11-15'],
                   'Deathdate': ['2001-02-24']}
               },
              {'_index': 'gnd',
               '_id': '118839225',
               '_score': 8.650627,
               '_source': {
                   'GND_ID': ['118839225'],
                   'Forenames': ['Siegfried'],
                   'Surnames': ['Heinimann'],
                   'Academics': ['Prof. Dr.'],
                   'Birthdate': ['1917-04-13'],
                   'Deathdate': ['1996-06-15']}
               },
              {'_index': 'gnd',
               '_id': '141983582',
               '_score': 8.650627,
               '_source': {
                   'GND_ID': ['141983582'],
                   'Forenames': ['Stefan'],
                   'Surnames': ['Heilemann'],
                   'Birthdate': ['1974']}
               }
          ]
        }
       }),
     (["Urs fosef"], "Cavelti", 15,
      {'1066273278': {'gid': {'1066273278'},
                      'prefForename': {'Urs Josef'},
                      'prefSurname': {'Cavelti'},
                      'varForename': {'Urs', 'Urs J.', 'Urs Joseph'},
                      'varSurname': {'Cavelti'},
                      'birthdate': {'1927-09-03'},
                      'deathdate': {'2003-11-04'},
                      'desc': {
                          'St. Galler Politiker, Rechtsanwalt und Redaktor'
                      },
                      'score': 21.423903}},
      {'hits': {
          'hits': [
              {'_index': 'gnd',
               '_id': '1066273278',
               '_score': 21.423903,
               '_source': {
                   'GND_ID': ['1066273278'],
                   'Forenames': ['Urs Josef'],
                   'Surnames': ['Cavelti'],
                   'VariantForenames': ['Urs Joseph', 'Urs J.', 'Urs'],
                   'VariantSurnames': ['Cavelti'],
                   'Descriptions': [
                       'St. Galler Politiker, Rechtsanwalt und Redaktor'
                    ],
                   'Birthdate': ['1927-09-03'],
                   'Deathdate': ['2003-11-04']}
               }
          ]
        }
       }
      ),
     ],
)
@patch("utility.linking_utils.requests.get")
def test_search_person_gnd(
     mock_get, fnames, lastname, gnd_limit, expected, get_res
     ):
    """
    We check
    (1) Do we get results even for misspelled or abbreviated entities.
    (2) Does it return at most gnd_limit results
    """
    mock_response = MagicMock()
    mock_response.json.return_value = get_res

    mock_get.return_value = mock_response

    assert search_person_gnd(fnames, lastname, gnd_limit) == expected
    assert (len(search_person_gnd(fnames, lastname, gnd_limit)) <= gnd_limit)


# -------------------------------------------------
# 3. Test convert_dates
# -------------------------------------------------
@pytest.mark.parametrize(
    "wikidata_date, expected",
    [
        ("+1796-10-16T00:00:00Z", "1796-10-16"),  # day
        ("+2025-02-00T00:00:00Z", "2025-02-00"),  # month
        ("+2025-00-00T00:00:00Z", "2025-00-00"),  # year
        ("+2010-00-00T00:00:00Z", "2010-00-00"),  # decade
        ("+2025-02-11T20:21:22Z", "2025-02-11")  # second
    ],
)
def test_convert_dates(wikidata_date, expected):
    """
    We check if the dates are converted properly.
    """
    assert convert_dates(wikidata_date) == expected


# -------------------------------------------------
# 4. Test get_wikidata_value
# -------------------------------------------------
@pytest.mark.parametrize(
    "wikidata_id, expected",
    [
        ("Q4964182", "Philosoph"),
        ("Q115088092", None),
        ("Q69345", "Neuenburg"),
        ("Q21387", "Niederbronn-les-Bains"),
        ("Q3391743", "bildender K\u00fcnstler"),
        ("Q2505739", "Hispanist")
    ],
)
def test_get_wikidata_value(wikidata_id, expected):
    """
    We check if the values are found in cache and not found
    if they don't exist.
    We can't check for values that aren't in cache because
    we would immediately add them (side-effect)
    """
    assert get_wikidata_value(wikidata_id) == expected


# -------------------------------------------------
# 5. Test search_person_wikidata
# -------------------------------------------------
@pytest.mark.parametrize(
    "search_term, wikidata_limit, expected, get_res",
    [
        ("D. Birchall", 5,
         {'129263265':
          {'desc': {'British graphic designer'},
           'prefForename': {'Derek'},
           'prefSurname': {'Birdsall'},
           'jobliteral': {'Grafikdesigner'},
           'birthdate': {'1934-08-01'},
           'gid': {'129263265'},
           'name': {'Derek Birdsall'},
           'score': 10.2981415},
          '1119113008':
          {'gid': {'1119113008'},
           'name': {'Douglas Birdsall'},
           'prefSurname': {'Birdsall'},
           'prefForename': {'Douglas'},
           'score': 10.2981415}},
         {'hits': {
             'hits': [
                 {'_index': 'wikidata',
                  '_id': 'Nm_WYYsBW8gB8I1O0o9X',
                  '_score': 10.2981415,
                  '_source': {
                      'id': 'Q5261808',
                      'labels': 'Derek Birdsall',
                      'descriptions': 'British graphic designer',
                      'aliases': [],
                      'claims': {
                          'P21': ['Q6581097'],
                          'P31': ['Q5'],
                          'P106': ['Q627325'],
                          'P227': ['129263265'],
                          'P569': ['+1934-08-01T00:00:00Z'],
                          'P734': ['Q56245395'],
                          'P735': ['Q11740724']
                      }
                    }
                  },
                 {'_index': 'wikidata',
                  '_id': 'nu30YYsBW8gB8I1OZr1w',
                  '_score': 10.2981415,
                  '_source': {
                      'id': 'Q113843374',
                      'labels': 'Douglas Birdsall',
                      'aliases': [],
                      'claims': {'P31': ['Q5'], 'P227': ['1119113008']}
                    }
                  }
             ]
            }
          }
         ),
        ("J.F. Bitschnau", 5,
         {'1065067526':
          {'prefForename': {'Johann'},
           'jobliteral': {'Arzt', 'Historiker', 'Politiker', 'Rechtsanwalt'},
           'birthdate': {'1776-00-00'},
           'deathdate': {'1819-00-00'},
           'gid': {'1065067526'},
           'name': {'Johann Josef Bitschnau'},
           'prefSurname': {'Bitschnau'},
           'score': 13.562946}},
         {'hits': {
             'hits': [
                 {'_index': 'wikidata',
                  '_id': 'rdLuYYsBW8gB8I1ONY30',
                  '_score': 13.562946,
                  '_source': {
                      'id': 'Q94917995',
                      'labels': 'Johann Josef Bitschnau',
                      'aliases': [],
                      'claims': {
                          'P21': ['Q6581097'],
                          'P31': ['Q5'],
                          'P106': ['Q39631', 'Q201788', 'Q40348', 'Q82955'],
                          'P227': ['1065067526'],
                          'P569': ['+1776-00-00T00:00:00Z'],
                          'P570': ['+1819-00-00T00:00:00Z'],
                          'P735': ['Q11122389'],
                          'P7902': ['1065067526']
                       }
                   }
                  }
             ]
            }
          }
         ),
        ("Viktor Amadeus", 5,
         {'117569518':
          {'prefForename': {'Viktor'},
           'jobliteral': {'Gymnasiallehrer'},
           'birthdate': {'1828-00-00'},
           'gid': {'117569518'},
           'name': {'Viktor Amadeus Meyer'},
           'prefSurname': {'Meyer'},
           'score': 15.509318},
          '142136859':
          {'desc': {'(1727-1793)'},
           'birthplaceLiteral': {'Mierczyce'},
           'prefForename': {'Viktor'},
           'jobliteral': {'Kammerherr'},
           'birthdate': {'1727-09-15'},
           'deathdate': {'1793-01-31'},
           'deathplaceLiteral': {'Königsberg'},
           'gid': {'142136859'},
           'name': {'Viktor Amadeus Henckel von Donnersmarck'},
           'prefSurname': {'Donnersmarck'},
           'score': 11.798985},
          '1193647002':
          {'prefForename': {'Viktor'},
           'birthdate': {'1821-00-00'},
           'deathdate': {'1880-00-00'},
           'gid': {'1193647002'},
           'name': {'Viktor Paul Amadeus von Wolff'},
           'prefSurname': {'Wolff'},
           'score': 11.798985},
          '135979773':
          {'desc': {'Duke of Savoy (1587–1637)'},
           'birthplaceLiteral': {'Turin'},
           'prefForename': {'Victor-Amédée'},
           'prefSurname': {'Savoia'},
           'jobliteral': {'Aristokrat', 'Politiker'},
           'birthdate': {'1587-05-08'},
           'deathdate': {'1637-10-07'},
           'deathplaceLiteral': {'Vercelli'},
           'gid': {'135979773'},
           'name': {'Victor Amadeus I of Savoy'},
           'score': 11.0242815},
          '118804537':
          {'desc': {'Duke of Savoy and King of Sardinia (1675-1732)'},
           'birthplaceLiteral': {'Turin'},
           'prefForename': {'Victor-Amédée'},
           'prefSurname': {'Savoia'},
           'jobliteral': {'Politiker'},
           'birthdate': {'1666-05-14'},
           'deathdate': {'1732-10-31'},
           'deathplaceLiteral': {'Moncalieri', 'Rivoli'},
           'gid': {'118804537'},
           'name': {'Victor Amadeus II of Savoy'},
           'score': 11.0242815}},
         {'hits': {
             'hits': [
                 {'_index': 'wikidata',
                  '_id': 'uejzYYsBW8gB8I1OVmQG',
                  '_score': 15.509318,
                  '_source': {
                      'id': 'Q95257658',
                      'labels': 'Viktor Amadeus Meyer',
                      'aliases': [],
                      'claims': {
                          'P21': ['Q6581097'],
                          'P31': ['Q5'],
                          'P106': ['Q5758653'],
                          'P227': ['117569518'],
                          'P569': ['+1828-00-00T00:00:00Z'],
                          'P735': ['Q16430022'],
                          'P7902': ['117569518']
                      }
                    }
                  },
                 {'_index': 'wikidata',
                  '_id': '627WYYsBW8gB8I1OaYbi',
                  '_score': 11.798985,
                  '_source': {
                      'id': 'Q2524210',
                      'labels': 'Viktor Amadeus Henckel von Donnersmarck',
                      'descriptions': '(1727-1793)',
                      'aliases': [],
                      'claims': {
                          'P19': ['Q11780376'],
                          'P20': ['Q4120832'],
                          'P21': ['Q6581097'],
                          'P26': ['Q1328078'],
                          'P27': ['Q27306'],
                          'P31': ['Q5'],
                          'P106': ['Q264323'],
                          'P227': ['142136859'],
                          'P569': ['+1727-09-15T00:00:00Z'],
                          'P570': ['+1793-01-31T00:00:00Z'],
                          'P735': ['Q16430022'],
                          'P7902': ['142136859']
                       }
                    }
                  },
                 {'_index': 'wikidata',
                  '_id': '6qfjYYsBW8gB8I1O9Fqm',
                  '_score': 11.798985,
                  '_source': {
                      'id': 'Q94911348',
                      'labels': 'Viktor Paul Amadeus von Wolff',
                      'aliases': [],
                      'claims': {
                          'P21': ['Q6581097'],
                          'P26': ['Q94773563'],
                          'P31': ['Q5'],
                          'P227': ['1193647002'],
                          'P569': ['+1821-00-00T00:00:00Z'],
                          'P570': ['+1880-00-00T00:00:00Z'],
                          'P735': ['Q16430022'],
                          'P7902': ['1193647002']
                      }
                    }
                  },
                 {'_index': 'wikidata',
                  '_id': 'TFfQYYsBW8gB8I1OrPD0',
                  '_score': 11.0242815,
                  '_source': {
                      'id': 'Q356145',
                      'labels': 'Victor Amadeus I of Savoy',
                      'descriptions': 'Duke of Savoy (1587–1637)',
                      'aliases': [
                          'Duke of Savoy Victor Amedee',
                          'Duke of Savoy Vittorio Amadeo',
                          'Vittorio Amedeo II',
                          'Vittorio Amedeo II di Savoia',
                          'Duke of Savoy Victor Amadeus I',
                          'Victor Amadeus I'
                      ],
                      'claims': {
                          'P19': ['Q495'],
                          'P20': ['Q5990'],
                          'P21': ['Q6581097'],
                          'P26': ['Q1083398'],
                          'P31': ['Q5'],
                          'P106': ['Q2478141', 'Q82955'],
                          'P227': ['135979773'],
                          'P509': ['Q12136'],
                          'P569': ['+1587-05-08T00:00:00Z'],
                          'P570': ['+1637-10-07T00:00:00Z'],
                          'P734': ['Q23041587'],
                          'P735': ['Q117804139'],
                          'P7902': ['135979773']
                      }
                    }
                  },
                 {'_index': 'wikidata',
                  '_id': 'iW3VYYsBW8gB8I1O6oWl',
                  '_score': 11.0242815,
                  '_source': {
                      'id': 'Q209579',
                      'labels': 'Victor Amadeus II of Savoy',
                      'descriptions': 'Duke of Savoy and King of Sardinia \
(1675-1732)',
                      'aliases': ['Vittorio Amedeo II', 'Victor Amadeus II'],
                      'claims': {
                          'P19': ['Q495'],
                          'P20': ['Q9474', 'Q10231'],
                          'P21': ['Q6581097'],
                          'P26': ['Q230873', 'Q275380'],
                          'P27': [],
                          'P31': ['Q5'],
                          'P106': ['Q82955'],
                          'P227': ['118804537'],
                          'P509': ['Q12202'],
                          'P569': ['+1666-05-14T00:00:00Z'],
                          'P570': ['+1732-10-31T00:00:00Z'],
                          'P734': ['Q23041587'],
                          'P735': ['Q117804139'],
                          'P1196': ['Q3739104'],
                          'P1559': [
                              'Victorius Amadeus II',
                              'Victor-Amédée II',
                              'Vittorio Amedeo II'
                          ],
                          'P7902': ['118804537']
                       }
                     }
                  }
                ]
            }
          }
         ),
        (" Hiilimann", 5,
         {'118554425':
          {'desc': {'member of the Swiss Federal Council (1918-1994)'},
           'birthplaceLiteral': {'Walchwil'},
           'prefForename': {'Hans'},
           'prefSurname': {'Hürlimann'},
           'jobliteral': {'Politiker'},
           'birthdate': {'1918-04-06'},
           'deathdate': {'1994-02-22'},
           'deathplaceLiteral': {'Zug'},
           'gid': {'118554425'},
           'name': {'Hans Hürlimann'},
           'score': 9.05033},
          '111657960X':
          {'desc': {'Swiss journalist and author'},
           'birthplaceLiteral': {'Basel'},
           'prefForename': {'Brigitte'},
           'prefSurname': {'Hürlimann'},
           'jobliteral': {'Journalist', 'Schriftsteller'},
           'birthdate': {'1963-01-01'},
           'gid': {'111657960X'},
           'name': {'Brigitte Hürlimann'},
           'score': 9.05033},
          '105795291':
          {'desc': {'Swiss classical philologist (1915-2006)'},
           'birthplaceLiteral': {'Bennwil'},
           'prefForename': {'Felix'},
           'prefSurname': {'Heinimann'},
           'jobliteral': {'Hochschullehrer', 'Klassischer Philologe'},
           'birthdate': {'1915-07-13'},
           'deathdate': {'2006-01-28'},
           'deathplaceLiteral': {'Basel'},
           'gid': {'105795291'},
           'name': {'Felix Heinimann'},
           'score': 9.05033},
          '112096590X': {
           'desc': {'researcher'},
           'prefForename': {'Andreas'},
           'prefSurname': {'Heinimann'},
           'jobliteral': {'Geograph'},
           'birthdate': {'2000-00-00'},
           'gid': {'112096590X'},
           'name': {'Andreas Heinimann'},
           'score': 9.05033},
          '119192241':
          {'desc': {'Swiss artist'},
           'birthplaceLiteral': {'Oberstaufen'},
           'prefForename': {'Manfred'},
           'prefSurname': {'Hürlimann'},
           'jobliteral': {'Maler'},
           'birthdate': {'1958-09-29'},
           'gid': {'119192241'},
           'name': {'Manfred Hürlimann'},
           'score': 9.05033}},
         {'hits': {
             'hits': [
                 {'_index': 'wikidata',
                  '_id': 'yq7lYYsBW8gB8I1OTk0I',
                  '_score': 9.05033,
                  '_source': {
                      'id': 'Q118178',
                      'labels': 'Hans Hürlimann',
                      'descriptions': 'member of the Swiss Federal Council \
(1918-1994)',
                      'aliases': ['Hans Huerlimann'],
                      'claims': {
                          'P19': ['Q66298'],
                          'P20': ['Q68144'],
                          'P21': ['Q6581097'],
                          'P27': ['Q39'],
                          'P31': ['Q5'],
                          'P106': ['Q82955'],
                          'P227': ['118554425'],
                          'P569': ['+1918-04-06T00:00:00Z'],
                          'P570': ['+1994-02-22T00:00:00Z'],
                          'P701': ['P25145'],
                          'P734': ['Q18183304'],
                          'P735': ['Q632842'],
                          'P1559': ['Hans Hürlimann'],
                          'P7902': ['118554425']
                      }
                    }
                  },
                 {'_index': 'wikidata',
                  '_id': '367lYYsBW8gB8I1Ojq9T',
                  '_score': 9.05033,
                  '_source': {
                      'id': 'Q916362',
                      'labels': 'Brigitte Hürlimann',
                      'descriptions': 'Swiss journalist and author',
                      'aliases': ['Brigitte Huerlimann'],
                      'claims': {
                          'P19': ['Q78'],
                          'P21': ['Q6581072'],
                          'P27': ['Q39'],
                          'P31': ['Q5'],
                          'P106': ['Q1930187', 'Q36180'],
                          'P227': ['111657960X'],
                          'P569': ['+1963-01-01T00:00:00Z'],
                          'P734': ['Q18183304'],
                          'P735': ['Q18175370']
                      }
                    }
                  },
                 {'_index': 'wikidata',
                  '_id': 'Iq7lYYsBW8gB8I1OqOnR',
                  '_score': 9.05033,
                  '_source': {
                      'id': 'Q1403503',
                      'labels': 'Felix Heinimann',
                      'descriptions': 'Swiss classical philologist \
(1915-2006)',
                      'aliases': [],
                      'claims': {
                          'P19': ['Q64735'],
                          'P20': ['Q78'],
                          'P21': ['Q6581097'],
                          'P27': ['Q39'],
                          'P31': ['Q5'],
                          'P106': ['Q16267607', 'Q1622272'],
                          'P227': ['105795291'],
                          'P569': ['+1915-07-13T00:00:00Z'],
                          'P570': ['+2006-01-28T00:00:00Z'],
                          'P734': ['Q76417878'],
                          'P735': ['Q18177136'],
                          'P7902': ['105795291']
                      }
                    }
                  },
                 {'_index': 'wikidata',
                  '_id': 'wl_TYYsBW8gB8I1OR_ew',
                  '_score': 9.05033,
                  '_source': {
                      'id': 'Q47708403',
                      'labels': 'Andreas Heinimann',
                      'descriptions': 'researcher',
                      'aliases': [],
                      'claims': {
                          'P21': ['Q6581097'],
                          'P31': ['Q5'],
                          'P106': ['Q901402'],
                          'P227': ['112096590X'],
                          'P569': ['+2000-00-00T00:00:00Z'],
                          'P734': ['Q76417878'],
                          'P735': ['Q4926263']
                      }
                    }
                  },
                 {'_index': 'wikidata',
                  '_id': 'KljQYYsBW8gB8I1O_pDU',
                  '_score': 9.05033,
                  '_source': {
                      'id': 'Q1632574',
                      'labels': 'Manfred Hürlimann',
                      'descriptions': 'Swiss artist',
                      'aliases': ['Manfred Huerlimann'],
                      'claims': {
                          'P19': ['Q127637'],
                          'P21': ['Q6581097'],
                          'P27': ['Q39', 'Q183'],
                          'P31': ['Q5'],
                          'P106': ['Q1028181'],
                          'P227': ['119192241'],
                          'P569': ['+1958-09-29T00:00:00Z'],
                          'P734': ['Q18183304'],
                          'P735': ['Q15627437']
                      }
                    }
                  }
                ]
              }
          }
         ),
        ("Urs fosef Cavelti", 5,
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
            'score': 22.652344}},
         {'hits': {
             'hits': [
                 {'_index': 'wikidata',
                  '_id': 'zovdYYsBW8gB8I1Ow7qQ',
                  '_score': 22.652344,
                  '_source': {
                      'id': 'Q55683152',
                      'labels': 'Urs Josef Cavelti',
                      'descriptions': '(1927-2003)',
                      'aliases': [],
                      'claims': {
                          'P19': ['Q69777'],
                          'P20': ['Q25607'],
                          'P21': ['Q6581097'],
                          'P27': ['Q39'],
                          'P31': ['Q5'],
                          'P106': ['Q185351'],
                          'P227': ['1066273278'],
                          'P569': ['+1927-09-03T00:00:00Z'],
                          'P570': ['+2003-11-04T00:00:00Z'],
                          'P735': ['Q7901129']
                      }
                    }
                  }
                ]
              }
          }
         ),
        ("Albert Einstein", 0, {}, {})
    ],
)
@patch("utility.linking_utils.requests.get")
def test_search_person_wikidata(
     mock_get, search_term, wikidata_limit, expected, get_res
     ):
    """
    We check
    (1) Do we get results even for misspelled or abbreviated entities.
    (2) Does it return at most GND_LIMIT results
    """
    mock_response = MagicMock()
    mock_response.json.return_value = get_res

    mock_get.return_value = mock_response
    assert search_person_wikidata(search_term, wikidata_limit) == expected
    assert len(
        search_person_wikidata(search_term, wikidata_limit)
    ) <= wikidata_limit


# -------------------------------------------------
# 6. Test convert_wikidata_format_kibana
# -------------------------------------------------
@pytest.mark.parametrize(
    "person_dict, expected",
    [
     ({'label': 'Derek Birdsall',
      'description': 'British graphic designer',
       'claims': {'P21': ['Q6581097'],
                  'P31': ['Q5'],
                  'P106': ['Q627325'],
                  'P227': ['129263265'],
                  'P569': ['+1934-08-01T00:00:00Z'],
                  'P734': ['Q56245395'],
                  'P735': ['Q11740724']}},
      {'desc': {'British graphic designer'},
         'prefForename': {'Derek'},
         'prefSurname': {'Birdsall'},
         'jobliteral': {'Grafikdesigner'},
         'birthdate': {'1934-08-01'},
         'gid': {'129263265'},
         'name': {'Derek Birdsall'}}),
     ({'label': 'Douglas Birdsall',
      'claims': {'P31': ['Q5'], 'P227': ['1119113008']}},
      {'gid': {'1119113008'},
       'name': {'Douglas Birdsall'},
       'prefSurname': {'Birdsall'},
       'prefForename': {'Douglas'}}),
     ({'label': 'Johann Josef Bitschnau',
       'claims': {'P21': ['Q6581097'],
                  'P31': ['Q5'],
                  'P106': ['Q39631', 'Q201788', 'Q40348', 'Q82955'],
                  'P227': ['1065067526'],
                  'P569': ['+1776-00-00T00:00:00Z'],
                  'P570': ['+1819-00-00T00:00:00Z'],
                  'P735': ['Q11122389'],
                  'P7902': ['1065067526']}},
      {'prefForename': {'Johann'},
       'jobliteral': {'Arzt', 'Historiker', 'Politiker', 'Rechtsanwalt'},
       'birthdate': {'1776-00-00'},
       'deathdate': {'1819-00-00'},
       'gid': {'1065067526'},
       'name': {'Johann Josef Bitschnau'},
       'prefSurname': {'Bitschnau'}}),
     ({'label': 'Victor Amadeus II of Savoy',
       'description': 'Duke of Savoy and King of Sardinia (1675-1732)',
       'claims': {'P19': ['Q495'],
                  'P20': ['Q9474', 'Q10231'],
                  'P21': ['Q6581097'],
                  'P26': ['Q230873', 'Q275380'],
                  'P27': [],
                  'P31': ['Q5'],
                  'P106': ['Q82955'],
                  'P227': ['118804537'],
                  'P509': ['Q12202'],
                  'P569': ['+1666-05-14T00:00:00Z'],
                  'P570': ['+1732-10-31T00:00:00Z'],
                  'P734': ['Q23041587'],
                  'P735': ['Q117804139'],
                  'P1196': ['Q3739104'],
                  'P1559': ['Victorius Amadeus II',
                            'Victor-Amédée II',
                            'Vittorio Amedeo II'],
                  'P7902': ['118804537']}},
      {'desc': {'Duke of Savoy and King of Sardinia (1675-1732)'},
       'birthplaceLiteral': {'Turin'},
       'prefForename': {'Victor-Amédée'},
       'prefSurname': {'Savoia'},
       'jobliteral': {'Politiker'},
       'birthdate': {'1666-05-14'},
       'deathdate': {'1732-10-31'},
       'deathplaceLiteral': {'Moncalieri', 'Rivoli'},
       'gid': {'118804537'},
       'name': {'Victor Amadeus II of Savoy'}}),
     ({'label': 'Victor Amadeus I of Savoy',
       'description': 'Duke of Savoy (1587–1637)',
       'claims': {'P19': ['Q495'],
                  'P20': ['Q5990'],
                  'P21': ['Q6581097'],
                  'P26': ['Q1083398'],
                  'P31': ['Q5'],
                  'P106': ['Q2478141', 'Q82955'],
                  'P227': ['135979773'],
                  'P509': ['Q12136'],
                  'P569': ['+1587-05-08T00:00:00Z'],
                  'P570': ['+1637-10-07T00:00:00Z'],
                  'P734': ['Q23041587'],
                  'P735': ['Q117804139'],
                  'P7902': ['135979773']}},
      {'desc': {'Duke of Savoy (1587–1637)'},
       'birthplaceLiteral': {'Turin'},
       'prefForename': {'Victor-Amédée'},
       'prefSurname': {'Savoia'},
       'jobliteral': {'Aristokrat', 'Politiker'},
       'birthdate': {'1587-05-08'},
       'deathdate': {'1637-10-07'},
       'deathplaceLiteral': {'Vercelli'},
       'gid': {'135979773'},
       'name': {'Victor Amadeus I of Savoy'}}),
     ({'label': 'Viktor Paul Amadeus von Wolff',
       'claims': {'P21': ['Q6581097'],
                  'P26': ['Q94773563'],
                  'P31': ['Q5'],
                  'P227': ['1193647002'],
                  'P569': ['+1821-00-00T00:00:00Z'],
                  'P570': ['+1880-00-00T00:00:00Z'],
                  'P735': ['Q16430022'],
                  'P7902': ['1193647002']}},
      {'prefForename': {'Viktor'},
       'birthdate': {'1821-00-00'},
       'deathdate': {'1880-00-00'},
       'gid': {'1193647002'},
       'name': {'Viktor Paul Amadeus von Wolff'},
       'prefSurname': {'Wolff'}}),
     ({'label': 'Viktor Amadeus Henckel von Donnersmarck',
       'description': '(1727-1793)',
       'claims': {'P19': ['Q11780376'],
                  'P20': ['Q4120832'],
                  'P21': ['Q6581097'],
                  'P26': ['Q1328078'],
                  'P27': ['Q27306'],
                  'P31': ['Q5'],
                  'P106': ['Q264323'],
                  'P227': ['142136859'],
                  'P569': ['+1727-09-15T00:00:00Z'],
                  'P570': ['+1793-01-31T00:00:00Z'],
                  'P735': ['Q16430022'],
                  'P7902': ['142136859']}},
      {'desc': {'(1727-1793)'},
       'birthplaceLiteral': {'Mierczyce'},
       'prefForename': {'Viktor'},
       'jobliteral': {'Kammerherr'},
       'birthdate': {'1727-09-15'},
       'deathdate': {'1793-01-31'},
       'deathplaceLiteral': {'Königsberg'},
       'gid': {'142136859'},
       'name': {'Viktor Amadeus Henckel von Donnersmarck'},
       'prefSurname': {'Donnersmarck'}}),
     ({'label': 'Viktor Amadeus Meyer',
       'claims': {'P21': ['Q6581097'],
                  'P31': ['Q5'],
                  'P106': ['Q5758653'],
                  'P227': ['117569518'],
                  'P569': ['+1828-00-00T00:00:00Z'],
                  'P735': ['Q16430022'],
                  'P7902': ['117569518']}},
      {'prefForename': {'Viktor'},
       'jobliteral': {'Gymnasiallehrer'},
       'birthdate': {'1828-00-00'},
       'gid': {'117569518'},
       'name': {'Viktor Amadeus Meyer'},
       'prefSurname': {'Meyer'}}),
     ({'label': 'Manfred Hürlimann',
       'description': 'Swiss artist',
       'claims': {'P19': ['Q127637'],
                  'P21': ['Q6581097'],
                  'P27': ['Q39', 'Q183'],
                  'P31': ['Q5'],
                  'P106': ['Q1028181'],
                  'P227': ['119192241'],
                  'P569': ['+1958-09-29T00:00:00Z'],
                  'P734': ['Q18183304'],
                  'P735': ['Q15627437']}},
      {'desc': {'Swiss artist'},
       'birthplaceLiteral': {'Oberstaufen'},
       'prefForename': {'Manfred'},
       'prefSurname': {'Hürlimann'},
       'jobliteral': {'Maler'},
       'birthdate': {'1958-09-29'},
       'gid': {'119192241'},
       'name': {'Manfred Hürlimann'}})
     ],
)
def test_convert_wikidata_format_kibana(person_dict, expected):
    assert convert_wikidata_format_kibana(person_dict) == expected


# -------------------------------------------------
# 6. Test convert_gnd_format_kibana
# -------------------------------------------------
@pytest.mark.parametrize(
    "person_dict, expected",
    [({'GND_ID': ['171726375'],
        'Forenames': ['David'],
        'Surnames': ['Birchall'],
        'VariantForenames': ['D. W.', 'David W.', 'D.'],
        'VariantSurnames': ['Birchall'],
        'Academics': ['Prof. em.'],
        'Descriptions': [
            'Henley Management College, Henley Business School, Univ. of \
Reading'
        ]},
      {'gid': {'171726375'},
        'prefForename': {'David'},
        'prefSurname': {'Birchall'},
        'varForename': {'D.', 'D. W.', 'David W.'},
        'varSurname': {'Birchall'},
        'academic': {'Prof. em.'},
        'desc': {
            'Henley Management College, Henley Business School, Univ. of \
Reading'
        }}),
     ({'GND_ID': ['1089259662'],
         'Forenames': ['J. D.'],
         'Surnames': ['Birchall'],
         'Descriptions': ['Chemiker, USA']},
        {'gid': {'1089259662'},
         'prefForename': {'J. D.'},
         'prefSurname': {'Birchall'},
         'desc': {'Chemiker, USA'}}),
     ({'GND_ID': ['1033767735'],
         'Forenames': ['Josef'],
         'Surnames': ['Bitschnau'],
         'Birthdate': ['1925-10-10']},
        {'gid': {'1033767735'},
         'prefForename': {'Josef'},
         'prefSurname': {'Bitschnau'},
         'birthdate': {'1925-10-10'}}),
     ({'GND_ID': ['1065067526'],
         'Forenames': ['Johann Josef'],
         'Surnames': ['Bitschnau'],
         'Academics': ['Dr.jur.et med.'],
         'Birthdate': ['1776'],
         'Deathdate': ['1819']},
        {'gid': {'1065067526'},
         'prefForename': {'Johann Josef'},
         'prefSurname': {'Bitschnau'},
         'academic': {'Dr.jur.et med.'},
         'birthdate': {'1776'},
         'deathdate': {'1819'}}),
     ({'GND_ID': ['1056411104'],
         'Forenames': ['Victor Oliveira'],
         'Surnames': ['Mateus'],
         'VariantForenames': ['Victor'],
         'VariantSurnames': ['Oliveira Mateus'],
         'Descriptions': ['geb. in Lissabon', ' Philosoph u. Dichter']},
        {'gid': {'1056411104'},
         'prefForename': {'Victor Oliveira'},
         'prefSurname': {'Mateus'},
         'varForename': {'Victor'},
         'varSurname': {'Oliveira Mateus'},
         'desc': {'geb. in Lissabon', ' Philosoph u. Dichter'}}),
     ({'GND_ID': ['1147518866'],
         'Forenames': ['Charles'],
         'Surnames': ['Hirlimann'],
         'Birthdate': ['1947']},
        {'gid': {'1147518866'},
         'prefForename': {'Charles'},
         'prefSurname': {'Hirlimann'},
         'birthdate': {'1947'}}),
     ({'GND_ID': ['115824839'],
         'Forenames': ['Christoph'],
         'Surnames': ['Hürlimann'],
         'Descriptions': ['Theologe', ' Schriftsteller'],
         'Birthdate': ['1938']},
      {'gid': {'115824839'},
         'prefForename': {'Christoph'},
         'prefSurname': {'Hürlimann'},
         'birthdate': {'1938'},
         'desc': {'Theologe', ' Schriftsteller'}}),
     ({'GND_ID': ['1066273278'],
         'Forenames': ['Urs Josef'],
         'Surnames': ['Cavelti'],
         'VariantForenames': ['Urs Joseph', 'Urs J.', 'Urs'],
         'VariantSurnames': ['Cavelti'],
         'Descriptions': ['St. Galler Politiker, Rechtsanwalt und Redaktor'],
         'Birthdate': ['1927-09-03'],
         'Deathdate': ['2003-11-04']},
      {'gid': {'1066273278'},
         'prefForename': {'Urs Josef'},
         'prefSurname': {'Cavelti'},
         'varForename': {'Urs', 'Urs J.', 'Urs Joseph'},
         'varSurname': {'Cavelti'},
         'birthdate': {'1927-09-03'},
         'deathdate': {'2003-11-04'},
         'desc': {'St. Galler Politiker, Rechtsanwalt und Redaktor'}})
     ],
)
def test_convert_gnd_format_kibana(person_dict, expected):
    assert convert_gnd_format_kibana(person_dict) == expected
