"""Left-hand chapter/bonus navigation sidebar, shared by every game's build
script so the markup lives in one place instead of being hand-copied per game.

    from sidebar import render_sidebar
    render_sidebar(
        chapters=[("ch01.html", "Chapter 1"), ("ch02.html", "Chapter 2"), ...],
        bonus=[("shop.html", "Shops"), ...],          # omit/empty if a game has none
        current_href="ch02.html",                      # this page's own link, for highlighting
        extra=("../supports/index.html", "Support Conversations"),  # FE6 only
    )

Every href is passed in already resolved relative to the page being built -
this module just renders markup, it knows nothing about any game's folder
layout.
"""
import html


def esc(s):
    return html.escape(s, quote=True)


def render_sidebar(chapters, current_href, bonus=None, extra=None, extra_current=False):
    def li(href, label):
        cur = ' class="current"' if href == current_href else ""
        return f'<li{cur}><a href="{esc(href)}">{esc(label)}</a></li>'

    parts = ['<nav class="side-nav" aria-label="Chapters">']
    if chapters:
        parts.append('<h2>Chapters</h2><ol>' + "".join(li(h, l) for h, l in chapters) + "</ol>")
    if bonus:
        parts.append('<h2>Bonus</h2><ol>' + "".join(li(h, l) for h, l in bonus) + "</ol>")
    if extra:
        href, label = extra
        cls = "side-extra current" if extra_current else "side-extra"
        parts.append(f'<a class="{cls}" href="{esc(href)}">{esc(label)} →</a>')
    parts.append("</nav>")
    return "".join(parts)
