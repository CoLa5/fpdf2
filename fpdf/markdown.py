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
import re
from typing import Final, Literal, TypeAlias, TYPE_CHECKING

from .drawing_primitives import Color, convert_to_device_color
from .enums import TextEmphasis
from .util import Number

if TYPE_CHECKING:
    from .line_break import TextLine


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
    MARKDOWN_ESCAPABLES: Final[set[str]] = set(
        chr(x)
        for x in (
            *range(33, 48),  # !, ", #, $, %, &, ', (, ), *, +, ,, -, ., / (U+0021–2F)
            *range(58, 65),  # :, ;, <, =, >, ?, @ (U+003A–0040)
            *range(91, 97),  # [, \, ], ^, _, ` (U+005B–0060)
            *range(123, 127),  # {, |, }, ~ (U+007B–007E)
        )
    )
    MARKDOWN_ESCAPE_CHARACTER: Final[Literal["\\"]] = "\\"

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

    # Pattern to escape markdown markers, the escape character itself and link-related characters
    _MD_ESCAPE_PATTERN: re.Pattern[str] = re.compile(rf"({'|'.join(
            re.escape(m)
            for m in (*_MD_MARKER_TO_EMPH, MARKDOWN_ESCAPE_CHARACTER, "[", "]")
            if m
        ):s})")

    # Pattern to search the link destination AFTER encountering an opening square bracket "["
    _MD_LINK_PATTERN: re.Pattern[str] = re.compile(
        rf"(?<!{2*MARKDOWN_ESCAPE_CHARACTER:s})([^]]*)\]\(([^()]*)\)"
    )

    @classmethod
    def _escape_markdown_chars(cls, text: str) -> str:
        return cls._MD_ESCAPE_PATTERN.sub(
            rf"{cls.MARKDOWN_ESCAPE_CHARACTER:s}\\1", text
        )

    def _join_markdown_text_lines(
        self,
        text_lines: list["TextLine"],
    ) -> list[str]:
        # NOTE:
        # Known limitations that make the markdown dry run-output differ from
        # the input, but do NOT change the appearance when finally being
        # printed:
        # - Order of markers is not kept: `"**__x__**" == "__**x**__"`
        # - Implicitly escaped markers and square brackets will be escaped
        #   explicitly: `"**x** **" == "**x** \\**"`
        # - Underline markers in or around links will not be kept if
        #   `MARKDOWN_LINK_UNDERLINE` is true:
        #   `"--[text](www.link.com)--" == "[text](www.link.com)"`

        output_lines: list[str] = []

        def open_markers(last_emph: TextEmphasis, next_emph: TextEmphasis) -> None:
            text_parts.extend(
                self._EMPH_TO_MD_MARKER[te] for te in (next_emph & ~last_emph)
            )

        def close_markers(last_emph: TextEmphasis, next_emph: TextEmphasis) -> None:
            text_parts.extend(
                self._EMPH_TO_MD_MARKER[te]
                for te in reversed(tuple(last_emph & ~next_emph))
            )

        for text_line in text_lines:
            text_parts: list[str] = []
            last_emph: TextEmphasis = TextEmphasis.NONE
            last_link_dest: int | str | None = None
            last_link_emph: TextEmphasis = TextEmphasis.NONE
            for i, frag in enumerate(text_line.fragments):
                next_emph = TextEmphasis.coerce(
                    frag.font_style
                    + ("U" if frag.underline else "")
                    + ("S" if frag.strikethrough else "")
                )
                next_link_dest = frag.link
                # If a fragment has a link and the global flag
                # `MARKDOWN_LINK_UNDERLINE` is true, the underline marker must
                # not be added because it is unclear whether it has been set
                # explicitly by a marker or just by the global flag
                if next_link_dest and self.MARKDOWN_LINK_UNDERLINE:
                    next_emph &= ~TextEmphasis.U
                # Close last link
                if last_link_dest is not None and last_link_dest != next_link_dest:
                    close_markers(last_emph, last_link_emph)
                    text_parts.append(f"]({last_link_dest!s:s})")
                    last_emph = last_link_emph
                    last_link_dest = None
                    last_link_emph = TextEmphasis.NONE
                # Open next link
                if last_link_dest is None and next_link_dest is not None:
                    # Find common link emphasis
                    next_link_emph = next_emph
                    for next_frag in text_line.fragments[i + 1 :]:
                        if next_frag.link != next_link_dest:
                            break
                        next_link_emph &= TextEmphasis.coerce(
                            next_frag.font_style
                            + (
                                "U"
                                if next_frag.underline
                                and not self.MARKDOWN_LINK_UNDERLINE
                                else ""
                            )
                            + ("S" if next_frag.strikethrough else "")
                        )
                    close_markers(last_emph, next_link_emph)
                    open_markers(last_emph, next_link_emph)
                    text_parts.append("[")
                    open_markers(next_link_emph, next_emph)
                    text_parts.append(
                        self._escape_markdown_chars("".join(frag.characters))
                    )
                    last_emph = next_emph
                    last_link_dest = next_link_dest
                    last_link_emph = next_link_emph
                # Close and open markers
                else:
                    close_markers(last_emph, next_emph)
                    open_markers(last_emph, next_emph)
                    text_parts.append(
                        self._escape_markdown_chars("".join(frag.characters))
                    )
                    last_emph = next_emph
                    continue
            # Close last link
            if last_link_dest is not None:
                close_markers(last_emph, last_link_emph)
                text_parts.append(f"]({last_link_dest!s:s})")
                last_emph = last_link_emph
            # Close last marker
            close_markers(last_emph, TextEmphasis.NONE)
            output_lines.append("".join(text_parts))
        return output_lines

    def _parse_markdown_chars(
        self,
        text: str,
        *,
        _in_link: bool = False,
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
                # assert t.text
                if t.link:
                    yield t.text, t.emphasis | t.link_emphasis, t.link, link_color
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
            # Handle escapable character
            # (must be AFTER escaped marker because of overlap of symbols like "\\*" vs. "\\**")
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
            if not _in_link and text[i] == "[" and i + 3 < n:
                is_link = self._MD_LINK_PATTERN.search(text, pos=i + 1)
                if is_link:
                    flush_chars()
                    link_text, link_dest = is_link.groups()
                    if link_dest.startswith("<") and link_dest.endswith(">"):
                        link_dest = link_dest[1:-1]
                    for link_chars, link_emphasis, _, _ in self._parse_markdown_chars(
                        link_text, _in_link=True
                    ):
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
                    i = is_link.end()
                    yield from flush_tokens()
                    continue
            # Handle marker
            if is_marker:
                emph = self._MD_MARKER_TO_EMPH[text[i : i + 2]]
                # Case: Marker with equal third character in case of an
                # opening marker, e.g. "***" == "*" + bold marker
                if (
                    not (current_emphasis & emph)
                    and i + 2 < n
                    and text[i] == text[i + 2]
                ):
                    current_chars.append(text[i])
                    i += 1
                    continue
                flush_chars()
                current_emphasis ^= emph
                i += 2
                yield from flush_tokens()
                continue
            # Handle all other characters
            current_chars.append(text[i])
            i += 1
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
            # Delete empty token (but not first one)
            if i > 0 and not tok:
                del tokens[i]
            current_emphasis = new_emphasis
        if current_emphasis != TextEmphasis.NONE:
            new_emphasis = current_emphasis & tokens[0].emphasis
            tokens[0].text = self._EMPH_TO_MD_MARKER[current_emphasis] + tokens[0].text
            tokens[0].emphasis &= ~current_emphasis
            current_emphasis = new_emphasis
            assert current_emphasis == TextEmphasis.NONE  # type: ignore[comparison-overlap]
        # Flush remaininig tokens
        yield from flush_tokens()
