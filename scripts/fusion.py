#!/usr/bin/env python3

# This script is used to fused screening results
# Requirements:
# - configuration file in <file>.json,
#       with Rs the list of reviewers and P the file prefix
#   example: see tests/study_001_config.json
# - source file <P>_source.ods
# - reviewers screening files <P>_<i>.ods, with <i> in Rs
# - target file <P>_target.ods

import sys
import os
import json
import pandas as pd

USAGE = "%s <prefix>" % sys.argv[0]
COMPLEMENT_SOURCE = "source"
COMPLEMENT_TARGET = "target"
SUFFIX = "ods"


class Configuration:
    def __init__(self, prefix, sheet, index, reviewers):
        self.prefix, self.sheet, self.index, self.reviewers = prefix, sheet, index, reviewers


class ApplicationError(Exception):
    def __init__(self, errors, message="application exception"):
        self.errors = errors
        self.message = "application exception, errors: %s" % errors
        super().__init__(self.message)

def parse_configuration_from_json(configuration_dict):
    if "prefix" in configuration_dict \
            and "sheet" in configuration_dict \
            and "index" in configuration_dict \
            and "reviewers" in configuration_dict:
        configuration = Configuration(prefix=configuration_dict["prefix"],
                                      sheet=configuration_dict["sheet"],
                                      index=configuration_dict["index"],
                                      reviewers=configuration_dict["reviewers"])
        return (configuration, "")
    else:
        return (None, "wrong JSON file")

# input files conditions
# - same number of records
# - same column headings
def check_inputs(source_df, reviews_df):
    errors = []
    nb_records_source = len(source_df)
    nb_records_reviews = [(r, len(df)) for (r, df) in reviews_df]
    incorrect_reviews_1 = [(r, l) for (r, l) in nb_records_reviews
                            if l != nb_records_source]
    if len(incorrect_reviews_1) > 0:
        errors.append("mismatching number of rows for reviews %s" %
                      [r for (r, l) in incorrect_reviews_1])
    header_source = list(source_df.columns)
    headers_reviews = [(r, list(df.columns)) for (r, df) in reviews_df]
    incorrect_reviews_2 = [(r, h) for (r, h) in headers_reviews
                           if h != header_source]
    if len(incorrect_reviews_2) > 0:
        errors.append("mismatching headers for reviews %s" %
                      [r for (r, l) in incorrect_reviews_2])
    return (len(errors) == 0, errors)


def make_filename(name, complement):
    return "%s_%s.%s" % (name, complement, SUFFIX)


def make_filename_and_check(name, complement):
    filename = make_filename(name, complement)
    if not os.path.exists(filename) or not os.path.isfile(filename):
        raise IOError("wrong input file %s" % filename)
    return filename


def work(source, target, reviews, configuration):
    sheet = configuration.sheet
    print("source is: %s" % source)
    print("target is: %s" % target)
    print("reviews are: %s" % reviews)
    source_df = pd.ExcelFile(source, engine="odf").parse(sheet_name=sheet)
    reviews_excels = [(r, pd.ExcelFile(rf, engine="odf"))
                      for (r, rf) in reviews]
    reviews_df = [(r, ef.parse(sheet_name=sheet))
                  for (r, ef) in reviews_excels]
    (correct, errors) = check_inputs(source_df, reviews_df)
    if correct:
        target_df = source_df.copy()
        writer = pd.ExcelWriter(target, engine="odf")
        target_df.to_excel(writer, sheet_name=configuration.sheet, index=False)
        writer.close()
    else:
        raise ApplicationError(errors=errors)


def run(configuration, directory):
    base_name = configuration.prefix
    reviewer_names = configuration.reviewers
    try:
        current_path = os.getcwd()
        os.chdir(directory)
        source = make_filename_and_check(base_name, COMPLEMENT_SOURCE)
        target = make_filename(base_name, COMPLEMENT_TARGET)
        reviews = [(n, make_filename_and_check(base_name, n))
                   for n in reviewer_names]
        work(source=source, target=target,
             reviews=reviews, configuration=configuration)
        os.chdir(current_path)
    except IOError as e:
        print("file not found, %s" % e)
    except ApplicationError as e:
        print("incorrect input files, %s" % e)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(USAGE)
        sys.exit(1)
    else:
        configuration_file = sys.argv[1]
        if not os.path.exists(configuration_file):
            print("file %s is not found" % configuration_file)
        else:
            print("running with configuration in %s" % configuration_file)
            directory = os.path.dirname(configuration_file)
            try:
                file = open(configuration_file)
                (configuration, error) = json.load(file, object_hook=parse_configuration_from_json)
                file.close()
                if configuration is None:
                    print("error in JSON file %s" % configuration_file)
                else:
                    run(configuration=configuration, directory=directory)
            except OSError:
                print("could not read file %s" % configuration_file)
