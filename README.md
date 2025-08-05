# CHNobLi

## How to run it

The repository for the Algorithmic Data Layer (ADL).

ADL is made up of three primary components (see
[docker-compose.yml](docker-compose.yml)).
Overview over the services:

- tagging: Contains Python code for tagging 
- aggregation: Aggregates entities based on names and where they appear in the text.
- linking: ElasticSearch index with databases from the Deutsche Nationalbibliothek and WikiData. [TODO which versions / when downloaded] used to link tagged entities.
 
### 2.1 Local deployment

1. Create a `docs` folder: TODO change this to "documents" folder or something, docs is now the documentation!
   ```bash
   mkdir -p private/docs  private/output
   ```
The folder `private/docs` and `private/output` is mounted into the linking container. The documents that need to processed must be copied to the docs folder.

2. Register the `private` folder in the file `.git/info/exclude` ("private" `.gitignore`)
   ```bash
   echo /private/ >> .git/info/exclude

3. Building and running the docker images
   ```docker compose -f docker-compose-dev.yml build --no-cache
      docker compose -f docker-compose-dev.yml up -d
   ```

4. Running it
   ```docker exec -it linking /bin/bash
   ```
   4.1 Tagging
   Always on year-level.
   ```python main.py --tasks prep,tag --magazine_year_paths /docs/obl/2004_000
   ```
   4.2 Linking
   if the tagging is already done, then it can be done on magazine-level.
   ```python main.py --tasks finish --magazine_year_paths /docs/obl
   ```

### Ground-Truth data
The text for our manually linked ground-truth data can be downloaded here: https://polybox.ethz.ch/index.php/s/uMqGWOaen8dVIAY

## How to evaluate
To evaluate the output of this system, you need
1. **Ground-Truth data**

There are two sets of ground-truth data both describing select years and pages of the same magazines [cmt,edu,fsi,gfr,hvg,obl,rep,tjb,woh,zlp,zut]. One set was created "with fuzzy matching" i.e. minor misspellings of the name of the entity are tolerated when looking for the corresponding GND entry, the other was created "without fuzzy matching", so only the name on the screen was considered.

To select which ground-truth dataset you would like to evaluate against, set the command-line argument "--fuzzy True" or "--fuzzy False". If nothing is set, the default is "--fuzzy True".

Your configuration file then specifies where the ground-truth data for the fuzzy level sits:
`nla/configs/eval_config.json`

2. **Evaluation level**

Evaluation can be done on an entity or reference level. To select which level of evaluation you would like to see, set the command-line argument "--eval_level ref" or "--eval_level ent".

3. **Run eval**

You can simply run the script:

`sh scripts/eval.sh`

Where the magazine_year_paths argument describes the path to the dictionary where the data to be evaluated lies.
No worries if that directory contains even more linked files, only the ones for which a corresponding GT file exist are compared.
**Note however that for each extant GT file, there must exist a corresponding linked file.** So if you would like to exclude some GT
files, you must exclude them by removing them from the directory of GT data. This is to ensure that your model is tested against a variety of magazines and can be fairly compared to previous runs.

4. **Analyze evaluation**

In the "PATH_TO_OUTFILE_FOLDER" specified in your "configurations.json" you can find the evaluations for each magazine in the corresponding file, for each year in a seperate file under the magazine directory, and aggregated for all magazines and years under for example `eval_ent_with_fuzzy.json`. 

## How to test
Our workflow makes sure that you pass all the unit tests as you commit, but if you would like to check for yourself if some integration tests work:


1. **scripts/test_linking.sh**

this script uses the tagging output of the system before your changes were made and runs linking on them. Then it compares it to a given magazine (default is obl-2004) and raises an exception if something changed. It only checks the data in "nla/data/test_data".

*NOTE* Unfortunately, the results change based on whether or not "data2" is mounted. That is because it gives us structure information which changes our aggregation. Thus we have two test data files, "data2" and "nodata2".

2. **scripts/test_tagging.sh**

This script uses the raw txt files of the obl magazine and runs your tagging on them. It then compares the output to "nla/data/test_data/output_before" where we keep the previous output of obl for comparison purposes. It raises an exception if anything changed.


3. **scripts/test_end_to_end.sh**

This script runs tagging and linking on the raw text files. It then compares the output to "nla/data/test_data/output_before" where we keep the previous output of obl for comparison purposes. It raises an exception if anything changed.

4. **Manual** 

If you would like to compare manually, compare the two jsons (previous output in "output_before" and new output) with a program ("meld" for example) or the vscode comparator.

For the vscode comparator, select the two files, right-click, select *compare selected* then in each document, right-click and select *format document*

Note that some differences may be due to re-ordering and some are due to the fact that the rule-based system is not entirely deterministic.