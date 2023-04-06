#!/usr/bin/env python3

# framework used to execute tasks based on configuration files

from typing import Any, TypeAlias, TypeVar, Callable
from expression import Result, Ok, Error, curry, curry_flip
from expression.extra.result import pipeline
from expression.collections import Seq

from io import TextIOWrapper
import sys
import os
import json

# Type variables (used with generic elements)
T = TypeVar('T')
U = TypeVar('U')
C = TypeVar('C')

# Type alias for IO
IO: TypeAlias = None

# Type alias for error messages
ErrorMessage: TypeAlias = str
TYPING_ERROR = ErrorMessage("typing error")

# Type alias for lists of error messages
ErrorList: TypeAlias = list[ErrorMessage]

# Type alias for some results
ResultWithErrors: TypeAlias = Result[T, ErrorList]

# Type alias for parsers
Parser: TypeAlias = Callable[[dict[Any, Any]], ResultWithErrors[T]]

# Type alias for setters
Setter: TypeAlias = Callable[[T], ResultWithErrors[T]]

# Type alias for workers
Worker: TypeAlias = Callable[[T], ResultWithErrors[U]]


class DirectoryPath:
    def __init__(self, name: str) -> None:
        self.name = name

    def chdir(self) -> None:
        os.chdir(self.name)


class FilePath:
    def __init__(self, name: str) -> None:
        self.name = name
        self.file = None

    def exists(self) -> bool:
        return os.path.exists(self.name)

    def isfile(self) -> bool:
        return os.path.isfile(self.name)

    def open(self) -> ResultWithErrors[TextIOWrapper]:
        try:
            self.file = open(self.name)
            return Ok(self.file)
        except IOError as e:
            return Error([ErrorMessage("could not open file %s, %s" % (self.name, e))])

    def close(self) -> None:
        if self.file is not None:
            self.file.close()

    def dirname(self) -> DirectoryPath:
        return DirectoryPath(os.path.dirname(self.name))

    def __repr__(self) -> str:
        return self.name.__repr__()


def result_folder(r: ResultWithErrors[T], acc: ResultWithErrors[T]) -> ResultWithErrors[T]:
    '''Folder for results with errors. Ok is neutral (takes acc for two Oks). Appends errors for Error.'''
    match r, acc:
        case Ok(_), _: return acc
        case Error(_), Ok(_): return r
        case Error(es1), Error(es2): return Error(es1+es2)
        case _: return Error([TYPING_ERROR])


def flatten(s: Seq[ResultWithErrors[T]], neutral: ResultWithErrors[T]) -> ResultWithErrors[T]:
    '''Flattens a sequence of results with errors'''
    result = neutral
    for r in s:
        result = result_folder(r, result)
    return result


@curry_flip(1)
def call_and_close(file: TextIOWrapper, f: Callable[[TextIOWrapper], T]) -> T:
    '''Calls f using file and then closes file'''
    assert (file is not None)
    result = f(file)
    file.close()
    return result


def make_file_path(name: str, complement: str, suffix: str) -> FilePath:
    '''Builds a file path from its parts'''
    return FilePath("%s_%s.%s" % (name, complement, suffix))


def make_file_path_and_check(name: str, complement: str, suffix: str) -> ResultWithErrors[FilePath]:
    '''Build a file path from its parts and checks if it corresponds to an existing file'''
    filename = make_file_path(name, complement, suffix)
    if not os.path.exists(filename.name) or not os.path.isfile(filename.name):
        return Error([ErrorMessage("wrong input file %s" % filename)])
    else:
        return Ok(filename)


@curry(1)
def load_configuration_from_file(parser: Parser[C], configuration_file: TextIOWrapper) -> ResultWithErrors[C]:
    '''Loads a configuration from a JSON file'''
    return json.load(configuration_file, object_hook=parser)


@curry(1)
def read_configuration(parser: Parser[C], configuration_path: FilePath) -> ResultWithErrors[C]:
    '''Reads a configuration from a file whose path is given'''
    return configuration_path.open().bind(call_and_close(load_configuration_from_file(parser)))


def run_with_config(configuration_path: FilePath, parser: Parser[C], setter: Setter[C], f: Worker[C, None]) -> ResultWithErrors[None]:
    '''Runs a function with a configuration file in the directory of this file'''
    assert (configuration_path.exists())
    current_path = DirectoryPath(os.getcwd())
    working_directory = configuration_path.dirname()
    working_directory.chdir()
    result = pipeline(
        read_configuration(parser),
        setter,
        f
    )(configuration_path)
    current_path.chdir()
    return result


def simple_main(args: list[str], parser: Parser[C], setter: Setter[C], f: Worker[C, None], usage: str) -> ResultWithErrors[None]:
    '''A very simple main.'''
    if len(args) != 2:
        return Error([ErrorMessage("wrong arguments\n%s" % usage)])
    configuration_filepath = FilePath(args[1])
    if not configuration_filepath.exists():
        return Error([ErrorMessage("file %s is not found" % configuration_filepath)])
    return run_with_config(configuration_filepath, parser, setter, f)


if __name__ == '__main__':
    exit_code = 0
    print("this is a framework, use import.")
    sys.exit(exit_code)
