"""
Convert Markdown to Word Document
"""
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import re

def markdown_to_word(md_file, output_file):
    """Convert markdown file to Word document"""
    
    # Read markdown file
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Create Word document
    doc = Document()
    
    # Set default font
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Calibri'
    font.size = Pt(11)
    
    # Process markdown line by line
    lines = md_content.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Skip empty lines
        if not line.strip():
            i += 1
            continue
        
        # Handle headers
        if line.startswith('# '):
            p = doc.add_heading(line[2:].strip(), level=1)
        elif line.startswith('## '):
            p = doc.add_heading(line[3:].strip(), level=2)
        elif line.startswith('### '):
            p = doc.add_heading(line[4:].strip(), level=3)
        elif line.startswith('#### '):
            p = doc.add_heading(line[5:].strip(), level=4)
        
        # Handle horizontal rules
        elif line.strip() == '---':
            doc.add_paragraph('_' * 50)
        
        # Handle bullet lists
        elif line.strip().startswith('- ') or line.strip().startswith('* '):
            text = line.strip()[2:]
            # Remove markdown formatting
            text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
            text = re.sub(r'`(.*?)`', r'\1', text)  # Code
            doc.add_paragraph(text, style='List Bullet')
        
        # Handle numbered lists
        elif re.match(r'^\d+\.', line.strip()):
            text = re.sub(r'^\d+\.\s*', '', line.strip())
            text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
            text = re.sub(r'`(.*?)`', r'\1', text)
            doc.add_paragraph(text, style='List Number')
        
        # Handle code blocks
        elif line.strip().startswith('```'):
            i += 1
            code_lines = []
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            if code_lines:
                code_text = '\n'.join(code_lines)
                p = doc.add_paragraph(code_text)
                p.style = 'Normal'
                for run in p.runs:
                    run.font.name = 'Courier New'
                    run.font.size = Pt(9)
        
        # Handle tables
        elif '|' in line and i + 1 < len(lines) and '|' in lines[i + 1]:
            # Parse table
            table_lines = []
            while i < len(lines) and '|' in lines[i]:
                table_lines.append(lines[i])
                i += 1
            i -= 1  # Step back one
            
            if len(table_lines) >= 2:
                # Parse header
                headers = [cell.strip() for cell in table_lines[0].split('|') if cell.strip()]
                
                # Parse rows (skip separator line)
                rows = []
                for line in table_lines[2:]:
                    row = [cell.strip() for cell in line.split('|') if cell.strip()]
                    if row:
                        rows.append(row)
                
                # Create table
                if rows:
                    table = doc.add_table(rows=len(rows) + 1, cols=len(headers))
                    table.style = 'Light Grid Accent 1'
                    
                    # Add headers
                    for j, header in enumerate(headers):
                        cell = table.rows[0].cells[j]
                        cell.text = header
                        for paragraph in cell.paragraphs:
                            for run in paragraph.runs:
                                run.bold = True
                    
                    # Add rows
                    for i, row in enumerate(rows):
                        for j, cell_text in enumerate(row):
                            if j < len(table.rows[i + 1].cells):
                                # Remove markdown formatting
                                cell_text = re.sub(r'\*\*(.*?)\*\*', r'\1', cell_text)
                                cell_text = re.sub(r'`(.*?)`', r'\1', cell_text)
                                table.rows[i + 1].cells[j].text = cell_text
                    
                    doc.add_paragraph()  # Add space after table
        
        # Handle regular paragraphs
        else:
            # Remove markdown formatting
            text = line.strip()
            
            # Skip if empty
            if not text:
                i += 1
                continue
            
            # Bold and code
            text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
            text = re.sub(r'`(.*?)`', r'\1', text)
            
            # Add paragraph
            p = doc.add_paragraph(text)
        
        i += 1
    
    # Save document
    doc.save(output_file)
    print(f"✅ Document saved: {output_file}")

if __name__ == "__main__":
    md_file = "AI_Testing_Cost_Analysis.md"
    word_file = "AI_Testing_Cost_Analysis.docx"
    
    print(f"Converting {md_file} to {word_file}...")
    markdown_to_word(md_file, word_file)
    print(f"\n✅ Conversion complete!")
    print(f"📄 Word document: {word_file}")
