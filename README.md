# トラキア776 会話集

Static site with the full Japanese script of Fire Emblem: Thracia 776, one page per chapter.

- Open `public/index.html` in a browser. No server needed.
- Rebuild after any change: `python3 tools/build.py` (standard library only).

## Layout

- `source/` – the dialogue transcriptions the site is built from (Shift_JIS HTML saved from
  the [Pegasus Knight Master Bible 会話集](https://www.pegasusknight.com/mb/fe5/st_index.html)).
  All dialogue comes from these files; the transcriber's own commentary (†) is left out.
- `tools/build.py` – parser + page generator. Chapter titles are listed at the top.
- `public/` – everything the web server serves (set it as the web directory). `public/chapters/`, `public/index.html` – generated pages. Don't edit by hand; they are overwritten.
- `data/script.json` – the parsed script (scene → text window → lines), also generated.
- `public/css/style.css` – all styling.
- `public/img/placeholder.svg` – stand-in portrait.
- `public/img/portraits/` – put `<name>.png` here and rebuild; `README.txt` in that folder lists
  every file name the pages look for.

## Reading the pages

- Each bubble is one in-game text window, with the game's line breaks.
- Headings, trigger conditions and stage directions are English translations of the transcriber's labels (see `tools/en.py`); they are notes on when a
  conversation triggers; it is not game text. Speaker labels such as `兵士（アイヒマン顔）`
  are also the transcriber's.

## Portraits

`python3 tools/fetch_portraits.py` downloads the 48×64 portraits from the
[Fire Emblem Wiki](https://fireemblemwiki.org) into `public/img/portraits/`, saved under the
Japanese speaker name. The name mapping is at the top of that script. Unnamed townspeople
(`市民(男)` etc.) use a best-match villager face, not necessarily the one shown in each scene.

## Furigana, translations and vocabulary

- The header toggle shows readings above kanji (remembered per browser).
- Clicking a speech bubble highlights it and shows its English translation plus a vocabulary
  list (word, dictionary form, reading, meaning): in the right margin on wide screens, in a
  modal on phones. Click the bubble again, press Esc, or use × to close.

**Translations** live in `translations/<chapter>.txt`, one line per text window:
`<window number><TAB><English>`. Window numbers count the bubbles on a page from the top
(the `data-n` attribute in the HTML). They are unofficial translations written for this
site; edit the text freely and re-run `python3 tools/build.py`. The build prints how many
windows are translated and warns if a file has more lines than the page has windows.

**Readings and vocabulary** come from `tools/analyze.py`, which tokenizes every line and
looks each word up in [JMdict](https://www.edrdg.org/jmdict/j_jmdict.html) (CC BY-SA 4.0,
credited in the footer):

    .venv/bin/python tools/analyze.py   # needs fugashi + unidic-lite in .venv; downloads JMdict to .cache/
    python3 tools/build.py

It writes `data/tokens.json` and `data/glossary.json`; the build puts each chapter's
glossary and translations in `public/chapters/gloss/`. This part is machine output and is sometimes
wrong, mainly where the game spells a word in kana that has homophones. Corrections go in
the tables at the top of `tools/analyze.py`: `OVERRIDES` / `COMPOUNDS` (readings),
`GLOSS_FIXES` (meanings), `PROPER` (names and places). `build.py` itself needs no packages.

## Hand-written vocabulary and grammar notes (`study/`)

Per-bubble study notes written by hand, replacing the automatic dictionary list for the
chapters that have them (the build prints which ones do).

- `study/vocab.txt` – the one central word list: `key | reading | meaning`.
- `study/grammar.txt` – the one central grammar list: `id | pattern | explanation`.
- `study/<chapter>.txt` – one line per bubble: `window | words | grammar ids`.
  Words are comma-separated; write `surface>key` when the form in the bubble differs from
  the vocab key (`はかせろ>吐く`), or just `key` when it is the same. Bubbles with nothing
  worth noting are simply left out.

The build checks that every word is in the bubble's text and that every key and id exists,
and prints `STUDY:` lines for anything that doesn't. It also generates `public/grammar.html` and
`public/vocab.html` from the two central files. Chapters without a `study/<chapter>.txt` keep the
automatic dictionary vocabulary and say so in the panel.

Everyday words (見る, 行く, この, 私 …) are included too; only particles, auxiliary verbs,
name fragments and bare exclamations are left out. `tools/study_gaps.py` helps keep that
consistent: it lists content words a chapter's notes don't cover yet, and with `--apply`
adds the ones mapped in `study/accept.txt` (`tokenizer base form | vocab key`, `-` = never).
