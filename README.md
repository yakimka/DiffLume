# DiffLume

[![Build Status](https://github.com/yakimka/DiffLume/actions/workflows/workflow-ci.yml/badge.svg?branch=main&event=push)](https://github.com/yakimka/DiffLume/actions/workflows/workflow-ci.yml)
[![codecov](https://codecov.io/gh/yakimka/DiffLume/branch/main/graph/badge.svg)](https://codecov.io/gh/yakimka/DiffLume)
[![pypi](https://img.shields.io/pypi/v/DiffLume.svg)](https://pypi.org/project/DiffLume/)
[![downloads](https://static.pepy.tech/personalized-badge/DiffLume?period=total&units=none&left_color=grey&right_color=blue&left_text=downloads)](https://pepy.tech/project/DiffLume)

TUI app for viewing deltas between text files

![screenshot](https://raw.githubusercontent.com/yakimka/DiffLume/main/assets/screenshot.png)

## Features

- Three-panel TUI for viewing deltas between text files
- Can view revisions of files (currently only CouchDB is supported)
- Navigate between revisions with ][ and }{ keys
- Sync content between panels
- Full screen mode

## Usage

Install via pip:

```bash
pip install --user DiffLume
```

Then type in your terminal:

```bash
difflume
# or
python -m difflume
```

Or you can run it in Docker:

```bash
docker run -it --rm yakim/difflume
```

## License

[MIT](https://github.com/yakimka/DiffLume/blob/main/LICENSE)


## Credits

This project was generated with [`yakimka/cookiecutter-pyproject`](https://github.com/yakimka/cookiecutter-pyproject).
