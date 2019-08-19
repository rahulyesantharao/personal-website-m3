#!/usr/bin/bash
cssfile=$1
jsfile=$2
npx postcss "$cssfile" -d build/css/
npx uglifyjs --compress --mangle -o "$jsfile" -- "$jsfile"
npx html-minifier -c html-config.conf --input-dir build/ --output-dir build/ --file-ext html
