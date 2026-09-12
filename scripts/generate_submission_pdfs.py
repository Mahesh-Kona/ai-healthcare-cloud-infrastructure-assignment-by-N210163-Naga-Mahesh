"""Generate polished submission PDFs from the project's Markdown reports."""

from pathlib import Path
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "submission"

REPORTS = [
    ("Architecture Document", ROOT / "docs" / "architecture.md", "Architecture_Document.pdf"),
    ("Security Report", ROOT / "docs" / "security-report.md", "Security_Report.pdf"),
    ("Incident Report", ROOT / "docs" / "incident-report.md", "Incident_Report.pdf"),
]

NAVY = colors.HexColor("#17324D")
TEAL = colors.HexColor("#087E8B")
SLATE = colors.HexColor("#425466")
PALE_BLUE = colors.HexColor("#EAF3F7")
PALE_TEAL = colors.HexColor("#E8F6F4")
LIGHT_GREY = colors.HexColor("#F4F6F8")
BORDER = colors.HexColor("#D7E0E7")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name="CoverTitle", parent=styles["Title"], fontName="Helvetica-Bold",
    fontSize=28, leading=34, textColor=NAVY, alignment=TA_CENTER, spaceAfter=12,
))
styles.add(ParagraphStyle(
    name="CoverSubtitle", parent=styles["Normal"], fontName="Helvetica",
    fontSize=12, leading=17, textColor=SLATE, alignment=TA_CENTER,
))
styles.add(ParagraphStyle(
    name="Section", parent=styles["Heading2"], fontName="Helvetica-Bold",
    fontSize=16, leading=20, textColor=NAVY, spaceBefore=14, spaceAfter=7,
))
styles.add(ParagraphStyle(
    name="Subsection", parent=styles["Heading3"], fontName="Helvetica-Bold",
    fontSize=11.5, leading=15, textColor=TEAL, spaceBefore=10, spaceAfter=4,
))
styles.add(ParagraphStyle(
    name="BodyProfessional", parent=styles["BodyText"], fontName="Helvetica",
    fontSize=9.5, leading=14, textColor=colors.HexColor("#263746"), spaceAfter=6,
))
styles.add(ParagraphStyle(
    name="BulletProfessional", parent=styles["BodyText"], fontName="Helvetica",
    fontSize=9.3, leading=13.5, leftIndent=15, firstLineIndent=-8,
    bulletIndent=4, textColor=colors.HexColor("#263746"), spaceAfter=3,
))
styles.add(ParagraphStyle(
    name="CodeProfessional", parent=styles["Code"], fontName="Courier",
    fontSize=7.2, leading=9.2, textColor=colors.HexColor("#25313B"),
    backColor=LIGHT_GREY, borderColor=BORDER, borderWidth=0.5,
    borderPadding=6, spaceBefore=4, spaceAfter=7,
))
styles.add(ParagraphStyle(
    name="SmallMeta", parent=styles["Normal"], fontName="Helvetica",
    fontSize=8.5, leading=12, textColor=SLATE, alignment=TA_CENTER,
))


def inline_markup(text: str) -> str:
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"`([^`]+)`", r"<font name='Courier'>\1</font>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", text)
    return text


class ArchitectureDiagram(Flowable):
    """Compact vector diagram for the primary architecture submission."""

    def __init__(self):
        super().__init__()
        self.width = 170 * mm
        self.height = 84 * mm

    def draw(self):
        canvas = self.canv
        canvas.setStrokeColor(BORDER)
        canvas.setFillColor(PALE_BLUE)
        canvas.roundRect(4 * mm, 48 * mm, 42 * mm, 22 * mm, 3 * mm, fill=1, stroke=1)
        canvas.setFillColor(PALE_TEAL)
        canvas.roundRect(58 * mm, 8 * mm, 105 * mm, 62 * mm, 3 * mm, fill=1, stroke=1)

        def box(x, y, w, h, label, fill=colors.white):
            canvas.setFillColor(fill)
            canvas.setStrokeColor(TEAL)
            canvas.roundRect(x * mm, y * mm, w * mm, h * mm, 2 * mm, fill=1, stroke=1)
            canvas.setFillColor(NAVY)
            canvas.setFont("Helvetica-Bold", 8)
            canvas.drawCentredString((x + w / 2) * mm, (y + h / 2 + 1) * mm, label)

        box(9, 53, 32, 12, "Public API")
        box(67, 52, 27, 12, "PostgreSQL")
        box(103, 52, 25, 12, "Redis Queue")
        box(137, 52, 20, 12, "Worker")
        box(67, 30, 27, 12, "AI Mock")
        box(103, 30, 25, 12, "EHR Mock")
        box(121, 10, 36, 12, "Prometheus / Grafana")

        canvas.setStrokeColor(SLATE)
        canvas.setLineWidth(1)
        arrows = [((41, 59), (67, 59)), ((94, 59), (103, 59)), ((128, 59), (137, 59)),
                  ((148, 52), (148, 42)), ((137, 52), (116, 42)), ((137, 52), (116, 36)),
                  ((121, 16), (116, 30))]
        for (x1, y1), (x2, y2) in arrows:
            canvas.line(x1 * mm, y1 * mm, x2 * mm, y2 * mm)
            canvas.circle(x2 * mm, y2 * mm, 0.8 * mm, fill=1, stroke=0)

        canvas.setFillColor(NAVY)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.drawString(8 * mm, 74 * mm, "PUBLIC TRUST ZONE")
        canvas.drawString(61 * mm, 74 * mm, "PRIVATE SERVICE ZONE")


