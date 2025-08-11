from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.files import Files
from mkdocs.structure.pages import Page


def on_page_markdown(markdown: str, page: Page, config: MkDocsConfig, files: Files):

    # print(f"on_page_markdown: {page}")
    return markdown

def on_page_content(html: str, page: Page, config: MkDocsConfig, files: Files):

    # README.md contains external URLs to this gh-pages. It's needed for publishing to pypi.
    # mkdocs includes the same README.md for convenience. Here we rewrite those external URLs
    # as mkdocs needs relative links to work correctly.
    return html.replace('https://jwnmulder.github.io/dbus2mqtt/', '')
