# utils.py
from docx.oxml.ns import nsdecls
from docx.oxml import parse_xml
from docx.shared import RGBColor

def set_cell_background(cell, color):
    """Sets the background color of a Word document table cell."""
    shading_elm = parse_xml(r'<w:shd {} w:fill="{}"/>'.format(nsdecls('w'), color))
    cell._tc.get_or_add_tcPr().append(shading_elm)