#! /usr/bin/env python
""" This module generates the store pickle file."""
import argparse
import os.path
import remember.command_store_lib as com_lib
from remember import handle_args

IGNORE_RULE_FILE_NAME = 'ignore_rules.txt'


def main():
    """Main entry point for this module."""
    args = handle_args.setup_args_for_generate()
    generate_store_from_args(args.historyfile, args.save_dir)


def generate_store_from_args(history_file_path, save_directory):
    store_file_path = com_lib.get_file_path(save_directory)
    commands_file_path = os.path.join(save_directory, com_lib.FILE_STORE_NAME)
    ignore_rule_file = os.path.join(save_directory, IGNORE_RULE_FILE_NAME)
    if not os.path.isfile(ignore_rule_file):
        ignore_rule_file = None
    else:
        print('Using ignore rules from ' + ignore_rule_file)
    store = com_lib.load_command_store(store_file_path)
    com_lib.read_history_file(
        store,
        history_file_path,
        commands_file_path,
        ignore_rule_file)
    print('Read ' + history_file_path)


if __name__ == "__main__":
    main()
