AUTHOR = "Marcus Desai"
SITENAME = "MRCSD Blog"
SITEURL = "http://localhost:8000"

PATH = "content"
ARTICLE_SAVE_AS = "{date:%Y}/{date:%b}/{slug}.html"
ARTICLE_URL = "{date:%Y}/{date:%b}/{slug}"

TIMEZONE = "Europe/London"

AUTHOR_SAVE_AS = ""
CATEGORY_SAVE_AS = ""
TAG_SAVE_AS = ""
ARCHIVES_SAVE_AS = ""
AUTHORS_SAVE_AS = ""
CATEGORIES_SAVE_AS = ""
TAGS_SAVE_AS = ""

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

THEME = "themes/simple"

DEFAULT_METADATA = {
    'status': 'draft',
}
DEFAULT_LANG = "en"
DEFAULT_PAGINATION = False

MARKDOWN = {
    "extension_configs": {
        "markdown.extensions.codehilite": {"css_class": "highlight"},
        "markdown.extensions.extra": {},
        "markdown.extensions.meta": {},
    },
    "output_format": "html5",
}