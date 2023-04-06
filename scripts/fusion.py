#!/usr/bin/env python3

# This script is used to fuse screening results
# Requirements:
# - configuration file in <file>.json,
#       with Rs the list of reviewers and P the file prefix
#   example: see tests/study_001_config.json
# - source file <P>_source.ods
# - reviewers screening files <P>_<i>.ods, with <i> in Rs
# - target file <P>_target.ods

import sys
from typing import Any, TypeAlias, TypeVar
from framework import FilePath, ErrorMessage, ResultWithErrors, simple_main, make_file_path, make_file_path_and_check, flatten
from expression import Ok, Error
from expression.collections import Seq
from pandas import DataFrame, ExcelFile, ExcelWriter

USAGE = "%s <prefix>" % sys.argv[0]
COMPLEMENT_SOURCE = "source"
COMPLEMENT_TARGET = "target"
SUFFIX = "ods"

# Type variable
T = TypeVar('T')

# Type alias for reviewer names
ReviewerName: TypeAlias = str

# Type alias for reviewer-associated data
Reviewed: TypeAlias = tuple[ReviewerName, T]


class Configuration:
    def __init__(self, prefix: str, sheet: str, index: str, reviewers: list[str]) -> None:
        self.prefix, self.sheet, self.index, self.reviewers = prefix, sheet, index, reviewers
        self.source_path: FilePath = FilePath("")
        self.target_path: FilePath = FilePath("")
        self.review_paths: list[Reviewed[FilePath]] = []


def check_same_length(source_df: DataFrame, review_df: Reviewed[DataFrame]) -> ResultWithErrors[None]:
    nb_records_source = len(source_df)
    (r, df) = review_df
    nb_records_review = len(df)
    if nb_records_review != nb_records_source:
        return Error([ErrorMessage("mismatching number of rows for review %s" % r)])
    else:
        return Ok(None)


def check_same_header(source_df: DataFrame, review_df: Reviewed[DataFrame]) -> ResultWithErrors[None]:
    header_source: list[str] = list(source_df.columns)
    (r, df) = review_df
    header_review: list[str] = list(df.columns)
    if header_review != header_source:
        return Error([ErrorMessage("mismatching header for review %s" % r)])
    else:
        return Ok(None)


def check_known_reviewers(source_df: DataFrame, review_df: Reviewed[DataFrame]) -> ResultWithErrors[None]:
    # TODO: check all reviewer names in reviewer columns are in the declared reviewers
    # TODO: check all reviewer names in reviewer columns have a corresponding reviewer file (until we do incremental fusion)
    return Ok(None)


def check_review(source_df: DataFrame, review_df: Reviewed[DataFrame]) -> ResultWithErrors[None]:
    checkers = Seq(
        [check_same_length, check_same_header, check_known_reviewers])
    return flatten(checkers.map(lambda f: f(source_df, review_df)), Ok(None))


def check_reviews(source_df: DataFrame, review_dfs: list[Reviewed[DataFrame]]) -> ResultWithErrors[None]:
    results = Seq(review_dfs).map(lambda r: check_review(source_df, r))
    return flatten(results, Ok(None))


def fuse(source_df: DataFrame, review_dfs: list[Reviewed[DataFrame]], configuration: Configuration) -> ResultWithErrors[None]:
    return Ok(None)  # TODO: implement function


def work(configuration: Configuration) -> ResultWithErrors[None]:
    sheet = configuration.sheet
    reader = ExcelFile(configuration.source_path.name, engine="odf")
    source_df = reader.parse(sheet_name=sheet)
    reviews_excels = [(reviewer, ExcelFile(review_path.name, engine="odf"))
                      for (reviewer, review_path) in configuration.review_paths]
    review_dfs = [(reviewer, ef.parse(sheet_name=sheet))
                  for (reviewer, ef) in reviews_excels]
    check_result = check_reviews(source_df, review_dfs)
    if check_result.is_ok():
        target_df = fuse(source_df, review_dfs, configuration)
        writer = ExcelWriter(configuration.target_path.name, engine="odf")
        target_df.to_excel(writer, sheet_name=configuration.sheet, index=False)
        writer.close()
        return Ok(None)
    else:
        return check_result


def set_paths(configuration: Configuration) -> ResultWithErrors[Configuration]:
    base_name = configuration.prefix
    reviewer_names = configuration.reviewers
    target_path = make_file_path(base_name, COMPLEMENT_TARGET, SUFFIX)
    source_path = make_file_path_and_check(
        base_name, COMPLEMENT_SOURCE, SUFFIX)
    review_paths = [(ReviewerName(n), make_file_path_and_check(base_name, n, SUFFIX))
                    for n in reviewer_names]


def parse(configuration_dict: dict[Any, Any]) -> ResultWithErrors[Configuration]:
    KEYS = ("prefix", "sheet", "index", "reviewers")
    if all(key in configuration_dict for key in KEYS):
        prefix, sheet, index, reviewers = [
            configuration_dict[key] for key in KEYS]
        configuration = Configuration(
            prefix=prefix, sheet=sheet, index=index, reviewers=reviewers)
        return Ok(configuration)
    else:
        return Error([ErrorMessage("wrong JSON file")])


if __name__ == '__main__':
    result = simple_main(sys.argv, parse, set_paths, work, USAGE)
    if result.is_error():
        print(result)
        sys.exit(1)
    else:
        sys.exit(0)
