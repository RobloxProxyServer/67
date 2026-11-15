import os, base64, mimetypes
from pathlib import Path
from flask import Flask, request, jsonify, render_template_string
import requests

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024

BASE_URL = os.getenv("AI_BASE_URL", "https://api.xingchiapi.com/v1").rstrip("/")
API_KEY = os.getenv("AI_API_KEY", "")
DEFAULT_MODEL = os.getenv("AI_MODEL", "gpt-6.1-sol")

HTML = r"""
<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sol Chat</title><style>
:root{color-scheme:dark;--bg:#171717;--panel:#212121;--line:#333;--muted:#aaa;--accent:#8b5cf6}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:#eee;font:15px system-ui,Arial;display:flex;height:100vh}
aside{width:255px;background:#101010;padding:16px;border-right:1px solid var(--line);display:flex;flex-direction:column;gap:12px}
button,select{background:#292929;color:#eee;border:1px solid #444;border-radius:9px;padding:10px;cursor:pointer}
button:hover{background:#383838}.new{width:100%;text-align:left}.small{font-size:12px;color:var(--muted)}
#history{overflow:auto;display:flex;flex-direction:column;gap:5px}.hist{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;text-align:left}
main{flex:1;display:flex;flex-direction:column;min-width:0}.top{height:58px;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;padding:0 20px}
#chat{flex:1;overflow:auto;padding:24px max(18px,calc((100% - 850px)/2));}
.welcome{text-align:center;color:#ddd;margin:15vh auto 0}.welcome h1{font-size:30px}
.msg{max-width:850px;margin:0 auto 22px;line-height:1.65;white-space:pre-wrap;overflow-wrap:anywhere}.user{background:#292929;padding:14px 17px;border-radius:18px;margin-left:auto;max-width:min(85%,720px);width:fit-content}.assistant{padding:5px 2px}
.msg pre{background:#0c0c0c;padding:14px;border-radius:10px;overflow:auto}.msg code{font-family:ui-monospace,monospace}
#composerWrap{padding:12px 18px 20px}.composer{max-width:850px;margin:auto;background:#252525;border:1px solid #444;border-radius:18px;padding:10px;display:flex;gap:8px;align-items:end}
textarea{flex:1;resize:none;background:transparent;color:white;border:0;outline:0;min-height:48px;max-height:180px;padding:10px;font:15px system-ui}
#send{background:var(--accent);border:0;font-weight:700}#file{display:none}.attach{font-size:22px;padding:8px}.filetag{max-width:850px;margin:0 auto 8px;color:#bbb;font-size:12px}
@media(max-width:650px){aside{width:62px;padding:8px}aside .hide{display:none}.top{padding:0 10px}#chat{padding:18px 12px}.user{max-width:94%}}
</style></head><body>
<aside><button class="new" onclick="newChat()">＋ <span class="hide">New chat</span></button>
<div class="small hide">CONVERSATIONS</div><div id="history"></div><div class="small hide" style="margin-top:auto">Local chat history is stored in this browser.</div></aside>
<main><div class="top"><b>✦ Sol Chat</b><select id="model"><option>{{model}}</option></select></div>
<div id="chat"><div class="welcome" id="welcome"><h1>How can I help?</h1><p class="small">Connected to your configured API provider</p></div></div>
<div id="composerWrap"><div class="filetag" id="filetag"></div><div class="composer">
<label class="attach" for="file" title="Attach file">＋</label><input id="file" type="file" multiple>
<textarea id="prompt" placeholder="Message the model..." rows="1"></textarea><button id="send" onclick="send()">↑</button></div>
<div class="small" style="text-align:center;margin-top:8px">Check important answers. Files are sent to your configured API provider.</div></div></main>
<script>
let chats=JSON.parse(localStorage.getItem('sol_chats')||'[]'), current=-1, attachments=[];
const chat=document.getElementById('chat'), promptBox=document.getElementById('prompt');
function persist(){localStorage.setItem('sol_chats',JSON.stringify(chats));drawHistory()}
function drawHistory(){let h=document.getElementById('history');h.innerHTML='';chats.forEach((c,i)=>{let b=document.createElement('button');b.className='hist';b.textContent=c.title||'New chat';b.onclick=()=>openChat(i);h.append(b)})}
function newChat(){chats.unshift({title:'New chat',messages:[]});current=0;persist();render()}
function openChat(i){current=i;render()}
function render(){chat.innerHTML='';let c=chats[current];if(!c||!c.messages.length){chat.innerHTML='<div class="welcome"><h1>How can I help?</h1><p class="small">Ask anything or attach a file</p></div>';return}
c.messages.forEach(m=>addBubble(m.role,m.text))}
function addBubble(role,text){let d=document.createElement('div');d.className='msg '+(role==='user'?'user':'assistant');d.textContent=text;chat.append(d);chat.scrollTop=chat.scrollHeight}
document.getElementById('file').onchange=e=>{attachments=[...e.target.files];document.getElementById('filetag').textContent=attachments.map(f=>f.name).join(' · ')};
promptBox.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send()}});
async function send(){let text=promptBox.value.trim();if(!text&&!attachments.length)return;if(current<0)newChat();
let files=attachments;attachments=[];document.getElementById('file').value='';document.getElementById('filetag').textContent='';
let display=text+(files.length?'\n\nAttachments: '+files.map(f=>f.name).join(', '):'');
chats[current].messages.push({role:'user',text:display});if(chats[current].title==='New chat')chats[current].title=(text||files[0].name).slice(0,35);
addBubble('user',display);promptBox.value='';persist();
let wait=document.createElement('div');wait.className='msg assistant';wait.textContent='Thinking…';chat.append(wait);chat.scrollTop=chat.scrollHeight;
try{
 let fd=new FormData();fd.append('message',text);fd.append('model',document.getElementById('model').value);
 fd.append('history',JSON.stringify(chats[current].messages.slice(0,-1)));
 files.forEach(f=>fd.append('files',f));
 let r=await fetch('/chat',{method:'POST',body:fd});let data=await r.json();if(!r.ok)throw new Error(data.error||'Request failed');
 wait.remove();chats[current].messages.push({role:'assistant',text:data.reply});addBubble('assistant',data.reply);persist();
}catch(err){wait.textContent='Error: '+err.message}
}
drawHistory();if(chats.length)openChat(0);
</script></body></html>
"""

