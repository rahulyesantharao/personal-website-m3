# TODO:
#  - Cache busting for css, html
#  - 
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

class PageBuilder(HTMLParser):
    def __init__(self, src_dir, build_dir, build_file, img_hash, main_page):
        super().__init__(convert_charrefs=True)
        self.srcdir = src_dir
        self.imghash = img_hash
        self.mainpg = main_page
        self.ofilepath = os.path.join(build_dir, build_file)
        self.ofile = None
    
    def __enter__(self):
        if not os.path.exists(os.path.dirname(self.ofilepath)):
            os.makedirs(os.path.dirname(self.ofilepath)) # let errors raise
        self.ofile = open(self.ofilepath, 'w+')
        return self
    
    def __exit__(self, *args):
        self.ofile.close()


    # utility
    @staticmethod
    def _build_attrs(attrs_list):
        if(not attrs_list): # empty list
            return ""
        
        attrs = map(lambda a: a[0] if a[1] is None else f'{a[0]}="{a[1]}"', attrs_list)
        return " " + functools.reduce(lambda a,b: f'{a} {b}', attrs)
    
    # default handlers: in -> out
    def handle_endtag(self, tag):
        self.ofile.write(f'</{tag}>')
    
    def handle_data(self, data):
        self.ofile.write(data)

    def handle_decl(self, decl):
        self.ofile.write(f'<!{decl}>')

    # hash css files
    def handle_starttag(self, tag, attrs):
        if tag == 'link':
            csspath = list(filter(lambda x: x[0] == 'href', attrs))[0][1] # extract path to css file
            csspath = os.path.normpath(csspath)
            csspath = os.path.join(os.path.dirname(self.ofilepath), csspath)
            assert os.path.exists(csspath) # make sure image exists
            newpath = self.imghash(csspath, 'css')
            if not self.mainpg:
                newpath = os.path.join('..', newpath)
            attrs = list(map(lambda x: (x[0], newpath) if x[0] == 'href' else x, attrs))
        self.ofile.write(f'<{tag}{PageBuilder._build_attrs(attrs)}>')

    # Markdown handler
    def handle_startendtag(self, tag, attrs):
        if tag == 'Markdown':
            pass
        elif tag == 'img':
            imgpath = list(filter(lambda x: x[0] == 'src', attrs))[0][1] # extract path to image
            imgpath = os.path.normpath(imgpath)
            imgpath = os.path.join(self.srcdir, imgpath)
            assert os.path.exists(imgpath) # make sure image exists
            newpath = self.imghash(imgpath, 'images')
            if not self.mainpg:
                newpath = os.path.join('..', newpath)
            attrs = list(map(lambda x: (x[0], newpath) if x[0] == 'src' else x, attrs))
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
            self.hashed_files[filepath] = os.path.join(destdir, newname)
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