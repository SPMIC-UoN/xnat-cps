import logging 

from .cli import ArgumentParser
from .commands import Migrate

def  main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
    options = ArgumentParser().parse_args()
    command = Migrate(options).run()

if __name__ == "__main__":
    main()
