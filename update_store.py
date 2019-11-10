import time

import remember.command_store_lib as command_store
from remember import handle_args
from remember.interactive import InteractiveCommandExecutor


def main(command_executor: InteractiveCommandExecutor) -> None:
    """Entry point for this executable python module."""
    args = handle_args.setup_args_for_update()
    store_file_path = command_store.get_file_path(args.save_dir)
    store = command_store.load_command_store(store_file_path)
    print('Looking for all past commands with: ' + ", ".join(args.query))
    start_time = time.time()
    search_results = store.search_commands(args.query, args.startswith, )
    end_time = time.time()
    print(f"Search time: {end_time - start_time} seconds")
    print(f"Number of results found: {str(len(search_results))}")
    if len(search_results) > args.max:
        print(f"Results truncated to the first: {args.max}")
    search_results = search_results[:args.max]
    if len(search_results) > 0:
        if args.delete:
            print("Delete mode")
            command_store.print_commands(search_results, args.query)
            command_executor.delete_interaction(store, search_results)
        if args.updateinfo:
            print("Updating Info mode")
            command_executor.command_info_interaction(search_results)


if __name__ == "__main__":
    main(InteractiveCommandExecutor())
