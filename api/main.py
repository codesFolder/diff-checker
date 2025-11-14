# api/main.py

import json
import difflib
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        # 1. Get data and options from the POST request
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data)
            text1 = data.get('text1', '')
            text2 = data.get('text2', '')
            # Get customization options, default to False if not provided
            ignore_whitespace = data.get('ignoreWhitespace', False)
            case_insensitive = data.get('caseInsensitive', False)
        except json.JSONDecodeError:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Invalid JSON'}).encode('utf-8'))
            return

        # 2. Calculate basic stats on original text
        stats = {
            'text1': {'chars': len(text1), 'words': len(text1.split()), 'lines': len(text1.splitlines())},
            'text2': {'chars': len(text2), 'words': len(text2.split()), 'lines': len(text2.splitlines())}
        }

        # 3. Pre-process text for diff based on options
        processed_text1 = text1
        processed_text2 = text2

        if case_insensitive:
            processed_text1 = processed_text1.lower()
            processed_text2 = processed_text2.lower()

        # Split into lines for whitespace processing and diffing
        text1_lines = processed_text1.splitlines()
        text2_lines = processed_text2.splitlines()

        if ignore_whitespace:
            text1_lines = [line.strip() for line in text1_lines]
            text2_lines = [line.strip() for line in text2_lines]

        # 4. Generate the visual HTML diff using the processed lines
        d = difflib.HtmlDiff(wrapcolumn=80)
        html_diff = d.make_file(text1_lines, text2_lines, fromdesc='Original Text', todesc='New Text')

        # 5. Calculate summary statistics using SequenceMatcher for accuracy
        s = difflib.SequenceMatcher(None, text1_lines, text2_lines)
        added_lines = 0
        deleted_lines = 0
        
        # Opcodes describe the differences: 'replace', 'delete', 'insert', 'equal'
        for tag, i1, i2, j1, j2 in s.get_opcodes():
            if tag == 'replace':
                deleted_lines += (i2 - i1)
                added_lines += (j2 - j1)
            elif tag == 'delete':
                deleted_lines += (i2 - i1)
            elif tag == 'insert':
                added_lines += (j2 - j1)
        
        summary = {
            'added': added_lines,
            'deleted': deleted_lines
        }

        # 6. Send the complete response
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            'diff_html': html_diff,
            'stats': stats,
            'summary': summary
        }
        self.wfile.write(json.dumps(response).encode('utf-8'))
        return
