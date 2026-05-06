from pathlib import Path

import pytest

from fpdf import FPDF
from fpdf.drawing_primitives import DeviceGray
from test.conftest import assert_pdf_equal

HERE = Path(__file__).resolve().parent


@pytest.mark.parametrize(
    ["head", "foot"],
    (
        (True, False),
        (False, True),
        (True, True),
    ),
)
def test_header_footer_not_leaking_into_page(head, foot, tmp_path):
    class PDF(FPDF):
        def header(self):
            if head:
                pdf.set_font(family="times", size=12)
                pdf.set_text_color("#0000ff")
                pdf.set_stretching(200)
                pdf.set_char_spacing(0.33)
                pdf.set_dash_pattern(dash=0.5, gap=0.25, phase=0.2)
                self.set_y(2)
                self.cell(text=f"Header {self.page_no()}")
                self.set_y(self.t_margin)

        def footer(self):
            if foot:
                pdf.set_font(family="times", size=12)
                pdf.set_text_color("#ff0000")
                pdf.set_stretching(300)
                pdf.set_char_spacing(0.66)
                pdf.set_dash_pattern(dash=0.25, gap=0.5, phase=0.2)
                self.set_y(-15)
                self.cell(text=f"Footer {self.page_no()}")

    pdf = PDF()
    pdf.set_font(family="helvetica", size=14)

    for _ in range(2):
        pdf.add_page()
        assert pdf.char_spacing == 0
        assert pdf.dash_pattern == {"dash": 0, "gap": 0, "phase": 0}
        assert pdf.font_family == "helvetica"
        assert pdf.font_size_pt == 14
        assert pdf.font_stretching == 100
        assert pdf.text_color == DeviceGray(0)
        pdf.multi_cell(w=0, text="\n".join(f"Line {i + 1}" for i in range(21)))

    file_parts = []
    if head:
        file_parts.append("header")
    if foot:
        file_parts.append("footer")
    file_parts.append("not_leaking_into_page.pdf")
    filename = "_".join(file_parts)
    assert_pdf_equal(pdf, HERE / filename, tmp_path)
