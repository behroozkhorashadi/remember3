"""
This module handles the command store interactive mode.
"""
import subprocess
from typing import List, Optional

import remember.command_store_lib as command_store
from remember.command_store_lib import bcolors, SqlCommandStore


class InteractiveCommandExecutor(object):
    def __init__(self, history_file_path: Optional[str] = None) -> None:
        self._history_file_path = history_file_path

    def run(self, result: List) -> bool:
        """Interactively enumerate a set of commands and pick one to run."""
        self._enumerate_commands(result)
        return self._select_command(result)

    def _select_command(self, command_results: List) -> bool:
        user_input = get_user_input('Choose command by # or type anything else to quit: ')
        value = represents_int(user_input)
        if value and value <= len(command_results) > 0:
            command = command_results[value - 1]
            if self._history_file_path:
                with open(self._history_file_path, "a") as myfile:
                    myfile.write(command.get_unique_command_id() + '\n')
            subprocess.call(command.get_unique_command_id(), shell=True)
            return True
        else:
            return False

    def command_info_interaction(self, command_results: List) -> bool:
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
                    print('Dropping invalid entry ' + index_str)
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
            print(bcolors.HEADER + "(" + str(idx + 1) + ") "
                  + bcolors.OKGREEN + command.get_unique_command_id()
                  + bcolors.ENDC)


def get_user_input(msg: str) -> str:
    result = input(msg)
    print(type(result))
    assert isinstance(result, str)
    return result


def represents_int(value: str) -> Optional[int]:
    try:
        return int(value)
    except ValueError:
        return None
