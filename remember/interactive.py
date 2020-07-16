"""
This module handles the command store interactive mode.
"""
import os
import subprocess
from typing import List, Optional

import remember.command_store_lib as command_store
from remember.command_store_lib import BColors, SqlCommandStore
from remember.sql_store import Command


class InteractiveCommandExecutor(object):
    def __init__(self, history_file_path: Optional[str] = None) -> None:
        self._history_file_path = history_file_path

    def run(self, result: List[command_store.Command]) -> bool:
        """Interactively enumerate a set of commands and pick one to run."""
        self._enumerate_commands(result)
        return self._select_command(result)

    def _select_command(self, command_results: List[command_store.Command]) -> bool:
        user_input = get_user_input('Choose command by # or type anything else to quit: ')
        value = represents_int(user_input)
        if value and value <= len(command_results) > 0:
            command = command_results[value - 1]
            if self._history_file_path:
                write_to_hist_file(self._history_file_path, command.get_unique_command_id())
            shell_env = os.getenv('SHELL')
            selected_command = command.get_unique_command_id()
            if not shell_env:
                subprocess.call(selected_command, shell=True)
            else:
                subprocess.call([shell_env, '-i', '-c', selected_command])
            return True
        else:
            return False

    def command_info_interaction(self,
                                 command_results: List[command_store.Command],
                                 store: SqlCommandStore) -> bool:
        """Interactively choose a command to set command info for."""
        self._enumerate_commands(command_results)

        user_input = get_user_input('Choose command by # or ' +
                                    'type anything else to quit: ')
        value = represents_int(user_input)
        if value and len(command_results) >= value > 0:
            command = command_results[value - 1]
            user_input = get_user_input('What would you like to add '
                                        'as searchable info for this command:\n')
            command.set_command_info(user_input)
            store.update_command_info(command)
            command_store.print_command(1, command)
            return True
        else:
            return False

    @staticmethod
    def delete_interaction(store: SqlCommandStore, commands: List) -> bool:
        """Delete a command from the store."""
        changes_made = False
        user_input = get_user_input('Which commands do you want '
                                    + 'delete (ex: 1,4,9,14 or allofthem or quit)?')
        if user_input == 'quit':
            return False
        if user_input == 'allofthem':
            delete_indicies = list(range(1, len(commands) + 1))
        else:
            delete_indicies = []
            for index_str in user_input.split(','):
                index = int(index_str.strip())
                if 0 < index <= len(commands):
                    delete_indicies.append(index)
                else:
                    print(f'{index} is not a valid index')
        if not delete_indicies:
            return False
        user_input = get_user_input('Delete ' + str(delete_indicies) + '? [y|n]')
        if user_input == 'y':
            for x in delete_indicies:
                command = commands[x - 1]
                store.delete_command(command.get_unique_command_id())
                print('deleting ' + command.get_unique_command_id())
                changes_made = True
        return changes_made

    @staticmethod
    def _enumerate_commands(command_results: List) -> None:
        for idx, command in enumerate(command_results):
            print(BColors.HEADER + "(" + str(idx + 1) + ") "
                  + BColors.OKGREEN + command.get_unique_command_id()
                  + BColors.ENDC)


def load_user_interactor(history_file_path: Optional[str] = None) -> InteractiveCommandExecutor:
    return InteractiveCommandExecutor(history_file_path)


def get_user_input(msg: str) -> str:
    result = input(msg)
    assert isinstance(result, str)
    return result


def represents_int(value: str) -> Optional[int]:
    try:
        return int(value)
    except ValueError:
        return None


def write_to_hist_file(history_file_path: str, command_to_write: str) -> None:
    last_line = _get_last_line(history_file_path)
    if last_line.startswith(":"):
        incremented_time = _get_history_line_time(last_line) + 1
        line_to_write = f': {incremented_time}:0;{command_to_write}'
    else:
        line_to_write = command_to_write
    with open(history_file_path, "a") as history_file:
        history_file.write(line_to_write + '\n')


def _get_history_line_time(history_file_entry: str) -> int:
    return int(history_file_entry.split(':')[1].strip())


def _get_last_line(history_file_path: str) -> str:
    with open(history_file_path, 'rb') as history_file:
        last_line_binary = history_file.readlines()[-1]
        return last_line_binary.decode("utf-8")


def display_and_interact_results(result: List[Command],
                                 max_return_count: int,
                                 save_dir: str,
                                 history_file_path: str,
                                 query: Optional[List[str]],
                                 execute: bool) -> Optional[str]:
    print(f"Number of results found: {str(len(result))}")
    if len(result) > max_return_count:
        print(f"Results truncated to the first: {max_return_count}")
        result = result[:max_return_count]
    last_saved_file_path = os.path.join(save_dir, command_store.DEFAULT_LAST_SAVE_FILE_NAME)
    command_store.save_last_search(last_saved_file_path, result)
    if execute:
        command_executor = load_user_interactor(history_file_path)
        if not command_executor.run(result):
            return 'Exit'
    command_store.print_commands(result, query)
    return None
