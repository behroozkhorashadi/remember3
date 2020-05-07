""" This module generates the store pickle file."""

import remember.command_store_lib as com_lib
from remember import handle_args

IGNORE_RULE_FILE_NAME = 'ignore_rules.txt'


def main() -> None:
    """Main entry point for this module."""
    args = handle_args.setup_args_for_generate()
    com_lib.generate_store_from_args(args.history_file_path, args.save_dir)


if __name__ == "__main__":
    main()
