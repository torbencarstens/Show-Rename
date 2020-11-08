import ctypes
import os
import re
from collections import defaultdict
from itertools import chain
from typing import Any, Dict, Tuple, Callable, Optional, List, Union

from imdbpie import Imdb

from rename_show import mkvpropedit

imdb: Imdb = None


def get_show(show_name: str, year: int, strict: bool) -> Dict[str, Any]:
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

    titles = [imdb.get_title(result["imdb_id"]) for result in results]

    results = list(filter(lambda show: show["base"]["titleType"] == "tvSeries", titles))

    if len(results) == 1:
        show = results[0]
        imdb_id = show["base"]["id"].replace("/title/", "").strip("/")
        return {'title': show["base"]["title"], 'year': show["base"]["year"],
                'plot_outline': show.get("plot", {}).get("outline", ""), 'imdb_id': imdb_id}
    elif len(results) > 1:
        shows = list(
            map(lambda show: {'title': show["base"]["title"], 'year': show["base"]["year"],
                              'plot_outline': show.get("plot", {}).get("outline", ""),
                              'imdb_id': show["base"]["id"].replace("/title/", "").rstrip("/")}, results))
        print(
            f"Multiple shows with <{show_name} | {year}> have been found. Please choose one from the following list: ")
        return get_user_decision(values=shows)

    raise ValueError("Show with <[name] {} | [year] {}> does not exist".format(show_name, year))


def get_episodes(show_id: str) -> Dict[str, Any]:
    global imdb
    episodes = imdb.get_title_episodes(show_id)

    return episodes


def retrieve_season_episode_from_file(filename: str) -> Tuple[int, int]:
    try:
        season_nr, episode_nr = re.findall(r"(?i).*?S(\d+).*?E(\d+).*", filename)[0]
    except IndexError:
        season_nr, episode_nr = re.findall("(?i).*?(\d+)x(\d+).*?", filename)[0]

    return int(season_nr), int(episode_nr)


def retrieve_season_from_path(path: str) -> Optional[int]:
    season_nr = re.findall(r"(?i)S(:?eason|taffel)?(:?\s*|[_-])(\d+)", path)

    if season_nr and season_nr[0] and season_nr[0][2].isnumeric():
        return int(season_nr[0][2])
    else:
        return None


def retrieve_episode_from_file(filename: str) -> int:
    try:
        episode_nr = re.findall(r"E(:?p(?:isode)?)?\s*(\d+)", filename, re.IGNORECASE)[0][1]
    except IndexError:
        basename = os.path.basename(filename)
        episode_nr = re.findall(r"S(:?eason)?\s*\d+.*?(\d+)", basename, re.IGNORECASE)[0][1]

    return int(episode_nr)


def get_user_decision(*, values, numbered: bool = False, type_cast_f: Optional[Callable] = None,
                      allow_custom: bool = False, message: str = ""):
    if not numbered:
        numbered = range(1, len(values) + 1)
        type_cast_f = int

    if len(values) == 1:
        return values[0]

    custom_number = numbered[len(numbered) - 1] + 1
    if not values:
        raise ValueError("Can't let user decide on an empty list")

    message = message if message else "Please enter your choice"
    print(message)
    for idx, value in enumerate(values):
        print("{}: {}".format(numbered[idx], value))
    if allow_custom:
        print("\n{}: Custom (User input)".format(custom_number))

    try:
        choice = type_cast_f(input("> "))
    except (ValueError, TypeError):
        print("Please enter a valid option")
        return get_user_decision(values=values, numbered=numbered, type_cast_f=type_cast_f, allow_custom=allow_custom)

    if not (choice in numbered or choice == custom_number):
        print("Please enter a valid option")
        return get_user_decision(values=values, numbered=numbered, type_cast_f=type_cast_f, allow_custom=allow_custom)

    if allow_custom and choice == custom_number:
        return input("Please put the new episode name:\n")
    else:
        return values[choice - 1]


