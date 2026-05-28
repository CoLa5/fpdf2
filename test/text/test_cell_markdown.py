from pathlib import Path

import pytest

from fpdf import FPDF, FPDFException
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent
FONTS_DIR = HERE.parent / "fonts"


def test_cell_markdown(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=32)
    pdf.cell(text="**Lorem** __ipsum__ --dolor-- ~~sit~~", markdown=True)
    assert_pdf_equal(pdf, HERE / "cell_markdown.pdf", tmp_path)


def test_cell_markdown_escaped(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=40)
    pdf.cell(text="**Lo\\rem** \\__Ipsum\\__ \\\\--dolor\\\\--", markdown=True)
    pdf.ln()
    pdf.cell(text="\\****BOLD**\\**", markdown=True)
    assert_pdf_equal(pdf, HERE / "cell_markdown_escaped.pdf", tmp_path)


def test_cell_markdown_bold_italic(tmp_path):
    # issue 1094
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=60)
    pdf.cell(text="**__Lorem --Ipsum--__**", markdown=True)
    assert_pdf_equal(pdf, HERE / "cell_markdown_bold_italic.pdf", tmp_path)


def test_cell_markdown_bold_italic_escaped(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=40)
    pdf.cell(text="**__Lorem \\--Ipsum\\--__**", markdown=True)
    assert_pdf_equal(pdf, HERE / "cell_markdown_bold_italic_escaped.pdf", tmp_path)


def test_cell_markdown_with_ttf_fonts(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("Roboto", "", FONTS_DIR / "Roboto-Regular.ttf")
    pdf.add_font("Roboto", "B", FONTS_DIR / "Roboto-Bold.ttf")
    pdf.add_font("Roboto", "I", FONTS_DIR / "Roboto-Italic.ttf")
    pdf.set_font("Roboto", size=60)
    pdf.cell(text="**Lorem** __Ipsum__ --dolor--", markdown=True)
    assert_pdf_equal(pdf, HERE / "cell_markdown_with_ttf_fonts.pdf", tmp_path)


def test_cell_markdown_with_ttf_fonts_escaped(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("Roboto", "", FONTS_DIR / "Roboto-Regular.ttf")
    pdf.add_font("Roboto", "B", FONTS_DIR / "Roboto-Bold.ttf")
    pdf.add_font("Roboto", "I", FONTS_DIR / "Roboto-Italic.ttf")
    pdf.set_font("Roboto", size=40)
    pdf.cell(text="**Lo\\rem** \\__Ipsum\\__ \\\\--dolor\\\\--", markdown=True)
    assert_pdf_equal(pdf, HERE / "cell_markdown_with_ttf_fonts_escaped.pdf", tmp_path)


def test_cell_markdown_missing_ttf_font():
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font(fname=FONTS_DIR / "Roboto-Regular.ttf")
    pdf.set_font("Roboto-Regular", size=60)
    with pytest.raises(FPDFException) as error:
        pdf.cell(text="**Lorem Ipsum**", markdown=True)
    expected_msg = "Undefined font: roboto-regularB - Use built-in fonts or FPDF.add_font() beforehand"
    assert str(error.value) == expected_msg


def test_cell_markdown_bleeding(tmp_path):  # issue 241
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=60)
    pdf.cell(text="**Lorem Ipsum dolor**", markdown=True, new_x="LMARGIN", new_y="NEXT")
    assert pdf.font_style == ""
    pdf.cell(text="No Markdown", markdown=False, new_x="LMARGIN", new_y="NEXT")
    pdf.cell(text="--Lorem Ipsum dolor--", markdown=True, new_x="LMARGIN", new_y="NEXT")
    assert pdf.font_style == ""
    pdf.cell(text="No Markdown", markdown=False, new_x="LMARGIN", new_y="NEXT")
    pdf.cell(text="__Lorem Ipsum dolor__", markdown=True, new_x="LMARGIN", new_y="NEXT")
    assert pdf.font_style == ""
    pdf.cell(text="No Markdown", markdown=False, new_x="LMARGIN", new_y="NEXT")
    assert_pdf_equal(pdf, HERE / "cell_markdown_bleeding.pdf", tmp_path)


def test_cell_markdown_right_aligned(tmp_path):  # issue 333
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("Roboto", fname=FONTS_DIR / "Roboto-Regular.ttf")
    pdf.add_font("Roboto", style="B", fname=FONTS_DIR / "Roboto-Bold.ttf")
    pdf.set_font("Roboto", size=60)
    pdf.cell(
        0,
        9,
        "**X** **X** **X** **X** **X** **X** **X** **X** **X**",
        markdown=True,
        align="R",
    )
    assert_pdf_equal(pdf, HERE / "cell_markdown_right_aligned.pdf", tmp_path)
