# Personal Website, mark 3
Yet another personal website rebuild - completely static this time!

## Usage
Run `python build.py` to build the site from `src/` to `build/`. Use `publish.sh` to publish the site to Github. The script `build.py` is reasonably general, and can be used to build other websites.

## Features
 - `<snippet src=""../>` - Use to substitute predefined snippets into html files
 - `<markdown src=""../>` - Use to include markdown files into html files
 - `{{ .. }}` - Use to write arbitrary python expressions in html files (single eval statements).
 
TODO:
 - [ ] run benchmarks to compare old and new sites
 - [ ] write a blog post about it
 - [ ] figure out how to get the publish script working with CNAME file
 - [ ] index.html cache busting
 - [ ] open markdown links in new tab - custom extension
 - [ ] facebook, twitter meta tags
 - [ ] site analytics
 - [ ] site cover for mobile drawer (darken website)
