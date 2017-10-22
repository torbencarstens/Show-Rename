""" Rename show
Usage:
    reshow.py [options]

Options:
    --name=<name>
    -d --directory=<directory>

"""

import colorama
from docopt import docopt
from rename_show.rename import main

if __name__ == "__main__":
    args = docopt(__doc__)
    directory, show_name = args["--directory"], args["--name"]

    main(directory, show_name)