def sanitize(name: str) -> str:
    bad_chars = ["?", "/", "<", ">", ":", "\"", "\\", "|", "*", " ", "\t", "\n", "\r"]

    # Sanitize ASCII Characters
    for i in chain(range(0, 47), range(158, 158), range(59, 64), range(91, 96), range(123, 127)):
        name = name.replace("{}".format(chr(i)), "_")

    for bad_char in bad_chars:
        name = name.replace(bad_char, "_")

    # Windows doesn't allow dots (.) or spaces ( ) at the end of a file

    name = re.sub("_+", r"_", name)
    return name.rstrip(".").rstrip(" ")


def get_episode(episodes: List[Dict[str, Any]], season_number: int, episode_number: int, has_zero_episode: bool,
                skip_first: bool) -> Dict[str, any]:
    # IMDB ocassionally starts episode numbers at `0`
    if episodes[0]["episode"] == 0 and not has_zero_episode and not skip_first:
        episode_number -= 1  # TODO: make it possible to skip the zeroest episode

    try:
        episode = [episode for episode in episodes if episode.get("episode", -1) == episode_number][0]
    except IndexError:
        raise ValueError(f"Couldn't find episode name for S{season_number}E{episode_number}")

    return episode


def rename(root_path: str, episodes: Dict[str, Any], show_name: str, file_ext: str, confirm_renaming: bool = False,
           manual_season: int = None, skip_first: bool = False, custom_format: str = None) -> None:
    renaming_mapping: Dict[str, Dict[str, Union[bool, str, int]]] = defaultdict(dict)
    if ".@__thumb" in root_path:  # plex autogenerates this and keeps the .mkv ending
        return

    season_number = 0

    episode_files = get_episodes_in_directory(root_path, file_ext)
    episode_files = sorted(episode_files)
    has_zero_episode = len(list(filter(
        lambda episode_number: episode_number == 0,
        [retrieve_episode_from_file(file) for file in episode_files]
    ))) > 0

    for file in episode_files:
        renaming_mapping[file]["success"] = True

        basename = os.path.basename(file)
        try:
            if manual_season:
                season_number = int(manual_season)
                episode_nr = retrieve_episode_from_file(basename)
            else:
                season_number, episode_nr = retrieve_season_episode_from_file(basename)
        except IndexError:
            print(f"Couldn't retrieve season/episode from {basename}")
            renaming_mapping[file]["success"] = False
            continue

        try:
            season_episodes = episodes["seasons"][season_number - 1]["episodes"]
        except (IndexError, KeyError, TypeError):
            print(f"Invalid season number ({season_number}), there are only {len(episodes['seasons'])} seasons")
            renaming_mapping[file]["success"] = False
            break

        try:
            episode = get_episode(season_episodes, season_number, episode_nr, has_zero_episode, skip_first)
            raw_title = episode["title"]
            title = sanitize(raw_title)
            renaming_mapping[file]["title"] = raw_title
            # renaming_mapping[file]["year"] = episode.get("year")
        except ValueError:
            print(f"couldn't retrieve episode title for S{season_number}E{episode_nr}")
            renaming_mapping[file]["success"] = False
            break

        default_format = "{show_name}_S{season_number:02d}_E{episode_number:02d}_{title}"
        formatting = default_format if not custom_format else custom_format
        new_name = formatting.format(show_name=show_name, season_number=season_number, episode_number=episode_nr,
                                     title=title)
        new_name = ".".join([new_name, file_ext])

        new = os.path.join(root_path, new_name)
        renaming_mapping[file]["name"] = new

    if all([result["success"] for _, result in renaming_mapping.items()]):
        print(f"directory: {root_path}")
        for old, new in renaming_mapping.items():
            new_name = os.path.basename(new.get("name"))
            old = os.path.basename(old)

            rename_episode = True
            if confirm_renaming:
                print("Do you want to rename {} to {}".format(old, new_name))
                if get_user_decision(values=["Yes", "No"]) == 'No':
                    rename_episode = False

            if rename_episode:
                new_name = new.get("name")
                old_path = os.path.join(root_path, os.path.basename(old))
                os.rename(old_path, new_name)
                if new_name.endswith(".mkv"):
                    if not mkvpropedit.set_title(new_name, new.get("title", "")):
                        print(f"mkv metadata for {new_name} couldn't be updated")
    else:
        print(f"Couldn't rename one of the episodes in S{season_number}, is there a double episode?")
        if get_user_decision(values=["Yes", "No"]) == "Yes":
            season_episodes: List[Dict[str, Any]] = episodes["seasons"][season_number - 1]["episodes"]
            print("Which one is the duplicate episode?")
            duplicate_title: Dict[str, Any] = get_user_decision(values=season_episodes)
            if not duplicate_title:
                print("Aborting due to missing input")
                raise ValueError("No information about a duplicate title was supplied")
            try:
                index, episode = [(index, episode) for index, episode in enumerate(season_episodes)
                                  if episode.get("title") == duplicate_title.get("title")][0]
                season_episodes.insert(index + 1, episode.copy())
                for episode in season_episodes[index + 1:]:
                    episode["episode"] = episode.get("episode") + 1

                episodes["seasons"][season_number - 1]["episodes"] = season_episodes
                return rename(root_path=root_path, episodes=episodes, show_name=show_name, file_ext=file_ext,
                              confirm_renaming=confirm_renaming, manual_season=manual_season,
                              custom_format=custom_format)
            except IndexError:
                # This shouldn't happen, since we pick the duplicate from the existing episode list
                print("Couldn't find that episode in season")