def extract_text(file_storage):
    name = file_storage.filename or "upload"
    data = file_storage.read()
    file_storage.stream.seek(0)
    ext = Path(name).suffix.lower()
    if ext in {".txt", ".md", ".csv", ".json", ".py", ".js", ".html", ".css", ".xml", ".log"}:
        return f"\n\n[File: {name}]\n" + data.decode("utf-8", errors="replace")
    if ext == ".pdf":
        try:
            from pypdf import PdfReader
            import io
            reader = PdfReader(io.BytesIO(data))
            return f"\n\n[PDF: {name}]\n" + "\n".join(p.extract_text() or "" for p in reader.pages)
        except Exception as e:
            raise ValueError(f"Could not read PDF {name}: {e}")
    if ext == ".docx":
        try:
            from docx import Document
            import io
            doc = Document(io.BytesIO(data))
            return f"\n\n[DOCX: {name}]\n" + "\n".join(p.text for p in doc.paragraphs)
        except Exception as e:
            raise ValueError(f"Could not read DOCX {name}: {e}")
    if ext in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
        mime = mimetypes.guess_type(name)[0] or "image/png"
        encoded = base64.b64encode(data).decode()
        return {"type": "input_image", "image_url": f"data:{mime};base64,{encoded}"}
    # Keep unsupported binary files from being silently misrepresented.
    raise ValueError(f"Unsupported file type: {name}. Try PDF, DOCX, TXT, CSV, JSON, code, or an image.")

@app.get("/")
def home():
    return render_template_string(HTML, model=DEFAULT_MODEL)

@app.post("/chat")
def chat():
    if not API_KEY:
        return jsonify(error="Missing AI_API_KEY. Set it in your environment before starting the app."), 500
    try:
        message = request.form.get("message", "")
        model = request.form.get("model") or DEFAULT_MODEL
        import json
        history = json.loads(request.form.get("history", "[]"))
        content = []
        if message:
            content.append({"type": "input_text", "text": message})
        for f in request.files.getlist("files"):
            extracted = extract_text(f)
            if isinstance(extracted, dict):
                content.append(extracted)
            else:
                content.append({"type": "input_text", "text": extracted})
        if not content:
            return jsonify(error="Please enter a message or attach a supported file."), 400

        # Send prior turns plus the new multimodal user message.
        input_items = []
        for item in history:
            role = item.get("role")
            if role in ("user", "assistant"):
                input_items.append({"role": role, "content": item.get("text", "")})
        input_items.append({"role": "user", "content": content})

        resp = requests.post(
            BASE_URL + "/responses",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            json={"model": model, "input": input_items},
            timeout=180
        )
        if not resp.ok:
            return jsonify(error=f"Provider returned HTTP {resp.status_code}: {resp.text[:1500]}"), resp.status_code
        payload = resp.json()
        answer = payload.get("output_text")
        if not answer:
            chunks = []
            for out in payload.get("output", []):
                for part in out.get("content", []):
                    if part.get("type") in ("output_text", "text"):
                        chunks.append(part.get("text", ""))
            answer = "\n".join(chunks).strip()
        if not answer:
            return jsonify(error="The API response did not contain output_text. Raw response: " + str(payload)[:1000]), 502
        return jsonify(reply=answer)
    except ValueError as e:
        return jsonify(error=str(e)), 400
    except requests.RequestException as e:
        return jsonify(error=f"Could not reach the API: {e}"), 502
    except Exception as e:
        return jsonify(error=str(e)), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)