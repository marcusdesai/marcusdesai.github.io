ARCHIVES_SAVE_AS = ""
ARTICLE_SAVE_AS = "{date:%Y}/{date:%b}/{slug}.html"
ARTICLE_URL = "{date:%Y}/{date:%b}/{slug}"
AUTHOR = "Marcus Desai"
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None
AUTHOR_SAVE_AS = ""
AUTHORS_SAVE_AS = ""

CATEGORY_FEED_ATOM = None
CATEGORY_SAVE_AS = ""
CATEGORIES_SAVE_AS = ""

DEFAULT_METADATA = {
    'status': 'draft',
}
DEFAULT_LANG = "en"
DEFAULT_PAGINATION = False

EXTRA_PATH_METADATA = {
    "images/favicon.ico": {"path": "favicon.ico"},
    "images/favicon-16x16.png": {"path": "favicon-16x16.png"},
    "images/favicon-32x32.png": {"path": "favicon-32x32.png"},
}

FEED_ALL_ATOM = "feeds/all.atom.xml"
FEED_ALL_RSS = "feeds/all.rss.xml"

MARKDOWN = {
    "extension_configs": {
        "markdown.extensions.codehilite": {"css_class": "highlight"},
        "markdown.extensions.extra": {},
        "markdown.extensions.meta": {},
        'markdown.extensions.toc': {},
    },
    "output_format": "html5",
}

PATH = "content"

SITEMAP = {
    "format": "xml",
    "priorities": {
        "articles": 0.5,
        "indexes": 0.5,
        "pages": 0.5,
    },
    "changefreqs": {
        "articles": "monthly",
        "indexes": "daily",
        "pages": "monthly",
    }
}
SITENAME = "MRCSD Blog"
SITEURL = "http://localhost:8000"
STATIC_PATHS = ["images"]

TAG_SAVE_AS = ""
TAGS_SAVE_AS = ""
TEMPLATE_PAGES = {
    "robots.txt": "robots.txt",
}
THEME = "themes/simple"
TIMEZONE = "Europe/London"
TRANSLATION_FEED_ATOM = None