def get_episodes_in_directory(path: str, file_ext: str) -> List[str]:
    for _, _, files in os.walk(path):
        return [os.path.join(path, file) for file in filter(lambda file: file.endswith(file_ext), files)]


def write_imdb_file(filename: str, imdb_id: str):
    with open(filename, "w+") as imdb_file:
        imdb_file.write(imdb_id)

    if os.name == "nt":
        ctypes.windll.kernel32.SetFileAttributesW(filename, 0x02)


def get_imdb_id(directory: str) -> Optional[str]:
    imdb_filepath = os.path.join(directory, ".imdb_id")
    if os.path.exists(imdb_filepath):
        with open(imdb_filepath, "r") as imdb_file:
            return "".join(imdb_file.readlines()).strip().rstrip()

    for root, directories, files in os.walk(directory):
        for directory in directories:
            try:
                with open(os.path.join(root, directory, ".imdb_id"), "r") as imdb_file:
                    return "".join(imdb_file.readlines()).strip().rstrip()
            except OSError:
                pass

    return None


def main(directory: str, show_name: str, file_ext: str, strict: bool = False, year: int = None,
         confirm_renaming: bool = False, rename_to: str = None, season: str = None, skip_first: bool = False,
         custom_format: str = None):
    global imdb

    if rename_to is None:
        rename_to = show_name
    rename_to = sanitize(rename_to)

    imdb = Imdb()
    print("Retrieving show from imdb")
    imdb_id = get_imdb_id(directory)
    if not imdb_id:
        show: Dict[str, Any] = get_show(show_name, year, strict)
        imdb_id = show["imdb_id"]
    print("Retrieving episodes for {} from imdb".format(show_name))
    episodes = get_episodes(imdb_id)

    print("Creating new episode names for {} files".format(file_ext))
    for root, directories, _ in os.walk(directory):
        write_imdb_file(os.path.join(root, directory, ".imdb_id"), imdb_id)
        if not season:
            season = retrieve_season_from_path(directory)

        rename(directory, episodes, rename_to, file_ext, confirm_renaming, season, skip_first,
               custom_format=custom_format)

        imdb_file_location = os.path.join(root, directory, ".imdb_id")
        if not os.path.exists(imdb_file_location):
            write_imdb_file(imdb_file_location, imdb_id)
        for directory in directories:
            if not season:
                season = retrieve_season_from_path(directory)

            imdb_file_location = os.path.join(root, directory, ".imdb_id")
            if not os.path.exists(imdb_file_location):
                write_imdb_file(imdb_file_location, imdb_id)

            directory = os.path.join(root, directory)
            rename(directory, episodes, rename_to, file_ext, confirm_renaming, season, skip_first,
                   custom_format=custom_format)
            season = None
