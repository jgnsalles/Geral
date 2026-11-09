"""Utilitarios para montar o relatorio em PDF (reportlab) a partir das tabelas Markdown geradas pelas analises."""
import re, pathlib
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FD = '/usr/share/fonts/truetype/dejavu/'
pdfmetrics.registerFont(TTFont('DejaVu', FD + 'DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DejaVu-Bold', FD + 'DejaVuSans-Bold.ttf'))
pdfmetrics.registerFont(TTFont('DejaVu-Oblique', FD + 'DejaVuSans.ttf'))
from reportlab.lib.fonts import addMapping
addMapping('DejaVu', 0, 0, 'DejaVu'); addMapping('DejaVu', 1, 0, 'DejaVu-Bold'); addMapping('DejaVu', 0, 1, 'DejaVu-Oblique')

INK, MUTED, ACCENT, RULE, SOFT = colors.HexColor('#1f2328'), colors.HexColor('#57606a'), colors.HexColor('#1f4e79'), colors.HexColor('#d0d7de'), colors.HexColor('#f3f6f9')
WARN = colors.HexColor('#fff4e5')
ss = getSampleStyleSheet()
S = {
    'title': ParagraphStyle('t', fontName='DejaVu-Bold', fontSize=20, leading=24, textColor=INK, spaceAfter=6),
    'subtitle': ParagraphStyle('st', fontName='DejaVu', fontSize=11, leading=15, textColor=MUTED, spaceAfter=14),
    'h1': ParagraphStyle('h1', fontName='DejaVu-Bold', fontSize=15, leading=19, textColor=ACCENT, spaceBefore=10, spaceAfter=6),
    'h2': ParagraphStyle('h2', fontName='DejaVu-Bold', fontSize=11.5, leading=15, textColor=INK, spaceBefore=8, spaceAfter=4),
    'p': ParagraphStyle('p', fontName='DejaVu', fontSize=9.3, leading=13.2, textColor=INK, spaceAfter=5),
    'small': ParagraphStyle('s', fontName='DejaVu', fontSize=7.8, leading=10.5, textColor=MUTED, spaceAfter=4),
    'bullet': ParagraphStyle('b', fontName='DejaVu', fontSize=9.3, leading=13.2, textColor=INK, leftIndent=12, bulletIndent=2, spaceAfter=2),
    'cell': ParagraphStyle('c', fontName='DejaVu', fontSize=7.4, leading=9.2, textColor=INK),
    'cellb': ParagraphStyle('cb', fontName='DejaVu-Bold', fontSize=7.4, leading=9.2, textColor=INK),
    'warn': ParagraphStyle('w', fontName='DejaVu', fontSize=9, leading=12.5, textColor=INK, backColor=WARN, borderPadding=6, spaceBefore=4, spaceAfter=10),
}


def md_inline(s):
    s = s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)', r'<i>\1</i>', s)
    s = re.sub(r'`(.+?)`', r'\1', s)
    return s


def P(text, style='p'):
    return Paragraph(md_inline(text), S[style])


def bullets(items):
    return [Paragraph(md_inline(t), S['bullet'], bulletText='•') for t in items]


def md_tables(path):
    """Devolve lista de (titulo_mais_proximo, linhas) para cada tabela Markdown do arquivo."""
    lines = pathlib.Path(path).read_text().splitlines()
    out, head, i = [], '', 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith('#'):
            head = ln.lstrip('#').strip()
        if ln.startswith('|') and i + 1 < len(lines) and re.match(r'^\|[\s:|-]+\|$', lines[i + 1].strip()):
            rows = [ln]
            j = i + 2
            while j < len(lines) and lines[j].startswith('|'):
                rows.append(lines[j]); j += 1
            cells = [[c.strip() for c in r.strip().strip('|').split('|')] for r in rows]
            out.append((head, cells)); i = j; continue
        i += 1
    return out


def find_table(path, contains, n=0):
    ts = [t for h, t in md_tables(path) if contains.lower() in h.lower()]
    return ts[n] if len(ts) > n else None


def table(cells, widths=None, max_rows=None, first_bold=False, width=17.6 * cm, header_bg=ACCENT):
    if cells is None: return P('(tabela não disponível)', 'small')
    rows = cells[: (max_rows + 1) if max_rows else None]
    data = []
    for k, r in enumerate(rows):
        st = S['cellb'] if k == 0 else S['cell']
        data.append([Paragraph(md_inline(c) if k else f'<font color="white">{md_inline(c)}</font>', st if not (first_bold and j == 0 and k) else S['cellb'])
                     for j, c in enumerate(r)])
    ncol = len(rows[0])
    if widths is None:
        first = min(5.2 * cm, width * 0.32) if ncol > 3 else width / ncol
        widths = [first] + [(width - first) / (ncol - 1)] * (ncol - 1) if ncol > 1 else [width]
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), header_bg), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, SOFT]), ('LINEBELOW', (0, 0), (-1, -1), 0.25, RULE),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5), ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 3), ('RIGHTPADDING', (0, 0), (-1, -1), 3)]))
    return t


def img(path, width=17.6 * cm):
    from PIL import Image as PI
    w, h = PI.open(path).size
    return Image(str(path), width=width, height=width * h / w)


def build(path, story, title):
    def deco(c, doc):
        c.saveState(); c.setFont('DejaVu', 7.5); c.setFillColor(MUTED)
        c.drawString(1.7 * cm, 1.0 * cm, title)
        c.drawRightString(A4[0] - 1.7 * cm, 1.0 * cm, f'{doc.page}')
        c.restoreState()
    doc = SimpleDocTemplate(str(path), pagesize=A4, leftMargin=1.7 * cm, rightMargin=1.7 * cm, topMargin=1.6 * cm, bottomMargin=1.6 * cm,
                            title=title, author='Price Tracker')
    doc.build(story, onFirstPage=deco, onLaterPages=deco)
