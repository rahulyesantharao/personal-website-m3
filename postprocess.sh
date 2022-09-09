#!/usr/bin/bash
cssfile=$1
jsfile=$2
echo "start postcss"
npx postcss "$cssfile" -d build/css/
echo "start uglifyjs"
npx uglifyjs --compress --mangle -o "$jsfile" -- "$jsfile"
echo "start html-minifier"
npx html-minifier -c html-config.conf --input-dir build/ --output-dir build/ --file-ext html
