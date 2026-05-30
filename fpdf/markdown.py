"""
Markdown Mixin.

The contents of this module are internal to fpdf2, and not part of the public API.
They may change at any time without prior warning or any deprecation period,
in non-backward-compatible ways.

Usage documentation at: <https://py-pdf.github.io/fpdf2/TextStyling.html#markdowntrue>
and <https://py-pdf.github.io/fpdf2/CombineWithMarkdown.html>
"""

from abc import ABC
from collections.abc import Iterator, Sequence
from dataclasses import asdict, dataclass
from functools import reduce
from operator import or_
import re
from typing import Final, Literal, TypeAlias, TYPE_CHECKING

from .drawing_primitives import Color, convert_to_device_color
from .enums import TextEmphasis
from .util import Number

if TYPE_CHECKING:
    from .line_break import Fragment, TextLine


MarkdownFragment: TypeAlias = tuple[str, TextEmphasis, str | None, Color | None]


@dataclass(kw_only=True, slots=True)
class MarkdownToken:
    """Markdown Token."""

    text: str
    emphasis: TextEmphasis
    link: str | None = None
    link_emphasis: TextEmphasis = TextEmphasis.NONE

    def __bool__(self) -> bool:
        return any(bool(a) for a in asdict(self).values())


def frag_emphasis(fragment: "Fragment") -> TextEmphasis:
    """
    Returns the fragment's text emphasis.
    """
    font_style = fragment.font_style
    if fragment.strikethrough:
        font_style += "S"
    if fragment.underline:
        font_style += "U"
    return TextEmphasis.coerce(font_style)


def frag_emphasis_len(
    fragments: Sequence["Fragment"],
    start: int,
    emph: TextEmphasis,
) -> int:
    """
    Find the last fragment index that has the given emphasis (without a gap),
    starting at index `start`.
    """
    for i in range(start, len(fragments)):
        if frag_emphasis(fragments[i]) & emph:
            continue
        return i
    return start


