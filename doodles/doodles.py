#!/usr/bin/python3
# coding: utf-8

from collections import defaultdict
import os
import pathlib
from anytree import Node, RenderTree
from anytree.resolver import Resolver
import re
import requests
from typing import Set, Dict
import time

pagesdir = os.path.join(os.getcwd(), 'pages')
media_ondisk = set()
with open('medialist.txt', 'r') as f:
    lines = f.read().split("\n")
    for line in lines:
        if "." in line:
            media_ondisk.add(line[6:].lower())


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
            links.append((link,src))
        return links
        
    def getmedia(self):
        return re_embeddedmedia.findall(self.src)



def is_template(filename):
    return (file.startswith('fr_') or file.startswith('f_') or file.startswith('_') or file.startswith('n_'))


# REGEX EXPRESSIONS
# matches any links, except signatures
re_link = re.compile(r'\[\[(?!.*\@ka-raceing\.de.*)(.*?)\]\]')
# matches any embedded media, complete link with sizes and title
# re_embeddedmedia=re.compile(r'\{\{(.*?)\}\}')
# matches any embedded media, only filename
re_embeddedmedia = re.compile(r'\{\{(.*?)[\||\?|}].*?\}\}')

pages = {}

rootns = Namespace(name = 'pages', parent=None)
for root, dirs, files in os.walk(pagesdir):
    relpath = os.path.relpath(root, pagesdir)

    for file in files:
        if not is_template(file):
            pagename = os.path.splitext(file)[0].strip()
            #print("{}/{}".format(relpath, pagename))
            with open(os.path.join(root, file), encoding=('utf-8')) as f:
                pagesrc = f.read()
                thispage = Wikipage(name=pagename, src=pagesrc,
                                    populate_immediately=True)
                if relpath == ".":
                    pages[pagename] = thispage
                else:
                    pages[relpath + "/" + pagename] = thispage

"""
Links
========
https://www.dokuwiki.org/namespaces

ToFix
=====
"firmenname":doku
:/namespace:page
somelink:to:page]
"""
#
##links_to = defaultdict(list)
#
#links = []
#external_links = []
#section_links = []
#ftp_links = []
#
#for p in pages.keys():
#    page_links = [link for link, name in pages[p].links]
#
#    # convert external internal links to internal
#    page_links = [link.replace("https://wiki.ka-raceing.de/", "")
#                  for link in page_links]
#
#    for link in page_links:
#
#        # add external links to external_links list
#        if "https://" in link or "http://" in link \
#                or "www." in link or "@" in link:
#            external_links.append(link)
#            continue
#        # add section links to section_links list
#        elif link.startswith("#"):
#            section_links.append(link)
#            continue
#        elif "ftp://" in link:
#            ftp_links.append(link)
#            continue
#        # process internal links
#        else:
#            ################################################
#            ## changes that dokuwiki makes from link to page
#            ################################################
#            link = link.lower()
#            link = ":".join([piece.strip() for piece in link.split(":")]) 
#            link = link.replace("ä", "ae")
#            link = link.replace("ö", "oe")
#            link = link.replace("ü", "ue")
#            link = link.replace("ß", "ss")
#            link = link.replace("&", "_")
#            if not link.startswith("/"):
#                link = link.replace("/", "_")
#            link = link.replace("\"","")
#            link = link.replace("+", "_")
#            link = link.replace("'", "_")
#            link = link.replace(" ","_")
#            link = link.replace("__","_")
#            link = link.replace("___","_")
#            if link.endswith(".") or link.endswith("]"): 
#                link = link[:-1]
#
#            #################################
#            ## Handle relative/absolute links
#            ###############################
#            # get link type
#            if ".." in link:
#                print(str(link) + "auf " + ":".join(p.split("/")))
#            if link.startswith("/"):
#                typ = "abs"
#            if link.startswith("."):
#                typ = "rel"
#            else:
#                if link.startswith(":"):
#                    typ = "abs"
#                else:
#                    if ":" in link:
#                        typ = "abs"
#                    else:
#                        typ = "rel"
#            # add full path to relativ links
#            if typ == "rel":
#                abspath = ":".join(p.split("/")[:-1])
#                if link.startswith("."):
#                    link = link[1:] 
#                if link.startswith(":"):
#                    link = abspath + link 
#                else:
#                    link = abspath + ":" + link 
#            if typ == "abs":
#                if link.startswith("/"):
#                    link = link[1:]
#            # add : at start of link
#            if not link.startswith(":"):
#                link = ":" + link
#            # add start if links ends with :
#            if link.endswith(":"):
#                link = link + "start"
#
#            links.append(link.strip())
#
#print("=======")
#from collections import Counter
#count = Counter(links)
#print("Max linked page: {}".format(count.most_common()[0]))
#links = list(set(links))
#page_names = [":" + p.replace("/",":") for p in pages.keys()]
#
#orphans = set(page_names) - set(links)
#print("Orphans: {} (laut Wiki 1792)".format(len(orphans)))
#
#wanted = set(links) - set(page_names)
#print("Wanted: {} (laut Wiki 16952)".format(len(wanted)))
#
#print("Valid: {} (laut Wiki 26762)".format("?"))
#
#"""
#Open in webbroser
#================
#import webbrowser
#wopen = webbrowser.open
#wopen('https://wiki.ka-raceing.de')
#wopen('https://wiki.ka-raceing.de/{}?do=backlink'.format(orphans[0]))
#"""
#
#def test_orphans(orphans: Set, time_between = 0.25) -> Dict:
#    confirmed_orphans = set()
#    not_orphans = set()
#
#    user = "testuser"
#    pw = input("PW for {}:".format(user))
#
#    loginurl = "https://wiki.ka-raceing.de/start?do=login"
#    payload = {
#        'u': user,
#        'p': pw
#    }
#
#    checked_orphans = set()
#    with open("orphans.txt", "r") as f:
#        for l in f.read().strip().split("\n"):
#            checked_orphans.add(l)
#
#    with requests.Session() as s:
#        p = s.post(loginurl, data=payload)
#
#        if "Benutzername oder Passwort sind falsch." in p.text:
#            print("Benutzername oder Passwort sind falsch.")
#            return
#
#        total = len(orphans)
#        for n,orphan_candidate in enumerate(orphans):
#            
#            if orphan_candidate in checked_orphans:
#                 print("Already confirmed {}/{}: {}".format(n, total, orphan_candidate))
#                 confirmed_orphans.add(orphan_candidate)
#            else:
#                print("Testing {}/{}: {}".format(n, total, orphan_candidate))
#                req = s.get('https://wiki.ka-raceing.de/{}?do=backlink'.format(
#                    orphan_candidate))
#
#                if "Nichts gefunden" in req.text:
#                    confirmed_orphans.add(orphan_candidate)
#                    print("orphan")
#                elif "Zugang verweigert" in req.text:
#                    print("Zugang verweigert!")
#                else:
#                    not_orphans.add(orphan_candidate)
#                    with open("sources.txt", 'a') as f2:
#                        f2.write(orphan_candidate)
#                        f2.write(req.text)
#                        f2.write("")
#                    print("not an orphan")
#                
#                time.sleep(time_between)
#
#    return confirmed_orphans, not_orphans
#
#confirmed, wrong = test_orphans(orphans)
#
#with open("wrong_orphans.txt", 'w') as f: 
#    for o in wrong: 
#      f.write("{}\n".format(o)) 
#
#with open("orphans.txt", 'w') as f: 
#    for o in confirmed: 
#        f.write("{}\n".format(o)) 
#