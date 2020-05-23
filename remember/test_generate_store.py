# flake8: noqa
import argparse
import os
from unittest import TestCase

import mock

import generate_store
from remember import command_store_lib
from remember.command_store_lib import generate_store_from_args

TEST_PATH_DIR = os.path.dirname(os.path.realpath(__file__))
TEST_FILES_PATH = os.path.join(TEST_PATH_DIR, "test_files")


class TestMain(TestCase):
    @mock.patch('argparse.ArgumentParser.parse_args',
                return_value=argparse.Namespace(history_file_path='foo', save_dir='bar', json=True,
                                                sql=False))
    def test_when_simple_args_generate_should_be_called_with_foo_bar_and_true(
            self, _: mock.Mock) -> None:
        with mock.patch('remember.command_store_lib.generate_store_from_args') as generate_from_args:
            generate_store.main()
            generate_from_args.assert_called_once_with('foo', 'bar')

    @mock.patch('argparse.ArgumentParser.parse_args',
                return_value=argparse.Namespace(history_file_path='foo', save_dir='bar', json=False,
                                                sql=False,))
    def test_when_json_arg_false_generate_should_be_called_with_foo_bar_and_false(
            self, _: mock.Mock) -> None:
        with mock.patch('remember.command_store_lib.generate_store_from_args') as generate_from_args:
            generate_store.main()
            generate_from_args.assert_called_once_with('foo', 'bar')

    def test_simple_assert_default_json_file_exists(self) -> None:
        file_path = command_store_lib.get_file_path(TEST_FILES_PATH)
        assert os.path.isfile(file_path)

    # def test_when_generate_from_args_should_use_ignore_file(self) -> None:
    #     tmp_holder = generate_store.IGNORE_RULE_FILE_NAME
    #     generate_store.IGNORE_RULE_FILE_NAME = "ignore_rules.txt"
    #     history_file_path = 'some/path'
    #     return_result_list = ["1", "2"]
    #     with mock.patch('remember.command_store_lib.process_history_commands') as read_file:
    #         with mock.patch('remember.command_store_lib.get_string_file_lines',
    #                    return_value=return_result_list):
    #             read_file.assert_not_called()
    #             generate_store_from_args(history_file_path, TEST_FILES_PATH)
    #             read_file.assert_called_once_with(mock.ANY, history_file_path, ['1', '2'], None)
    #     generate_store.IGNORE_RULE_FILE_NAME = tmp_holder
