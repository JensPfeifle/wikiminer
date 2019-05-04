import os
import pathlib
import re

# the directory of mediafiles you are considering deleting
# do not add a leading ':' !
MATCH = 'infovault:bilder'

pagesdir = os.path.join(os.getcwd(), 'data/pages')
re_embeddedmedia = re.compile(r'\{\{(.*?)[\||\?|}].*?\}\}')

def is_template(filename):
    """ matches our custom template files """
    return (filename.startswith('fr_') or filename.startswith('f_') \
        or filename.startswith('_') or filename.startswith('n_'))

def get_mediafiles():
    """ Reads in a TXT representation (directory listing)
    of media files on the webserver filesystem
    To create the txt file:
    cd to /dokuwiki/data/media
    find  -not -type d | cut -c 2- | tr '/' ':' > /tmp/mediafiles.txt
    """
    mediafiles = set()
    with open('data/mediafiles.txt', 'r') as f:
        lines = f.read().split("\n")
        for line in lines:
            mediafiles.add(line[1:].lower())
    return mediafiles

def medialink_cleanup(inp):
    """ Cleans up dokuwiki media links """
    media = inp.strip()
    if "gallery>" in media:
        print("Gallery detected!: {}".format(media))
    elif 'http' in media or 'www.' in media:
        if media.startswith('https://wiki.ka-raceing.de/_media/'):
            return media[34:].replace(":", "/")
        else:
            print("External media detected!: {}".format(media))
    else:
        media = media.lower()
        media = media.replace("ä", "ae")
        media = media.replace("ö", "oe")
        media = media.replace("ü", "ue")
        media = media.replace("ß", "ss")
        media.replace("__", "_")
        media = media.strip()
        if media.startswith(":"):
            return media[1:]#.replace(":", "/")
        else:
            return media#.replace(":", "/"))

def get_pages():
    """ Returns a list of pages in the format
              (pagename, pagepath, pagemedia)
    """
    pages = []
    for root, dirs, files in os.walk(pagesdir):
        relpath = os.path.relpath(root, pagesdir)
        for file_ in files:
            if not is_template(file_):
                with open(os.path.join(root, file_), encoding=('utf-8')) as f:
                    pagename = os.path.splitext(file_)[0]
                    pagesrc = f.read()
                    pagepath = ':' + os.path.join(relpath, file_).replace('/',':')
                    pagemedia = set()
                    for media in re_embeddedmedia.findall(pagesrc):
                            pagemedia.add(medialink_cleanup(media))
                    pages.append((pagename, pagepath, pagemedia))
    return pages

def get_linked_media():
    """ Returns a set of all linked media, over all pages """
    linkedmedia = set()
    for root, dirs, files in os.walk(pagesdir):
        relpath = os.path.relpath(root, pagesdir)
        for file_ in files:
            if not is_template(file_):
                with open(os.path.join(root, file_), encoding=('utf-8')) as f:
                    pagesrc = f.read()
                    pagemedia = set()
                    for media in re_embeddedmedia.findall(pagesrc):
                            pagemedia.add(medialink_cleanup(media))
                    linkedmedia.update(pagemedia)
    return linkedmedia

def pages_containing(link, page_list):
    """
    Returns a list of pages containing the given link
    link: 
        a dokuwiki media path
        e.g. :elektronik:kit10:entwicklung:lenkradkonzept01.jpg
    page list:
        [(pagename, pagepath, pagemedia),...]
    """
    matched = []
    for page in page_list:
        name, path, media = page
        if link in media:
            matched.append(path) # only page path for now
    return matched

def pprint(myset):
    for s in myset:
        print(s)

if __name__ == "__main__":
    mediafiles = get_mediafiles()
    pages = get_pages()

    # just in case..
    if MATCH.startswith(':'):
        MATCH = MATCH[1:]

    # make a set of mediafiles matching
    todelete = set()
    for m in mediafiles:
        if m.startswith(MATCH):
            todelete.add(m)
    # did we miss any?
    for m in mediafiles:
        if MATCH in m and m not in todelete:
            print(m)

    results = {}
    for candidate in todelete:
        references = pages_containing(candidate, pages)
        if len(references) > 0:
            print()
            print(candidate)
            print(references)
            print()
            results[candidate] = references

    # write referenced mediafiles to dont-delete.txt
    with open('dont-delete.txt', 'w') as f:
        for k in results.keys():
            line = './' + k.replace(':', '/')
            f.write(line + '\n')

        

