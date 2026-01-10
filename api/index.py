from flask import Flask, request, jsonify, send_file
import difflib
import re
import io
import chardet
from html import escape

app = Flask(__name__)
# Increase upload limit to 16MB per request (standard for Vercel functions)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

def detect_encoding(file_bytes):
    """
    Detects the encoding of a file (UTF-8, ASCII, Windows-1252, etc.)
    to prevent 'UnicodeDecodeError' crashes.
    """
    result = chardet.detect(file_bytes)
    return result['encoding'] or 'utf-8'

def strip_comments(text, ext):
    """
    Removes comments based on file extension.
    Useful for the 'Ignore Comments' feature.
    """
    if not ext: return text
    
    # Python / YAML / Shell / Configs
    if ext in ['py', 'yaml', 'yml', 'sh', 'bash', 'conf', 'ini', 'toml']:
        return re.sub(r'#.*', '', text)
    
    # C-style (JS, C++, CSS, Java, PHP, Go, Rust)
    elif ext in ['js', 'ts', 'jsx', 'tsx', 'c', 'cpp', 'java', 'css', 'scss', 'php', 'go', 'rs']:
        # Remove // comments
        text = re.sub(r'//.*', '', text)
        # Remove /* */ comments (multiline)
        text = re.sub(r'/\*[\s\S]*?\*/', '', text)
        return text
        
    # HTML / XML / SVG
    elif ext in ['html', 'xml', 'svg']:
        return re.sub(r'', '', text)
    
    return text

def apply_regex_ignore(text, pattern):
    """
    Removes lines matching a user-provided Regex pattern.
    Useful for ignoring logs, timestamps, or specific IDs.
    """
    if not pattern: return text
    try:
        # Split lines, filter out matching ones, rejoin
        lines = text.splitlines()
        regex = re.compile(pattern)
        filtered = [line for line in lines if not regex.search(line)]
        return '\n'.join(filtered)
    except re.error:
        # If user provides invalid regex, just return original text (fail safe)
        return text 

@app.route('/api/generate_report', methods=['POST'])
def generate_report():
    try:
        if 'file1' not in request.files or 'file2' not in request.files:
            return jsonify({'error': 'Missing files'}), 400

        f1 = request.files['file1']
        f2 = request.files['file2']
        
        # 1. Read Files & Handle Encoding Safely
        b1 = f1.read()
        b2 = f2.read()
        
        enc1 = detect_encoding(b1)
        enc2 = detect_encoding(b2)
        
        text1 = b1.decode(enc1, errors='replace')
        text2 = b2.decode(enc2, errors='replace')

        # 2. Process User Options
        ignore_white = request.form.get('ignore_whitespace') == 'true'
        ignore_comments = request.form.get('ignore_comments') == 'true'
        regex_pattern = request.form.get('regex_pattern', '')

        # Get file extensions (e.g. 'py' from 'script.py')
        ext1 = f1.filename.split('.')[-1].lower() if '.' in f1.filename else ''
        
        # 3. Apply Filters (Strip Comments / Regex)
        if ignore_comments:
            text1 = strip_comments(text1, ext1)
            text2 = strip_comments(text2, ext1) 

        if regex_pattern:
            text1 = apply_regex_ignore(text1, regex_pattern)
            text2 = apply_regex_ignore(text2, regex_pattern)

        lines1 = text1.splitlines()
        lines2 = text2.splitlines()

        if ignore_white:
            lines1 = [l.strip() for l in lines1]
            lines2 = [l.strip() for l in lines2]

        # 4. Generate HTML Report
        # Using difflib.HtmlDiff to create a standalone, color-coded HTML table
        diff_html = difflib.HtmlDiff(wrapcolumn=90).make_file(
            lines1, lines2, 
            fromdesc=f"Original: {f1.filename}", 
            todesc=f"New: {f2.filename}",
            context=False, # Set to True if you only want to see changed lines + context
            numlines=5
        )

        # 5. Send as Downloadable File
        mem_file = io.BytesIO()
        mem_file.write(diff_html.encode('utf-8'))
        mem_file.seek(0)

        return send_file(
            mem_file,
            as_attachment=True,
            download_name='diff_report.html',
            mimetype='text/html'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route catch-all for local testing
@app.route('/')
def home():
    return "Backend Running"

if __name__ == '__main__':
    app.run(debug=True, port=5000)