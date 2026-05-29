import itertools
from pathlib import Path
from typing import Iterator

import fpdf
from test.conftest import assert_pdf_equal
from test.conftest import LOREM_IPSUM

import pytest

HERE = Path(__file__).resolve().parent
FONTS_DIR = HERE.parent / "fonts"


def test_multi_cell_markdown(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=32)
    text = (  # Some text where styling occur over line breaks:
        "Lorem ipsum dolor amet, **consectetur adipiscing** elit,"
        " sed do eiusmod __tempor incididunt__ ut labore et dolore --magna aliqua--."
    )
    pdf.multi_cell(
        w=pdf.epw, text=text, markdown=True
    )  # This is tricky to get working well
    pdf.ln()
    pdf.multi_cell(w=pdf.epw, text=text, markdown=True, align="L")
    assert_pdf_equal(pdf, HERE / "multi_cell_markdown.pdf", tmp_path)


def test_multi_cell_markdown_strikethrough(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=32)
    pdf.multi_cell(w=pdf.epw, text="~~strikethrough~~", markdown=True)
    assert_pdf_equal(pdf, HERE / "multi_cell_markdown_strikethrough.pdf", tmp_path)


def test_multi_cell_markdown_escaped(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=32)
    text = (  # Some text where styling occur over line breaks:
        "Lorem ipsum \\ dolor amet, \\**consectetur adipiscing\\** elit,"
        " sed do eiusmod \\\\__tempor incididunt\\\\__ ut labore et dolore --magna aliqua--."
    )
    pdf.multi_cell(
        w=pdf.epw, text=text, markdown=True
    )  # This is tricky to get working well
    pdf.ln()
    pdf.multi_cell(w=pdf.epw, text=text, markdown=True, align="L")
    assert_pdf_equal(pdf, HERE / "multi_cell_markdown_escaped.pdf", tmp_path)


