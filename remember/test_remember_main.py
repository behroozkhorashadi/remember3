# flake8: noqa
import argparse
import os
from typing import List
from unittest import TestCase
import remember_main
import mock
from mock import Mock

from remember.command_store_lib import SqlCommandStore, DEFAULT_LAST_SAVE_FILE_NAME, Command

def create_test_sql_command_store(command_strs: List[str]) -> SqlCommandStore:
    store = SqlCommandStore()
    for command_str in command_strs:
        store.add_command(Command(command_str))
    return store


SINGLE_COMMAND_STORE = create_test_sql_command_store(['grep foo'])
DOUBLE_COMMAND_STORE = create_test_sql_command_store(['grep foo', 'grep command'])


class TestMain(TestCase):
    def test_setup_args_for_search_but_missing_save_dir_should_return_error_string(self) -> None:
        with mock.patch(
                'argparse.ArgumentParser.parse_args', return_value=argparse.Namespace(
                    json=True, sql=False, all=True, startswith=True, execute=False,
                    save_dir=None, history_file_path='hist', max=1000, query='query')):
            result = remember_main.main()
            assert result
            assert result.startswith("To many or too few args")

    @mock.patch('remember.command_store_lib.load_command_store', return_value=SINGLE_COMMAND_STORE)
    @mock.patch('remember.command_store_lib.start_history_processing')
    def test_run_remember_command_whenSaveDir_shouldWriteLastCommand(
            self, process_mock: Mock, load_mock: Mock) -> None:
        with mock.patch('remember.command_store_lib.open', mock.mock_open()) as write_mock:
            remember_main.run_remember_command("test", 'test_hist', ['grep'], False, False,
                                               False, 10)
            load_mock.assert_called_once()
            process_mock.assert_called_once()
            write_mock.assert_called_once_with(
                os.path.join('test', DEFAULT_LAST_SAVE_FILE_NAME), 'w')
            handle = write_mock()
            handle.write.assert_called_with('grep foo\n')

    @mock.patch('argparse.ArgumentParser.parse_args',
                return_value=argparse.Namespace(
                    all=True, startswith=False, execute=False, save_dir='save_dir',
                    history_file_path=None, query='query'))
    def test_setup_args_for_search_but_missing_history_file_path_should_return_error_string(
            self, _: mock.Mock) -> None:
        result = remember_main.main()
        assert result
        assert result.startswith("To many or too few args")

    @mock.patch('remember.command_store_lib.load_command_store', return_value=DOUBLE_COMMAND_STORE)
    @mock.patch('remember.command_store_lib.print_commands')
    @mock.patch('remember.command_store_lib.start_history_processing')
    def test_setup_args_for_search_should_make_appropriate_calls_into_command_store_lib(
            self, process_mock: mock.Mock, print_mock: mock.Mock, load_mock: mock.Mock) -> None:
        with mock.patch('argparse.ArgumentParser.parse_args',
                        return_value=argparse.Namespace(json=True,
                                                        sql=False,
                                                        all=True,
                                                        startswith=True,
                                                        execute=False,
                                                        save_dir='save_dir',
                                                        history_file_path='hist',
                                                        max=1000,
                                                        query='grep')):
            with mock.patch('remember.command_store_lib.open', mock.mock_open()) as write_mock:
                remember_main.main()
                print_mock.assert_called_once()
                load_mock.assert_called_once()
                process_mock.assert_called_once()
                write_mock.assert_called_once()

    @mock.patch('remember_main.load_user_interactor')
    @mock.patch('remember.command_store_lib.load_command_store',return_value=DOUBLE_COMMAND_STORE)
    @mock.patch('remember.command_store_lib.print_commands')
    @mock.patch('remember.command_store_lib.start_history_processing')
    def test_setup_args_for_search_should_make_appropriate_calls_into_command_store_libwithexec(
            self, process_mock: mock.Mock, print_mock: mock.Mock, load_mock: mock.Mock,
            executor: mock.Mock) -> None:
        with mock.patch('argparse.ArgumentParser.parse_args',
                        return_value=argparse.Namespace(json=True,
                                                        sql=False,
                                                        all=True,
                                                        startswith=True,
                                                        execute=True,
                                                        save_dir='save_dir',
                                                        history_file_path='hist',
                                                        max=1,
                                                        query='grep')):
            with mock.patch('remember.command_store_lib.open', mock.mock_open()) as write_mock:
                remember_main.main()
                print_mock.assert_called_once()
                load_mock.assert_called_once()
                process_mock.assert_called_once()
                executor.assert_called_once()
                write_mock.assert_called_once()

    @mock.patch('remember_main.load_user_interactor')
    @mock.patch('remember.command_store_lib.load_command_store',return_value=DOUBLE_COMMAND_STORE)
    @mock.patch('remember.command_store_lib.print_commands')
    @mock.patch('remember.command_store_lib.start_history_processing')
    def test_setup_args_for_search_should_make_call_but_return_exit(
            self, process_mock: mock.Mock, print_mock: mock.Mock, load_mock: mock.Mock,
            executor: mock.Mock) -> None:
        with mock.patch('argparse.ArgumentParser.parse_args',
                        return_value=argparse.Namespace(json=True,
                                                        sql=False,
                                                        all=True,
                                                        startswith=True,
                                                        execute=True,
                                                        save_dir='save_dir',
                                                        history_file_path='hist',
                                                        max=1,
                                                        query='grep')):
            with mock.patch('remember.command_store_lib.open', mock.mock_open()) as write_mock:
                interactor_mock = Mock()
                interactor_mock.run.return_value = ''
                executor.return_value = interactor_mock
                remember_main.main()
                print_mock.assert_not_called()
                load_mock.assert_called_once()
                process_mock.assert_called_once()
                executor.assert_called_once()
                write_mock.assert_called_once()
