# TODO:
#  - Jinja style snippets (with variable substitution)
#  - Stop output paths in files from having backslashes
#  - Cache busting for html
import os
import shutil
import functools
import pathlib
from html.parser import HTMLParser
import hashlib
import logging

import sass
import cssutils
cssutils.log.setLevel(logging.CRITICAL)

class HTMLBuilder(HTMLParser):
    '''Base class for HTML compilers. 
    
    Streams input HTML to output file, specified by parameters.
    Use as a ContextManager (with) in order to manage file properly.
    
    Attributes:
        build_dir (str): directory of output HTML file
        build_file (str): file name of output file (with extension)
    '''

    def __init__(self, build_dir, build_file):
        super().__init__(convert_charrefs=True)
        self.ofilepath = os.path.join(build_dir, build_file)
        self.ofile = None
    
    def __enter__(self):
        '''Entry method for context manager.

        Opens and returns output file.

        Raises:
            Any error associated with making the file (and its directory)
        '''
        if not os.path.exists(os.path.dirname(self.ofilepath)):
            os.makedirs(os.path.dirname(self.ofilepath)) # let errors raise
        self.ofile = open(self.ofilepath, 'w+')
        return self
    
    def __exit__(self, *args):
        '''Exit method for context manager.

        Closes the output file.
        '''
        self.ofile.close()

    @staticmethod
    def _build_attrs(attrs_list):
        '''Converts the list of attributes into HTML `attribute=value` format.

        Args:
            attrs_list (list): List of tuples of the form `(attr, value)`.
                Should be the list of attributes returned by HTMLParser
                handler methods.
        '''
        if(not attrs_list): # empty list
            return ""
        
        attrs = map(lambda a: a[0] if a[1] is None else f'{a[0]}="{a[1]}"', attrs_list)
        return " " + functools.reduce(lambda a,b: f'{a} {b}', attrs)
    
    # default handlers: in -> out
    def handle_starttag(self, tag, attrs):
        self.ofile.write(f'<{tag}{PageBuilder._build_attrs(attrs)}>')

    def handle_startendtag(self, tag, attrs):
        self.ofile.write(f'<{tag}{PageBuilder._build_attrs(attrs)}/>')

    def handle_endtag(self, tag):
        self.ofile.write(f'</{tag}>')
    
    def handle_data(self, data):
        self.ofile.write(data)

    def handle_decl(self, decl):
        self.ofile.write(f'<!{decl}>')


class PageBuilder(HTMLBuilder):
    '''Class to build top level HTML source pages, with Snippet and Markdown tags.

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
        main_page (bool): indicates whether this is the top level index.html; TODO: Convert this to `resource_prefix` or something more general
    '''

    def __init__(self, src_dir, build_dir, build_file, file_hash, main_page):
        super().__init__(build_dir, build_file)
        self.srcdir = src_dir
        self.imghash = file_hash
        self.mainpg = main_page

    def _replace_src(self, src_file, src_dir, dest_dir):
        '''Helper function to hash a given source file.

        Checks whether the source file exists, and then calls self.file_hash
        on it.

        Args:
            src_file (str): name of source file
            src_dir (str): directory of source file
            dest_dir (str): intended directory of output (hash-tagged) file,
                relative to top level build directory. TODO: Use os.path to get path between current self.srcdir and overall build directory to make this more general.
        
        Returns:
            The path of the output file, relative to the top level build directory.
        '''
        src_path = os.path.normpath(src_file)
        src_path = os.path.join(src_dir, src_path)
        assert os.path.exists(src_path) # make sure file exists
        newpath = self.imghash(src_path, dest_dir)
        if not self.mainpg:
            newpath = os.path.join('..', newpath)
        return newpath
    
    def _replace_attr(self, attrs, attr_name, src_dir, dest_dir, testfunc):
        src_file = list(filter(lambda x: x[0] == attr_name, attrs))[0][1] # extract name of file to be hashed
        if testfunc(src_file):
            newpath = self._replace_src(src_file, src_dir, dest_dir)
            attrs[:] = map(lambda x: (x[0], newpath) if x[0] == attr_name else x, attrs)

    # hash css files
    def handle_starttag(self, tag, attrs):
        if tag == 'link':
            if list(filter(lambda x: x[0] == 'rel', attrs))[0][1] == 'stylesheet':
                self._replace_attr(attrs, 'href', os.path.dirname(self.ofilepath), 'css', 
                    lambda x: not x.startswith('http'))
        self.ofile.write(f'<{tag}{PageBuilder._build_attrs(attrs)}>')

    # Build handler
    def handle_startendtag(self, tag, attrs):
        if tag == 'Markdown':
            pass
        elif tag == 'Snippet':
            pass
        elif tag == 'img':
            self._replace_attr(attrs, 'src', self.srcdir, 'images', lambda x: True)
            self.ofile.write(f'<{tag}{PageBuilder._build_attrs(attrs)}/>')
        else:
            self.ofile.write(f'<{tag}{PageBuilder._build_attrs(attrs)}/>')


