# --- START OF FILE __init__.py ---

# -*- coding: utf-8 -*-
import urllib.request
import urllib.parse
import ssl
import base64
import json
from aqt import mw
from aqt import gui_hooks
from aqt.utils import tooltip
from aqt.qt import *

# --- CẤU HÌNH ---
SHORTCUT_KEY = "F5"
SILENCE_DURATION = 0.6  # Giây (Để fix lỗi Bluetooth)
DEFAULT_LANG = "en"     # Ngôn ngữ mặc định

# --- PHẦN 1: JAVASCRIPT (INTELLIGENT SEGMENTATION) ---
JS_INJECTION = """
<script>
(function(){
    var AudioContext = window.AudioContext || window.webkitAudioContext;
    var audioCtx = new AudioContext();

    function base64ToArrayBuffer(base64) {
        var binary_string = window.atob(base64);
        var len = binary_string.length;
        var bytes = new Uint8Array(len);
        for (var i = 0; i < len; i++) {
            bytes[i] = binary_string.charCodeAt(i);
        }
        return bytes.buffer;
    }

    window.iacPlayB64 = function(b64Data) {
        if (audioCtx.state === 'suspended') audioCtx.resume();

        try {
            var audioData = base64ToArrayBuffer(b64Data);
            audioCtx.decodeAudioData(audioData, function(decodedBuffer) {
                var sampleRate = decodedBuffer.sampleRate;
                var silenceSecs = SILENCE_PLACEHOLDER; 
                var silenceSamples = Math.ceil(silenceSecs * sampleRate);
                var totalLength = decodedBuffer.length + silenceSamples;

                var newBuffer = audioCtx.createBuffer(
                    decodedBuffer.numberOfChannels, totalLength, sampleRate
                );

                for (var channel = 0; channel < decodedBuffer.numberOfChannels; channel++) {
                    var oldData = decodedBuffer.getChannelData(channel);
                    var newData = newBuffer.getChannelData(channel);
                    newData.set(oldData, silenceSamples);
                }

                var source = audioCtx.createBufferSource();
                source.buffer = newBuffer;
                source.connect(audioCtx.destination);
                source.start(0);
            }, function(e){ console.error("Decode error: " + e.err); });
        } catch (err) { console.error(err); }
    };

    window.iacReadText = function(text, lang) {
        if (!text || text.trim() === "") return;
        lang = lang || "DEFAULT_LANG_PLACEHOLDER";
        pycmd("iac_read_text:" + text.toString() + ":" + lang);
    };

    // --- HÀM TÁCH TỪ THÔNG MINH (UPDATED) ---
    function getWordAtPoint(x, y, langCode) {
        if (!document.caretRangeFromPoint) return null;
        var range = document.caretRangeFromPoint(x, y);
        if (!range || range.startContainer.nodeType !== Node.TEXT_NODE) return null;
        
        var textNode = range.startContainer;
        var fullText = textNode.textContent;
        var offset = range.startOffset; // Vị trí con trỏ trong chuỗi

        // 1. XỬ LÝ ĐẶC BIỆT CHO TIẾNG TRUNG (Sử dụng Intl.Segmenter)
        // Nếu langCode chứa 'zh', 'cn' hoặc 'chi'
        if (langCode && (langCode.includes('zh') || langCode.includes('cn'))) {
            if (typeof Intl !== 'undefined' && Intl.Segmenter) {
                try {
                    // Tạo bộ tách từ tiếng Trung
                    const segmenter = new Intl.Segmenter(langCode, { granularity: 'word' });
                    const segments = segmenter.segment(fullText);
                    
                    // Duyệt qua các từ đã tách để tìm từ chứa vị trí click
                    for (const segment of segments) {
                        // segment: {segment: "你们", index: 0, input: "..."}
                        var wordStart = segment.index;
                        var wordEnd = wordStart + segment.segment.length;
                        
                        if (offset >= wordStart && offset < wordEnd) {
                            var word = segment.segment.trim();
                            // Loại bỏ các dấu câu nếu vô tình click trúng
                            if (/^[\p{P}\p{S}]+$/u.test(word)) return null;
                            return word;
                        }
                    }
                } catch (e) {
                    console.error("Intl.Segmenter error:", e);
                }
            }
        }

        // 2. XỬ LÝ MẶC ĐỊNH CHO CÁC NGÔN NGỮ KHÁC (Regex)
        // Regex Unicode mở rộng
        var wordRegex = /[\w\u00C0-\u1EF9\u0400-\u04FF\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\u3400-\u4DBF\uAC00-\uD7AF'-]/;

        var start = offset;
        while (start > 0 && wordRegex.test(fullText.charAt(start - 1))) start--;
        var end = offset;
        while (end < fullText.length && wordRegex.test(fullText.charAt(end))) end++;
        
        var result = fullText.substring(start, end).trim();
        return result.length > 0 ? result : null;
    }

    document.body.addEventListener('click', function(e) {
        if (e.target.tagName === 'BUTTON' || e.target.closest('button')) return;
        if (window.getSelection().toString().trim().length > 0) return;
        
        var ttsElement = e.target.closest('[tts]');
        if (!ttsElement) return;

        var lang = ttsElement.getAttribute('tts');
        if (lang === "on" || lang === "") lang = "DEFAULT_LANG_PLACEHOLDER";

        // Truyền thêm lang vào hàm getWordAtPoint để quyết định thuật toán tách từ
        var word = getWordAtPoint(e.clientX, e.clientY, lang);
        
        if (word) {
            pycmd("iac_lookup:" + word + ":" + lang);
        }
    }, true);

    window.iacGetSelection = function() {
        var text = window.getSelection().toString().trim();
        var anchor = window.getSelection().anchorNode;
        var lang = "DEFAULT_LANG_PLACEHOLDER";
        if (anchor && anchor.parentElement) {
             var ttsEl = anchor.parentElement.closest('[tts]');
             if (ttsEl) {
                 var attr = ttsEl.getAttribute('tts');
                 if (attr !== "on" && attr !== "") lang = attr;
             }
        }
        if (text) pycmd("iac_selection:" + text + ":" + lang);
        else pycmd("iac_no_selection");
    }
})();
</script>
"""

