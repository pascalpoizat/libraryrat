#!/usr/bin/env python3

# This script is used to fused screening results
# Requirements:
# - configuration file in <file>.json,
#       with Rs the list of reviewers and P the file prefix
#   example: see tests/study_001_config.json
# - source file <P>_source.ods
# - reviewers screening files <P>_<i>.ods, with <i> in Rs
# - target file <P>_target.ods

from typing import Any, TypeAlias
from pandas import DataFrame, ExcelFile, ExcelWriter
from expression import curry, Result, Ok, Error
from expression.extra.result import pipeline
from io import TextIOWrapper
import sys
import os
import json

USAGE = "%s <prefix>" % sys.argv[0]
COMPLEMENT_SOURCE = "source"
COMPLEMENT_TARGET = "target"
SUFFIX = "ods"

# Type alias for IO
IO: TypeAlias = None

# Type alias for error messages
ErrorMessage: TypeAlias = str

# Type alias for lists of error messages
ErrorList: TypeAlias = list[ErrorMessage]

# Type alias for reviewer names
ReviewerName: TypeAlias = str


class DirectoryPath:
    def __init__(self, name: str) -> None:
        self.name = name

    def chdir(self) -> None:
        os.chdir(self.name)


class FilePath:
    def __init__(self, name: str) -> None:
        self.name = name

    def exists(self) -> bool:
        return os.path.exists(self.name)

    def isfile(self) -> bool:
        return os.path.isfile(self.name)

    def open(self) -> Result[TextIOWrapper, ErrorList]:
        try:
            file = open(self.name)
            return Ok(file)
        except IOError as e:
            return Error([ErrorMessage("could not open file %s, %s" % (self.name, e))])

    def dirname(self) -> DirectoryPath:
        return DirectoryPath(os.path.dirname(self.name))

    def __repr__(self) -> str:
        return self.name.__repr__()


class Configuration:
    def __init__(self, prefix: str, sheet: str, index: str, reviewers: list[str]) -> None:
        self.prefix, self.sheet, self.index, self.reviewers = prefix, sheet, index, reviewers


class ApplicationError(Exception):
    def __init__(self, errors: ErrorList) -> None:
        self.errors = errors
        self.message = "application exception, errors: %s" % errors
        super().__init__(self.message)


def parse_configuration_from_json(configuration_dict: dict[Any, Any]) -> Result[Configuration, ErrorList]:
    if "prefix" in configuration_dict \
            and "sheet" in configuration_dict \
            and "index" in configuration_dict \
            and "reviewers" in configuration_dict:
        prefix = configuration_dict["prefix"]
        sheet = configuration_dict["sheet"]
        index = configuration_dict["index"]
        reviewers = configuration_dict["reviewers"]
        configuration = Configuration(
            prefix=prefix, sheet=sheet, index=index, reviewers=reviewers)
        return Ok(configuration)
    else:
        return Error([ErrorMessage("wrong JSON file")])


def check_inputs(source_df: DataFrame, reviews_df: list[tuple[ReviewerName, DataFrame]]) -> Result[None, ErrorList]:
    errors: ErrorList = []
    nb_records_source = len(source_df)
    nb_records_reviews = [(r, len(df)) for (r, df) in reviews_df]
    incorrect_reviews_1 = [(r, l) for (r, l) in nb_records_reviews
                           if l != nb_records_source]
    if len(incorrect_reviews_1) > 0:
        errors.append(ErrorMessage("mismatching number of rows for reviews %s" %
                      [r for (r, _) in incorrect_reviews_1]))
    header_source: list[str] = list(source_df.columns)
    headers_reviews: list[tuple[ReviewerName, list[str]]] = [
        (r, list(df.columns)) for (r, df) in reviews_df]
    incorrect_reviews_2 = [(r, h) for (r, h) in headers_reviews
                           if h != header_source]
    if len(incorrect_reviews_2) > 0:
        errors.append(ErrorMessage("mismatching headers for reviews %s" %
                      [r for (r, _) in incorrect_reviews_2]))
    if len(errors) == 0:
        return Ok(None)
    else:
        return Error(errors)


def make_filename(name: str, complement: str) -> FilePath:
    return FilePath("%s_%s.%s" % (name, complement, SUFFIX))


def make_filename_and_check(name: str, complement: str) -> FilePath:
    filename = make_filename(name, complement)
    if not os.path.exists(filename.name) or not os.path.isfile(filename.name):
        raise IOError("wrong input file %s" % filename)
    return filename


def work(source: FilePath, target: FilePath, reviews: list[tuple[ReviewerName, FilePath]], configuration: Configuration) -> Result[None, ErrorList]:
    sheet = configuration.sheet
    reader = ExcelFile(source.name, engine="odf")
    source_df = reader.parse(sheet_name=sheet)
    reviews_excels = [(r, ExcelFile(rf.name, engine="odf"))
                      for (r, rf) in reviews]
    reviews_df = [(r, ef.parse(sheet_name=sheet))
                  for (r, ef) in reviews_excels]
    check_result = check_inputs(source_df, reviews_df)
    if check_result.is_ok():
        target_df = source_df.copy()
        writer = ExcelWriter(target.name, engine="odf")
        target_df.to_excel(writer, sheet_name=configuration.sheet, index=False)
        writer.close()
    return check_result

@curry(1)
def run(directory: DirectoryPath, configuration: Configuration) -> Result[None, ErrorList]:
    base_name = configuration.prefix
    reviewer_names = configuration.reviewers
    try:
        current_path = DirectoryPath(os.getcwd())
        directory.chdir()
        source = make_filename_and_check(base_name, COMPLEMENT_SOURCE)
        target = make_filename(base_name, COMPLEMENT_TARGET)
        reviews = [(ReviewerName(n), make_filename_and_check(base_name, n))
                   for n in reviewer_names]
        work_result = work(source=source, target=target,
                           reviews=reviews, configuration=configuration)
        current_path.chdir()
        return work_result
    except IOError as e:
        return Error([ErrorMessage("file not found, %s" % e)])

def open_configuration_file(configuration_filepath: FilePath) -> Result[TextIOWrapper, ErrorList]:
    return configuration_filepath.open()

def load_configuration(file: TextIOWrapper) -> Result[Configuration, ErrorList]:
    return json.load(file, object_hook=parse_configuration_from_json)

def execute(configuration_filepath: FilePath) -> Result[None, ErrorList]:
    return pipeline(
        open_configuration_file,
        load_configuration,
        run(configuration_filepath.dirname())
    )(configuration_filepath)


if __name__ == '__main__':
    exit_code = 1
    if len(sys.argv) != 2:
        print(USAGE)
    else:
        configuration_filepath = FilePath(sys.argv[1])
        if not configuration_filepath.exists():
            print("file %s is not found" % configuration_filepath)
        else:
            print("running with configuration in %s" % configuration_filepath)
            match execute(configuration_filepath):
                case Error(errors):
                    print(errors)
                case Ok(_):
                    exit_code = 0
                case _:
                    pass
    sys.exit(exit_code)
