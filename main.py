""" Rename show
Usage:
    reshow.py [options]

Options:
    --name=<name>
    -d --directory=<directory>

"""

from docopt import docopt

from rename_show.rename import main

# from rename_show.rename import main

if __name__ == "__main__":
    args = docopt(__doc__)
    directory, show_name, file_ext = args["--directory"], args["--name"], args["--file-ext"]
    if not file_ext:
        file_ext = ".mkv"
    elif not file_ext.startswith("."):
        file_ext = ".{}".format(file_ext)
    main(directory, show_name, file_ext=file_ext)
