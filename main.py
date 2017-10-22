""" Rename show
Usage:
    reshow.py [options]

Options:
    --name=<name>
    -d --directory=<directory>

"""

from imdbpie import Imdb
from docopt import docopt

# from rename_show.rename import main

if __name__ == "__main__":
    args = docopt(__doc__)
    directory, show_name = args["--directory"], args["--name"]

    imdb = Imdb()
    results = list(filter(lambda x: x['title'] == show_name, imdb.search_for_title(show_name)))

    titles = []
    for idx, result in enumerate(results):
        titles.append(imdb.get_title_by_id(result['imdb_id']))

    for title in titles:
        print(
            "Title: {} - Year: {} - Type: {} - Genres: {} - Plot: {}".format(title.title, title.year, title.type,
                                                                             title.genres, title.plot_outline))
        # main(directory, show_name, 2009)
