import fitz  # PyMuPDF
import json
from collections import Counter

pdf_path = r'c:\Users\mv\Downloads\NBA User manual updated.pdf'
doc = fitz.open(pdf_path)

# Basic info
total_pages = len(doc)
print(f'=' * 100)
print(f'PDF ANALYSIS: NBA User Manual Updated')
print(f'=' * 100)
print(f'\n1. TOTAL PAGES: {total_pages}')
print(f'\n' + '=' * 100)

# Collect all headings and analyze structure
all_headings = []
page_details = []
colors_found = set()
fonts_found = set()

for page_num in range(total_pages):
    page = doc[page_num]
    
    # Get text with detailed formatting
    blocks = page.get_text('dict')['blocks']
    
    # Get images
    images = page.get_images()
    
    # Get drawings (shapes, lines, arrows)
    drawings = page.get_drawings()
    
    # Analyze text blocks
    page_headings = []
    page_fonts = []
    page_colors = []
    
    for block in blocks:
        if block.get('type') == 0:  # text block
            for line in block.get('lines', []):
                for span in line.get('spans', []):
                    size = span.get('size', 0)
                    font = span.get('font', '')
                    color = span.get('color', 0)
                    text_content = span.get('text', '').strip()
                    
                    # Track fonts and colors
                    if font:
                        fonts_found.add(f"{font} ({size:.1f}pt)")
                        page_fonts.append((font, size))
                    if color:
                        colors_found.add(f"#{color:06x}")
                        page_colors.append(color)
                    
                    # Identify headings (larger fonts or bold)
                    if text_content and len(text_content) > 3:
                        if size > 14 or 'Bold' in font or 'bold' in font.lower():
                            heading_info = {
                                'text': text_content,
                                'size': size,
                                'font': font,
                                'page': page_num + 1
                            }
                            page_headings.append(heading_info)
                            if size > 12:  # Major headings
                                all_headings.append(heading_info)
    
    # Get full text for content type analysis
    full_text = page.get_text()
    
    # Analyze content type
    has_bullets = '•' in full_text or '·' in full_text or chr(8226) in full_text
    has_numbers = any(f'{i}.' in full_text for i in range(1, 10))
    has_steps = 'step' in full_text.lower() or 'Step' in full_text
    
    page_info = {
        'page': page_num + 1,
        'headings': page_headings[:5],
        'images': len(images),
        'drawings': len(drawings),
        'has_bullets': has_bullets,
        'has_numbered_list': has_numbers,
        'has_steps': has_steps,
        'text_length': len(full_text),
        'unique_fonts': len(set(page_fonts)),
        'text_preview': full_text[:300].replace('\n', ' ').strip()
    }
    page_details.append(page_info)

# Print section headings
print('\n2. SECTION/CHAPTER HEADINGS (in order):')
print('=' * 100)
for i, heading in enumerate(all_headings[:50], 1):  # Limit to first 50 major headings
    page_num = heading['page']
    text = heading['text'][:80]
    size = heading['size']
    print(f"   Page {page_num:3d}: {text} (font size: {size:.1f}pt)")

# Layout analysis
print('\n\n3. OVERALL LAYOUT STYLE:')
print('=' * 100)
first_page = page_details[0]
if first_page['headings']:
    print(f"   - Cover page with title: {first_page['headings'][0]['text'][:60]}")
else:
    print(f"   - Cover page detected")

# Check for TOC
toc_pages = [p for p in page_details[:10] if 'table of contents' in p['text_preview'].lower() or 'contents' in p['text_preview'].lower()]
if toc_pages:
    print(f"   - Table of Contents found on page {toc_pages[0]['page']}")
else:
    print(f"   - No explicit Table of Contents detected")

# Determine format style
avg_images_per_page = sum(p['images'] for p in page_details) / len(page_details)
if avg_images_per_page > 0.5:
    print(f"   - Visual/Slide format (avg {avg_images_per_page:.1f} images per page)")
else:
    print(f"   - Text-heavy format (avg {avg_images_per_page:.1f} images per page)")

