import logging 

from .cli import ArgumentParser
from .commands import Migrate

def  main():
    logging.basicConfig(level=logging.INFO)
    options = ArgumentParser().parse_args()
    command = globals().get(options.command.title(), None)
    if command is not None:
        command().run(options)
    else:
        raise ValueError(f"No such command: {options.command}")

if __name__ == "__main__":
    main()
