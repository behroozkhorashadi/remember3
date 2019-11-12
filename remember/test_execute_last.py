import argparse
import os
from unittest import TestCase

import mock
from unittest.mock import patch

import execute_last
from remember.command_store_lib import DEFAULT_LAST_SAVE_FILE_NAME


class TestMain(TestCase):
    @patch('subprocess.call')
    @patch('builtins.input', side_effect=[''])
    @patch('remember.command_store_lib.open', mock.mock_open(read_data='some command'))
    @patch('remember.interactive.open', mock.mock_open(read_data=b'some command'))
    def test_run_remember_command_whenLoadLast_shouldReadFile(self,
                                                              _: mock.Mock,
                                                              mock_subproc_call: mock.Mock) -> None:
        argparse_args = argparse.Namespace(save_dir="test", history_file_path='whatever', index=1)
        with mock.patch('argparse.ArgumentParser.parse_args', return_value=argparse_args):
            execute_last.main()
            mock_subproc_call.assert_called_once_with('some command', shell=True)

    @mock.patch('subprocess.call')
    def test_run_remember_command_whenSaveDirAndNoNumSelected_shouldReturn(
            self, mock_subproc_call: mock.Mock) -> None:
        user_input = ['no']
        argparse_args = argparse.Namespace(save_dir="test", history_file_path='', index=1)
        with mock.patch('builtins.input', side_effect=user_input):
            with mock.patch('argparse.ArgumentParser.parse_args', return_value=argparse_args):
                with mock.patch('remember.command_store_lib.open',
                                mock.mock_open(read_data='some command')) as read_mock:
                    execute_last.main()
                    read_mock.assert_called_once_with(os.path.join(
                        'test', DEFAULT_LAST_SAVE_FILE_NAME))
                    mock_subproc_call.assert_not_called()
