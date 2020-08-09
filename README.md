# Personal Website, mark 3
Yet another personal website rebuild - completely static this time!
The script `build.py` is reasonably general, and can be used to build other websites. Making it fully general is a work-in-progress.

## Setup
First, set up the Python environment.
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Then, set up the Node environment.
```
npm install
```

## Usage
 - Run `python build.py` to build the site from `src/` to `build/`.
 - Use `publish.sh` to publish the site to GitHub. 

## Features
 - `<snippet src=""../>` - Use to substitute predefined snippets into html files
 - `<markdown src=""../>` - Use to include markdown files into html files
 - `{{ .. }}` - Use to write arbitrary python expressions in html files (single eval statements).

