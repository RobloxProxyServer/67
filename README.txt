SOL CHAT — local ChatGPT-style interface

1) Install Python 3.10+
2) Open a terminal in this folder:
   python -m venv .venv
   Windows: .venv\Scripts\activate
   WSL/Linux: source .venv/bin/activate
3) Install dependencies:
   pip install -r requirements.txt
4) Set your API key as an environment variable (do not paste it into app.py):
   Windows PowerShell:
     $env:AI_API_KEY="YOUR_NEW_ROTATED_KEY"
   WSL/Linux:
     export AI_API_KEY="YOUR_NEW_ROTATED_KEY"
5) Optional settings:
   Windows PowerShell:
     $env:AI_BASE_URL="https://api.xingchiapi.com/v1"
     $env:AI_MODEL="gpt-6.1-sol"
   WSL/Linux:
     export AI_BASE_URL="https://api.xingchiapi.com/v1"
     export AI_MODEL="gpt-6.1-sol"
6) Start:
   python app.py
7) Open http://127.0.0.1:5000

Notes:
- API key stays on the Python server, not in browser JavaScript.
- Supports text/code files, PDF, DOCX, and common images. PDF/DOCX text is extracted locally.
- Image input uses Responses API input_image data URLs. Your provider/model must support this.
- This starter uses non-streaming Responses requests for compatibility. It sends chat history on each turn.
- File contents are sent to your configured API provider when you submit them.
- Do not expose port 5000 publicly without adding authentication and HTTPS.
- Rotate the API token you pasted into chat before using this app.
