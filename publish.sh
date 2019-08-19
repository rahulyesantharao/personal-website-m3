python build.py
sed -i 's/build//' .gitignore
git add build && git commit -m "Build $1"
git subtree push --prefix build origin gh-pages
git checkout -- .gitignore
git reset --hard HEAD^
