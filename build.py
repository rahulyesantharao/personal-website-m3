# TODO:
#  - Jinja style snippets (with variable substitution)
#  - Do some serious refactoring of directory management
#  - Check if there's a better way to replace backslashes than just string replace
#  - issue with nbsp in footer
#  - Cache busting for html
import os
import shutil
import functools
import pathlib
from html.parser import HTMLParser
import hashlib
import logging
import re
import json
from datetime import date
import urllib
import importlib.util

import sass
import cssutils
import markdown

cssutils.log.setLevel(logging.CRITICAL)


def slugify(x):
    slug = x
    slug = re.compile("[^\s\w_]+").sub("", slug)  # remove non alphanumeric
    slug = re.compile("\s+").sub("-", slug)  # whitespace to dash
    slug = slug.lower()  # lowercase
    slug = urllib.parse.quote(slug)  # quote anything remaining
    return slug


class HTMLBuilder(HTMLParser):
    """Base class for HTML compilers.

    Streams input HTML to output file, specified by parameters.
    Use as a ContextManager (with) in order to manage file properly.

    Attributes:
        build_dir (str): directory of output HTML file
        build_file (str): file name of output file (with extension)
    """

    def __init__(self, build_dir, build_file):
        super().__init__(convert_charrefs=True)
        self.ofilepath = os.path.join(build_dir, build_file)
        self.ofile = None

    def __enter__(self):
        """Entry method for context manager.

        Opens and returns output file.

        Raises:
            Any error associated with making the file (and its directory)

        Returns:
            Output file object.
        """
        if not os.path.exists(os.path.dirname(self.ofilepath)):
            os.makedirs(os.path.dirname(self.ofilepath))  # let errors raise
        self.ofile = open(self.ofilepath, "a+", buffering=1)
        return self

    def __exit__(self, *args):
        """Exit method for context manager.

        Closes the output file.
        """
        self.ofile.close()

    @staticmethod
    def _build_attrs(attrs_list):
        """Converts the list of attributes into HTML `attribute=value` format.

        Args:
            attrs_list (list): List of tuples of the form `(attr, value)`.
                Should be the list of attributes returned by HTMLParser
                handler methods.

        Returns:
            string of `attr=val` pairs, for injection in HTML
        """
        if not attrs_list:  # empty list
            return ""

        attrs = map(lambda a: a[0] if a[1] is None else f'{a[0]}="{a[1]}"', attrs_list)
        return " " + functools.reduce(lambda a, b: f"{a} {b}", attrs)

    # default handlers: in -> out
    def handle_starttag(self, tag, attrs):
        self.ofile.write(f"<{tag}{PageBuilder._build_attrs(attrs)}>")

    def handle_startendtag(self, tag, attrs):
        self.ofile.write(f"<{tag}{PageBuilder._build_attrs(attrs)}/>")

    def handle_endtag(self, tag):
        self.ofile.write(f"</{tag}>")

    def handle_data(self, data):
        self.ofile.write(data)

    def handle_decl(self, decl):
        self.ofile.write(f"<!{decl}>")


