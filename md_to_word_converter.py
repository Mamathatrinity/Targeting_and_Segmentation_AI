"""
Simple and robust Markdown to Word converter for Project Analysis
"""
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
import re

def add_formatted_heading(doc, text, level=1):
    """Add a formatted heading"""
    heading = doc.add_heading(text, level=level)
    if heading.runs:
        heading.runs[0].font.color.rgb = RGBColor(0, 70, 135)
    return heading

def parse_markdown_table(lines, start_idx):
    """Parse a markdown table from lines"""
    table_lines = []
    i = start_idx
    
    # Collect all table lines
    while i < len(lines) and lines[i].strip().startswith('|'):
        table_lines.append(lines[i].strip())
        i += 1
    
    if len(table_lines) < 3:  # Need at least header, separator, and one row
        return None, start_idx + 1
    
    # Parse header
    header_line = table_lines[0]
    headers = [cell.strip() for cell in header_line.split('|')[1:-1]]
    
    # Parse data rows (skip separator line at index 1)
    rows = []
    for line in table_lines[2:]:
        cells = [cell.strip() for cell in line.split('|')[1:-1]]
        rows.append(cells)
    
    return {'headers': headers, 'rows': rows}, i

def add_table_to_doc(doc, table_data):
    """Add a formatted table to the document"""
    headers = table_data['headers']
    rows = table_data['rows']
    
    # Create table
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = 'Light Grid Accent 1'
    
    # Add headers with formatting
    header_cells = table.rows[0].cells
    for i, header_text in enumerate(headers):
        # Remove markdown bold markers
        clean_text = header_text.replace('**', '')
        header_cells[i].text = clean_text
        
        # Format header cell
        for paragraph in header_cells[i].paragraphs:
            for run in paragraph.runs:
                run.font.bold = True
                run.font.size = Pt(10)
                run.font.color.rgb = RGBColor(255, 255, 255)
        
        # Set background color
        shading_elm = header_cells[i]._element.get_or_add_tcPr()
        from lxml import etree
        shading = etree.SubElement(shading_elm, qn('w:shd'))
        shading.set(qn('w:fill'), '4472C4')
    
    # Add data rows
    for row_idx, row_data in enumerate(rows, start=1):
        cells = table.rows[row_idx].cells
        for col_idx, cell_text in enumerate(row_data):
            # Check if text should be bold
            is_bold = '**' in cell_text
            clean_text = cell_text.replace('**', '')
            cells[col_idx].text = clean_text
            
            # Apply formatting
            for paragraph in cells[col_idx].paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(9)
                    if is_bold:
                        run.font.bold = True

def convert_markdown_to_word(md_file, docx_file):
    """Main conversion function"""
    print(f"📄 Reading {md_file}...")
    
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create Word document
    doc = Document()
    
    # Set page margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)
    
    # Set default font
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Calibri'
    font.size = Pt(11)
    
    lines = content.split('\n')
    i = 0
    
    print("🔄 Converting content...")
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            i += 1
            continue
        
        # Handle headings
        if stripped.startswith('#### '):
            add_formatted_heading(doc, stripped[5:], level=4)
            i += 1
        elif stripped.startswith('### '):
            add_formatted_heading(doc, stripped[4:], level=3)
            i += 1
        elif stripped.startswith('## '):
            add_formatted_heading(doc, stripped[3:], level=2)
            i += 1
        elif stripped.startswith('# '):
            add_formatted_heading(doc, stripped[2:], level=1)
            i += 1
        
        # Handle tables
        elif stripped.startswith('|'):
            table_data, new_i = parse_markdown_table(lines, i)
            if table_data:
                add_table_to_doc(doc, table_data)
                doc.add_paragraph()  # Add spacing after table
                i = new_i
            else:
                i += 1
        
        # Handle lists
        elif stripped.startswith('- ') or stripped.startswith('* '):
            text = stripped[2:].replace('**', '')
            doc.add_paragraph(text, style='List Bullet')
            i += 1
        
        elif re.match(r'^\d+\.\s', stripped):
            text = re.sub(r'^\d+\.\s+', '', stripped).replace('**', '')
            doc.add_paragraph(text, style='List Number')
            i += 1
        
        # Handle regular paragraphs
        else:
            text = stripped.replace('**', '')
            if text:
                p = doc.add_paragraph(text)
                # Check for description paragraphs (italic)
                if 'Description:' in text:
                    for run in p.runs:
                        run.font.italic = True
                        run.font.color.rgb = RGBColor(60, 60, 60)
            i += 1
    
    # Save document
    print(f"💾 Saving {docx_file}...")
    doc.save(docx_file)
    print(f"✅ Successfully created: {docx_file}")
    print(f"📊 Document contains comprehensive cost analysis with all tables and descriptions")

if __name__ == "__main__":
    md_file = "Project_Testing_Analysis_HCP.md"
    docx_file = "Project_Testing_Analysis_HCP.docx"
    
    try:
        convert_markdown_to_word(md_file, docx_file)
        print(f"\n✨ Conversion complete!")
        print(f"📍 Location: {docx_file}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