# Content type analysis
print('\n\n4. CONTENT TYPE BY MAJOR SECTIONS:')
print('=' * 100)
section_ranges = []
current_section = None
for i, heading in enumerate(all_headings):
    if heading['size'] > 16:  # Major section headings
        if current_section:
            current_section['end_page'] = heading['page'] - 1
            section_ranges.append(current_section)
        current_section = {
            'title': heading['text'][:60],
            'start_page': heading['page'],
            'end_page': total_pages
        }
if current_section:
    section_ranges.append(current_section)

for section in section_ranges[:20]:  # First 20 sections
    start = section['start_page']
    end = min(section['end_page'], total_pages)
    section_pages = [p for p in page_details if start <= p['page'] <= end]
    
    total_images = sum(p['images'] for p in section_pages)
    has_bullets = any(p['has_bullets'] for p in section_pages)
    has_steps = any(p['has_steps'] for p in section_pages)
    
    content_types = []
    if total_images > 0:
        content_types.append(f"{total_images} screenshots/images")
    if has_bullets:
        content_types.append("bullet points")
    if has_steps:
        content_types.append("step-by-step instructions")
    
    print(f"   Pages {start}-{end}: {section['title']}")
    print(f"      Content: {', '.join(content_types) if content_types else 'text content'}")

# Annotation styles
print('\n\n5. ANNOTATION STYLES:')
print('=' * 100)
total_drawings = sum(p['drawings'] for p in page_details)
if total_drawings > 0:
    print(f"   - {total_drawings} graphical elements detected (boxes, arrows, shapes)")
    print(f"   - Avg {total_drawings/total_pages:.1f} annotations per page")
else:
    print(f"   - Minimal graphical annotations detected")

pages_with_images = len([p for p in page_details if p['images'] > 0])
print(f"   - {pages_with_images} pages contain images/screenshots")

# Color scheme
print('\n\n6. COLOR SCHEME AND BRANDING:')
print('=' * 100)
print(f"   Colors detected: {len(colors_found)} unique colors")
sorted_colors = sorted(list(colors_found))[:10]
print(f"   Sample colors: {', '.join(sorted_colors)}")

# Font analysis
print('\n\n7. FONT STYLES AND FORMATTING:')
print('=' * 100)
print(f"   Fonts detected: {len(fonts_found)} font variations")
for font in sorted(list(fonts_found))[:15]:
    print(f"   - {font}")

# Explanation style
print('\n\n8. HOW ACTIONS/FEATURES ARE EXPLAINED:')
print('=' * 100)
bullet_pages = len([p for p in page_details if p['has_bullets']])
numbered_pages = len([p for p in page_details if p['has_numbered_list']])
step_pages = len([p for p in page_details if p['has_steps']])

print(f"   - Bullet points: Used on {bullet_pages} pages ({bullet_pages*100//total_pages}%)")
print(f"   - Numbered lists: Used on {numbered_pages} pages ({numbered_pages*100//total_pages}%)")
print(f"   - Step-by-step: Mentioned on {step_pages} pages ({step_pages*100//total_pages}%)")
print(f"   - Screenshots/visuals: Present on {pages_with_images} pages ({pages_with_images*100//total_pages}%)")

# Detailed page breakdown
print('\n\n' + '=' * 100)
print('DETAILED PAGE-BY-PAGE BREAKDOWN:')
print('=' * 100)
for info in page_details:
    print(f"\nPage {info['page']}:")
    if info['headings']:
        print(f"  Main headings:")
        for h in info['headings'][:3]:
            print(f"    - {h['text'][:70]}")
    print(f"  Images: {info['images']}, Drawings: {info['drawings']}")
    content_features = []
    if info['has_bullets']:
        content_features.append("bullets")
    if info['has_numbered_list']:
        content_features.append("numbered list")
    if info['has_steps']:
        content_features.append("step-by-step")
    if content_features:
        print(f"  Features: {', '.join(content_features)}")
    print(f"  Preview: {info['text_preview'][:100]}...")

doc.close()
print('\n' + '=' * 100)
print('ANALYSIS COMPLETE')
print('=' * 100)