# TODO: USE ffmpeg to compress images
class SiteBuilder:
    '''
    Assumes source structure below:
    src/
        favicons/ - copied directly to build
        images/ - only relevant images copied to build
        sass/ - compiled and moved to build
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
        images/
        
    '''
    
    def __init__(self, src_base, build_base):
        super().__init__()
        self.srcdir = src_base
        self.builddir = build_base
        self.hashed_files = {}
    
    def file_hash(self, filepath, destdir, *, save=True):
        # TODO: use os.path.samefile to check for equality; shouldn't need this with abspath (below)
        if filepath.startswith('http'): # TODO: hack for checking for web urls
            return filepath
        filepath = os.path.abspath(filepath)
        if filepath in self.hashed_files:
            return self.hashed_files[filepath]

        hasher = hashlib.md5()
        BLOCKSIZE = 65536
        with open(filepath, 'rb') as img:
            buf = img.read(BLOCKSIZE)
            while len(buf) > 0:
                hasher.update(buf)
                buf = img.read(BLOCKSIZE)

        origname = os.path.basename(os.path.normpath(filepath))
        lastdot = origname.rfind('.')
        newname = f'{origname[:lastdot]}.{hasher.hexdigest()}.{origname[lastdot+1:]}'
        if save:
            self.hashed_files[filepath] = os.path.normpath(os.path.join(destdir, newname))
            return self.hashed_files[filepath]
        else:
            return newname
        
    
    def build(self):
        assert not os.path.exists(self.builddir) # make sure it doesn't exist
        
        # favicons
        shutil.copytree(f'{self.srcdir}/favicons', f'{self.builddir}/') # copy over favicons, create builddir

        # sass
        os.makedirs(os.path.join(self.builddir, 'css'))
        ocsspath = os.path.join(self.builddir, 'css', 'main.css')
        with open(ocsspath, 'w+') as css:
            css.write(sass.compile(filename='src/scss/styles.scss'))

        # replace images
        cssFile = cssutils.parseFile(ocsspath)
        cssutils.replaceUrls(cssFile, 
            lambda x: os.path.join('..',self.file_hash(os.path.join('src','scss',os.path.normpath(x)), 'images')), ignoreImportRules=True)
        with open(ocsspath, 'wb') as css:
            css.write(cssFile.cssText)

        # html
        html_to_build = []
        for dirpath, _, filenames in os.walk(self.srcdir):
            if(dirpath.find('snippets') == -1):
                for filename in filenames:
                    if filename.endswith(".html"):
                        html_to_build.append((dirpath, filename))

        print(html_to_build)
        for path, filename in html_to_build:
            src_dir = path
            build_base = pathlib.Path(path)
            print(path)
            print("becomes")
            print(build_base.parts)
            build_base = pathlib.Path(*build_base.parts[1:])
            build_base = os.path.join(self.builddir, build_base)
            build_file = filename
            main_page = os.path.samefile(self.srcdir, path)
            print(src_dir)
            print(build_base)
            print(build_file)
            print(main_page)
            print()
            with PageBuilder(src_dir, build_base, build_file, self.file_hash, main_page) as pb:
                with open(os.path.join(path, filename)) as f:
                    data = f.read()
                pb.feed(data)

        # images and css (hashed files)
        print(self.hashed_files)
        os.makedirs(os.path.join(self.builddir, 'images'))
        for src in self.hashed_files:
            dst = self.hashed_files[src]
            dst = os.path.join(self.builddir, dst)
            print(f'{src}->{dst}')
            if not os.path.exists(dst):
                shutil.copyfile(src, dst)

        # delete unhashed css file
        os.remove(os.path.join(self.builddir, 'css', 'main.css'))


if __name__ == '__main__':
    sb = SiteBuilder('src', 'build')
    sb.build()