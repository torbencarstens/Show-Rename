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
    --confirm
    --skip-first-episode
    --custom-format=<custom-format>
"""
import os
import sys

from docopt import docopt

from rename_show.rename import main


# noinspection PyShadowingNames
def validate_options():
    args = docopt(__doc__)
    directory = args["--directory"] or "."
    show_name = args["--name"]
    file_ext = args["--file-ext"] or "mkv"
    rename_to = args['--rename-to']
    season = args['--season']
    skip_first = args['--skip-first-episode'] or False
    confirm_renaming = args['--confirm'] or False
    strict = 'strict' in args.keys()
    custom_format = args['--custom-format']
    if file_ext.startswith("."):
        file_ext = file_ext[1:]

    if not os.path.exists(directory):
        raise ValueError("directory does not exist")

    if not show_name:
        raise ValueError("No show_name has been provided")

    return directory, show_name, file_ext, strict, rename_to, season, confirm_renaming, skip_first, custom_format


if __name__ == "__main__":
    directory, show_name, file_ext, strict, rename_to, season, confirm_renaming, skip_first, custom_format = validate_options()

    try:
        main(directory, show_name, file_ext=file_ext, strict=strict, rename_to=rename_to, season=season,
             confirm_renaming=confirm_renaming, skip_first=skip_first, custom_format=custom_format)
    except ValueError as e:
        print(f"An error has occured: {e}", file=sys.stderr)
