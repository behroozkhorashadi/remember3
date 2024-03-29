import argparse
import os

from remember.constants import CUSTOM_HISTORY_FILE_PATH


def setup_for_execute_last() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    add_save_dir(parser)
    add_history_arg_to_parser(parser)
    parser.add_argument(
        "index",
        type=int,
        help="The index for the command to re-execute")
    return parser.parse_args()


def setup_args_for_update() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    add_search(parser)
    parser.add_argument(
        "-u",
        "--updateinfo",
        help="Search the commands AND the extra command context info .",
        action="store_true")
    parser.add_argument(
        "-d",
        "--delete",
        help="Delete mode where you able to delete commands from the store.",
        action="store_true")
    add_required_terms(parser, False)
    return parser.parse_args()


def setup_args_for_search() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    add_search(parser)
    parser.add_argument(
        "-e",
        "--execute",
        help="Execute the searched commands.",
        action="store_true")
    add_required_terms(parser, True)
    return parser.parse_args()


def setup_args_for_setup() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    # auto find this
    parser.add_argument(
        "--rc_file",
        required=False,
        help="The path to you bash or zsh rc file.")
    return parser.parse_args()


def setup_args_for_generate() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    add_history_arg_to_parser(parser)
    add_save_dir(parser)
    return parser.parse_args()


def setup_args_for_local_history() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    add_save_dir(parser)
    add_history_arg_to_parser(parser)
    add_result_count_max(parser)
    parser.add_argument(
        "-q",
        "--query",
        default='',
        nargs='?',
        help="The term to search for. ex: 'git', 'foo'")
    parser.add_argument(
        "-e",
        "--execute",
        help="Execute the searched commands.",
        action="store_true")
    return parser.parse_args()


def add_history_arg_to_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-p",
        "--history_file_path",
        default=CUSTOM_HISTORY_FILE_PATH,
        help="The path to the history file. ex: '~/.bash_history'")


def add_search(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-a",
        "--all",
        help="Search the commands AND the extra command context info .",
        action="store_true")
    parser.add_argument(
        "-s",
        "--startswith",
        help="Show only commands that strictly start with input command.",
        action="store_true")
    add_result_count_max(parser)


def add_save_dir(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-s"
        "--save_dir",
        default=os.path.expanduser("~/.remember3"),
        help="The directory path. ex: ~/dir/where/serializedfile/is")


def add_result_count_max(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-m",
        "--max",
        type=int,
        default=10,
        help="the maximum number of returned results you want to see.")


def add_required_terms(parser: argparse.ArgumentParser, add_history_arg: bool = False) -> None:
    add_save_dir(parser)
    if add_history_arg:
        add_history_arg_to_parser(parser)
    parser.add_argument(
        "query",
        nargs='+',
        help="The term to search for. ex: 'git pull', git")
