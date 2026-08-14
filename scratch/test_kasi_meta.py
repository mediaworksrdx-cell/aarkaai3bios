import sys
sys.path.insert(0, '.')

import unittest.mock as mock

with mock.patch.dict('sys.modules', {'diffusers': mock.MagicMock(), 'torch': mock.MagicMock()}):
    from modules.gamma_pdf import _default_domain_metadata
    from modules.gamma_domains import detect_domain

    topic = 'Kasi Temple (Varanasi)'
    domain = detect_domain(topic)
    print(f'Domain detected: {domain}')
    print()

    meta = _default_domain_metadata(topic, domain)

    print('=== PDF METADATA (fallback) ===')
    print()
    print('cover_desc:')
    print(' ', meta['cover_desc'])
    print()
    print('section_titles:')
    for i, t in enumerate(meta['section_titles']):
        print(f'  {i+1}. {t}')
    print()
    print('section_hints:')
    for i, h in enumerate(meta['section_hints']):
        print(f'  {i+1}. {h}')
    print()
    print('watermarks:', meta['watermarks'])
    print('page_badges:', meta['page_badges'])
    print()
    print('checklist_title:', meta['checklist_title'])
    print('checklist_items:')
    for item in meta['checklist_items']:
        print(f'  - {item}')
    print()
    print('callout_quote:')
    print(' ', meta['callout_quote'])
    print()
    print('chart_footnotes:')
    for i, f in enumerate(meta['chart_footnotes']):
        print(f'  {i+1}. {f}')
    print()
    print('source_credits:')
    for i, s in enumerate(meta['source_credits']):
        print(f'  {i+1}. {s}')
    print('source_badges:', meta['source_badges'])
    print()
    print('methodology_text:')
    print(' ', meta['methodology_text'])
    print()
    print('opp_title:', meta['opp_title'])
    print('opp_items:')
    for item in meta['opp_items']:
        print(f'  - {item}')
    print()
    print('sources_title:', meta['sources_title'])
    print('players_label:', meta['players_label'])
    print('table_title:', meta['table_title'])
    print('milestones_title:', meta['milestones_title'])
