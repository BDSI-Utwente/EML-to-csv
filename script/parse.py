from pathlib import Path
import sys
import datetime as dt
from docopt import docopt

from candidates import create_candidate_list

if __name__ == "__main__":
    doc = """
    Usage:
        parse.py <source> <target> [--force]

    Options:
        <source>            Path to eml data files folder.
        <target>            Path to output folder.
        --force             Force overwrite of output folder if it exists.
    """

    args = docopt(doc)

    print(args)

    SOURCE = Path(args["<source>"]) if args["<source>"] else None
    TARGET = Path(args["<target>"]) if args["<target>"] else None
    FORCE = args["--force"]

    if not SOURCE or not TARGET:
        print("Please provide a source and target path.")
        SOURCE = Path(input("Path to eml data files folder: "))
        TARGET = Path(input("Path to output folder: "))

    if not FORCE:
        CONFIRM = input(
            f"input: {SOURCE.resolve()}\n"
            + f"output: {TARGET.resolve()}.\n\nIs this correct? (Y/n): "
        )
        if CONFIRM in ["No", "no", "n", "N"]:
            print("Ok, bye!")
            exit()

    if not TARGET.exists():
        TARGET.mkdir(parents=True, exist_ok=True)

    if not FORCE:
        print("\nDo you also want to create a csv with results per candidate?")
        print("This will take up more disk space (~1GB)\n")
        PER_CANDIDATE = input("Per candidate (Y/n): ")

    start = dt.datetime.now()

    if FORCE or not PER_CANDIDATE in ["No", "no", "n", "N"]:
        create_candidate_list(SOURCE, TARGET)

    duration = dt.datetime.now() - start
    print("Duration: {} seconds".format(round(duration.total_seconds())))
