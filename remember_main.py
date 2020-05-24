""" An executable python script that handles the remember command of the store.

This module runs the remember portion of the command store interaction. It
allows you to query all the stored commands and also delete them if you choose.
"""
import os
import time
from typing import Optional, List

import remember.command_store_lib as command_store
from remember.handle_args import setup_args_for_search
from remember.interactive import display_and_interact_results

IGNORE_RULE_FILE_NAME = 'ignore_rules.txt'


def main() -> Optional[str]:
    """Entry point for this executable python module."""
    args = setup_args_for_search()
    if not args.save_dir:
        return """To many or too few args.\n$> remember.py [
                 file_store_directory_path] [history_file_path]
                 ['word|phrase to look up']"""
    if not args.history_file_path:
        return """To many or too few args.\n$> remember.py [
                 file_store_directory_path] [history_file_path]
                 ['word|phrase to look up']"""
    return run_remember_command(args.save_dir, args.history_file_path, args.query,
                                args.all, args.startswith, args.execute, args.max)


def run_remember_command(save_dir: str, history_file_path: str, query: List[str], search_all: bool,
                         search_starts_with: bool, execute: bool,
                         max_return_count: int) -> Optional[str]:
    store_file_path = command_store.get_file_path(save_dir)
    store = command_store.load_command_store(store_file_path)
    command_store.start_history_processing(store, history_file_path, save_dir, 20)
    print('Looking for all past commands with: ' + ", ".join(query))
    start_time = time.time()
    result = store.search_commands(query, search_starts_with, search_info=search_all)
    total_time = time.time() - start_time
    print("Search time %.5f:  seconds" % total_time)
    return display_and_interact_results(
        result, max_return_count, save_dir, history_file_path, query, execute)


if __name__ == "__main__":
    main()
