# flake8: noqa
import os
import subprocess
import sys
import unittest
from functools import partial
from typing import Tuple, Any

import remember.command_store_lib as command_store_lib
import remember.interactive as interactive
from remember.command_store_lib import Command
from remember.interactive import InteractiveCommandExecutor

TEST_PATH_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, TEST_PATH_DIR + '/../')


class Test(unittest.TestCase):
    def test_command_update_info_should_correctly_set_info(self) -> None:
        interactive_command = InteractiveCommandExecutor()
        command = Command("git rest --hard HEAD")
        command_info = 'command info'
        self.set_input('1', command_info)
        interactive_command.command_info_interaction([command])
        self.assertEqual(command.get_command_info(), command_info)
        self.reset_input()

    def test_command_update_info_should_fail_set_info_because_exit(self) -> None:
        interactive_command = InteractiveCommandExecutor()
        command = Command("git rest --hard HEAD")
        self.set_input('exit')
        self.assertFalse(interactive_command.command_info_interaction([command]))
        self.assertEqual(command.get_command_info(), "")
        self.reset_input()

    def test_delete_command_from_store_should_delete(self) -> None:
        store = command_store_lib.SqlCommandStore(':memory:')
        command = Command("testing delete this command")
        store.add_command(command)
        self.assertEqual(store.get_num_commands(), 1)
        interactive_command = InteractiveCommandExecutor()
        self.set_input('1', 'y')
        self.assertTrue(interactive_command.delete_interaction(store, [command]))
        self.assertEqual(store.get_num_commands(), 0)
        self.reset_input()

    def test_delete_command_from_store_when_no_should_not_delete(self) -> None:
        store = command_store_lib.SqlCommandStore(':memory:')
        command = Command("testing delete this command")
        store.add_command(command)
        self.assertEqual(store.get_num_commands(), 1)
        interactive_command = InteractiveCommandExecutor()
        self.set_input('1', 'n')
        self.assertFalse(interactive_command.delete_interaction(store, [command]))
        self.assertEqual(store.get_num_commands(), 1)
        self.reset_input()

    def test_delete_command_from_store_with_all_should_remove_all(self) -> None:
        store = command_store_lib.SqlCommandStore(':memory:')
        command = Command("testing delete this command")
        command2 = Command("remove this also")
        self.assertEqual(store.get_num_commands(), 0)
        store.add_command(command)
        store.add_command(command2)
        self.assertEqual(store.get_num_commands(), 2)
        interactive_command = InteractiveCommandExecutor()
        self.set_input('allofthem', 'y')
        self.assertTrue(interactive_command.delete_interaction(store, [command, command2]))
        self.assertEqual(store.get_num_commands(), 0)
        self.reset_input()

    def test_delete_command_from_store_with_1_2_should_remove_all(self) -> None:
        store = command_store_lib.SqlCommandStore(':memory:')
        command = Command("testing delete this command")
        command2 = Command("remove this also")
        self.assertEqual(store.get_num_commands(), 0)
        store.add_command(command)
        store.add_command(command2)
        self.assertEqual(store.get_num_commands(), 2)
        interactive_command = InteractiveCommandExecutor()
        self.set_input('1, 2', 'y')
        self.assertTrue(interactive_command.delete_interaction(store, [command, command2]))
        self.assertEqual(store.get_num_commands(), 0)
        self.reset_input()

    def test_delete_command_from_store_with_invalid_should_remove_1(self) -> None:
        store = command_store_lib.SqlCommandStore(':memory:')
        command = Command("testing delete this command")
        command2 = Command("remove this also")
        self.assertEqual(store.get_num_commands(), 0)
        store.add_command(command)
        store.add_command(command2)
        self.assertEqual(store.get_num_commands(), 2)
        interactive_command = InteractiveCommandExecutor()
        self.set_input('1, 9', 'y')
        self.assertTrue(interactive_command.delete_interaction(store, [command, command2]))
        self.assertEqual(store.get_num_commands(), 1)
        self.reset_input()

    def test_delete_command_from_store_with_both_invalid_should_remove_0(self) -> None:
        store = command_store_lib.SqlCommandStore(':memory:')
        command = Command("testing delete this command")
        command2 = Command("remove this also")
        self.assertEqual(store.get_num_commands(), 0)
        store.add_command(command)
        store.add_command(command2)
        self.assertEqual(store.get_num_commands(), 2)
        interactive_command = InteractiveCommandExecutor()
        self.set_input('8, 9')
        self.assertFalse(interactive_command.delete_interaction(store, [command, command2]))
        self.assertEqual(store.get_num_commands(), 2)
        self.reset_input()

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
        self.set_input('1')
        self.assertTrue(interactive_command.run([command, command2]))
        self.reset_input()
        subprocess.call = old_call

    def set_input(self, *args: str) -> None:
        self.original_raw_input = interactive.get_user_input
        # noinspection Mypy
        interactive.get_user_input = InputMock(args)  # type: ignore

    def reset_input(self) -> None:
        if self.original_raw_input:
            interactive.get_user_input = self.original_raw_input

    def subprocess_call_mock(self, command_str: str, expected: str, shell: Any) -> None:
        self.assertEqual(expected, command_str)
        self.assertTrue(shell)


class InputMock(object):
    def __init__(self, args: Tuple[str, ...]) -> None:
        self.index = 0
        self.args = args

    def __call__(self, _: Any) -> str:
        return_value = self.args[self.index % len(self.args)]
        self.index = self.index + 1
        return return_value


if __name__ == '__main__':
    unittest.main()
