# flake8: noqa
import os
import subprocess
import sys
import unittest
from functools import partial
from typing import Any
from unittest import mock

from mock import patch, Mock, mock_open

import remember.command_store_lib as command_store_lib
from remember.command_store_lib import Command
from remember.interactive import InteractiveCommandExecutor, display_and_interact_results, \
    load_user_interactor

TEST_PATH_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, TEST_PATH_DIR + '/../')


class Test(unittest.TestCase):
    def test_command_update_info_should_correctly_set_info(self) -> None:
        interactive_command = InteractiveCommandExecutor()
        store = command_store_lib.SqlCommandStore()
        command = Command("git rest --hard HEAD")
        command_info = 'command info'
        user_input = ['1', command_info]
        store.add_command(command)
        with patch('builtins.input', side_effect=user_input):
            interactive_command.command_info_interaction([command], store)
        self.assertEqual(command.get_command_info(), command_info)
        self.assertEqual(command_info, store.search_commands(['git'])[0].get_command_info())

    def test_command_update_info_should_fail_set_info_because_exit(self) -> None:
        interactive_command = InteractiveCommandExecutor()
        command = Command("git rest --hard HEAD")
        user_input = ['exit']
        store = mock.Mock()
        with patch('builtins.input', side_effect=user_input):
            self.assertFalse(interactive_command.command_info_interaction([command], store))
        self.assertEqual(command.get_command_info(), "")
        store.update_command_info.assert_not_called()

    def test_delete_command_from_store_should_delete(self) -> None:
        store = command_store_lib.SqlCommandStore(':memory:')
        command = Command("testing delete this command")
        store.add_command(command)
        self.assertEqual(store.get_num_commands(), 1)
        user_input = ['1', 'y']
        with patch('builtins.input', side_effect=user_input):
            self.assertTrue(InteractiveCommandExecutor.delete_interaction(store, [command]))
        self.assertEqual(store.get_num_commands(), 0)

    def test_delete_command_from_store_when_no_should_not_delete(self) -> None:
        store = command_store_lib.SqlCommandStore(':memory:')
        command = Command("testing delete this command")
        store.add_command(command)
        self.assertEqual(store.get_num_commands(), 1)
        user_input = ['1', 'n']
        with patch('builtins.input', side_effect=user_input):
            self.assertFalse(InteractiveCommandExecutor.delete_interaction(store, [command]))
        self.assertEqual(store.get_num_commands(), 1)

    def test_delete_command_from_store_with_all_should_remove_all(self) -> None:
        store = command_store_lib.SqlCommandStore(':memory:')
        command = Command("testing delete this command")
        command2 = Command("remove this also")
        self.assertEqual(store.get_num_commands(), 0)
        store.add_command(command)
        store.add_command(command2)
        self.assertEqual(store.get_num_commands(), 2)
        user_input = ['allofthem', 'y']
        with patch('builtins.input', side_effect=user_input):
            self.assertTrue(InteractiveCommandExecutor.delete_interaction(store,
                                                                          [command, command2]))
        self.assertEqual(store.get_num_commands(), 0)

    def test_delete_command_from_store_with_1_2_should_remove_all(self) -> None:
        store = command_store_lib.SqlCommandStore(':memory:')
        command = Command("testing delete this command")
        command2 = Command("remove this also")
        self.assertEqual(store.get_num_commands(), 0)
        store.add_command(command)
        store.add_command(command2)
        self.assertEqual(store.get_num_commands(), 2)
        interactive_command = InteractiveCommandExecutor()
        user_input = ['1, 2', 'y']
        with patch('builtins.input', side_effect=user_input):
            self.assertTrue(interactive_command.delete_interaction(store, [command, command2]))
        self.assertEqual(store.get_num_commands(), 0)

    def test_delete_command_from_store_with_invalid_should_remove_1(self) -> None:
        store = command_store_lib.SqlCommandStore(':memory:')
        command = Command("testing delete this command")
        command2 = Command("remove this also")
        self.assertEqual(store.get_num_commands(), 0)
        store.add_command(command)
        store.add_command(command2)
        self.assertEqual(store.get_num_commands(), 2)
        interactive_command = InteractiveCommandExecutor()
        user_input = ['1, 9', 'y']
        with patch('builtins.input', side_effect=user_input):
            self.assertTrue(interactive_command.delete_interaction(store, [command, command2]))
        self.assertEqual(store.get_num_commands(), 1)

    def test_delete_command_from_store_with_both_invalid_should_remove_0(self) -> None:
        store = command_store_lib.SqlCommandStore(':memory:')
        command = Command("testing delete this command")
        command2 = Command("remove this also")
        self.assertEqual(store.get_num_commands(), 0)
        store.add_command(command)
        store.add_command(command2)
        self.assertEqual(store.get_num_commands(), 2)
        user_input = ['8, 9']
        with patch('builtins.input', side_effect=user_input):
            self.assertFalse(InteractiveCommandExecutor.delete_interaction(store, [command, command2]))
        self.assertEqual(store.get_num_commands(), 2)

    def test_delete_command_whenUserTypesQuit_shouldReturnFalse(self) -> None:
        user_input = ['quit']
        with patch('builtins.input', side_effect=user_input):
            self.assertFalse(InteractiveCommandExecutor.delete_interaction(Mock(), []))

    def test_run_when_command_is_executed(self) -> None:
        old_call = subprocess.call
        store = command_store_lib.SqlCommandStore(':memory:')
        command_str = "testing delete this command"
        command = Command(command_str)
        command2 = Command("remove this also")
        test_call = partial(self.subprocess_call_mock, expected=command_str)
        subprocess.call = test_call  # type: ignore
        self.assertEqual(store.get_num_commands(), 0)
        store.add_command(command)
        store.add_command(command2)
        self.assertEqual(store.get_num_commands(), 2)
        interactive_command = InteractiveCommandExecutor()
        user_input = ['1']
        with patch('builtins.input', side_effect=user_input):
            self.assertTrue(interactive_command.run([command, command2]))
        subprocess.call = old_call

    def test_run_whenResultsAreEmpty_shouldReturnFalse(self) -> None:
        interactive_command = InteractiveCommandExecutor()
        user_input = ['1']
        with patch('builtins.input', side_effect=user_input):
            self.assertFalse(interactive_command.run([]))

    def test_run_whenCommandChosen_shouldWriteToHistFile(self) -> None:
        command_str = "Command to write to history file"
        command = Command(command_str)
        interactive_command = InteractiveCommandExecutor('SomeHistoryFile.txt')
        user_input = ['1']
        with patch('builtins.input', side_effect=user_input):
            with patch('remember.interactive.open', mock_open(read_data=b'some command')) as m:
                self.assertTrue(interactive_command.run([command]))
                handle = m()
                handle.write.assert_called_with(command_str + '\n')

    def test_run_whenCommandChosenInZsh_shouldWriteToHistFile(self) -> None:
        command_str = "Command to write to history file"
        command = Command(command_str)
        interactive_command = InteractiveCommandExecutor('SomeHistoryFile.txt')
        user_input = ['1']
        hist_file_content = b': 1573535428:0;vim ~/.histfile\n'
        expected = ': 1573535429:0;Command to write to history file\n'
        with patch('builtins.input', side_effect=user_input):
            with patch('remember.interactive.open', mock_open(read_data=hist_file_content)) as m:
                self.assertTrue(interactive_command.run([command]))
                handle = m()
                handle.write.assert_called_with(expected)

    def subprocess_call_mock(self, command_str: str, expected: str, shell: Any) -> None:
        self.assertEqual(expected, command_str)
        self.assertTrue(shell)

    @mock.patch('remember.interactive.load_user_interactor')
    @mock.patch('remember.command_store_lib.save_last_search')
    def test_display_and_interact_whenSaveAndExecute_shouldDoBoth(
            self, save_search: Mock, load_interactor: Mock) -> None:
        results = [Command('grep command'), Command('vim command')]
        rr = display_and_interact_results(results, 5, 'save_dir', 'history_file', ['grep'], True)
        self.assertEqual(rr, None)
        expected_path = os.path.join("save_dir", command_store_lib.DEFAULT_LAST_SAVE_FILE_NAME)
        save_search.assert_called_once_with(expected_path, results)
        load_interactor.assert_called_once_with('history_file')

    @mock.patch('remember.interactive.load_user_interactor')
    @mock.patch('remember.command_store_lib.save_last_search')
    def test_display_and_interact_whenTruncateResult_shouldOnlySaveTruncatedResult(
            self, save_search: Mock, load_interactor: Mock) -> None:
        results = [Command('grep command'), Command('vim command')]
        rr = display_and_interact_results(results, 1, 'save_dir', 'history_file', ['grep'], True)
        self.assertEqual(rr, None)
        expected_path = os.path.join("save_dir", command_store_lib.DEFAULT_LAST_SAVE_FILE_NAME)
        results = results[:1]
        save_search.assert_called_once_with(expected_path, results)
        load_interactor.assert_called_once_with('history_file')


    @mock.patch('remember.command_store_lib.print_commands')
    @mock.patch('subprocess.call')
    @mock.patch('remember.interactive.load_user_interactor',
                return_value=InteractiveCommandExecutor())
    @mock.patch('remember.command_store_lib.save_last_search')
    def test_display_nd_interact_whenUserChooses1_shouldDo1(
            self, save_search: Mock, load_interactor: Mock, subprocess_mock: Mock,
            print_mock: Mock) -> None:
        command = Command('grep command')
        results = [command, Command('vim command')]
        user_input = ['1']
        with patch('builtins.input', side_effect=user_input):
            rr = display_and_interact_results(
                results, 1, 'save_dir', 'history_file', ['grep'], True)
        self.assertEqual(rr, None)
        expected_path = os.path.join("save_dir", command_store_lib.DEFAULT_LAST_SAVE_FILE_NAME)
        results = results[:1]
        save_search.assert_called_once_with(expected_path, results)
        load_interactor.assert_called_once_with('history_file')
        subprocess_mock.assert_called_once_with(command.get_unique_command_id(), shell=True)
        print_mock.assert_called_once()

    def test_load_interactive_whenCallingLoad_shouldHaveCorrectHistoryFile(self) -> None:
        interactive = load_user_interactor('history_file_path')
        self.assertEqual(interactive._history_file_path, 'history_file_path')
