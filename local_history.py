import os
import time
from typing import Optional

from remember.handle_args import setup_args_for_local_history
import remember.command_store_lib as command_store
from remember.interactive import load_user_interactor


def main() -> Optional[str]:
    args = setup_args_for_local_history()
    if not args.save_dir:
        return """To many or too few args.\n$> remember.py [
                 file_store_directory_path] [history_file_path]
                 ['word|phrase to look up']"""
    if not args.history_file_path:
        return """To many or too few args.\n$> remember.py [
                 file_store_directory_path] [history_file_path]
                 ['word|phrase to look up']"""
    return run_history_command(args.save_dir, args.history_file_path, os.getcwd(),
                               args.execute, args.max)


def run_history_command(save_dir: str, history_file_path: str, directory: str,
                        execute: bool, max_results: int) -> Optional[str]:
    store_file_path = command_store.get_file_path(save_dir)
    store = command_store.load_command_store(store_file_path)
    command_store.start_history_processing(store, history_file_path, save_dir, 1)
    print(f'Looking for all past commands with: {directory}')
    start_time = time.time()
    result = store.get_command_with_context(directory)
    total_time = time.time() - start_time
    print("Search time %.5f:  seconds" % total_time)
    print(f"Number of results found: {str(len(result))}")
    last_saved_file_path = os.path.join(save_dir, command_store.DEFAULT_LAST_SAVE_FILE_NAME)
    command_store.save_last_search(last_saved_file_path, result)
    if execute:
        command_executor = load_user_interactor()
        if not command_executor.run(result):
            return 'Exit'
    command_store.print_commands(result)
    return ''


if __name__ == "__main__":
    main()
