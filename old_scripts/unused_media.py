#!/usr/bin/env python
# coding: utf-8

# In[1]:


# -*- coding: utf-8 -*-
from anytree import PreOrderIter
import os
import pathlib
from anytree import Node, RenderTree
from anytree.resolver import Resolver
import re


# ![](img_9561_robert_confused.jpg)

# Import data

# In[52]:


pagesdir = os.path.join(os.getcwd(), 'pages')
media_ondisk = set()
with open('medialist.txt', 'r') as f:
    lines = f.read().split("\n")
    for line in lines:
        if "." in line:
            media_ondisk.add(line[6:].lower())


# In[40]:


def is_template(filename):
    return (file.startswith('fr_') or file.startswith('f_') or file.startswith('_') or file.startswith('n_'))


# Any directories (namespaces) that do not contain child-namespaces or pages?

# In[93]:


count = 0
for root, dirs, files in os.walk(pagesdir):
    count += len(files)
print("{} pages".format(count))

count_empty = 0
for root, dirs, files in os.walk(pagesdir):
    if len(files) == 0:
        count_empty += 1
        print(root)
print("{} empty namespaces".format(count_empty))


# Regexes for links and embedded media

# In[48]:


# REGEX EXPRESSIONS
# matches any links, except signatures
re_link = re.compile(r'\[\[(?!.*\@ka-raceing\.de.*)(.*?)\]\]')
# matches any embedded media, complete link with sizes and title
# re_embeddedmedia=re.compile(r'\{\{(.*?)\}\}')
# matches any embedded media, only filename
re_embeddedmedia = re.compile(r'\{\{(.*?)[\||\?|}].*?\}\}')


# Classes

# In[83]:


class Namespace(Node):
    """
    A namespace has a name and contains pages
    """

    def __init__(self, name, parent=None, pages=[]):
        super().__init__(name, parent)
        self.pages = pages

    def __repr__(self):
        return '<ns> {}'.format(self.name)


class Wikipage:
    """
    A wikipage has a name and source code. 
    It can also generate a list of links and media from the source.
    """

    def __init__(self, name, src, populate_immediately=False):
        self.name = name
        self.src = src
        if populate_immediately:
            self.links = set(self.getlinks())
            self.media = set(self.getmedia())
        else:
            self.links = set()
            self.media = set()

    def __repr__(self):
        return('{} [{} links, {} media]'.format(self.name,
                                                len(self.links),
                                                len(self.media)))

    def getlinks(self):
        srclinks = re_link.findall(self.src)
        links = []

        for match in srclinks:
            try:
                link, src = match.split('|')
            except ValueError:
                link = match
                src = ''
            links.append((link, src))
        return links

    def getmedia(self):
        return re_embeddedmedia.findall(self.src)


# Build tree

# In[84]:


r = Resolver('name')

rootns = Namespace(name='pages', parent=None)
for root, dirs, files in os.walk(pagesdir):
    relpath = os.path.relpath(root, pagesdir)

    if relpath == '.':
        basens = rootns
    else:
        basens = r.get(rootns, relpath)

    for directory in dirs:
        ns = Namespace(name=directory, parent=basens)

    basens.pages = []
    for file in files:
        if not is_template(file):
            with open(os.path.join(root, file), encoding=('utf-8')) as f:
                pagesrc = f.read()
                pagename = os.path.splitext(file)[0]
                thispage = Wikipage(name=pagename, src=pagesrc,
                                    populate_immediately=True)
                basens.pages.append(thispage)


# In[96]:


PRINT = False
if PRINT:
    for pre, fill, node in RenderTree(rootns):
        print("{}{}".format(pre, node.name.upper()))
        if len(node.pages) == 1:
            print("{} * {}".format(pre, node.pages[0]))
        if len(node.pages) > 1:
            for page in node.pages[1:]:
                print("{} * {}".format(fill, page))


# Create media lists: internally linked media, externally linked media, and pages which use the gallery plugin
#
# Dokuwiki does not care about capitalization, and it also replaces any umlauts or ß with the anglisized versions. So we will do that as well in the media list.
# Furthermore, __ in any links is replaced with _ , as in infovault/bilder/2014/sponsoren/etas/fsg/fotowettbewerb/etas__0001.jpg

# In[97]:


allmedia = set()
externalmedia = set()
pages_with_galleries = set()

for namespace in PreOrderIter(rootns):
    for page in namespace.pages:
        for media in page.media:
            media = media.strip()
            if "gallery>" in media:
                pages_with_galleries.add((namespace.path, page))
            elif 'http' in media or 'www.' in media:
                if media.startswith('https://wiki.ka-raceing.de/_media/'):
                    allmedia.add(media[34:].replace(":", "/"))
                else:
                    externalmedia.add(media)
            else:
                media = media.lower()
                media = media.replace("ä", "ae")
                media = media.replace("ö", "oe")
                media = media.replace("ü", "ue")
                media = media.replace("ß", "ss")
                media.replace("__", "_")
                if media[0] == ":":
                    allmedia.add(media[1:].replace(":", "/"))
                else:
                    allmedia.add(media.replace(":", "/"))


# Pages which use the gallery plugin

# In[98]:


pages_with_galleries = [
    "/".join([n.name for n in p[0][1:]]) + "/" + p[1].name for p in pages_with_galleries]
for p in sorted(pages_with_galleries):
    print(p)


# Media that is linked, but was not found on disk

# In[99]:


media_notondisk = allmedia - media_ondisk
print(len(media_notondisk))
for l in sorted(media_notondisk):
    # if "eigen__steuer" in l:
    print(l)


# Media that is on disk, but not linked

# In[100]:


media_nolinked = media_ondisk - allmedia

for l in sorted(media_nolinked):
    found = False
    for p in pages_with_galleries:
        if l[20:] in p:
            found = True
    if found:
        media_nolinked.remove(l)
    else:
        print(l)
print(len(media_nolinked))


# media which could be deleted. Check one last time if they are linked somewhere

# In[101]:


to_delete = [
    "infovault/bilder/2016/fsg",
    "infovault/bilder/2016/fsa",
    "infovault/bilder/2016/fss",
    "infovault/bilder/2016/fsuk",
    "infovault/bilder/2016/rolloutallg",
    "infovault/bilder/2016/sonstiges",
    "infovault/bilder/2016/sponsorentag",
    "infovault/bilder/2016/fsa",
    "infovault/bilder/2016/fsa",
]
for td in to_delete:
    for n in sorted(allmedia):
        if td in n:
            print(n)


# In[ ]:
