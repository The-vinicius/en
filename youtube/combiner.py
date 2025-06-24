import os
import re
import html
from itertools import zip_longest

def strip_html_tags(text):
    """First unescape HTML entities, then remove tags."""
    text = html.unescape(text)
    return re.sub(r'<[^>]+>', '', text)

def parse_vtt_manual(path):
    """Parse VTT file manually into list of dicts with start, end, text."""
    segments = []
    with open(path, 'r', encoding='utf-8') as f:
        lines = [line.rstrip('\n') for line in f]
    idx = 0
    # Skip header if present
    while idx < len(lines) and '-->' not in lines[idx]:
        idx += 1
    # Parse blocks
    while idx < len(lines):
        timing_line = lines[idx]
        if '-->' not in timing_line:
            idx += 1
            continue
        start_raw, end_raw = timing_line.split(' --> ')
        start = start_raw.replace('.', ',')
        end = end_raw.replace('.', ',')
        idx += 1
        # Parse text lines
        texts = []
        while idx < len(lines) and lines[idx].strip() != "":
            texts.append(strip_html_tags(lines[idx]))
            idx += 1
        segments.append({
            'start': start,
            'end': end,
            'text': ' '.join(texts).strip()
        })
        while idx < len(lines) and lines[idx].strip() == "":
            idx += 1
    return segments

def combine_subtitles_vtt(primary_path, secondary_path, output_path):
    prim = parse_vtt_manual(primary_path)
    sec = parse_vtt_manual(secondary_path)
    
    combined_lines = []
    idx = 1
    for b1, b2 in zip_longest(prim, sec):
        if b1 and b2:
            start = b1['start']
            end = max(b1['end'], b2['end'])
        elif b1:
            start, end = b1['start'], b1['end']
        else:
            start, end = b2['start'], b2['end']
        
        text1 = b1['text'] if b1 else ''
        text2 = b2['text'] if b2 else ''
        
        combined_lines.append(str(idx))
        combined_lines.append(f"{start} --> {end}")
        if text1:
            combined_lines.append(text1)
        if text2:
            combined_lines.append(text2)
        combined_lines.append("")
        idx += 1
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(combined_lines))

    return combined_lines

