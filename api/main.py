# api/main.py

import json
import difflib
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data)
            text1 = data.get('text1', '')
            text2 = data.get('text2', '')
        except json.JSONDecodeError:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Invalid JSON'}).encode('utf-8'))
            return

        # --- NEW: Calculate Statistics ---
        stats = {
            'text1': {
                'chars': len(text1),
                'words': len(text1.split()),
                'lines': len(text1.splitlines())
            },
            'text2': {
                'chars': len(text2),
                'words': len(text2.split()),
                'lines': len(text2.splitlines())
            }
        }

        # Generate the diff
        text1_lines = text1.splitlines()
        text2_lines = text2.splitlines()
        d = difflib.HtmlDiff(wrapcolumn=80)
        html_diff = d.make_file(text1_lines, text2_lines, fromdesc='Original Text', todesc='New Text')

        # Send the response
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        # Add the stats to our response JSON
        response = {
            'diff_html': html_diff,
            'stats': stats  # <-- NEW
        }
        self.wfile.write(json.dumps(response).encode('utf-8'))
        return
