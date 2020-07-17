import argparse
import os
from unittest import TestCase

import mock
from mock import patch, Mock

import remember_setup


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
        content = open(file_name).read()
        user_input = ['n', 'y']
        with patch('builtins.input', side_effect=user_input):
            remember_setup.main()
            mock_write.assert_called_once_with('rc_file', content)

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
        content = open(file_name).read()

        user_input = ['y', 'y']
        with patch('builtins.input', side_effect=user_input):
            remember_setup.main()
            mock_write.assert_called_once_with('rc_file', content)

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
        with patch('builtins.input', side_effect=user_input):
            remember_setup.main()
            mock_write.assert_called_once_with(ZSHFILE, '')