class MarkdownMixin(ABC):
    """Mix-in to be added to `fpdf.FPDF` in order to support markdown.

    Supported features:
    - Style markers:
      - Bold: `"**bold**"`
      - Italics: `"__italics__"`
      - Strikethrough: `"~~strikethorugh~~"`
      - Underline: `"--underline--"`
    - Links: `"[fpdf2](https://py-pdf.github.io/fpdf2)"`
    - Styled links: `"**[fpdf__2__](https://py-pdf.github.io/fpdf2)**"`
    - Escaping of markers and/or square brackets:
      - `"\\**"`
      - `"[\\[fpdf2\\]](https://py-pdf.github.io/fpdf2)"`

    Not closed markers will be handled as being implicitly escaped:
    `"**bold** **" == "**bold** \\**"`
    """

    # Markers
    MARKDOWN_BOLD_MARKER: Final[Literal["**"]] = "**"
    MARKDOWN_ITALICS_MARKER: Final[Literal["__"]] = "__"
    MARKDOWN_STRIKETHROUGH_MARKER: Final[Literal["~~"]] = "~~"
    MARKDOWN_UNDERLINE_MARKER: Final[Literal["--"]] = "--"

    # Escape
    MARKDOWN_ESCAPE_CHARACTER: Final[Literal["\\"]] = "\\"
    MARKDOWN_ESCAPABLES: Final[set[str]] = set(
        (MARKDOWN_ESCAPE_CHARACTER, "[", "]")
    )  # besides markers

    # Links
    MARKDOWN_LINK_COLOR: Number | Color | str | Sequence[Number] | None = None
    MARKDOWN_LINK_UNDERLINE: bool = True

    # Internals
    _EMPH_TO_MD_MARKER: Final[dict[TextEmphasis, str]] = {
        TextEmphasis.NONE: "",
        TextEmphasis.B: MARKDOWN_BOLD_MARKER,
        TextEmphasis.I: MARKDOWN_ITALICS_MARKER,
        TextEmphasis.U: MARKDOWN_UNDERLINE_MARKER,
        TextEmphasis.S: MARKDOWN_STRIKETHROUGH_MARKER,
    }
    _MD_MARKER_TO_EMPH: Final[dict[str, TextEmphasis]] = {
        v: k for k, v in _EMPH_TO_MD_MARKER.items()
    }
    _MD_MARKERS: Final[set[str]] = set(_MD_MARKER_TO_EMPH)

    # Patterns to escape markdown
    _MD_ESCAPE_PATTERN: re.Pattern[str] = re.compile(rf"({'|'.join(
            re.escape(m)
            for m in (*_MD_MARKER_TO_EMPH, MARKDOWN_ESCAPE_CHARACTER)
            if m
        ):s})")
    _MD_ESCAPE_LINK_TEXT_PATTERN: re.Pattern[str] = re.compile(rf"({'|'.join(
            re.escape(m)
            for m in (*_MD_MARKER_TO_EMPH, MARKDOWN_ESCAPE_CHARACTER, *MARKDOWN_ESCAPABLES)
            if m
        ):s})")

    # Pattern to find link text and destination
    _MD_LINK_PATTERN: re.Pattern[str] = re.compile(
        # opening square bracket
        rf"\["
        # link text (char not in "[]\n" or char in escaped square brackets)
        rf"((?:[^\[\]\n]|{2*MARKDOWN_ESCAPE_CHARACTER:s}[\[\]])*)"
        # closing unescaped square bracket
        rf"(?<!{2*MARKDOWN_ESCAPE_CHARACTER:s})\]"
        # link destination (char not in "()" or any whitespace)
        rf"\(([^()\s]*)\)"
    )

    @classmethod
    def _escape_markdown_chars(cls, text: str, *, in_link: bool = False) -> str:
        pat = cls._MD_ESCAPE_LINK_TEXT_PATTERN if in_link else cls._MD_ESCAPE_PATTERN
        return pat.sub(rf"{cls.MARKDOWN_ESCAPE_CHARACTER:s}\\1", text)

    def _join_markdown_text_lines(
        self,
        text_lines: list["TextLine"],
    ) -> list[str]:
        # NOTE:
        # Known limitations that make the markdown dry run-output differ from
        # the input, but do NOT change the appearance when finally being
        # printed:
        # - Order of markers is not kept: `"**__x__**" == "__**x**__"`
        # - Not closed markers are implicitly escaped and will be escaped
        #   explicitly: `"**x** **" == "**x** \\**"`
        # - Underline markers in or around links will not be kept if
        #   `MARKDOWN_LINK_UNDERLINE` is true:
        #   `"--[text](www.link.com)--" == "[text](www.link.com)"`

        output_lines: list[str] = []

        def flush_markers(
            fragments: Sequence["Fragment"],
            start: int,
            next_emph: TextEmphasis,
        ) -> None:
            cur_emph = reduce(or_, emph_stack)
            add_emph = next_emph & ~cur_emph
            remove_emph = cur_emph & ~next_emph
            if remove_emph:
                while remove_emph & emph_stack[-1]:
                    emph = emph_stack[-1]
                    text_parts.extend(
                        self._EMPH_TO_MD_MARKER[te] for te in (remove_emph & emph)
                    )
                    emph_stack[-1] = emph & ~remove_emph
                    if emph_stack[-1] == TextEmphasis.NONE:
                        emph_stack.pop()
                    remove_emph &= ~emph
                if remove_emph:
                    raise ValueError(
                        f"invalid change: removing {remove_emph!r:s} from "
                        f"stack {emph_stack!r:s}"
                    )
            if add_emph:
                # We need to look ahead to push longer-lived markers first
                add_emph_ls = list(add_emph)
                add_emph_ls.sort(
                    key=lambda te: frag_emphasis_len(fragments, start, te),
                )
                text_parts.extend(self._EMPH_TO_MD_MARKER[te] for te in add_emph_ls)
                emph_stack.append(add_emph)

        for text_line in text_lines:
            text_parts: list[str] = []
            emph_stack: list[TextEmphasis] = [TextEmphasis.NONE]
            last_link_dest: int | str | None = None
            last_link_emph: TextEmphasis = TextEmphasis.NONE
            i: int = 0
            for i, frag in enumerate(text_line.fragments):
                next_emph = frag_emphasis(frag)
                next_link_dest = frag.link
                # If a fragment has a link and the global flag
                # `MARKDOWN_LINK_UNDERLINE` is true, the underline marker must
                # not be added because it is unclear whether it has been set
                # explicitly by a marker or just by the global flag
                if next_link_dest is not None and self.MARKDOWN_LINK_UNDERLINE:
                    next_emph &= ~TextEmphasis.U
                # Close last link
                if last_link_dest is not None and last_link_dest != next_link_dest:
                    flush_markers(text_line.fragments, i, last_link_emph)
                    text_parts.append(f"]({last_link_dest!s:s})")
                    last_link_dest = None
                    last_link_emph = TextEmphasis.NONE
                # Open next link
                if last_link_dest is None and next_link_dest is not None:
                    # Find common link emphasis
                    next_link_emph = next_emph
                    for next_frag in text_line.fragments[i + 1 :]:
                        if next_frag.link != next_link_dest:
                            break
                        next_link_emph &= frag_emphasis(next_frag)
                    flush_markers(text_line.fragments, i, next_link_emph)
                    text_parts.append("[")
                    flush_markers(text_line.fragments, i, next_emph)
                    text_parts.append(
                        self._escape_markdown_chars(
                            "".join(frag.characters), in_link=True
                        )
                    )
                    last_link_dest = next_link_dest
                    last_link_emph = next_link_emph
                # Close and open markers
                else:
                    flush_markers(text_line.fragments, i, next_emph)
                    text_parts.append(
                        self._escape_markdown_chars("".join(frag.characters))
                    )
                    continue
            # Close last link
            if last_link_dest is not None:
                flush_markers(text_line.fragments, i, last_link_emph)
                text_parts.append(f"]({last_link_dest!s:s})")
            # Close last marker
            flush_markers(text_line.fragments, i, TextEmphasis.NONE)
            output_lines.append("".join(text_parts))
        return output_lines

    def _parse_markdown_chars(
        self,
        text: str,
        *,
        in_link: bool = False,
    ) -> Iterator[MarkdownFragment]:
        current_chars: list[str] = []
        current_emphasis: TextEmphasis = TextEmphasis.NONE
        escape_run: bool = False
        link_color: Color | None = (
            convert_to_device_color(self.MARKDOWN_LINK_COLOR)
            if self.MARKDOWN_LINK_COLOR
            else None
        )
        tokens: list[MarkdownToken] = []

        def flush_chars() -> None:
            nonlocal current_chars
            if not current_chars and not current_emphasis:
                return
            tokens.append(
                MarkdownToken(text="".join(current_chars), emphasis=current_emphasis)
            )
            current_chars = []

        def flush_tokens() -> Iterator[MarkdownFragment]:
            nonlocal tokens
            if current_emphasis != TextEmphasis.NONE:
                return
            for t in tokens:
                if not t.text and t.link is None:
                    continue
                if t.link is not None:
                    yield t.text, t.emphasis | t.link_emphasis, t.link, link_color
                else:
                    yield t.text, t.emphasis, None, None
            tokens = []

        i = 0
        n = len(text)
        while i < n:
            # Handle escape character
            if not escape_run and text[i] == self.MARKDOWN_ESCAPE_CHARACTER:
                escape_run = True
                i += 1
                continue
            is_marker = text[i : i + 2] in self._MD_MARKERS
            # Handle escaped marker
            if escape_run and is_marker:
                current_chars.extend(text[i : i + 2])
                escape_run = False
                i += 2
                continue
            # Handle escaped character
            if escape_run and text[i] in self.MARKDOWN_ESCAPABLES:
                current_chars.append(text[i])
                escape_run = False
                i += 1
                continue
            # Handle escape character without trailing marker or escapable character
            if escape_run:
                current_chars.append(self.MARKDOWN_ESCAPE_CHARACTER)
                escape_run = False
            # Handle a link (bare minimum `[]()` - minimum length 4)
            if not in_link and text[i] == "[" and i + 3 < n:
                is_link = self._MD_LINK_PATTERN.match(text, pos=i)
                if is_link:
                    flush_chars()
                    link_text, link_dest = is_link.groups()
                    if link_text:
                        for (
                            link_chars,
                            link_emphasis,
                            _,
                            _,
                        ) in self._parse_markdown_chars(link_text, in_link=True):
                            tokens.append(
                                MarkdownToken(
                                    text=link_chars,
                                    emphasis=current_emphasis,
                                    link=link_dest,
                                    link_emphasis=(
                                        (link_emphasis | TextEmphasis.U)
                                        if self.MARKDOWN_LINK_UNDERLINE
                                        else link_emphasis
                                    ),
                                )
                            )
                    else:
                        tokens.append(
                            MarkdownToken(
                                text="",
                                emphasis=current_emphasis,
                                link=link_dest,
                                link_emphasis=TextEmphasis.NONE,
                            )
                        )
                    i = is_link.end()
                    yield from flush_tokens()
                    continue
            # Handle marker
            if is_marker:
                emph = self._MD_MARKER_TO_EMPH[text[i : i + 2]]
                # Case: Equal character(s) after marker escape the marker
                if i + 2 < n and text[i] == text[i + 2]:
                    half_marker = text[i]
                    j = i + 3
                    while j < n and text[j] == half_marker:
                        j += 1
                    current_chars.extend(text[i:j])
                    i = j
                    continue
                flush_chars()
                current_emphasis ^= emph
                i += 2
                yield from flush_tokens()
                continue
            # Handle all other characters
            current_chars.append(text[i])
            i += 1
        # Handle remaining escape run
        if escape_run:
            current_chars.append(self.MARKDOWN_ESCAPE_CHARACTER)
        # Handle remaininig characters
        flush_chars()
        # Handle unclosed markers
        for i in range(len(tokens) - 1, -1, -1):
            tok = tokens[i]
            new_emphasis = current_emphasis & tok.emphasis
            tok.text += self._EMPH_TO_MD_MARKER[current_emphasis & ~tok.emphasis]
            tok.emphasis &= ~current_emphasis
            # Merge two consecutive tokens with same properties beside text
            if (
                i < len(tokens) - 1
                and tok.emphasis == tokens[i + 1].emphasis
                and tok.link == tokens[i + 1].link
                and tok.link_emphasis == tokens[i + 1].link_emphasis
            ):
                tok.text += tokens[i + 1].text
                del tokens[i + 1]
            current_emphasis = new_emphasis
        if current_emphasis != TextEmphasis.NONE:
            new_emphasis = current_emphasis & tokens[0].emphasis
            tokens[0].text = self._EMPH_TO_MD_MARKER[current_emphasis] + tokens[0].text
            tokens[0].emphasis &= ~current_emphasis
            current_emphasis = new_emphasis
            assert current_emphasis == TextEmphasis.NONE  # type: ignore[comparison-overlap]
        # Flush remaininig tokens
        yield from flush_tokens()
