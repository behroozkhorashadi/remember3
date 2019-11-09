""" This module generates the store pickle file."""
import os.path

import remember.command_store_lib as com_lib
from remember import handle_args

IGNORE_RULE_FILE_NAME = 'ignore_rules.txt'


def main() -> None:
    """Main entry point for this module."""
    args = handle_args.setup_args_for_generate()
    generate_store_from_args(args.history_file_path, args.save_dir)


def generate_store_from_args(history_file_path: str, save_directory: str) -> None:
    store_file_path = com_lib.get_file_path(save_directory)
    commands_file_path = os.path.join(save_directory, com_lib.FILE_STORE_NAME)
    store = com_lib.load_command_store(store_file_path)
    tmp_file_path = os.path.join(save_directory, IGNORE_RULE_FILE_NAME)
    ignore_rule_file = tmp_file_path if os.path.isfile(tmp_file_path) else None
    com_lib.read_history_file(
        store,
        history_file_path,
        commands_file_path,
        ignore_rule_file)
    print('Read ' + history_file_path)


if __name__ == "__main__":
    main()
