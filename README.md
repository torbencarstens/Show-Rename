# Show-Rename

## Requirements

- Python >=3.6

## Usage

### Installation

```shell
git clone https://github.com/torbencarstens/Show-Rename/
cd Show-Rename

# Creating a virtual environemnt and activating it
python3 -m pip install virtualenv --user
virtualenv -p $(which python3) .venv
chmod +x .venv/bin/activate
source .venv/bin/activate

# Install all requirements
pip install -r requirements.txt
```

### Renaming

```shell
python main.py --name {SHOW_NAME} --directory {SHOW_DIRECTORY}

# Example
python main.py --name "My Cool Show" --directory /mnt/shows/fuckingamazinglocation
```

```
Usage:
    main.py [options]
   
    Options:
        --name=<name>
        -d --directory=<directory>
        -f --file-ext=<file-ext>
        --strict
        --rename-to=<rename-to>
        --season=<season>
        --skip-first-episode
        --confirm
        --custom_format=<custom_format>
```

#### Examples for custom fomrat

Possible keys: `show_name`, `season_number`, `episode_number`, `title`:
```
{show_name}_S{season_number:02d}_E{episode_number:02d}_{title} # default
S{season_number:02d}_E{episode_number:02d}_{title}
```

#### Using an .imdb_id

Create a file `.imdb_id` in the directory and write the imdb id into it.

#### Ignoring a directory

Placing an `.imdbignore` file into a directory will result in the directory and all its subdirectories being ignored.
