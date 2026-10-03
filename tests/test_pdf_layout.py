"""PDF layout inspection: two-column detection on hand-built PDFs."""

import unittest

from app.services.parser import inspect_layout


def build_pdf(columns: list[tuple[int, list[str]]]) -> bytes:
    """Build a one-page PDF with text lines placed at the given x positions."""
    ops = ["BT", "/F1 10 Tf"]
    for x, lines in columns:
        for i, line in enumerate(lines):
            ops.append(f"1 0 0 1 {x} {750 - i * 14} Tm ({line}) Tj")
    ops.append("ET")
    stream = "\n".join(ops).encode("latin-1")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = b"%PDF-1.4\n"
    offsets = []
    for n, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{n} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    out += b"".join(f"{o:010d} 00000 n \n".encode() for o in offsets)
    out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode()
    return out


LEFT = [f"Left column skill item number {i}" for i in range(30)]
RIGHT = [f"Right column experience line {i}" for i in range(30)]


class TestPdfLayout(unittest.TestCase):
    def test_two_columns_detected(self):
        layout = inspect_layout(build_pdf([(40, LEFT), (330, RIGHT)]), "resume.pdf")
        self.assertEqual(layout.pages, 1)
        self.assertTrue(layout.multi_column)

    def test_single_column_not_flagged(self):
        layout = inspect_layout(build_pdf([(40, LEFT + RIGHT[:20])]), "resume.pdf")
        self.assertFalse(layout.multi_column)
        self.assertEqual((layout.tables, layout.images), (0, 0))


if __name__ == "__main__":
    unittest.main()
