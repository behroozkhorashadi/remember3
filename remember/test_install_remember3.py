import os
import pathlib
from typing import OrderedDict
from unittest import TestCase
from unittest.mock import mock_open
import mock
from mock import patch, Mock

import install_remember3
from remember.constants import ALIASES

TEST_PATH_DIR = os.path.dirname(os.path.realpath(__file__))
TEST_FILES_PATH = os.path.join(TEST_PATH_DIR, "test_files")
ZSHFILE = os.path.join(TEST_FILES_PATH, "zshrc.txt")


expected = OrderedDict([('HISTSIZE', 'HISTSIZE=50000\n'), ('SAVEHIST', 'SAVEHIST=50000\n'), ('HISTFILESIZE', 'HISTFILESIZE=50000\n'), ('setopt INC_APPEND_HISTORY', 'setopt INC_APPEND_HISTORY\n'), ('# Remember command hook',
                       '\n# Remember command hook\nautoload -U add-zsh-hook\nhook_function() {\n  last_line=$(tail -1 histfile_path)\n  pwdresult=$(pwd)\n  echo "$pwdresult<<!>>$last_line" >> ~/.remember3/.histcontext\n}\nadd-zsh-hook precmd hook_function\n\n'), ('HISTFILE', 'HISTFILE=histfile_path\n')])  # pylint: disable=line-too-long

remember_home = remember_home = pathlib.Path(__file__).parent.parent.resolve()
alias_lines = ALIASES.format(remember_home=remember_home, save_dir="save_dir").split('\n')
expected_aliases = install_remember3.get_alias_dict(alias_lines)


class TestMain(TestCase):
    @mock.patch('os.mkdir')
    @mock.patch('os.path.exists')
    def test_setup_all_files_and_dirs_when_bash(self, exists_mock: Mock, _mkdir_mock: Mock):
        exists_mock.return_value = True
        user_input = ['n', 'n', 'n']
        with patch('builtins.input', side_effect=user_input):
            setup_args = install_remember3.setup_all_files_and_dirs(Mock())
            assert setup_args
            assert not setup_args.is_zsh
            assert setup_args.history_file_path == os.path.expanduser('~/.bash_history')
            assert setup_args.rc_file_path == os.path.expanduser('~/.bashrc')
            assert setup_args.save_dir_path == os.path.expanduser('~/.remember3')

    @mock.patch('os.mkdir')
    @mock.patch('os.path.exists')
    def test_setup_all_files_and_dirs_when_zsh(self, exists_mock: Mock, _mkdir_mock: Mock):
        exists_mock.return_value = True
        user_input = ['y', 'n', 'n']
        with patch('builtins.input', side_effect=user_input):
            setup_args = install_remember3.setup_all_files_and_dirs(Mock())
            assert setup_args
            assert setup_args.is_zsh
            assert setup_args.history_file_path == os.path.expanduser('~/.histfile')
            assert setup_args.rc_file_path == os.path.expanduser('~/.zshrc')
            assert setup_args.save_dir_path == os.path.expanduser('~/.remember3')

    @mock.patch('argparse.ArgumentParser.parse_args')
    @mock.patch('install_remember3.write_lines_to_files')
    @mock.patch('install_remember3.setup_all_files_and_dirs')
    @mock.patch('os.path.exists')
    def test_main(self, exists_mock: Mock, setup_remember_mock: Mock, write_lines_mock: Mock,
                  _arg_parse: Mock):
        exists_mock.return_value = True
        setup_remember_mock.return_value = install_remember3.SetupArgs(
            True, "save_dir", "histfile_path", "rc_file_path")
        install_remember3.main()
        write_lines_mock.assert_called_once_with(
            "rc_file_path", "save_dir", expected, expected_aliases)

    @mock.patch('install_remember3.create_db_if_doesnt_exist')
    @mock.patch('os.path.exists')
    def test_write_lines_to_files(self, exists_mock: Mock, _create_db_mock: Mock):
        exists_mock.return_value = False
        user_input = ['y', 'y', 'y']
        with patch('builtins.input', side_effect=user_input):
            with patch('install_remember3.open', mock_open()) as mocked_file:
                install_remember3.write_lines_to_files(
                    "rc_path", "save_path", expected, expected_aliases)
                mocked_file.assert_called()
