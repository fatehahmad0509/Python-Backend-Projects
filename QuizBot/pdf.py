from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os, re

def _register_fonts():
    import reportlab
    font_dir = os.path.join(os.path.dirname(reportlab.__file__), "fonts")
    pdfmetrics.registerFont(TTFont("Vera", os.path.join(font_dir, "Vera.ttf")))
    pdfmetrics.registerFont(TTFont("Vera-Bold", os.path.join(font_dir, "VeraBd.ttf")))

_register_fonts()

def _superscript(text: str) -> str:
    return re.sub(r'\^(-?\d+)', lambda m: '<super>' + m.group(1) + '</super>', text)

def create_pdf(questions: list[dict], grade: str = "", subject: str = "", topic: str = "", difficulty: str = "", school: str = "") -> tuple[str, str]:
    filename = ("quiz_" + grade + "_" + subject + "_" + topic + ".pdf").replace(" ", "_")
    doc = SimpleDocTemplate(filename, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    title_style = ParagraphStyle("title", fontName="Vera-Bold", fontSize=14,
                                  alignment=TA_CENTER, spaceAfter=4)
    sub_style   = ParagraphStyle("sub",   fontName="Vera",      fontSize=10,
                                  alignment=TA_CENTER, spaceAfter=12, textColor="grey")
    q_style     = ParagraphStyle("q",     fontName="Vera-Bold", fontSize=11,
                                  spaceAfter=4, leading=16)
    opt_style   = ParagraphStyle("opt",   fontName="Vera",      fontSize=10,
                                  leftIndent=12, spaceAfter=2, leading=14)

    elements = []
    if school:
        elements.append(Paragraph(school.upper(), title_style))
    elements.append(Paragraph("Grade " + grade + " | " + subject + " | " + topic + " | " + difficulty, sub_style))

    answers = []
    for i, q in enumerate(questions, 1):
        block = [
            Paragraph(str(i) + ") " + _superscript(q['question']), q_style),
            Paragraph("A) " + _superscript(q['A']), opt_style),
            Paragraph("B) " + _superscript(q['B']), opt_style),
            Paragraph("C) " + _superscript(q['C']), opt_style),
            Paragraph("D) " + _superscript(q['D']), opt_style),
            Spacer(1, 10),
        ]
        elements.append(KeepTogether(block))
        answers.append(str(i) + ") " + q['answer'])

    doc.build(elements)
    return filename, "\n".join(answers)
