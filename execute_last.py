import os
import subprocess

from remember import command_store_lib, interactive
from remember.command_store_lib import read_last_search, DEFAULT_LAST_SAVE_FILE_NAME
from remember.handle_args import setup_for_execute_last
from remember.interactive import get_user_input


def main() -> None:
    args = setup_for_execute_last()
    file_path = os.path.join(args.save_dir, DEFAULT_LAST_SAVE_FILE_NAME)
    last_search_results = read_last_search(file_path)
    selected_command = last_search_results[args.index - 1]
    red = command_store_lib.BColors.FAIL
    white = command_store_lib.BColors.ENDC
    msg = f'You want to execute -> {red}{selected_command}{white} (just hit enter for yes and ' \
          f'type anything else for no): '
    user_response = get_user_input(msg)
    if user_response:
        return
    subprocess.call(selected_command, shell=True)
    interactive.write_to_hist_file(args.history_file_path, selected_command)


if __name__ == "__main__":
    main()
