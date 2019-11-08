#! /usr/bin/env python
import remember.command_store_lib as command_store
from remember import handle_args
from remember.interactive import InteractiveCommandExecutor


def main(command_executor):
    """Entry point for this executable python module."""
    args = handle_args.setup_args_for_update()
    store_file_path = command_store.get_file_path(args.save_dir)
    store = command_store.load_command_store(store_file_path)
    print('Looking for all past commands with: ' + ", ".join(args.query))
    search_results = store.search_commands(args.query, args.startswith, )
    print("Number of results found: " + str(len(search_results)))
    if args.delete and len(search_results) > 0:
        print("Delete mode")
        command_store.print_commands(search_results, args.query)
        command_executor.delete_interaction(store, search_results)
    if args.updateinfo and len(search_results) > 0:
        print("Updating Info mode")
        command_executor.command_info_interaction(search_results)


if __name__ == "__main__":
    main(InteractiveCommandExecutor())
