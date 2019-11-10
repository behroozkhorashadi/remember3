# flake8: noqa
import os
import subprocess
import sys
import unittest
from functools import partial
from typing import Any

from mock import patch, Mock, mock_open

import remember.command_store_lib as command_store_lib
from remember.command_store_lib import Command
from remember.interactive import InteractiveCommandExecutor

TEST_PATH_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, TEST_PATH_DIR + '/../')


class Test(unittest.TestCase):
    def test_command_update_info_should_correctly_set_info(self) -> None:
        interactive_command = InteractiveCommandExecutor()
        command = Command("git rest --hard HEAD")
        command_info = 'command info'
        user_input = ['1', command_info]
        with patch('builtins.input', side_effect=user_input):
            interactive_command.command_info_interaction([command])
        self.assertEqual(command.get_command_info(), command_info)

    def test_command_update_info_should_fail_set_info_because_exit(self) -> None:
        interactive_command = InteractiveCommandExecutor()
        command = Command("git rest --hard HEAD")
        user_input = ['exit']
        with patch('builtins.input', side_effect=user_input):
            self.assertFalse(interactive_command.command_info_interaction([command]))
        self.assertEqual(command.get_command_info(), "")

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
            with patch('remember.interactive.open', mock_open()) as m:
                self.assertTrue(interactive_command.run([command]))
                handle = m()
                handle.write.assert_called_with(command_str + '\n')

    def subprocess_call_mock(self, command_str: str, expected: str, shell: Any) -> None:
        self.assertEqual(expected, command_str)
        self.assertTrue(shell)