def test_multi_cell_markdown_with_ttf_fonts(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.add_font("Roboto", "", FONTS_DIR / "Roboto-Regular.ttf")
    pdf.add_font("Roboto", "B", FONTS_DIR / "Roboto-Bold.ttf")
    pdf.add_font("Roboto", "I", FONTS_DIR / "Roboto-Italic.ttf")
    pdf.set_font("Roboto", size=32)
    text = (  # Some text where styling occur over line breaks:
        "Lorem ipsum dolor, **consectetur adipiscing** elit,"
        " eiusmod __tempor incididunt__ ut labore et dolore --magna aliqua--."
    )
    pdf.multi_cell(
        w=pdf.epw, text=text, markdown=True
    )  # This is tricky to get working well
    pdf.ln()
    pdf.multi_cell(w=pdf.epw, text=text, markdown=True, align="L")
    assert_pdf_equal(pdf, HERE / "multi_cell_markdown_with_ttf_fonts.pdf", tmp_path)


def test_multi_cell_markdown_with_ttf_fonts_escaped(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.add_font("Roboto", "", FONTS_DIR / "Roboto-Regular.ttf")
    pdf.add_font("Roboto", "B", FONTS_DIR / "Roboto-Bold.ttf")
    pdf.add_font("Roboto", "I", FONTS_DIR / "Roboto-Italic.ttf")
    pdf.set_font("Roboto", size=32)
    text = (  # Some text where styling occur over line breaks:
        "Lorem ipsum \\ dolor, \\**consectetur adipiscing\\** elit,"
        " eiusmod \\\\__tempor incididunt\\\\__ ut labore et dolore --magna aliqua--."
    )
    pdf.multi_cell(
        w=pdf.epw, text=text, markdown=True
    )  # This is tricky to get working well
    pdf.ln()
    pdf.multi_cell(w=pdf.epw, text=text, markdown=True, align="L")
    assert_pdf_equal(
        pdf, HERE / "multi_cell_markdown_with_ttf_fonts_escaped.pdf", tmp_path
    )


def test_multi_cell_markdown_missing_ttf_font():
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.add_font(fname=FONTS_DIR / "Roboto-Regular.ttf")
    pdf.set_font("Roboto-Regular", size=60)
    with pytest.raises(fpdf.FPDFException) as error:
        pdf.multi_cell(w=pdf.epw, text="**Lorem Ipsum**", markdown=True)
    expected_msg = "Undefined font: roboto-regularB - Use built-in fonts or FPDF.add_font() beforehand"
    assert str(error.value) == expected_msg


def test_multi_cell_markdown_with_fill_color(tmp_path):  # issue 348
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=10)
    pdf.set_fill_color(255, 0, 0)
    pdf.multi_cell(
        50,
        markdown=True,
        text="aa bb cc **dd ee dd ee dd ee dd ee dd ee dd ee**",
    )
    assert_pdf_equal(pdf, HERE / "multi_cell_markdown_with_fill_color.pdf", tmp_path)


def test_multi_cell_markdown_justified(tmp_path):  # issue 327
    pdf = fpdf.FPDF()
    pdf.add_page()
    for font in ("Helvetica", "Courier"):
        pdf.set_font(family=font, size=12)
        pdf.set_y(pdf.y + 3)
        pdf.multi_cell(
            190,
            markdown=True,
            align="J",
            text=(
                "Lorem **ipsum** dolor sit amet, **consectetur** adipiscing elit, "
                "sed do eiusmod tempor incididunt ut labore et dolore magna "
                "aliqua. Ut enim ad minim veniam, __quis__ nostrud exercitation "
                "ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis "
                "aute irure dolor in reprehenderit in voluptate velit esse cillum "
                "dolore eu fugiat nulla pariatur. Excepteur sint occaecat "
                "cupidatat non proident, sunt in culpa qui officia deserunt "
                "mollit anim id est laborum."
            ),
        )
        pdf.set_x(10)
        pdf.set_y(pdf.y + 5)
    assert_pdf_equal(pdf, HERE / "multi_cell_markdown_justified.pdf", tmp_path)


def test_multi_cell_markdown_link(tmp_path):
    pdf = fpdf.FPDF()
    pdf.set_font("Helvetica")
    pdf.add_page()
    pdf.multi_cell(
        pdf.epw,
        text="**Start** [fpdf2 github](https://github.com/py-pdf/fpdf2) __End__",
        markdown=True,
    )
    assert_pdf_equal(pdf, HERE / "multi_cell_markdown_link.pdf", tmp_path)


def test_multi_cell_markdown_link_dry_run(tmp_path):
    pdf = fpdf.FPDF()
    pdf.set_font("Helvetica")
    pdf.add_page()
    assert len(pdf.pages[1].annots) == 0

    pdf.multi_cell(
        pdf.epw,
        text="**Start** [fpdf2 github](https://github.com/py-pdf/fpdf2) __End__",
        dry_run=True,
        markdown=True,
        new_x="left",
        new_y="next",
    )
    assert len(pdf.pages[1].annots) == 0

    pdf.multi_cell(
        pdf.epw,
        text="**Start** [fpdf2 github](https://github.com/py-pdf/fpdf2) __End__",
        markdown=True,
        new_x="left",
        new_y="next",
    )
    assert len(pdf.pages[1].annots) == 1

    pdf.multi_cell(
        pdf.epw,
        text="**Start** [fpdf2 github](https://github.com/py-pdf/fpdf2) __End__",
        dry_run=True,
        markdown=True,
        new_x="left",
        new_y="next",
    )
    assert len(pdf.pages[1].annots) == 1

    pdf.multi_cell(
        pdf.epw,
        text="**Start** [fpdf2 github](https://github.com/py-pdf/fpdf2) __End__",
        markdown=True,
        new_x="left",
        new_y="next",
    )
    assert len(pdf.pages[1].annots) == 2

    assert_pdf_equal(pdf, HERE / "multi_cell_markdown_link_dry_run.pdf", tmp_path)


def test_multi_cell_markdown_link_inner_style(tmp_path):
    styles = (
        ("Bold", "**"),
        ("Italics", "__"),
        ("Strikethrough", "~~"),
        ("Underline", "--"),
    )
    style_combinations = []
    for i in range(1, len(styles) + 1):
        for combo in itertools.combinations(styles, i):
            style = "-".join(c[0] for c in combo)
            marker = "".join(c[1] for c in combo)
            style_combinations.append((style, marker))

    pdf = fpdf.FPDF()
    pdf.set_font("Helvetica")
    pdf.add_page()

    for link_color, link_underline in itertools.product(
        (None, "#0000ff"),
        (False, True),
    ):
        pdf.MARKDOWN_LINK_COLOR = link_color
        pdf.MARKDOWN_LINK_UNDERLINE = link_underline
        for style, marker in style_combinations:
            pdf.multi_cell(
                pdf.epw,
                text=f"**Start** [{marker:s}{style:s}{marker:s} Link](https://github.com/py-pdf/fpdf2) __End__",
                markdown=True,
                new_x="left",
                new_y="next",
            )
        pdf.ln()

    assert_pdf_equal(pdf, HERE / "multi_cell_markdown_link_inner_style.pdf", tmp_path)


def test_multi_cell_markdown_link_mixed_style(tmp_path):
    # Mixed inner and outer link styles
    styles = (
        ("Bold", "**"),
        ("Italics", "__"),
        ("Strikethrough", "~~"),
        ("Underline", "--"),
    )
    style_combinations = []
    for i in range(1, len(styles) + 1):
        for combo in itertools.combinations(styles, i):
            style = "-".join(c[0] for c in combo)
            marker = "".join(c[1] for c in combo)
            style_combinations.append((style, marker))

    pdf = fpdf.FPDF()
    pdf.set_font("Helvetica")
    pdf.add_page()

    for link_color, link_underline in itertools.product(
        (None, "#0000ff"),
        (False, True),
    ):
        pdf.MARKDOWN_LINK_COLOR = link_color
        pdf.MARKDOWN_LINK_UNDERLINE = link_underline
        for style, marker in style_combinations:
            for i in range(2, len(marker), 2):
                m1 = marker[:i]
                m2 = marker[i:]
                pdf.multi_cell(
                    pdf.epw,
                    text=f"**Start** {m1:s}[{m2:s}{style:s}{m2:s} Link](https://github.com/py-pdf/fpdf2){m1:s} __End__",
                    markdown=True,
                    new_x="left",
                    new_y="next",
                )
        pdf.ln()

    assert_pdf_equal(pdf, HERE / "multi_cell_markdown_link_mixed_style.pdf", tmp_path)


def test_multi_cell_markdown_link_outer_style(tmp_path):
    styles = (
        ("Bold", "**"),
        ("Italics", "__"),
        ("Strikethrough", "~~"),
        ("Underline", "--"),
    )
    style_combinations = []
    for i in range(1, len(styles) + 1):
        for combo in itertools.combinations(styles, i):
            style = "-".join(c[0] for c in combo)
            marker = "".join(c[1] for c in combo)
            style_combinations.append((style, marker))

    pdf = fpdf.FPDF()
    pdf.set_font("Helvetica")
    pdf.add_page()

    for link_color, link_underline in itertools.product(
        (None, "#0000ff"),
        (False, True),
    ):
        pdf.MARKDOWN_LINK_COLOR = link_color
        pdf.MARKDOWN_LINK_UNDERLINE = link_underline
        for style, marker in style_combinations:
            pdf.multi_cell(
                pdf.epw,
                text=f"**Start** {marker:s}[{style:s} Link](https://github.com/py-pdf/fpdf2){marker:s} __End__",
                markdown=True,
                new_x="left",
                new_y="next",
            )
        pdf.ln()

    assert_pdf_equal(pdf, HERE / "multi_cell_markdown_link_outer_style.pdf", tmp_path)


def test_multi_cell_markdown_link_sequence(tmp_path):
    link1 = "[fpdf2 github](https://github.com/py-pdf/fpdf2)"
    link2 = "[fpdf2 github Releases](https://github.com/py-pdf/fpdf2/releases)"
    link3 = "[fpdf2 **github**](https://github.com/py-pdf/fpdf2)"

    pdf = fpdf.FPDF()
    pdf.set_font("Helvetica")
    pdf.add_page()
    # Two different links with space gap
    pdf.multi_cell(
        pdf.epw,
        text=f"**Start** {link1:s} {link2:s} __End__",
        markdown=True,
        new_x="left",
        new_y="next",
    )
    assert len(pdf.pages[pdf.page].annots) == 2
    # Two different links without space gap
    pdf.multi_cell(
        pdf.epw,
        text=f"**Start** {link1:s}{link2:s} __End__",
        markdown=True,
        new_x="left",
        new_y="next",
    )
    assert len(pdf.pages[pdf.page].annots) == 4
    # Link with inner style
    pdf.multi_cell(
        pdf.epw,
        text=f"**Start** {link3:s} __End__",
        markdown=True,
        new_x="left",
        new_y="next",
    )
    assert len(pdf.pages[pdf.page].annots) == 5
    # Two equal links with outer style
    pdf.multi_cell(
        pdf.epw,
        text=f"**Start** {link1:s}**{link1:s}** __End__",
        markdown=True,
        new_x="left",
        new_y="next",
    )
    assert len(pdf.pages[pdf.page].annots) == 6
    # Three equal links with outer style
    pdf.multi_cell(
        pdf.epw,
        text=f"**Start** {link1:s}**{link1:s}**--{link1:s}-- __End__",
        markdown=True,
        new_x="left",
        new_y="next",
    )
    assert len(pdf.pages[pdf.page].annots) == 7
    # Two equal links with fragment inbetween
    pdf.multi_cell(
        pdf.epw,
        text=f"**Start** {link1:s} Middle {link1:s} __End__",
        markdown=True,
        new_x="left",
        new_y="next",
    )
    assert len(pdf.pages[pdf.page].annots) == 9

    assert_pdf_equal(pdf, HERE / "multi_cell_markdown_link_sequence.pdf", tmp_path)


@pytest.mark.parametrize(
    "text",
    [
        "**Start** [fpdf2 __github__](https://github.com/py-pdf/fpdf2)\n__End__",
        LOREM_IPSUM
        + "\n**Start** [fpdf2 __github__](https://github.com/py-pdf/fpdf2)\n__End__",
        LOREM_IPSUM[: len(LOREM_IPSUM) // 2]
        + " **\nStart** [fpdf2 __github__](https://github.com/py-pdf/fpdf2)\n__End__ "
        + LOREM_IPSUM[len(LOREM_IPSUM) // 2 :],
    ],
)
def test_multi_cell_markdown_dry_run_lines_output(text):
    pdf = fpdf.FPDF()
    pdf.set_font("Helvetica")
    pdf.add_page()

    lines = pdf.multi_cell(
        pdf.epw,
        text=text,
        dry_run=True,
        markdown=True,
        new_x="left",
        new_y="next",
        output=fpdf.enums.MethodReturnValue.LINES,
    )
    joined_text = "\n".join(lines)
    # The parts of the special markdown text must be in the lines list, but not
    # in the same line

    assert any("**Start**" in line for line in lines), joined_text
    assert any(
        "[fpdf2 __github__](https://github.com/py-pdf/fpdf2)" in line for line in lines
    ), joined_text
    assert any("__End__" in line for line in lines), joined_text
    start_line = next(i for i, line in enumerate(lines) if "**Start**" in line)
    end_line = next(i for i, line in enumerate(lines) if "__End__" in line)
    assert start_line + 1 == end_line, joined_text

    assert (
        "**Start** [fpdf2 __github__](https://github.com/py-pdf/fpdf2)\n__End__"
        in joined_text
    ), joined_text


def test_multi_cell_markdown_dry_run_lines_output_print(tmp_path):
    # Test that output="LINES" keeps markdown format
    text = (
        LOREM_IPSUM[: len(LOREM_IPSUM) // 2]
        + "\n**Start** ~~test~~ "
        # Note: Order matters - test that text will be underlined after link
        + "[fpdf2 __github__](https://github.com/py-pdf/fpdf2) --test--\n"
        + "__End__ "
        + LOREM_IPSUM[len(LOREM_IPSUM) // 2 :]
    )

    pdf = fpdf.FPDF()
    pdf.set_font("Helvetica")
    pdf.add_page()

    # Normal text
    pdf.multi_cell(
        pdf.epw,
        text=text,
        markdown=True,
        new_x="left",
        new_y="next",
    )
    pdf.ln()

    # Join text after dry run by `"\n"`
    lines = pdf.multi_cell(
        pdf.epw,
        text=text,
        dry_run=True,
        markdown=True,
        new_x="left",
        new_y="next",
        output=fpdf.enums.MethodReturnValue.LINES,
    )
    pdf.multi_cell(
        pdf.epw,
        text="\n".join(lines),
        markdown=True,
        new_x="left",
        new_y="next",
    )

    assert_pdf_equal(
        pdf, HERE / "multi_cell_markdown_dry_run_lines_output.pdf", tmp_path
    )


def test_multi_cell_markdown_dry_run_lines_output_escape(tmp_path):
    # Test that escaped markdown markers stay escaped
    text = (
        LOREM_IPSUM[: len(LOREM_IPSUM) // 2]
        + "\n**Start** \\** "
        # NOTE: Second bold marker inside of link text is implicitly escaped
        + "[fpdf2 \\**github**](https://github.com/py-pdf/fpdf2) \\__ "
        + "\\~~ \\-- \\\\ \\\\\\\\ \n"
        + "__End__ "
        + LOREM_IPSUM[len(LOREM_IPSUM) // 2 :]
    )

    pdf = fpdf.FPDF()
    pdf.set_font("Helvetica")
    pdf.add_page()

    # Normal text
    pdf.multi_cell(
        pdf.epw,
        text=text,
        markdown=True,
        new_x="left",
        new_y="next",
    )
    pdf.ln()

    # Join text after dry run by `"\n"`
    lines = pdf.multi_cell(
        pdf.epw,
        text=text,
        dry_run=True,
        markdown=True,
        new_x="left",
        new_y="next",
        output=fpdf.enums.MethodReturnValue.LINES,
    )
    pdf.multi_cell(
        pdf.epw,
        text="\n".join(lines),
        markdown=True,
        new_x="left",
        new_y="next",
    )

    assert_pdf_equal(
        pdf, HERE / "multi_cell_markdown_dry_run_lines_output_escape.pdf", tmp_path
    )


def commonmark_header(msg: str, *example_num: int) -> str:
    numbers = ", ".join(str(n) for n in example_num)
    return f"CommonMark Spec - {msg:s} - Example{'s' if len(example_num) > 1 else '':s} {numbers:s}"


def commonmark_msg(msg: str, *example_num: int) -> str:
    links = ", ".join(
        f"https://spec.commonmark.org/0.31.2/#example-{n:d}" for n in example_num
    )
    return f"CommonMark Spec - {msg:s} - {links:s}"


def markdown_markers() -> Iterator[str]:
    for mt in ("bold", "italics", "strikethrough", "underline"):
        yield getattr(fpdf.FPDF, f"MARKDOWN_{mt.upper():s}_MARKER")


def emph_examples() -> Iterator[tuple[str, str, str, tuple[int, ...]]]:
    esc = fpdf.FPDF.MARKDOWN_ESCAPE_CHARACTER
    lf = ("\n", "\n", "", tuple())
    yield from (
        (
            f"{m:s}foo bar{m:s}",
            f"{m:s}foo bar{m:s}",
            "Default",
            (350, 357, 378, 382),
        )
        for m in markdown_markers()
    )
    yield lf
    yield from (
        (
            f"foo{m:s}bar{m:s}",
            f"foo{m:s}bar{m:s}",
            "Intraword emphasis",
            (355, 381),
        )
        for m in markdown_markers()
    )
    yield lf
    yield from (
        (
            f"5{m:s}6{m:s}78",
            f"5{m:s}6{m:s}78",
            "Intraword emphasis",
            (356,),
        )
        for m in markdown_markers()
    )
    yield lf
    yield from (
        (
            f"{m1:s}foo{m2:s}",
            f"{esc:s}{m1:s}foo{esc:s}{m2:s}",
            "Not matching markers",
            (365,),
        )
        for m1, m2 in itertools.permutations(markdown_markers(), 2)
    )
    yield lf
    yield from (
        (
            f"{m:s}foo{m:s}bar",
            f"{m:s}foo{m:s}bar",
            "Intraword emphasis",
            (370, 396),
        )
        for m in markdown_markers()
    )
    yield lf
    yield from (
        (
            f"{m:s}fpdf2 on [GitHub](https://github.com/py-pdf/fpdf2){m:s}",
            f"{m:s}fpdf2 on {m if m == "--" else "":s}"
            f"[GitHub](https://github.com/py-pdf/fpdf2){m if m != "--" else "":s}",
            "Link inside emphasis",
            (404, 422),
        )
        for m in markdown_markers()
    )
    yield lf
    yield from (
        (
            f"{m:s}foo\nbar{m:s}",
            f"{m:s}foo{m:s}\n{m:s}bar{m:s}",
            "Line ending between markers",
            (405, 423),
        )
        for m in markdown_markers()
    )
    yield lf
    yield from (
        (
            f"{m1:s}foo {m2:s}bar{m2:s} baz{m1:s}",
            f"{m1:s}foo {m2:s}bar{m2:s} baz{m1:s}",
            "Nested emphasis",
            (406, 407, 410, 424, 428),
        )
        for m1, m2 in itertools.permutations(markdown_markers(), 2)
    )
    yield from (
        (
            f"{m1:s}foo {m2:s}bar {m3:s}baz{m3:s} qux{m2:s} quux{m1:s}",
            f"{m1:s}foo {m2:s}bar {m3:s}baz{m3:s} qux{m2:s} quux{m1:s}",
            "Nested emphasis",
            (406, 407, 410),
        )
        for m1, m2, m3 in itertools.permutations(markdown_markers(), 3)
    )
    yield from (
        (
            f"{m1:s}foo {m2:s}bar {m3:s}baz {m4:s}qux{m4:s} quux{m3:s} quux{m2:s} quuux{m1:s}",
            f"{m1:s}foo {m2:s}bar {m3:s}baz {m4:s}qux{m4:s} quux{m3:s} quux{m2:s} quuux{m1:s}",
            "Nested emphasis",
            (406, 407, 410),
        )
        for m1, m2, m3, m4 in itertools.permutations(markdown_markers(), 4)
    )
    yield from (
        (
            f"{m1:s}{m2:s}foo{m2:s} bar{m1:s}",
            f"{m1:s}{m2:s}foo{m2:s} bar{m1:s}",
            "Nested emphasis",
            (408, 430),
        )
        for m1, m2 in itertools.permutations(markdown_markers(), 2)
    )
    yield from (
        (
            f"{m1:s}foo {m2:s}bar{m2:s}{m1:s}",
            f"{m1:s}foo {m2:s}bar{m2:s}{m1:s}",
            "Nested emphasis",
            (409, 431),
        )
        for m1, m2 in itertools.permutations(markdown_markers(), 2)
    )
    yield from (
        (
            f"{m1:s}foo{m2:s}bar{m2:s}baz{m1:s}",
            f"{m1:s}foo{m2:s}bar{m2:s}baz{m1:s}",
            "Nested emphasis",
            (411, 429),
        )
        for m1, m2 in itertools.permutations(markdown_markers(), 2)
    )
    yield lf
    yield from (
        (
            f"{m:s}foo{m:s}{m:s}bar{m:s}",
            f"{m:s}foo{esc:s}{m:s}{esc:s}{m:s}bar{m:s}",
            "Nested emphasis",
            (412,),
        )
        for m in markdown_markers()
    )
    yield lf
    yield from (
        (
            f"{m1:s}{m2:s}foo{m2:s} bar{m1:s}",
            f"{m1:s}{m2:s}foo{m2:s} bar{m1:s}",
            "Nested emphasis",
            (413, 426),
        )
        for m1, m2 in itertools.permutations(markdown_markers(), 2)
    )
    yield from (
        (
            f"{m1:s}foo {m2:s}bar{m2:s}{m1:s}",
            f"{m1:s}foo {m2:s}bar{m2:s}{m1:s}",
            "Nested emphasis",
            (414, 427),
        )
        for m1, m2 in itertools.permutations(markdown_markers(), 2)
    )
    yield from (
        (
            f"{m1:s}foo{m2:s}bar{m2:s}{m1:s}",
            f"{m1:s}foo{m2:s}bar{m2:s}{m1:s}",
            "Nested emphasis",
            (415,),
        )
        for m1, m2 in itertools.permutations(markdown_markers(), 2)
    )
    yield lf
    yield from (
        (
            f"{m:s}{m:s} is not an empty emphasis",
            f"{esc:s}{m:s}{esc:s}{m:s} is not an empty emphasis",
            "No empty emphasis",
            (420, 421, 434, 435),
        )
        for m in markdown_markers()
    )
    yield lf
    yield from (
        (
            f"foo {m:s}{m[0]:s}",
            f"foo {esc:s}{m:s}{m[0]:s}",
            "Half emphasis",
            (436,),
        )
        for m in markdown_markers()
    )
    yield from (
        (
            f"foo {m[0]:s}{esc:s}{m:s}",
            f"foo {esc:s}{m:s}{m[0]:s}",
            "Nested half emphasis",
            (437,),
        )
        for m in markdown_markers()
    )
    yield from (
        (
            f"foo {m1:s}{m2:s}{m1:s}",
            f"foo {m1:s}{esc:s}{m2:s}{m1:s}",
            "Nested unclosed emphasis",
            (438,),
        )
        for m1, m2 in itertools.permutations(markdown_markers(), 2)
    )
    yield from (
        (
            f"foo {m:s}{m[0]:s}{m:s}",
            f"foo {esc:s}{m:s}{esc:s}{m:s}{m[0]:s}",
            "Nested half emphasis",
            (439,),
        )
        for m in markdown_markers()
    )
    yield from (
        (
            f"foo {m:s}{esc:s}{m[0]:s}{m:s}",
            f"foo {esc:s}{m:s}{esc:s}{m:s}{m[0]:s}",
            "Nested half escapeds emphasis",
            (440,),
        )
        for m in markdown_markers()
    )
    yield from (
        (
            f"foo {m1:s}{m2[0]:s}{m1:s} {m2[0]:s}",
            f"foo {m1:s}{m2[0]:s}{m1:s} {m2[0]:s}",
            "Nested half emphasis",
            (441,),
        )
        for m1, m2 in itertools.permutations(markdown_markers(), 2)
    )
    yield lf


def test_multi_cell_markdown_emphasis_cm(tmp_path) -> None:
    # NOTE:
    # Reference is CommonMark 0.31.2 - https://spec.commonmark.org/0.31.2/#links
    # fpdf2 DOES NOT fulfill the specification, but the specs are used here as
    # a reference for the examples to find bugs in the markdown parser
    w0 = 20.0

    pdf = fpdf.FPDF()
    pdf.set_font("Helvetica")
    pdf.add_page()

    for text, parsed_text, msg, example_num in emph_examples():
        # LF
        if text == "\n":
            pdf.ln()
            continue
        # New page (3 lines per example case)
        if pdf.y + 3 * pdf.font_size > pdf.page_break_trigger:
            pdf.add_page()
        # Title
        pdf.set_font(style="B")
        pdf.cell(
            w=pdf.epw,
            text=commonmark_header(msg, *example_num),
            new_x=fpdf.XPos.LMARGIN,
            new_y=fpdf.YPos.NEXT,
        )
        pdf.set_font(style="")
        # Normal
        pdf.cell(text="Normal: ")
        pdf.set_x(pdf.l_margin + w0)
        pdf.multi_cell(
            w=pdf.epw - w0,
            text=text,
            markdown=True,
            new_x=fpdf.XPos.LMARGIN,
            new_y=fpdf.YPos.NEXT,
        )
        # Dry-run
        pdf.cell(text="Dry-Run: ")
        pdf.set_x(pdf.l_margin + w0)
        lines = pdf.multi_cell(
            w=pdf.epw - w0,
            text=text,
            dry_run=True,
            markdown=True,
            new_x=fpdf.XPos.LMARGIN,
            new_y=fpdf.YPos.NEXT,
            output=fpdf.enums.MethodReturnValue.LINES,
        )
        joined_lines = "\n".join(lines)
        assert joined_lines == parsed_text, commonmark_msg(msg, *example_num)
        pdf.multi_cell(
            w=pdf.epw - w0,
            text=joined_lines,
            markdown=True,
            new_x=fpdf.XPos.LMARGIN,
            new_y=fpdf.YPos.NEXT,
        )
        pdf.ln()

    assert_pdf_equal(pdf, HERE / "multi_cell_markdown_emphasis_cm.pdf", tmp_path)


def link_examples() -> Iterator[tuple[str, str, str, tuple[int, ...]]]:
    lf = ("\n", "\n", "", tuple())

    yield (
        "[fpdf2 on GitHub](https://github.com/py-pdf/fpdf2)",
        "[fpdf2 on GitHub](https://github.com/py-pdf/fpdf2)",
        "Default link",
        (483,),
    )
    yield lf
    yield (
        "[](https://github.com/py-pdf/fpdf2)",
        "[](https://github.com/py-pdf/fpdf2)",
        "Empty link text",
        (484,),
    )
    yield lf
    yield (
        "[fpdf2 on GitHub]()",
        "[fpdf2 on GitHub]()",
        "Empty link destination",
        (485,),
    )
    yield lf
    yield (
        "[]()",
        "[]()",
        "Empty link text and destination",
        (487,),
    )
    yield lf
    yield (
        "[fpdf2 on GitHub](https:// github.com/py-pdf/fpdf2)",
        "[fpdf2 on GitHub](https:// github.com/py-pdf/fpdf2)",
        "No space in link destination",
        (488,),
    )
    yield lf
    yield (
        "[fpdf2 on GitHub](https://\ngithub.com/py-pdf/fpdf2)",
        "[fpdf2 on GitHub](https://\ngithub.com/py-pdf/fpdf2)",
        "No line ending in link destination",
        (490,),
    )
    yield lf
    yield (
        "[fpdf2 on GitHub] (https://github.com/py-pdf/fpdf2)",
        "[fpdf2 on GitHub] (https://github.com/py-pdf/fpdf2)",
        "No space between link text and link destination",
        (511,),
    )
    yield lf
    yield (
        "[fpdf2 [on [GitHub]]](https://github.com/py-pdf/fpdf2)",
        "[fpdf2 [on [GitHub]]](https://github.com/py-pdf/fpdf2)",
        "Balanced square brackets in link text (NOT SUPPORTED)",
        (512,),
    )
    yield (
        "[fpdf2 on] GitHub](https://github.com/py-pdf/fpdf2)",
        "[fpdf2 on] GitHub](https://github.com/py-pdf/fpdf2)",
        "Unbalanced square brackets in link text",
        (513,),
    )
    yield (
        "[fpdf2 on [GitHub](https://github.com/py-pdf/fpdf2)",
        "[fpdf2 on [GitHub](https://github.com/py-pdf/fpdf2)",
        "Unbalanced square brackets in link text",
        (514,),
    )
    yield (
        "[fpdf2 on \\[GitHub](https://github.com/py-pdf/fpdf2)",
        "[fpdf2 on \\[GitHub](https://github.com/py-pdf/fpdf2)",
        "Unbalanced escaped square bracket in link text",
        (515,),
    )
    yield lf
    yield (
        "[fpdf2 __on **GitHub**__](https://github.com/py-pdf/fpdf2)",
        "[fpdf2 __on **GitHub**__](https://github.com/py-pdf/fpdf2)",
        "Inline content (style in link text)",
        (516,),
    )
    yield lf
    yield (
        "[fpdf2 on [GitHub](https://github.com)](https://github.com/py-pdf/fpdf2)",
        "[fpdf2 on [GitHub](https://github.com)](https://github.com/py-pdf/fpdf2)",
        "No nested links",
        (518,),
    )
    yield (
        "[fpdf2 **[on [GitHub](https://github.com)](https://github.com/py-pdf)**](https://github.com/py-pdf/fpdf2)",
        "[fpdf2 **[on [GitHub](https://github.com)](https://github.com/py-pdf)**](https://github.com/py-pdf/fpdf2)",
        "No nested links",
        (519,),
    )
    yield lf
    yield (
        "**[fpdf2** on GitHub](https://github.com/py-pdf/fpdf2)",
        "\\**[fpdf2\\** on GitHub](https://github.com/py-pdf/fpdf2)",
        "Precedence of link text grouping over emphasis grouping",
        (521,),
    )
    yield (
        "[fpdf2 on **GitHub](https://github.com/py-pdf/fpdf2/**)",
        "[fpdf2 on \\**GitHub](https://github.com/py-pdf/fpdf2/**)",
        "Precedence of link text grouping over emphasis grouping",
        (522,),
    )
    yield lf
    yield (
        "**fpdf2 [on** GitHub]",
        "**fpdf2 [on** GitHub]",
        "No Precedence of no link text square brackets",
        (523,),
    )
    yield lf


def test_multi_cell_markdown_link_cm(tmp_path) -> None:
    # NOTE:
    # Reference is CommonMark 0.31.2 - https://spec.commonmark.org/0.31.2/#links
    # fpdf2 DOES NOT fulfill the specification, but the specs are used here as
    # a reference for the examples to find bugs in the markdown parser
    w0 = 20.0

    pdf = fpdf.FPDF()
    pdf.set_font("Helvetica")
    pdf.add_page()

    for text, parsed_text, msg, example_num in link_examples():
        # LF
        if text == "\n":
            pdf.ln()
            continue
        # New page (3 lines per example case)
        if pdf.y + 3 * pdf.font_size > pdf.page_break_trigger:
            pdf.add_page()
        # Title
        pdf.set_font(style="B")
        pdf.cell(
            w=pdf.epw,
            text=commonmark_header(msg, *example_num),
            new_x=fpdf.XPos.LMARGIN,
            new_y=fpdf.YPos.NEXT,
        )
        pdf.set_font(style="")
        # Normal
        pdf.cell(text="Normal: ")
        pdf.set_x(pdf.l_margin + w0)
        pdf.multi_cell(
            w=pdf.epw - w0,
            text=text,
            markdown=True,
            new_x=fpdf.XPos.LMARGIN,
            new_y=fpdf.YPos.NEXT,
        )
        # Dry-run
        pdf.cell(text="Dry-Run: ")
        pdf.set_x(pdf.l_margin + w0)
        lines = pdf.multi_cell(
            w=pdf.epw - w0,
            text=text,
            dry_run=True,
            markdown=True,
            new_x=fpdf.XPos.LMARGIN,
            new_y=fpdf.YPos.NEXT,
            output=fpdf.enums.MethodReturnValue.LINES,
        )
        joined_lines = "\n".join(lines)
        assert joined_lines == parsed_text, commonmark_msg(msg, *example_num)
        pdf.multi_cell(
            w=pdf.epw - w0,
            text=joined_lines,
            markdown=True,
            new_x=fpdf.XPos.LMARGIN,
            new_y=fpdf.YPos.NEXT,
        )
        pdf.ln()

    assert_pdf_equal(pdf, HERE / "multi_cell_markdown_link_cm.pdf", tmp_path)
