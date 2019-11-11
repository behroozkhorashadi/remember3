import argparse
import os
from unittest import TestCase

import mock

import execute_last
from remember.command_store_lib import DEFAULT_LAST_SAVE_FILE_NAME


class TestMain(TestCase):
    @mock.patch('subprocess.call')
    def test_run_remember_command_whenLoadLast_shouldReadFile(self,
                                                              mock_subproc_call: mock.Mock) -> None:
        user_input = ['']
        with mock.patch('builtins.input', side_effect=user_input):
            with mock.patch('argparse.ArgumentParser.parse_args',
                            return_value=argparse.Namespace(save_dir="test", index=1)):
                with mock.patch('remember.command_store_lib.open',
                                mock.mock_open(read_data='some command')) as read_mock:
                    execute_last.main()
                    read_mock.assert_called_once_with(os.path.join(
                        'test', DEFAULT_LAST_SAVE_FILE_NAME))
                    mock_subproc_call.assert_called_once_with('some command', shell=True)

    @mock.patch('subprocess.call')
    def test_run_remember_command_whenSaveDirAndNoNumSelected_shouldReturn(
            self, mock_subproc_call: mock.Mock) -> None:
        user_input = ['no']
        with mock.patch('builtins.input', side_effect=user_input):
            with mock.patch('argparse.ArgumentParser.parse_args',
                            return_value=argparse.Namespace(save_dir="test", index=1)):
                with mock.patch('remember.command_store_lib.open',
                                mock.mock_open(read_data='some command')) as read_mock:
                    execute_last.main()
                    read_mock.assert_called_once_with(os.path.join(
                        'test', DEFAULT_LAST_SAVE_FILE_NAME))
                    mock_subproc_call.assert_not_called()
