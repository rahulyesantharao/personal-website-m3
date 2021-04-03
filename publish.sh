#!/bin/bash
set -e
set -u
set -o pipefail

if [ $# -ne 1 ]; then # check number of inputs
  echo "usage: publish.sh <commit message>"
  exit 1
fi

# create build folder
python build.py
echo "rahulyesantharao.com" > build/CNAME

# Old, force push
#sed -i 's/build//' .gitignore
#git add build && git commit -m "$1"
#git push origin `git subtree split --prefix build master`:gh-pages --force
##git subtree push --prefix build origin gh-pages
#git checkout -- .gitignore
#git reset --hard HEAD^

# New, saves progress
echo "BUILD FINISHED"
git checkout gh-pages # eventually, change to git switch
echo "SWITCHED TO gh-pages"
git ls-files -z | xargs -0 rm -f # remove all tracked files
echo "REMOVED files"
git ls-tree --name-only -d -r -z HEAD | sort -rz | xargs -0 rmdir # remove tracked directories
echo "REMOVED dirs"
git add build # add build files
echo "ADDED build"
git mv build/* .
echo "MOVED build"
git commit -m "$1"
echo "COMMITTED"
git push origin gh-pages
echo "DONE"
git checkout master
