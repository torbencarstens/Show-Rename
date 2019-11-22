import ctypes
import os
import re
from itertools import chain
from typing import Any, Dict, Tuple, Callable, Optional, List

from imdbpie import Imdb

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
            f"Multiple shows with <[name] {show_name} | [year] {year}> have been found. Please choose one from the following list: ")
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


def retrieve_episode_from_file(filename: str) -> int:
    episode_nr = re.findall(r"(?i)E(:?p(?:isode)?)?\s*(\d+)", filename)[0][1]

    return int(episode_nr)


def get_user_decision(*, values, numbered: bool = None, type_cast_f: Optional[Callable] = None,
                      allow_custom: bool = False):
    if not numbered:
        numbered = range(0, len(values))
        type_cast_f = int

    if len(values) == 1:
        return values[0]

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


def sanitize(name: str) -> str:
    bad_chars = ["?", "/", "<", ">", ":", "\"", "\\", "|", "*", " ", "\t", "\n", "\r"]

    # Sanitize ASCII Characters
    for i in chain(range(0, 47), range(158, 158), range(59, 64), range(91, 96), range(123, 127)):
        name = name.replace("{:02d}".format(i), "_")

    for bad_char in bad_chars:
        name = name.replace(bad_char, "_")

    # Windows doesn't allow dots (.) or spaces ( ) at the end of a file

    name = re.sub("_+", r"_", name)
    return name.rstrip(".").rstrip(" ")


def get_episode_title(episodes: Dict[str, Any], season_nr: int, episode_nr: int) -> str:
    try:
        episodes = episodes["seasons"][season_nr - 1]["episodes"]
    except (IndexError, KeyError):
        raise ValueError(f"Invalid season number ({season_nr}), there are only {len(episodes['seasons'])} seasons")

    try:
        episode = episodes[episode_nr - 1]
    except IndexError:
        raise ValueError(f"Couldn't find episode name for S{season_nr}E{episode_nr}")

    return sanitize(episode["title"])


def rename(root_path: str, episodes: Dict[str, Any], show_name: str, file_ext: str, confirm_renaming: bool = False,
           manual_season: int = None) -> None:
    renaming_mapping = {}
    for file in get_episodes_in_directory(root_path, file_ext):
        basename = os.path.basename(file)
        try:
            if manual_season:
                season_nr = int(manual_season)
                episode_nr = retrieve_episode_from_file(basename)
            else:
                season_nr, episode_nr = retrieve_season_episode_from_file(basename)
        except IndexError:
            print(f"Couldn't retrieve season/episode from {basename}")
            continue
        title = get_episode_title(episodes, season_nr, episode_nr)

        new_name = "_".join([i for i in [show_name, f"S{season_nr:02d}", f"E{episode_nr:02d}", title] if i])
        new_name = ".".join([new_name, file_ext])

        new = os.path.join(root_path, new_name)
        renaming_mapping[file] = new

    if confirm_renaming:
        print("Do you want to rename the previous episodes in {}:".format(root_path))
        if get_user_decision(values=['Yes', 'No']) == 'No':
            return None

    print("Renaming episodes")
    for old, new in renaming_mapping.items():
        os.rename(old, new)


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
         confirm_renaming: bool = False, rename_to: str = None, season: str = None):
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
        rename(directory, episodes, rename_to, file_ext, confirm_renaming, season)
        write_imdb_file(os.path.join(root, ".imdb_id"), imdb_id)
        for directory in directories:
            write_imdb_file(os.path.join(root, directory, ".imdb_id"), imdb_id)
            directory = os.path.join(root, directory)
            rename(directory, episodes, rename_to, file_ext, confirm_renaming)
