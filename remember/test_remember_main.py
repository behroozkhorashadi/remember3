# flake8: noqa
import argparse
from unittest import TestCase
import remember_main
import mock

from remember.command_store_lib import SqlCommandStore


class TestMain(TestCase):
    def test_setup_args_for_search_but_missing_save_dir_should_return_error_string(self) -> None:
        with mock.patch('argparse.ArgumentParser.parse_args',
                        return_value=argparse.Namespace(json=True,
                                                        sql=False,
                                                        all=True,
                                                        startswith=True,
                                                        execute=False,
                                                        save_dir=None,
                                                        history_file_path='hist',
                                                        max=1000,
                                                        query='query')):
            result = remember_main.main()
            assert result
            assert result.startswith("To many or too few args")

    @mock.patch('argparse.ArgumentParser.parse_args',
                return_value=argparse.Namespace(all=True,
                                                startswith=False,
                                                execute=False,
                                                save_dir='save_dir',
                                                history_file_path=None,
                                                query='query'))
    def test_setup_args_for_search_but_missing_history_file_path_should_return_error_string(
            self, _: mock.Mock) -> None:
        result = remember_main.main()
        assert result
        assert result.startswith("To many or too few args")

    @mock.patch('remember.command_store_lib.load_command_store', return_value=SqlCommandStore())
    @mock.patch('remember.command_store_lib.print_commands')
    def test_setup_args_for_search_should_make_appropriate_calls_into_command_store_lib(
            self, print_mock: mock.Mock, load_mock: mock.Mock) -> None:
        with mock.patch('argparse.ArgumentParser.parse_args',
                        return_value=argparse.Namespace(json=True,
                                                        sql=False,
                                                        all=True,
                                                        startswith=True,
                                                        execute=False,
                                                        save_dir='save_dir',
                                                        history_file_path='hist',
                                                        max=1000,
                                                        query='query')):
            remember_main.main()
            print_mock.assert_called_once()
            load_mock.assert_called_once()
