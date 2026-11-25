"""A4 PDF rendering for editable complaint drafts using ReportLab."""

from html import escape
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer


class _NumberedCanvas(canvas.Canvas):
    """Draws 'Page X of Y' and draft disclaimer footer on every A4 page."""

    def __init__(self, *args, case_reference: str = "", doc_title: str = "", **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states: list[dict] = []
        self._case_reference = case_reference
        self._doc_title = doc_title

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_chrome(num_pages)
            super().showPage()
        super().save()

    def _draw_chrome(self, page_count: int) -> None:
        width, height = A4
        self.saveState()

        # Header band
        self.setFont("Helvetica-Bold", 8.5)
        self.setFillColor(colors.HexColor("#101C35"))
        self.drawString(20 * mm, height - 13 * mm, "FINTRACE — DOCUMENT & COMPLAINT ASSISTANT")
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawRightString(width - 20 * mm, height - 13 * mm, f"Case Ref: {self._case_reference}")
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.line(20 * mm, height - 15.5 * mm, width - 20 * mm, height - 15.5 * mm)

        # Footer disclaimer + Page X of Y
        self.line(20 * mm, 16 * mm, width - 20 * mm, 16 * mm)
        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor("#B45309"))
        self.drawString(
            20 * mm,
            11.5 * mm,
            "DRAFT — Review all details before submitting to the relevant authority. FINTRACE does not submit complaints.",
        )
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawRightString(
            width - 20 * mm,
            11.5 * mm,
            f"Page {self._pageNumber} of {page_count}",
        )
        self.restoreState()


def render_draft_pdf(
    *,
    case_reference: str,
    title: str,
    recipient: str,
    subject: str,
    content: str,
    attachments: list[dict] | None = None,
) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=21 * mm,
        bottomMargin=22 * mm,
        title=title,
    )

    styles = getSampleStyleSheet()
    draft_banner_style = ParagraphStyle(
        "DraftBanner",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#92400E"),
        backColor=colors.HexColor("#FFFBEB"),
        borderPadding=6,
        spaceAfter=8,
    )
    heading_style = ParagraphStyle(
        "DocHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12.5,
        leading=16,
        textColor=colors.HexColor("#101C35"),
        spaceAfter=4,
    )
    meta_style = ParagraphStyle(
        "DocMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#172033"),
        spaceAfter=3,
    )
    body_style = ParagraphStyle(
        "DocBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.8,
        leading=14,
        textColor=colors.HexColor("#172033"),
        spaceAfter=4,
    )
    section_heading_style = ParagraphStyle(
        "DocSectionHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#101C35"),
        spaceBefore=6,
        spaceAfter=2,
    )

    story = [
        Paragraph(
            "DRAFT — Please review all information before submitting this document to the relevant authority.",
            draft_banner_style,
        ),
        Paragraph(escape(title), heading_style),
        Paragraph(f"<b>To:</b><br/>{escape(recipient).replace(chr(10), '<br/>')}", meta_style),
        Paragraph(f"<b>Subject:</b> {escape(subject)}", meta_style),
        Spacer(1, 3 * mm),
        HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#CBD5E1")),
        Spacer(1, 3 * mm),
    ]

    for raw_line in content.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            story.append(Spacer(1, 2.2 * mm))
            continue
        if stripped.startswith("DRAFT —"):
            continue
        # Emphasize numbered section headers (e.g., "1. COMPLAINANT DETAILS")
        is_section = len(stripped) < 75 and (
            (stripped[0].isdigit() and ". " in stripped[:5] and stripped.split(". ", 1)[1].isupper())
            or stripped.startswith("SUBJECT:")
        )
        safe_line = escape(raw_line).replace("  ", "&nbsp;&nbsp;")
        story.append(Paragraph(safe_line, section_heading_style if is_section else body_style))

    if attachments:
        story.append(Spacer(1, 4 * mm))
        story.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#CBD5E1")))
        story.append(Paragraph("ATTACHMENT CHECKLIST (FOR COMPLAINANT REVIEW)", section_heading_style))
        for item in attachments:
            status_label = "Available in case" if item.get("available") else "Pending / attach separately"
            story.append(
                Paragraph(
                    f"[&nbsp;&nbsp;] {escape(str(item.get('label', '')))} — <i>{escape(status_label)}</i>",
                    body_style,
                )
            )

    doc.build(
        story,
        canvasmaker=lambda *args, **kwargs: _NumberedCanvas(
            *args, case_reference=case_reference, doc_title=title, **kwargs
        ),
    )
    return buffer.getvalue()