# --- PHẦN 2: PYTHON DOWNLOADER ---

def get_audio_sources(text, lang, is_sentence=False):
    google_lang = lang
    youdao_lang = lang
    
    if lang.lower() in ['zh', 'cn', 'zh-cn', 'chi']:
        google_lang = 'zh-CN'
        youdao_lang = 'zh'
    if lang.lower() in ['zh-tw', 'tw']:
        google_lang = 'zh-TW'
        youdao_lang = 'zh' 

    safe_text = urllib.parse.quote(text.lower())
    sources = []

    # Ưu tiên Youdao cho Tiếng Trung
    if youdao_lang == 'zh':
        sources.append(f"https://dict.youdao.com/dictvoice?audio={safe_text}&le=zh")
        sources.append(f"https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl={google_lang}&q={safe_text}")
    
    elif lang == 'en':
        if not is_sentence:
            w = text.lower()
            if len(w) > 0:
                f1, f3, f5 = w[0], w[:3].ljust(3, "_"), w[:5].ljust(5, "_")
                sources.append(f"https://www.oxfordlearnersdictionaries.com/media/english/us_pron/{f1}/{f3}/{f5}/{w}__us_1.mp3")
        sources.append(f"https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl=en&q={safe_text}")
        sources.append(f"https://dict.youdao.com/dictvoice?type=2&le=eng&audio={safe_text}")

    else:
        sources.append(f"https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl={google_lang}&q={safe_text}")
        sources.append(f"https://dict.youdao.com/dictvoice?type=2&le={youdao_lang}&audio={safe_text}")

    return sources

def download_worker_b64(text, lang, is_sentence=False):
    sources = get_audio_sources(text, lang, is_sentence)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    for url in sources:
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://translate.google.com/'
            })
            with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
                data = response.read()
                if len(data) > 500:
                    return (base64.b64encode(data).decode('ascii'), text, lang)
        except Exception:
            continue
    return (None, text, lang)

def on_download_complete_b64(future):
    try:
        b64_str, text, lang = future.result()
        if b64_str:
            js_code = f"window.iacPlayB64({json.dumps(b64_str)});"
            mw.reviewer.web.eval(js_code)
        else:
            tooltip(f"❌ Không tìm thấy audio ({lang}): {text}")
    except Exception as e:
        tooltip(f"Lỗi: {e}")

# --- PHẦN 3: XỬ LÝ SỰ KIỆN ---

def trigger_selection_read():
    if mw.state != "review": return
    mw.reviewer.web.eval("window.iacGetSelection()")

def parse_message(message, command_prefix):
    content = message[len(command_prefix):] 
    parts = content.rsplit(":", 1) 
    
    if len(parts) == 2 and len(parts[1]) <= 6:
        text = parts[0]
        lang = parts[1]
    else:
        text = content
        lang = DEFAULT_LANG
    return text, lang

def handle_js_message(handled, message, context):
    if not isinstance(message, str): return handled
    
    cmd_read = "iac_read_text:"
    cmd_lookup = "iac_lookup:"
    cmd_select = "iac_selection:"

    if message.startswith(cmd_read):
        text, lang = parse_message(message, cmd_read)
        if len(text) > 800: text = text[:800]
        mw.taskman.run_in_background(lambda: download_worker_b64(text, lang, True), on_download_complete_b64)
        return (True, None)

    elif message.startswith(cmd_lookup):
        text, lang = parse_message(message, cmd_lookup)
        tooltip(f"⬇️ {lang.upper()}: {text}", period=500)
        mw.taskman.run_in_background(lambda: download_worker_b64(text, lang, False), on_download_complete_b64)
        return (True, None)
    
    elif message.startswith(cmd_select):
        text, lang = parse_message(message, cmd_select)
        if len(text) > 800: text = text[:800]
        tooltip(f"⏳ Đang tải ({lang})...", period=800)
        mw.taskman.run_in_background(lambda: download_worker_b64(text, lang, True), on_download_complete_b64)
        return (True, None)

    elif message == "iac_no_selection":
        tooltip(f"⚠️ Hãy bôi đen text rồi nhấn {SHORTCUT_KEY}")
        return (True, None)

    return handled

def setup_shortcuts(state, shortcuts):
    if state == "review":
        shortcuts.append((SHORTCUT_KEY, trigger_selection_read))

def inject_script(web_content, context):
    if hasattr(mw, 'reviewer') and context == mw.reviewer:
        script = JS_INJECTION.replace("SILENCE_PLACEHOLDER", str(SILENCE_DURATION))
        script = script.replace("DEFAULT_LANG_PLACEHOLDER", DEFAULT_LANG)
        web_content.body += script

gui_hooks.webview_will_set_content.append(inject_script)
gui_hooks.webview_did_receive_js_message.append(handle_js_message)
gui_hooks.state_shortcuts_will_change.append(setup_shortcuts)