class SubmissionDoc(BaseDocTemplate):
    def __init__(self, filename, title):
        super().__init__(filename, pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm,
                         topMargin=20 * mm, bottomMargin=18 * mm, title=title, author="Cloud Infrastructure Simulation")
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="normal")
        self.addPageTemplates([PageTemplate(id="main", frames=frame, onPage=self._header_footer)])
        self.report_title = title

    def _header_footer(self, canvas, document):
        canvas.saveState()
        canvas.setStrokeColor(BORDER)
        canvas.line(18 * mm, 13 * mm, A4[0] - 18 * mm, 13 * mm)
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(SLATE)
        canvas.drawString(18 * mm, 8 * mm, "AI Healthcare Platform | Cloud Infrastructure Simulation")
        canvas.drawRightString(A4[0] - 18 * mm, 8 * mm, f"Page {document.page}")
        canvas.restoreState()


def cover(title):
    return [
        Spacer(1, 28 * mm),
        Paragraph("CLOUD INFRASTRUCTURE SIMULATION", styles["SmallMeta"]),
        Spacer(1, 10 * mm),
        Paragraph(title, styles["CoverTitle"]),
        Paragraph("Secure, Reliable &amp; Scalable Infrastructure for an AI Healthcare Platform", styles["CoverSubtitle"]),
        Spacer(1, 20 * mm),
        Table([[Paragraph("DEVSECOPS • CLOUD ENGINEERING • RELIABILITY • OPERATIONS", styles["SmallMeta"])]],
              colWidths=[170 * mm], style=TableStyle([
                  ("BACKGROUND", (0, 0), (-1, -1), PALE_BLUE),
                  ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
                  ("LEFTPADDING", (0, 0), (-1, -1), 8),
                  ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                  ("TOPPADDING", (0, 0), (-1, -1), 8),
                  ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
              ])),
        Spacer(1, 22 * mm),
        Paragraph("Prepared for project submission", styles["SmallMeta"]),
        Spacer(1, 8 * mm),
        Paragraph("N210163 | Naga Mahesh Kona", styles["SmallMeta"]),
        Paragraph("Rajiv Gandhi University of Knowledge Technologies, Nuzvid", styles["SmallMeta"]),
        Paragraph("Phone: 9133889049 | Email: n210163@rguktn.ac.in", styles["SmallMeta"]),
        Spacer(1, 8 * mm),
        Paragraph("Version 1.0 | September 2026", styles["SmallMeta"]),
        PageBreak(),
    ]


def parse_markdown(path, include_diagram=False):
    story = []
    lines = path.read_text(encoding="utf-8").splitlines()
    in_code = False
    code_lines = []
    paragraph = []

    def flush_paragraph():
        if paragraph:
            story.append(Paragraph(inline_markup(" ".join(paragraph)), styles["BodyProfessional"]))
            paragraph.clear()

    for line in lines:
        if line.startswith("```"):
            flush_paragraph()
            if in_code:
                if code_lines and not any("flowchart" in item for item in code_lines):
                    story.append(Paragraph(inline_markup("\n".join(code_lines)), styles["CodeProfessional"]))
                code_lines.clear()
                in_code = False
            else:
                in_code = True
            continue
        if in_code:
            code_lines.append(line)
            continue
        if not line.strip():
            flush_paragraph()
            continue
        if line.startswith("# "):
            flush_paragraph()
            continue
        if line.startswith("## "):
            flush_paragraph()
            heading = line[3:].strip()
            story.append(Paragraph(inline_markup(heading), styles["Section"]))
            if include_diagram and heading.lower() == "primary architecture diagram":
                story.append(ArchitectureDiagram())
                story.append(Spacer(1, 5 * mm))
            continue
        if line.startswith("### "):
            flush_paragraph()
            story.append(Paragraph(inline_markup(line[4:].strip()), styles["Subsection"]))
            continue
        if line.startswith("- "):
            flush_paragraph()
            story.append(Paragraph(inline_markup(line[2:].strip()), styles["BulletProfessional"], bulletText="•"))
            continue
        if re.match(r"^\d+\. ", line):
            flush_paragraph()
            item = re.sub(r"^\d+\. ", "", line)
            story.append(Paragraph(inline_markup(item), styles["BulletProfessional"]))
            continue
        if line.startswith("| "):
            flush_paragraph()
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if not all(set(cell) <= {"-", ":", " "} for cell in cells):
                story.append(Table([[Paragraph(inline_markup(cell), styles["BodyProfessional"]) for cell in cells]],
                                   colWidths=[170 * mm / len(cells)], style=TableStyle([
                                       ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GREY),
                                       ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
                                       ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                       ("LEFTPADDING", (0, 0), (-1, -1), 5),
                                       ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                                   ])))
            continue
        paragraph.append(line.strip())

    flush_paragraph()
    return story


def build_pdf(title, source, filename):
    OUTPUT.mkdir(exist_ok=True)
    document = SubmissionDoc(str(OUTPUT / filename), title)
    story = cover(title)
    story.extend(parse_markdown(source, include_diagram=title == "Architecture Document"))
    document.build(story)


if __name__ == "__main__":
    for title, source, filename in REPORTS:
        build_pdf(title, source, filename)
        print(f"Generated {OUTPUT / filename}")
