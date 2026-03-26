"""
Generates a Behovsvurdering PDF using the internal RAG answerer.
"""

import io
import re

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_CENTER

from src.api.dependencies import get_current_user
from src.db.database import get_db
from src.db.models import User
from src.rag.answer import get_answerer

router = APIRouter()


# Request schema

class BehovsvurderingFormData(BaseModel):
    typeAnlegg: str = ""
    typeAnleggAnnet: str = ""
    behovBeskrivelse: str = ""
    antallBrukere: str = ""
    kommunalePlanerBeskrivelse: str = ""
    avstandAndreAnlegg: str = ""
    avstandKm: str = ""
    kommune: str = ""
    innbyggertall: str = ""
    befolkningINeromraade: str = ""
    brukerBeskrivelse: str = ""
    idrettslag: str = ""
    antallMedlemmer: str = ""
    driftsansvarlig: str = ""
    driftsmodell: str = ""


# RAG query

def generate_behovsvurdering_text(form: BehovsvurderingFormData) -> str:
    """
    Build a query from the form data and run it through the RAG answerer.
    The answerer uses the local vector store (bestemmelser PDF) as context,
    so the output is grounded in the actual regulations.
    """
    type_anlegg = form.typeAnleggAnnet if form.typeAnlegg == "annet" else form.typeAnlegg

    question = f"""
Skriv en komplett Behovsvurdering for et idrettsanlegg basert på følgende informasjon.
Dokumentet skal dekke alle 8 påkrevde punkter i henhold til gjeldende bestemmelser.
Bruk en formell og saklig tone som passer for offentlige tilskuddssøknader. Svar på norsk bokmål.

Strukturer svaret med nummererte overskrifter slik:
1. Type anlegg
2. Behov (innhold og dimensjonering)
3. Vurdering i kommunens planer
4. Plassering relativt til andre anlegg
5. Innbyggertall og befolkningsdata
6. Beskrivelse av brukerne
7. Idrettslag og medlemstall
8. Driftsansvarlig

Informasjon om anlegget:
- Type anlegg: {type_anlegg}
- Behov og dimensjonering: {form.behovBeskrivelse} | Estimert antall brukere: {form.antallBrukere}
- Kommunale planer: {form.kommunalePlanerBeskrivelse}
- Avstand til andre anlegg: {form.avstandAndreAnlegg} | Nærmeste lignende anlegg: {form.avstandKm} km
- Kommune: {form.kommune} | Innbyggertall: {form.innbyggertall} | Befolkning i nedslagsfelt: {form.befolkningINeromraade}
- Brukerne: {form.brukerBeskrivelse}
- Idrettslag: {form.idrettslag} | Antall medlemmer: {form.antallMedlemmer}
- Driftsansvarlig: {form.driftsansvarlig} | Driftsmodell: {form.driftsmodell}
"""

    answerer = get_answerer()
    result = answerer.answer(question)
    return result["answer"]


# PDF builder

def build_pdf(text: str, kommune: str) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
    )

    styles = getSampleStyleSheet()

    style_title = ParagraphStyle(
        "DocTitle",
        parent=styles["Title"],
        fontSize=18,
        textColor=colors.HexColor("#1B2025"),
        spaceAfter=6,
        alignment=TA_CENTER,
    )
    style_subtitle = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontSize=11,
        textColor=colors.HexColor("#555555"),
        spaceAfter=20,
        alignment=TA_CENTER,
    )
    style_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=colors.HexColor("#1B2025"),
        spaceBefore=16,
        spaceAfter=4,
    )
    style_body = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=10,
        leading=15,
        textColor=colors.HexColor("#222222"),
        spaceAfter=8,
    )

    story = []

    story.append(Paragraph("Behovsvurdering", style_title))
    if kommune:
        story.append(Paragraph(f"Kommune: {kommune}", style_subtitle))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1B2025")))
    story.append(Spacer(1, 16))

    # Split on numbered headings
    sections = re.split(r'(?m)^(\d+\.\s+.+)$', text)

    if len(sections) <= 1:
        for line in text.split("\n"):
            line = line.strip()
            if line:
                story.append(Paragraph(line, style_body))
    else:
        if sections[0].strip():
            story.append(Paragraph(sections[0].strip(), style_body))

        it = iter(sections[1:])
        for heading in it:
            body = next(it, "")
            story.append(Paragraph(heading.strip(), style_heading))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")))
            story.append(Spacer(1, 4))
            for line in body.strip().split("\n"):
                line = line.strip()
                if line:
                    story.append(Paragraph(line, style_body))

    doc.build(story)
    return buffer.getvalue()


# Route

@router.post("/api/generate-pdf")
async def generate_pdf(
    form: BehovsvurderingFormData,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    text = generate_behovsvurdering_text(form)
    pdf_bytes = build_pdf(text, form.kommune)

    filename = f"behovsvurdering_{form.kommune or 'dokument'}.pdf".replace(" ", "_")

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
