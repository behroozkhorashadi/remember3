""" An executable python script that handles the remember command of the store.

This module runs the remember portion of the command store interaction. It
allows you to query all the stored commands and also delete them if you choose.
"""
from typing import Optional, List

import remember.command_store_lib as command_store
from remember.handle_args import setup_args_for_search
from remember.interactive import InteractiveCommandExecutor


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
                                args.all, args.startswith, args.execute)


def run_remember_command(save_dir: str, history_file_path: str, query: List[str], search_all: bool,
                         search_starts_with: bool, execute: bool) -> Optional[str]:
    store_file_path = command_store.get_file_path(save_dir)
    store = command_store.load_command_store(store_file_path)
    print('Looking for all past commands with: ' + ", ".join(query))
    result = store.search_commands(query, search_starts_with, search_info=search_all)
    print("Number of results found: " + str(len(result)))
    try:
        if execute:
            command_executor = InteractiveCommandExecutor(history_file_path)
            if not command_executor.run(result):
                return 'Exit'
        command_store.print_commands(result, query)
        return None
    finally:
        store.close()


if __name__ == "__main__":
    main()
