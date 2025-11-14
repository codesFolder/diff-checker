# api/main.py

import json
import difflib
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        # 1. Get the data from the POST request
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            # Parse the JSON data
            data = json.loads(post_data)
            text1 = data.get('text1', '')
            text2 = data.get('text2', '')
        except json.JSONDecodeError:
            self.send_response(400) # Bad Request
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Invalid JSON'}).encode('utf-8'))
            return

        # 2. Prepare the text for comparison (split into lines)
        text1_lines = text1.splitlines()
        text2_lines = text2.splitlines()

        # 3. Generate the HTML diff
        # HtmlDiff is the class that creates a side-by-side HTML table
        d = difflib.HtmlDiff(wrapcolumn=80) # wrapcolumn makes it more readable
        html_diff = d.make_file(text1_lines, text2_lines, fromdesc='Original Text', todesc='New Text')

        # 4. Send the response
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        # We send the generated HTML inside a JSON object
        response = {'diff_html': html_diff}
        self.wfile.write(json.dumps(response).encode('utf-8'))
        return