class PageBuilder(HTMLBuilder):
    """Class to build top level HTML source pages, with Snippet and Markdown tags.

    Compiles custom HTML pages into pure HTML source files to serve. In particular,
    performs several different operations.
        1. Parses `<Markdown src="...">` tags and replaces them with the converted
           Markdown content from the `src` file.
        2. Parses `<Snippet src="..." var1="..." var2="...">` tags and replaces them
           with the converted HTML snippet files, with the variables substituted in.
        3. Adds hashes to included CSS and image files (for cache busting)

    Attributes:
        src_dir (str): directory of input source file
        build_dir (str): directory of output HTML file
        build_file (str): file name of output file (with extension)
        file_hash (func): hash function that returns name of file with hash value added
        top_prefix (str): prefix of the file from the top build folder
            TODO: Convert this to `resource_prefix` or something more general
        var (dict): dictionary of variables to substitute into the raw page data
    """

    def __init__(self, src_dir, build_dir, build_file, file_hash, top_prefix, var):
        super().__init__(build_dir, build_file)
        self.srcdir = src_dir
        self.builddir = build_dir
        self.buildfile = build_file
        self.filehash = file_hash
        self.topprefix = top_prefix
        self.var = var
        datafile = os.path.join(self.srcdir, "data.json")
        if os.path.exists(datafile):
            with open(datafile, "r") as f:
                self.var["data"] = json.load(f)

    def feed(self, data):
        def f(x):
            # print(x.group(1))
            return eval(
                x.group(1),
                {
                    "slugify": slugify,
                    "date": date,
                    "quote": urllib.parse.quote,
                    "base_url": "https://rahulyesantharao.com",
                },
                self.var,
            )

        try:
            data = re.sub(r"{{ (.*?) }}", f, data, flags=re.DOTALL)
        except Exception as e:
            print("***** ERROR *****")
            print(e)
        super().feed(data)

    def _replace_src(self, src_file, src_dir, dest_dir):
        """Helper function to hash a given source file.

        Checks whether the source file exists, and then calls self.file_hash
        on it.

        Args:
            src_file (str): name of source file
            src_dir (str): directory of source file
            dest_dir (str): intended directory of output (hash-tagged) file, relative to top level
                build directory.
                TODO: Use os.path to get path between current self.srcdir and overall build
                      directory to make this more general.

        Returns:
            The path of the output file, relative to the top level build directory.
        """
        src_path = os.path.normpath(src_file)  # normalize path to file
        src_path = os.path.join(
            src_dir, src_path
        )  # create relative path from cwd to file
        # print(src_path)
        # print(f"src_dir: {self.srcdir}")
        # print(f"build_dir: {self.builddir}")
        assert os.path.exists(src_path)  # make sure file exists
        newpath = self.filehash(src_path, dest_dir)
        newpath = os.path.join(self.topprefix, newpath)
        return newpath

    def _replace_attr(self, attrs, attr_name, src_dir, dest_dir, test_func):
        """Helper function to replace an attribute in a list with a hashed version.

        Checks whether the attribute value should be hashed, and if so, calls
        self._replace_src to get the hashed value and replaces it in attrs

        Args:
            attrs (list): a list of tuples `(attr, val)` to be modified
            attr_name (str): the specific attribute to give a hash-tagged value
            src_dir (str): directory of source file
            dest_dir (str): intended directory of output (hash-tagged) file
            test_func (func): function to check if `val` should be hashed or not.

        Returns:
            Nothing, but modifies attrs
        """
        # extract name of file to be hashed
        try:
            src_file = list(filter(lambda x: x[0] == attr_name, attrs))[0][1]
        except:
            pass
        else:
            if test_func(src_file):
                newpath = self._replace_src(src_file, src_dir, dest_dir)
                attrs[:] = map(
                    lambda x: (x[0], newpath.replace("\\", "/"))
                    if x[0] == attr_name
                    else x,
                    attrs,
                )

    def handle_starttag(self, tag, attrs):
        """Parses start tags, and hashes the included local CSS files.

        Replaces local CSS files with a hash-tagged version for cache-busting.
        Is called automatically by HTMLParser base class when an HTML file is
        fed with feed()
        """
        if tag == "link":
            rel_type = list(filter(lambda x: x[0] == "rel", attrs))[0][
                1
            ]  # extract rel type of <link> tag
            if (
                rel_type == "stylesheet"
            ):  # if it's a stylesheet, hash it as long as it's local
                self._replace_attr(
                    attrs,
                    "href",
                    os.path.dirname(self.ofilepath),
                    "css",
                    lambda x: not x.startswith("http"),
                )
        elif tag == "script":
            self._replace_attr(
                attrs,
                "src",
                os.path.dirname(self.ofilepath),
                "scripts",
                lambda x: not x.startswith("http"),
            )
        elif tag == "a":
            if (
                len(list(filter(lambda t: t[0] == "target", attrs))) == 0
            ):  # no target, default to external
                attrs.append(("target", "_blank"))
                attrs.append(("rel", "noopener noreferrer external"))

        self.ofile.write(f"<{tag}{PageBuilder._build_attrs(attrs)}>")
        if tag == "li":
            self.ofile.write("<span>")

    def handle_startendtag(self, tag, attrs):
        """Parses start/end tags (`<.../>`), and performs the necessary compile steps.

        Is called automatically by base class. Performs several replacements (also
        documented in class docstring)
            1. Parses `<Markdown src="...">` tags and replaces them with the converted
            Markdown content from the `src` file.
            2. Parses `<Snippet src="..." var1="..." var2="...">` tags and replaces them
            with the converted HTML snippet files, with the variables substituted in.
            3. Adds hashes to included image files (for cache busting).
        """
        # TODO: Make this cleanly recursive for tag expansion
        if tag == "markdown":
            attrs = dict(attrs)
            with open(
                os.path.join(self.srcdir, os.path.normpath(attrs["src"])),
                mode="r",
                encoding="utf-8",
            ) as f:
                data = f.read()
            with PageBuilder(
                self.srcdir,
                self.builddir,
                self.buildfile,
                self.filehash,
                self.topprefix,
                attrs,
            ) as pb:
                pb.feed(
                    markdown.markdown(
                        data,
                        extensions=["codehilite"],
                        extension_configs={"codehilite": {"linenums": True}},
                    )
                )
            # self.ofile.write(markdown.markdown(data))
        elif tag == "snippet":
            self._replace_attr(
                attrs,
                "fb_img",
                self.srcdir,
                "images",
                lambda x: not x.startswith("http"),
            )
            attrs = dict(attrs)
            if "fb_img" in attrs:
                attrs["fb_img"] = os.path.basename(attrs["fb_img"])
            with open(
                os.path.join(self.srcdir, os.path.normpath(attrs["src"])), "r"
            ) as snippet:
                data = snippet.read()
            # data = re.sub(r'{{ (.*?) }}', lambda x: attrs[x.group(1)], data)
            with PageBuilder(
                self.srcdir,
                self.builddir,
                self.buildfile,
                self.filehash,
                self.topprefix,
                attrs,
            ) as pb:
                pb.feed(data)
        elif tag == "img":
            self._replace_attr(
                attrs, "src", self.srcdir, "images", lambda x: not x.startswith("http")
            )
            self.ofile.write(f"<{tag}{PageBuilder._build_attrs(attrs)}/>")
        elif tag == "python":
            attrs = dict(attrs)

            # load the module: https://stackoverflow.com/a/67692
            module_name = attrs["src"][: attrs["src"].rfind(".")]
            module_path = os.path.join(self.srcdir, os.path.normpath(attrs["src"]))
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            # run the code
            old_cwd = os.getcwd()
            os.chdir(self.srcdir)
            data = mod.func()
            os.chdir(old_cwd)

            # recurse the data in
            with PageBuilder(
                self.srcdir,
                self.builddir,
                self.buildfile,
                self.filehash,
                self.topprefix,
                attrs,
            ) as pb:
                pb.feed(data)
        else:
            self.ofile.write(f"<{tag}{PageBuilder._build_attrs(attrs)}/>")

    def handle_endtag(self, tag):
        if tag == "li":
            self.ofile.write("</span>")
        self.ofile.write(f"</{tag}>")


