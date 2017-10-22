import re
import os
from typing import Tuple

import colorama
from imdbpie import Imdb


def get_episodes(show_name, year):
    imdb = Imdb()
    results = imdb.search_for_title(show_name)

    results = list(
        filter(lambda result: int(result['year']) == year,
               filter(lambda result:
                      result['title'] == show_name, results)))

    ids = map(lambda res: res['imdb_id'], results)
    episodes = imdb.get_episodes(ids.__next__())

    return episodes


def retrieve_season_episode_from_file(filename, show_name) -> Tuple[int, int]:
    season_nr, episode_nr = re.findall(r"{}.*?S(\d+).*?E(\d+).*".format(show_name), filename)[0]
    return int(season_nr), int(episode_nr)


def get_user_decision(*, values, numbered, type_cast_f, allow_custom=True):
    custom_number = numbered[len(numbered) - 1] + 1
    if not values:
        raise ValueError("Can't let user decide on an empty list")
    for idx, value in enumerate(values):
        print("{}: {}".format(value, numbered[idx]))
    if allow_custom:
        print("\n{}: Custom (User input)".format(custom_number))

    try:
        choice = type_cast_f(input("What should the episode be renamed to?\n"))
    except TypeError:
        print("Please enter a valid option")
        return get_user_decision(values=values, numbered=numbered, type_cast_f=type_cast_f)

    if not (choice in numbered or choice == custom_number):
        print("Please enter a valid option")
        return get_user_decision(values=values, numbered=numbered, type_cast_f=type_cast_f)

    if allow_custom and choice == custom_number:
        return input("Please put the new episode name:\n")
    else:
        return values[choice]


def main(directory: str, show_name: str):
    episodes = get_episodes(show_name, year=2009)

    for path, directories, files in os.walk(directory):
        mkv_files = filter(lambda file: file.endswith(".mkv"), files)
        for mkv in mkv_files:
            try:
                season_nr, episode_nr = retrieve_season_episode_from_file(mkv, show_name)
            except IndexError:
                print("Couldn't retrieve season/episode from {}".format(mkv))
                continue

            file = os.path.join(path, mkv)
            possible_episodes = list(filter(lambda ep: ep.season == season_nr and ep.episode == episode_nr,
                                            episodes))
            if len(possible_episodes) == 1:
                episode = possible_episodes[0]
            elif len(possible_episodes) > 1:
                print("Found multiple episode names for one episode: ")
                try:
                    episode = get_user_decision(values=possible_episodes, numbered=range(0, len(possible_episodes) - 1),
                                                type_cast_f=lambda x: int(x))
                except InterruptedError:
                    print("Haven't renamed episode S{}E{}".format(season_nr, episode_nr))
                    continue
            else:
                print("Couldn't find episode name for S{}E".format(season_nr, episode_nr))
                continue

            title = episode.title.replace(" ", "_")
            title = title.replace(":", "-")
            show_name = show_name.replace(" ", "_")

            new_name = "{}_S{}_E{}_{}.mkv".format(show_name, season_nr, episode_nr, title)
            os.rename(file, os.path.join(path, new_name))
