""" Rename show
Usage:
    reshow.py [options]

Options:
    --name=<name>
    -d --directory=<directory>
    -f --file-ext=<file-ext>
    --strict
    --rename-to=<rename-to>
"""

from docopt import docopt

from rename_show.rename import main

# from rename_show.rename import main

if __name__ == "__main__":
    args = docopt(__doc__)
    directory, show_name, file_ext = args["--directory"], args["--name"], args["--file-ext"]
    rename_to = args['--rename-to']
    strict = 'nostrict' in args.keys()
    if not file_ext:
        file_ext = ".mkv"
    elif not file_ext.startswith("."):
        file_ext = ".{}".format(file_ext)

    main(directory, show_name, file_ext=file_ext, strict=strict, rename_to=rename_to)
