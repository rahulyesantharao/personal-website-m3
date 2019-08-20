if [ $# -ne 1 ]; then # check number of inputs
  echo "usage: publish.sh <commit message>"
  exit 1
fi

python build.py
sed -i 's/build//' .gitignore
echo "rahulvgy.com" > build/CNAME
git add build && git commit -m "$1"
git push origin `git subtree split --prefix build master`:gh-pages --force
#git subtree push --prefix build origin gh-pages
git checkout -- .gitignore
git reset --hard HEAD^
