"""
Analyze multiple URLs from the project
"""
from ai_agent.tools.ui_extractor import UIExtractor
import json

urls = [
    'https://ce-ts-dev.trinitylifesciences.com/universe-summary',
    'https://ce-ts-dev.trinitylifesciences.com/segments',
    'https://ce-ts-dev.trinitylifesciences.com/segment/SG000904',
    'https://ce-ts-dev.trinitylifesciences.com/target-list',
    'https://ce-ts-dev.trinitylifesciences.com/target-list/TG000572'
]

extractor = UIExtractor(headless=True)

results = {}
for url in urls:
    try:
        print(f'\n=== Analyzing: {url} ===')
        result = extractor.extract_summary(url)
        results[url] = result
        print(f'Title: {result["title"]}')
        print(f'Inputs: {len(result["inputs"])} elements')
        print(f'Buttons: {len(result["buttons"])} elements')
        print(f'Dropdowns: {len(result["dropdowns"])} elements')
        print(f'Total: {result["total"]} interactive elements')
    except Exception as e:
        print(f'Error: {str(e)}')
        results[url] = {'error': str(e)}

print('\n\n=== SUMMARY ===')
for url, data in results.items():
    page_name = url.split('/')[-1] or 'root'
    if 'error' not in data:
        print(f'\n{page_name}:')
        print(f'  Total elements: {data["total"]}')
        print(f'  Complexity: {"High" if data["total"] > 20 else "Medium" if data["total"] > 10 else "Low"}')
