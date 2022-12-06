# Library Rat / scripts

- DBLP-related scripts
    - `doiFromDblpJson`: gets the list of electronic edition links from a DBLP JSON export file
    - `doiFromDblpJsonMulti`: run `doiFromDblpJson` for a list of DBLP JSON export files sharing a given prefix (all `<prefix>_*.json` files)
    - `urlFromDblp`: gets the list of URLs from a DBLP JSON export file

## Examples

### Getting all links (DOI, ArXiV, ...) from a search

1. search for papers with `"systematic mapping study"` in the title on [DBLP](dblp.org), you can [click here](https://dblp.org/search?q=%20systematic%20mapping%20study%20).

2. export the search in JSON format into file `SMS.json`

3. get links using `doiFromDblpJson`:

```sh
➜ ./doiFromDblpJson.sh SMS.json
https://doi.org/10.1109/ACCESS.2022.3165079
https://doi.org/10.1145/3555228.3555273
https://doi.org/10.1007/s10723-021-09587-7
...
```

4. you can then import these in your favorite bibliography tool.

### Getting all links (DOI, ArXiV, ...) from several constrained searches

1. search for papers with `"systematic mapping study"` in the Information \& Software Technology journal (`type:Journal_Articles: streamid:journals/infsof:`) by [clicking here](https://dblp.org/search?q=%20systematic%20mapping%20study%20%20type%3AJournal_Articles%3A%20streamid%3Ajournals%2Finfsof%3A). Export as JSON in file `SMS_IST.json`.

2. perform the search search in the Journal of Systems and Software journal (`"systematic mapping study" type:Journal_Articles: streamid:journals/jss:`) by [clicking here](https://dblp.org/search?q=%20systematic%20mapping%20study%20%20type%3AJournal_Articles%3A%20streamid%3Ajournals%2Fjss%3A). Export as JSON in file `SMS_JSS.json`.

3. get links using `doiFromDblpJsonMulti`:

```sh
➜ ./doiFromDblpJsonMulti.sh SMS
2 files treated
89 DOI found
➜ cat SMS.doi
https://doi.org/10.1016/j.infsof.2022.107018
https://doi.org/10.1016/j.infsof.2021.106675
https://doi.org/10.1016/j.infsof.2020.106448
...
```

