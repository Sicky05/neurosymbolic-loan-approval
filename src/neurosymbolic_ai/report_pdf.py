"""Esportazione locale del risultato, senza ricalcolare la valutazione."""

from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape


def esporta_pdf(percorso, risultato):
    """Scrive il risultato e la motivazione originale in un PDF A4 multipagina.

    La dipendenza opzionale viene caricata solo all'esportazione. Il documento
    viene composto in memoria prima di aprire il file di destinazione.
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    import reportlab

    # Vera è incluso in ReportLab: accenti ed euro senza font di sistema.
    font = Path(reportlab.__file__).parent / 'fonts' / 'Vera.ttf'
    pdfmetrics.registerFont(TTFont('PrestitiVera', str(font)))
    styles = getSampleStyleSheet()
    for style in styles.byName.values():
        style.fontName = 'PrestitiVera'
    styles['BodyText'].leading = 16
    styles['BodyText'].splitLongWords = True
    styles['Title'].textColor = colors.HexColor('#18354a')

    def paragraph(value, style='BodyText'):
        return Paragraph(escape(str(value)).replace('\n', '<br/>'), styles[style])

    reddito = risultato['reddito']
    story = [paragraph('Valutazione prestito', 'Title'), Spacer(1, .5 * cm)]
    for label, value in (
        ('Pratica', risultato['sid']),
        ('Rischio finanziario', risultato['rischio']),
        ('Reddito dichiarato', 'Non disponibile' if reddito is None else '{} €'.format(reddito)),
        ('Verdetto', risultato['verdetto']),
    ):
        story.append(paragraph('{}: {}'.format(label, value)))
    story.extend([
        Spacer(1, .5 * cm), paragraph('Motivazione XAI', 'Heading2'),
        paragraph(risultato['motivazione']), Spacer(1, .5 * cm),
        paragraph('La motivazione è quella prodotta dalle regole del sistema esperto; '
                  'non spiega i singoli pesi della rete neurale.'),
        paragraph('Prototipo didattico: le predizioni non sono una misura validata '
                  'di affidabilità creditizia né uno strumento per decisioni reali.'),
    ])

    def footer(canvas, doc):
        canvas.setFont('PrestitiVera', 9)
        canvas.drawRightString(A4[0] - 2 * cm, cm, 'Pagina {}'.format(doc.page))

    buffer = BytesIO()
    SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2 * cm, leftMargin=2 * cm,
                      topMargin=2 * cm, bottomMargin=2 * cm,
                      title='Valutazione prestito').build(
                          story, onFirstPage=footer, onLaterPages=footer)
    Path(percorso).write_bytes(buffer.getvalue())
