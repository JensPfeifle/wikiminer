#!/usr/bin/python3
# coding: utf-8

import os
import networkx as nx
from anytree import PreOrderIter
from anytree.resolver import Resolver
from anytree import RenderTree
from typing import Dict, List, Tuple

from classes import Namespace, Wikipage

DATADIR = os.path.join(os.getcwd(), 'data')
PAGESDIR = os.path.join(DATADIR, 'pages')


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
            relpath = ''
        else:
            basens = r.get(rootns, relpath)

        for directory in dirs:
            Namespace(name=directory, parent=basens)

        basens.pages = []
        for file in files:
            page_name = os.path.splitext(file)[0]
            page_file_path = os.path.join(relpath, file)
            if exclude_templates and is_template(page_name):
                print("{} is template".format(page_name))
            else:
                basens.pages.append((page_name, page_file_path))

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


def build_page_graph(tree_rootns: Namespace) -> nx.DiGraph:
    """
    Walk the structure and build a directed graph of the pages of the wiki
    Pages are represented in the graph by their full, absolute wikipath
    e.g. :start or :infovault:bilder
    Directed edges represent links from/to pages.   
    """

    pagegraph = nx.DiGraph()

    for namespace in PreOrderIter(tree_rootns):
        for page_name, page_file_path in namespace.pages:
            page = Wikipage(page_name, page_file_path,
                            populate_immediately=True)
            pagegraph.add_node(page.path, object=page)
            # for link in page.internal_links:
            #    pagegraph.add_edge(page.path, link)
            # alternative?
            pagegraph.add_edges_from([[page.path, link]
                                      for link in page.internal_links])

    return pagegraph


def rank_pagerank(pagegraph: nx.DiGraph) -> List:
    """
    Returns a list of all wikipages, ranked using the pagerank
    algorithm, from most important to least important.
    """
    prdict = nx.algorithms.pagerank(pagegraph)
    return sorted(prdict, key=prdict.get, reverse=True)


def rank_hits(pagegraph: nx.DiGraph) -> Tuple[List, List]:
    """
    Returns a tuple of hubs and authorities according to the HITS algorithm
    from most important to least important.
    """
    hdict, authdict = nx.algorithms.hits(pagegraph)
    hubs = sorted(hdict, key=hdict.get, reverse=True)
    authorities = sorted(authdict, key=authdict.get, reverse=True)
    return (hubs, authorities)


if __name__ == "__main__":
    rootns = build_namespace_tree(PAGESDIR)

    G = build_page_graph(rootns)
    pr = rank_pagerank(G)
    h, a = rank_hits(G)

    # get links to page with
    print("Links to :start ->")
    print([*G.predecessors(":start")])
    # get links from page with
    print("Links from :start ->")
    print([*G.successors(":start")])
