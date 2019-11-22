""" Rename show
Usage:
    reshow.py [options]

Options:
    --name=<name>
    -d --directory=<directory>
    -f --file-ext=<file-ext>
    --strict
    --rename-to=<rename-to>
    --season=<season>
"""

from docopt import docopt

from rename_show.rename import main

# from rename_show.rename import main

if __name__ == "__main__":
    args = docopt(__doc__)
    directory, show_name, file_ext = args["--directory"], args["--name"], args["--file-ext"]
    rename_to = args['--rename-to']
    season = args['--season']
    strict = 'strict' in args.keys()
    if not file_ext:
        file_ext = "mkv"
    elif file_ext.startswith("."):
        file_ext = file_ext[1:]

    if not directory:
        directory = "."

    if not show_name:
        print("Please enter a show name")
    else:
        main(directory, show_name, file_ext=file_ext, strict=strict, rename_to=rename_to, season=season)
