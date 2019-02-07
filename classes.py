import os
import re
from typing import Set, Tuple
from anytree import Node

# TODO: this is defined in more than one place
DATADIR = os.path.join(os.getcwd(), 'data')
PAGESDIR = os.path.join(DATADIR, 'pages')

# REGEX
# matches any links, except signatures
RE_LINK = re.compile(r'\[\[(?!.*\@ka-raceing\.de.*)(.*?)\]\]')
# matches any embedded media, complete link with sizes and title
# RE_EMBEDDEDMEDIA=re.compile(r'\{\{(.*?)\}\}')
# matches any embedded media, only filename
RE_EMBEDDEDMEDIA = re.compile(r'\{\{(.*?)[\||\?|}].*?\}\}')


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

    def __init__(self, name, file_path,
                 encoding="UTF-8",
                 # encoding="ISO-8859-1",
                 # encoding="1252",
                 populate_immediately=False):
        self.name = name
        self.file_path = file_path
        self.encoding = encoding

        if populate_immediately:
            self.populate()
        else:
            self.src = None
            self.links = set()
            self.media = set()

    def read_src(self) -> str:
        with open(os.path.join(PAGESDIR, self.file_path), 'r',
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

    @property
    def namespace(self) -> str:
        namespace, page = os.path.split(self.file_path)
        return ":" + namespace.replace("/", ":")

    @property
    def path(self) -> str:
        pth, _ = os.path.splitext(self.file_path)
        return ":" + pth.replace("/", ":")

    @property
    def internal_links(self) -> Set:
        """
        Get all internal wikilinks as absolute
        paths from the root namespace
        """
        internal = set()
        for raw_link, _ in self.links:
            link, typ = __class__.parse_raw_link(raw_link)
            if typ == "relative":
                if ".." in link:
                    print("RELATIVE LINK WITH '..' : " + str(link))
                abs_link = self.namespace + ":".join(link.split(":")[1:])
                internal.add(abs_link)
            if typ == "absolute":
                internal.add(link)
        return internal

    @property
    def external_links(self) -> Set:
        """
        Get all external wikilinks
        """
        external = set()
        for raw_link, _ in self.links:
            link, typ = __class__.parse_raw_link(raw_link)
            if typ == "external":
                external.add(link)
        return external

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

    @staticmethod
    def parse_raw_link(rawlink: str) -> str:
        """
        Parses raw links as described in https://www.dokuwiki.org/link,
        making any changes that dokuwiki makes from link to page,
        e.g. replace umlauts.
        Returns a tuple of (link_str, link_type)
        link_type is one of:
            * external  -> pointing to a site outside of the wiki
            * relative  -> internal wikilink, relativ to page
            * absolute  -> internal wikilink, absolute from root
            * section   -> link to a specific section of the page
            * interwiki -> link to another wiki, e.g. doku> or wpde>
        """
        # external links
        if "https://" in rawlink or "http://" in rawlink \
                or "www." in rawlink or "@" in rawlink:
            typ = "external"
        # section links
        elif rawlink.startswith("#"):
            typ = "section"
        elif ">" in rawlink:
            typ = "interwiki"
        else:
            typ = "internal"

        if typ == "external" and rawlink.startswith("https://wiki.ka-raceing.de/"):
            rawlink = rawlink.replace("https://wiki.ka-raceing.de/", ":")
            typ = "internal"

        link = rawlink

        if typ == "internal":
            # Process internal links
            link = link.lower()
            link = ":".join([piece.strip() for piece in link.split(":")])
            link = link.replace("ä", "ae")
            link = link.replace("ö", "oe")
            link = link.replace("ü", "ue")
            link = link.replace("ß", "ss")
            link = link.replace("\"", "")
            for s in ["&", "\"", "+", "'", " ", "__", "___"]:
                link = link.replace(s, "_")
            if not link.startswith("/"):
                link = link.replace("/", "_")
            if link.endswith(".") or link.endswith("]"):
                link = link[:-1]

            if "#" in link:
                if link.count("#") > 1:
                    print("MULTIPLE SECTION LINK: " + str(link))
                else:
                    link = link.split("#")[0]

            # Handle relative/absolute links according to
            # https://www.dokuwiki.org/namespaces
            typ = "relative"
            # if link.startswith("."):
            #    typ = "relative"
            if link.startswith("/"):
                typ = "absolute"
            if link.startswith(":"):
                typ = "absolute"
            if not link.startswith(":") and not link.startswith("."):
                if ":" in link:
                    typ = "absolute"

            if typ == "absolute":
                if link.startswith("/"):
                    link = link[1:]
                if not link.startswith(":"):
                    link = ":" + link

            if typ == "relative":
                if not link.startswith("."):
                    link = ".:" + link

            # links that end in ":" implicitly link to "start" page
            if link.endswith(":"):
                link = link + "start"

        assert not typ == "internal"
        return (link.strip(), typ)