# TODO: USE ffmpeg to compress images
class SiteBuilder:
    """
    Assumes source structure below:
    src/
        favicons/ - copied directly to build
        images/ - only relevant images copied to build
        sass/ - compiled and moved to build
        scripts/ - copied to build
        snippets/ - shared snippets of html
        *.html - compiled and moved to build

    Creates build structure below:
    build/
        favicons/* (in main directory)
        index.html
        filename/
            index.html
        css/
            main.hash.css
        scripts/
            main.hash.js
        images/

    """

    def __init__(self, src_base, build_base):
        super().__init__()
        self.srcdir = src_base
        self.builddir = build_base
        self.hashed_files = {}

    def file_hash(self, filepath, destdir, *, save=True):
        # TODO: use os.path.samefile to check for equality; shouldn't need this with abspath (below)
        if filepath.startswith("http"):  # TODO: hack for checking for web urls
            return filepath
        filepath = os.path.abspath(filepath)
        if filepath in self.hashed_files:
            return self.hashed_files[filepath]

        hasher = hashlib.md5()
        BLOCKSIZE = 65536
        with open(filepath, "rb") as img:
            buf = img.read(BLOCKSIZE)
            while len(buf) > 0:
                hasher.update(buf)
                buf = img.read(BLOCKSIZE)

        origname = os.path.basename(os.path.normpath(filepath))
        lastdot = origname.rfind(".")
        newname = f"{origname[:lastdot]}.{hasher.hexdigest()}.{origname[lastdot+1:]}"
        if save:
            self.hashed_files[filepath] = os.path.normpath(
                os.path.join(destdir, newname)
            )
            return self.hashed_files[filepath]
        else:
            return newname

    def build(self):
        if os.path.exists(self.builddir):  # make sure it doesn't exist
            shutil.rmtree(self.builddir)

        # favicons
        print("* Copying Favicons")
        shutil.copytree(
            f"{self.srcdir}/favicons", f"{self.builddir}/"
        )  # copy over favicons, create builddir

        # sass
        print("* Compiling SCSS")
        os.makedirs(os.path.join(self.builddir, "css"))
        ocsspath = os.path.join(self.builddir, "css", "main.css")
        with open(ocsspath, "w+") as css:
            css.write(sass.compile(filename="src/scss/styles.scss"))

        # copy over js
        print("* Moving JS")
        os.makedirs(os.path.join(self.builddir, "scripts"))
        shutil.copyfile(
            f"{self.srcdir}/scripts/main.js", f"{self.builddir}/scripts/main.js"
        )  # copy over favicons, create builddir

        # replace images
        cssFile = cssutils.parseFile(ocsspath)
        cssutils.replaceUrls(
            cssFile,
            lambda x: os.path.join(
                "..",
                self.file_hash(
                    os.path.join("src", "scss", os.path.normpath(x)), "images"
                ),
            ).replace("\\", "/"),
            ignoreImportRules=True,
        )
        with open(ocsspath, "wb") as css:
            css.write(cssFile.cssText)

        # html
        print("* Gathering HTML files to build")
        html_to_build = []
        for dirpath, _, filenames in os.walk(self.srcdir):
            if dirpath.find("snippets") == -1 and dirpath.find("projects") == -1:
                for filename in filenames:
                    if filename == "index.html":
                        html_to_build.append((dirpath, filename))

        print("* Building HTML files")
        for path, filename in html_to_build:
            src_dir = path
            build_file = filename
            build_base = pathlib.Path(path)
            print(f"  - src: {path} ({build_base.parts}) : {build_file}")
            build_base = pathlib.Path(*build_base.parts[1:])
            build_base = os.path.join(self.builddir, build_base)
            main_page = os.path.samefile(self.srcdir, path)
            print(f"  - build_base: {build_base}")
            print(f"  - main_page: {main_page}\n")
            with PageBuilder(
                src_dir,
                build_base,
                build_file,
                self.file_hash,
                "" if main_page else "..",
                {},
            ) as pb:
                with open(os.path.join(path, filename)) as f:
                    data = f.read()
                pb.feed(data)

        # blog/projects
        print("* Building Blog")
        for page, subpage, prefix in [("blog", "posts", "../../..")]:
            pagedir = os.path.join(self.srcdir, page)
            if os.path.exists(pagedir):
                with open(
                    os.path.join(pagedir, "data.json"), "r", encoding="utf-8"
                ) as f:
                    posts = json.load(f)
                for i, post in enumerate(posts):
                    # convert dates to [date] object
                    for key in ["post_date", "update_date"]:
                        if key in post:
                            post[key] = date(*([int(x) for x in post[key].split("-")]))
                            post[key] = post[key].strftime("%B %d, %Y")
                        else:
                            post[key] = None
                    # create slug
                    if "url" not in post:
                        post["url"] = slugify(post["title"])
                    # author
                    post["author"] = "Rahul Yesantharao"
                    post["num"] = i + 1

            # print("* POST DATA *")
            # print(posts)
            # print()
            postdest = os.path.join(os.path.join(self.builddir, page), subpage)
            if not os.path.exists(postdest):
                os.mkdir(postdest)
            for i in range(len(posts)):
                postdir = os.path.join(postdest, posts[i]["url"])
                os.mkdir(postdir)
                print(f"  - {posts[i]['url']} -> {pagedir}")
                with PageBuilder(
                    pagedir, postdir, "index.html", self.file_hash, prefix, posts[i]
                ) as pb:
                    with open(
                        os.path.join(pagedir, "post.html"), "r", encoding="utf-8"
                    ) as f:
                        data = f.read()
                        pb.feed(data)

        # images and css (hashed files)
        cssfiles = []
        jsfiles = []
        print("* Moving hashed files")
        os.makedirs(os.path.join(self.builddir, "images"))
        for src in self.hashed_files:
            dst = self.hashed_files[src]
            dst = os.path.join(self.builddir, dst)
            if dst.endswith(".js"):
                jsfiles.append(dst)
            if dst.endswith(".css"):
                cssfiles.append(dst)
            print(f"  - {src} -> {dst}")
            if not os.path.exists(dst):
                shutil.copyfile(src, dst)

        # delete unhashed css file
        os.remove(os.path.join(self.builddir, "css", "main.css"))
        os.remove(os.path.join(self.builddir, "scripts", "main.js"))

        # postprocess
        print("* Postprocessing!")
        print(cssfiles)
        print(jsfiles)
        os.system(f"bash postprocess.sh {cssfiles[0]} {jsfiles[0]}")


if __name__ == "__main__":
    sb = SiteBuilder("src", "build")
    sb.build()
