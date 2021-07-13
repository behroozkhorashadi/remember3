import argparse
import os
from unittest import TestCase

import mock
from mock import patch, Mock

import remember_setup
from remember.command_store_lib import CUSTOM_HIST_HEAD

TEST_PATH_DIR = os.path.dirname(os.path.realpath(__file__))
TEST_FILES_PATH = os.path.join(TEST_PATH_DIR, "test_files")
ZSHFILE = os.path.join(TEST_FILES_PATH, "zshrc.txt")


class TestMain(TestCase):

    @mock.patch('argparse.ArgumentParser.parse_args',
                return_value=argparse.Namespace(rc_file='rc_file',
                                                history_file_path='history_file_path',
                                                save_dir='save',
                                                remember3_dir='r3'))
    @mock.patch('remember_setup.write_lines_to_file')
    @mock.patch('remember_setup.create_db_if_doesnt_exist')
    def test_setup_args_for_update_when(
            self, mock_db_write: Mock, mock_write: Mock, mock_args: Mock) -> None:
        file_name = os.path.join(TEST_FILES_PATH, "bashrc.txt")
        with open(file_name) as test_file:
            content = test_file.read()
        user_input = ['n', 'y']
        expanded_path = os.path.expanduser('~/.histcontext')
        with patch('builtins.input', side_effect=user_input):
            remember_setup.main()
            assert mock_write.call_count == 2
            calls = [mock.call('rc_file', content), mock.call(expanded_path, CUSTOM_HIST_HEAD)]
            mock_write.assert_has_calls(calls)

    @mock.patch('argparse.ArgumentParser.parse_args',
                return_value=argparse.Namespace(rc_file='rc_file',
                                                history_file_path='history_file_path',
                                                save_dir='save',
                                                remember3_dir='r3'))
    @mock.patch('remember_setup.write_lines_to_file')
    @mock.patch('remember_setup.create_db_if_doesnt_exist')
    def test_setup_args_for_update_when_zshrc(
            self, mock_db_write: Mock, mock_write: Mock, mock_args: Mock) -> None:
        file_name = os.path.join(TEST_FILES_PATH, "zshrc.txt")
        with open(file_name) as test_file:
            content = test_file.read()

        user_input = ['y', 'y']
        expanded_path = os.path.expanduser('~/.histcontext')
        with patch('builtins.input', side_effect=user_input):
            remember_setup.main()
            assert mock_write.call_count == 2
            calls = [mock.call('rc_file', content), mock.call(expanded_path, CUSTOM_HIST_HEAD)]
            mock_write.assert_has_calls(calls)

    @mock.patch('argparse.ArgumentParser.parse_args',
                return_value=argparse.Namespace(rc_file='rc_file',
                                                history_file_path='history_file_path',
                                                save_dir='save',
                                                remember3_dir='r3'))
    @mock.patch('remember_setup.write_lines_to_file')
    @mock.patch('remember_setup.create_db_if_doesnt_exist')
    def test_setup_args_for_update_when_exit(
            self, mock_db_write: Mock, mock_write: Mock, mock_args: Mock) -> None:
        user_input = ['e']
        with patch('builtins.input', side_effect=user_input):
            remember_setup.main()
            mock_write.assert_not_called()

    @mock.patch('argparse.ArgumentParser.parse_args',
                return_value=argparse.Namespace(rc_file=ZSHFILE,
                                                history_file_path='history_file_path',
                                                save_dir='save',
                                                remember3_dir='r3'))
    @mock.patch('remember_setup.write_lines_to_file')
    @mock.patch('remember_setup.create_db_if_doesnt_exist')
    def test_setup_args_for_update_whenEverythingIsThereAlready(
            self, mock_db_write: Mock, mock_write: Mock, mock_args: Mock) -> None:
        user_input = ['y', 'y']
        expanded_path = os.path.expanduser('~/.histcontext')
        with patch('builtins.input', side_effect=user_input):
            remember_setup.main()
            assert mock_write.call_count == 2
            calls = [mock.call(ZSHFILE, ''), mock.call(expanded_path, CUSTOM_HIST_HEAD)]
            mock_write.assert_has_calls(calls)