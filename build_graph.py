#!/usr/bin/python3
# coding: utf-8

import os
import re
import networkx as nx
from anytree import Node, RenderTree
from anytree import PreOrderIter
from anytree.resolver import Resolver
from typing import Set, Tuple

# REGEX EXPRESSIONS
# matches any links, except signatures
RE_LINK = re.compile(r'\[\[(?!.*\@ka-raceing\.de.*)(.*?)\]\]')
# matches any embedded media, complete link with sizes and title
# RE_EMBEDDEDMEDIA=re.compile(r'\{\{(.*?)\}\}')
# matches any embedded media, only filename
RE_EMBEDDEDMEDIA = re.compile(r'\{\{(.*?)[\||\?|}].*?\}\}')

DATADIR = os.path.join(os.getcwd(), 'data')
PAGESDIR = os.path.join(DATADIR, 'pages')


class Namespace(Node):
    """
    A namespace represents a directory or folder.
    It has a name and contains pages (and other namespaces).
    This class extends anytree.Node to add a list of pages.
    """

    def __init__(self, name, parent=None, pages=set()):
        super().__init__(name, parent)
        self.pages = pages

    def __repr__(self):
        return "Namepace('{}')".format(self.name)


class Wikipage:
    """
    A page is the core feature of a wiki, and is defined by its source.
    The first header is considered as the title of the page.
    It can include links to other pages or external sizes, as well
    as embedded media.
    A page should have at least one link pointing to it, otherwise
    it is considered an "orphan".
    """

    def __init__(self, name, path,
                 encoding="ISO-8859-1",
                 populate_immediately=False):
        self.name = name
        self.path = path
        self.encoding = encoding

        if populate_immediately:
            self.populate()
        else:
            self.src = None
            self.links = set()
            self.media = set()

    def read_src(self) -> str:
        with open(os.path.join(PAGESDIR, self.path), 'r',
                  encoding=self.encoding) as f:
            source = f.read()
        return source

    def populate(self) -> None:
        self.src = self.read_src()
        self.links = __class__.get_links(self.src)
        self.media = __class__.get_media(self.src)

    def __repr__(self):
        if self.src:
            return('{} [{} links, {} media]'.format(self.name,
                                                    len(self.links),
                                                    len(self.media)))
        else:
            return('{} [unpopulated]'.format(self.name))

    @staticmethod
    def get_links(source: str) -> Set[Tuple[str, str]]:
        """
        Parse links from source
        Returns set of tuples (link, title)
         """
        srclinks = RE_LINK.findall(source)
        links = set()

        for match in srclinks:
            try:
                link, title = match.split('|')
            except ValueError:
                link = match
                title = ''
            links.add((link, title))
        return links

    @staticmethod
    def get_media(source: str) -> Set[str]:
        """
        Parse embedded media from source
        Returns set of str: {'mediafile'
         """
        return set(RE_EMBEDDEDMEDIA.findall(source))


def is_template(filename: str) -> bool:
    return (filename.startswith('fr_') or filename.startswith('f_') or
            filename.startswith('_') or filename.startswith('n_'))


def build_namespace_tree(pagesdir: str, exclude_templates: bool = True) -> Namespace:
    """
    Walk the pagesdir and build a tree representing the structures of the wiki.
    The nodes are Namepspace objects, which contain a list of pages.
    Returns the root node of the tree, i.e. the root namespace.
    """
    r = Resolver('name')
    rootns = Namespace(name='pages', parent=None)

    for root, dirs, files in os.walk(pagesdir):
        relpath = os.path.relpath(root, pagesdir)

        if relpath == '.':
            basens = rootns
        else:
            basens = r.get(rootns, relpath)

        for directory in dirs:
            Namespace(name=directory, parent=basens)

        basens.pages = []
        for file in files:
            page_name = os.path.splitext(file)[0]
            page_path = os.path.join(relpath, file)
            if exclude_templates and is_template(page_name):
                print("{} is template".format(page_name))
            else:
                basens.pages.append((page_name, page_path))

    return rootns


def print_structure(treeroot):
    """
    Print the wiki structure using anytree.RenderTree.
    Must be passed the root of the tree.
    """
    assert type(rootns) is Namespace, "Tree nodes must be of type Namespace"
    for pre, fill, node in RenderTree(treeroot):
        print("{}{}".format(pre, node.name.upper()))
        if len(node.pages) == 1:
            print("{} {}".format(pre, node.pages[0]))
        if len(node.pages) > 1:
            for page in node.pages[1:]:
                print("{} {}".format(fill, page))


def build_page_graph(tree_rootns: Namespace) -> nx.Graph:
    """
    Walk the structure and build a graph representing the pages of the wiki
    and the links between them
    """

    pagegraph = nx.Graph()

    for namespace in PreOrderIter(tree_rootns):
        for page_name, page_path in namespace.pages:
            print(page_path)
            pagegraph.add_node(
                Wikipage(page_name, page_path, populate_immediately=True))

    """
    for root, dirs, files in os.walk(pagesdir):
        ns_path = os.path.relpath(root, pagesdir)
        parent_path, ns_name = os.path.split(ns_path)
        print("===")
        print(ns_path)
        print("---")
        print("namespace: " + str(ns_name))
        print("parent: " + str(parent_path))

        ns_pages = set()
        for file in files:
            # if not is_template(file):
            pagename = os.path.splitext(file)[0].strip()
            ns_pages.add(pagename)
            if ns_path == ".":
                pagepath = pagename
            else:
                pagepath = ns_path + "/" + pagename
            ns_pages.add((pagename, pagepath))
        print("pages: " + str(ns_pages))

        if ns_path == ".":
            namespaces.add_node("", name="pages", pages=ns_pages)
        else:
            namespaces.add_node(ns_path, name=ns_name, pages=ns_pages)
            namespaces.add_edge(parent_path, ns_path)
        """

    return pagegraph


if __name__ == "__main__":
    rootns = build_namespace_tree(PAGESDIR)

    G = build_page_graph(rootns)
