import os
import re
from imdbpie import Imdb
from typing import Any, Dict, Tuple

imdb: Imdb = None


def get_show(show_name, year, strict):
    global imdb

    results = imdb.search_for_title(show_name)
    if year:
        results = filter(lambda result: result['year'] and int(result['year']) == year, results)

    if strict:
        results = list(
            filter(lambda result:
                   result['title'] == show_name, results))
    else:
        results = list(
            filter(lambda result:
                   show_name in result['title'], results))

    if len(results) == 1:
        return results[0]
    elif len(results) > 1:
        shows = map(lambda result: imdb.get_title_by_id(result['imdb_id']), results)
        shows = list(
            map(lambda show: {'title': show.title, 'year': show.year, 'plot_outline': show.plot_outline,
                              'imdb_id': show.imdb_id}, shows))
        print(
            "Multiple shows with <[name] {} | [year] {}> have been found. Please choose one from the following list: ".format(
                show_name, year))
        return get_user_decision(values=shows)

    raise ValueError("Show with <[name] {} | [year] {}> does not exist".format(show_name, year))


def get_episodes(show_id):
    global imdb
    episodes = imdb.get_episodes(show_id)

    return episodes


def retrieve_season_episode_from_file(filename) -> Tuple[int, int]:
    try:
        season_nr, episode_nr = re.findall(r"(?i).*?S(\d+).*?E(\d+).*", filename)[0]
    except IndexError:
        season_nr, episode_nr = re.findall("(?i).*?(\d+)x(\d+).*?", filename)[0]
    return int(season_nr), int(episode_nr)


def get_user_decision(*, values, numbered=None, type_cast_f=None, allow_custom=False):
    if not numbered:
        numbered = range(0, len(values))
        type_cast_f = int

    custom_number = numbered[len(numbered) - 1] + 1
    if not values:
        raise ValueError("Can't let user decide on an empty list")
    for idx, value in enumerate(values):
        print("{}: {}".format(numbered[idx], value))
    if allow_custom:
        print("\n{}: Custom (User input)".format(custom_number))

    try:
        choice = type_cast_f(input("Please enter your choice?\n"))
    except TypeError:
        print("Please enter a valid option")
        return get_user_decision(values=values, numbered=numbered, type_cast_f=type_cast_f, allow_custom=allow_custom)

    if not (choice in numbered or choice == custom_number):
        print("Please enter a valid option")
        return get_user_decision(values=values, numbered=numbered, type_cast_f=type_cast_f, allow_custom=allow_custom)

    if allow_custom and choice == custom_number:
        return input("Please put the new episode name:\n")
    else:
        return values[choice]


def sanitize(name: str):
    bad_chars = ["?", "/", "<", ">", ":", "\"", "\\", "|", "*", " ", "\t", "\n", "\r"]

    # Sanitize first 32 ASCII Characters
    for i in range(0, 31):
        name = name.replace("{:02d}".format(i), "_")

    for bad_char in bad_chars:
        name = name.replace(bad_char, "_")

    # Windows doesn't allow dots (.) or spaces ( ) at the end of a file
    return name.rstrip(".").rstrip(" ")


def main(directory: str, show_name: str, file_ext: str, strict: bool = False, year: int = None,
         season_prefix: str = "S", episode_prefix: str = "E", confirm_renaming: bool = False):
    global imdb

    if not file_ext.startswith("."):
        file_ext = ".{}".format(file_ext)

    imdb = Imdb()
    print("Retrieving show from imdb")
    show: Dict[str, Any] = get_show(show_name, year, strict)
    print("Retrieving episodes for {} from imdb".format(show_name))
    episodes = get_episodes(show['imdb_id'])
    renaming_mapping = {}

    print("Creating new episode names for {} files".format(file_ext))
    for path, _, files in os.walk(directory):
        video_files = filter(lambda file: file.endswith(file_ext), files)
        for video in video_files:
            try:
                season_nr, episode_nr = retrieve_season_episode_from_file(video)
            except IndexError:
                print("Couldn't retrieve season/episode from {}".format(video))
                continue

            file = os.path.join(path, video)
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
            title = sanitize(title)

            new_name = "{}_{}{}_{}{}_{}{}".format(show_name, season_prefix, season_nr, episode_prefix, episode_nr,
                                                  title, file_ext)

            new = os.path.join(path, new_name)
            renaming_mapping[file] = new
            print("{} -> {}".format(os.path.basename(file), os.path.basename(new)))

        if confirm_renaming:
            print("Do you want to rename the previous episodes in {}:".format(path))
            if get_user_decision(values=['Yes', 'No']) == 'No':
                return None
        print("Renaming episodes")
        for old, new in renaming_mapping.items():
            os.rename(old, new)
