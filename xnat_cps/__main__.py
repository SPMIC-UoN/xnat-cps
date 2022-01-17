import logging 

from .cli import ArgumentParser
from .command import XnatCps

def  main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    options = ArgumentParser().parse_args()
    XnatCps(options).run()

if __name__ == "__main__":
    main()
