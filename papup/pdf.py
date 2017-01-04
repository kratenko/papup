"""
Created on Jan 3, 2017

@author: kratenko
"""

import io

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus.flowables import HRFlowable, PageBreak


def wrap_pil_image(pil_image):
    image_file = io.BytesIO()

    # save to open filehandle, so specifying the expected format is required
    pil_image.save(image_file, format='PNG')
    return image_file


def build_pdf(file, name):
    pdfmetrics.registerFont(TTFont('DejaVuSansMono', 'DejaVuSansMono.ttf'))

    doc = SimpleDocTemplate(name, pagesize=A4,
                            rightMargin=1 * cm, leftMargin=1 * cm,
                            topMargin=1 * cm, bottomMargin=1 * cm)

    style1 = ParagraphStyle("Mono1", fontName="DejaVuSansMono")

    story = []
    for page in file.pages:
        for line in page.page_legend:
            story.append(Paragraph(line, style1))
        story.append(
            HRFlowable(width="100%", thickness=1, lineCap='square', color="black",))
        story.append(Spacer(width=0.5 * cm, height=0.5 * cm))
        story.append(Image(wrap_pil_image(page.page_image)))
        story.append(PageBreak())
    doc.build(story)
