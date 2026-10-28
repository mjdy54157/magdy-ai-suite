# -*- coding: utf-8 -*-
"""
Magdy AI Suite
==============
ملف واحد جاهز للنشر على GitHub + Streamlit Cloud.

المفتاح (GROQ_API_KEY) يُقرأ بهذا الترتيب:
  1) الخانة اليدوية في الشريط الجانبي (للتجربة فقط)
  2) Streamlit Secrets   <- المكان الصحيح على Streamlit Cloud
  3) متغير بيئة / ملف .env   <- للتشغيل المحلي

الخلفية مدمجة داخل الملف. لتغييرها ضع صورة باسم background.jpg بجوار app.py.
"""

import base64
import os
import re
from datetime import datetime
from pathlib import Path

import streamlit as st

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:  # اختياري
    pass

try:
    import groq
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

# ------------------------------------------------------------------ إعدادات
PROJECT_NAME = "Magdy_AI_Suite"
APP_TITLE = "Magdy AI Suite"
OUTPUT_DIR = Path(__file__).parent / "outputs"
PLACEHOLDER_KEY = "YOUR_GROQ_API_KEY_HERE"
MAX_HISTORY = 20
# حد تقريبي لحجم سجل المحادثة المرسل (بالحروف). الخطة المجانية في Groq لها حد توكنز لكل طلب
# يختلف حسب النموذج، لذلك نرسل الأحدث فقط ونتجاهل الأقدم.
MAX_CONTEXT_CHARS = 9000
CTE_NAME = "🧭 Clear Thinking Engine"

# قائمة احتياطية فقط لو تعذّر جلب النماذج الحالية من Groq.
# (llama3-* و mixtral-* متوقفة، وllama-3.3-70b-versatile حسب صفحة Groq الرسمية
#  حدد لها إيقافًا في 16 أغسطس 2026، لذلك لا نثبّت أي اسم بل نسأل Groq عن المتاح)
FALLBACK_MODELS = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]
NON_CHAT_HINTS = ("whisper", "tts", "orpheus", "guard", "safeguard", "embed")

BASE_RULES = (
    " اكتب بالعربية الواضحة، والمصطلحات التقنية والمعادلات والأكواد بالإنجليزية."
    " إذا لم تكن متأكدًا من معلومة فقل ذلك صراحة، ولا تخترع مراجع أو أرقامًا أو روابط."
)

WORKSPACES = {
    "Video Generator Planner": {
        "desc": "تخطيط فيديو كامل: فكرة، سيناريو، مشاهد، ولقطات.",
        "prompt": "أنت منتج محتوى فيديو محترف. حوّل فكرة المستخدم إلى خطة: الفكرة، السيناريو، "
                  "قائمة المشاهد واللقطات، ومدة كل مشهد، وملاحظات المونتاج." + BASE_RULES,
    },
    "AI Video & Visual Hub": {
        "desc": "كتابة أوامر (prompts) دقيقة لأدوات توليد الصور والفيديو.",
        "prompt": "أنت خبير كتابة prompts لأدوات توليد الصور والفيديو. اكتب prompts مفصلة بالإنجليزية "
                  "(الموضوع، الإضاءة، زاوية الكاميرا، الأسلوب)، واشرح بالعربية سبب كل اختيار. "
                  "لا تدّعِ قدرات أداة معينة إلا إذا كنت متأكدًا منها." + BASE_RULES,
    },
    "Analytics & Performance Hub": {
        "desc": "تحليل أرقام الأداء واقتراح تحسينات.",
        "prompt": "أنت محلل بيانات. حلّل الأرقام التي يعطيها المستخدم، وحدّد الأنماط والمشاكل، "
                  "واقترح تحسينات قابلة للقياس. لا تفترض بيانات لم تُذكر." + BASE_RULES,
    },
    "Code & Script Analyzer": {
        "desc": "مراجعة الأكواد وإصلاح الأخطاء وتحسينها.",
        "prompt": "أنت مراجع أكواد محترف. اذكر الأخطاء والمخاطر مرتبة حسب الأهمية، ثم قدّم نسخة "
                  "محسّنة كاملة قابلة للتشغيل مع شرح موجز لكل تغيير." + BASE_RULES,
    },
    "Cybersecurity & Bugs": {
        "desc": "أمن المعلومات الدفاعي وفحص الثغرات في أكوادك أنت.",
        "prompt": "أنت مهندس أمن معلومات دفاعي. ساعد في اكتشاف الثغرات وإصلاحها وتأمين الأنظمة "
                  "وحماية المفاتيح والبيانات. ارفض كتابة برمجيات خبيثة أو استغلال أنظمة الغير." + BASE_RULES,
    },
    "AI Mentor": {
        "desc": "مرشد لتعلّم الذكاء الاصطناعي والبرمجة وبناء المشاريع.",
        "prompt": "أنت مرشد يساعد طالبًا على تعلّم الذكاء الاصطناعي والبرمجة. اشرح خطوة بخطوة مع مثال "
                  "عملي، ثم اقترح تمرينًا صغيرًا." + BASE_RULES,
    },
    "Ain Shams Studies": {
        "desc": "مذاكرة مواد الهندسة (رياضيات، فيزياء، وغيرها) بمثال وتمرين.",
        "prompt": "أنت مدرّس هندسة لطالب في بداية دراسته. اشرح خطوة بخطوة مع مثال رقمي، وتحقق من "
                  "الحسابات والوحدات، واختم بمسألة تدريب واحدة. لا تخترع مراجع كتب ولا معلومات عن "
                  "مقررات أو دكاترة بعينهم." + BASE_RULES,
    },
    "Life Coach & Routine": {
        "desc": "تنظيم الوقت والروتين وتحويل الأهداف لخطوات.",
        "prompt": "أنت مدرب حياة عملي. حوّل أهداف المستخدم إلى روتين وخطوات صغيرة قابلة للتنفيذ، "
                  "بدون وعظ أو كلام تحفيزي عام." + BASE_RULES,
    },
    "Projects & GUI Dev": {
        "desc": "تخطيط المشاريع وتصميم الواجهات وبنائها.",
        "prompt": "أنت مهندس برمجيات ومصمم واجهات. ساعد في تصميم المشاريع وهيكلة الكود والواجهات، "
                  "وقدّم كودًا كاملًا قابلًا للتشغيل عند الطلب." + BASE_RULES,
    },
    "General Assistant": {
        "desc": "مساعد عام لأي سؤال.",
        "prompt": "أنت مساعد ذكي ودود ومباشر." + BASE_RULES,
    },
}

# ------------------------------------------------------------------ التصميم
CSS_TEMPLATE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
:root {
  --ink: #f2f4f7; --muted: #a9afba;
  --glass: rgba(12, 13, 16, 0.58); --glass-strong: rgba(9, 10, 12, 0.82);
  --line: rgba(255, 255, 255, 0.13); --glow: #e8eef7;
}
.stApp {
  background-image:
    linear-gradient(180deg, rgba(0,0,0,0.30) 0%, rgba(0,0,0,0.55) 100%),
    url("data:__MIME__;base64,__B64__");
  background-size: cover; background-position: center; background-repeat: no-repeat;
  background-attachment: fixed; background-color: #000; color: var(--ink);
}
@supports (-webkit-touch-callout: none) { .stApp { background-attachment: scroll; } }
[data-testid="stAppViewContainer"], [data-testid="stMain"],
[data-testid="stHeader"] { background: transparent !important; }
footer { visibility: hidden; }

.stApp, .stMarkdown, p, li, label, h1, h2, h3, h4, textarea, input, button {
  font-family: 'Cairo', system-ui, 'Segoe UI', Tahoma, sans-serif;
}
.stApp, .stApp p, .stApp li, .stApp label, .stApp h1, .stApp h2, .stApp h3,
.stApp h4, [data-testid="stWidgetLabel"] p { color: var(--ink); }
[data-testid="stCaptionContainer"], .stApp small { color: var(--muted); }
.block-container { max-width: 960px !important; padding-top: 2.5rem; padding-bottom: 7rem; }

.hero { text-align: center; margin-bottom: 0.5rem; }
.hero h1 { font-weight: 700; font-size: clamp(2rem, 5vw, 3.2rem); letter-spacing: -0.01em;
  margin: 0; padding: 0; text-shadow: 0 2px 28px rgba(0,0,0,0.85); }
.hero p { color: var(--muted); margin: 0.35rem 0 0 0; font-size: 1.05rem; }

[data-testid="stSidebar"] {
  background: var(--glass-strong); -webkit-backdrop-filter: blur(14px);
  backdrop-filter: blur(14px); border-right: 1px solid var(--line);
}
[data-testid="stSidebar"] p { unicode-bidi: plaintext; text-align: start; }

[data-testid="stChatMessage"], [data-testid="stExpander"],
[data-testid="stVerticalBlockBorderWrapper"] {
  background: var(--glass); -webkit-backdrop-filter: blur(10px); backdrop-filter: blur(10px);
  border: 1px solid var(--line); border-radius: 16px;
}
[data-testid="stChatMessage"] { padding: 1rem 1.1rem; direction: rtl; }
[data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li,
.stMarkdown p, .stMarkdown li { unicode-bidi: plaintext; text-align: start; }
pre, code, [data-testid="stCodeBlock"] { direction: ltr; text-align: left; unicode-bidi: normal; }
table { color: var(--ink); } th, td { border-color: var(--line) !important; }

[data-testid="stBottom"], [data-testid="stBottom"] > div { background: transparent !important; }
[data-testid="stChatInput"] { background: var(--glass-strong); border: 1px solid var(--line); border-radius: 12px; }
[data-testid="stChatInput"] textarea { color: var(--ink); unicode-bidi: plaintext; text-align: start; }
textarea, input { unicode-bidi: plaintext; }

[data-baseweb="select"] > div, [data-baseweb="input"] > div, [data-baseweb="textarea"] {
  background: rgba(255,255,255,0.06) !important; border-color: var(--line) !important;
  color: var(--ink); border-radius: 10px;
}
[data-baseweb="popover"] ul { background: #0d0e11; }

.stButton > button, .stDownloadButton > button {
  background: rgba(255,255,255,0.06); color: var(--ink); border: 1px solid var(--line);
  border-radius: 999px; transition: border-color .15s ease, box-shadow .15s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover {
  border-color: rgba(232,238,247,0.6); box-shadow: 0 0 18px rgba(232,238,247,0.18); color: var(--ink);
}
.stButton > button:focus-visible, .stDownloadButton > button:focus-visible {
  outline: 2px solid var(--glow); outline-offset: 2px;
}
@media (prefers-reduced-motion: reduce) {
  .stButton > button, .stDownloadButton > button { transition: none; }
}
</style>
"""


def load_background():
    mimes = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
    folder = Path(__file__).parent
    for name in ("background.jpg", "background.jpeg", "background.png", "background.webp"):
        path = folder / name
        if path.exists():
            try:
                return base64.b64encode(path.read_bytes()).decode(), mimes[path.suffix]
            except OSError:
                break
    return BG_IMAGE_B64, "image/jpeg"


def inject_css():
    b64, mime = load_background()
    st.markdown(CSS_TEMPLATE.replace("__MIME__", mime).replace("__B64__", b64), unsafe_allow_html=True)


# ------------------------------------------------------------------ المفتاح
def normalize_key(raw):
    """ينظّف المفتاح من المسافات وعلامات التنصيص وبادئة GROQ_API_KEY= لو نُسخت بالغلط."""
    k = str(raw or "").strip().strip("\"'").strip()
    if "=" in k:
        k = k.split("=", 1)[1].strip().strip("\"'").strip()
    return k


def resolve_key(manual):
    """يرجع (المفتاح، مصدره)."""
    k = normalize_key(manual)
    if k:
        return k, "الخانة اليدوية"
    try:
        v = normalize_key(st.secrets.get("GROQ_API_KEY", ""))
        if v:
            return v, "Streamlit Secrets"
    except Exception:  # لا يوجد ملف secrets أو صيغته خاطئة
        pass
    v = normalize_key(os.getenv("GROQ_API_KEY", ""))
    if v:
        return v, "متغير بيئة أو ملف .env"
    return "", "لا يوجد"


def mask_key(k):
    return f"{k[:4]}…{k[-4:]}  (الطول {len(k)})" if len(k) > 10 else "(قصير جدًا)"


def key_problems(k):
    out = []
    if k == PLACEHOLDER_KEY:
        out.append("المفتاح هو النص التجريبي وليس مفتاحًا حقيقيًا.")
    if not k.isascii():
        out.append("المفتاح فيه حروف غير إنجليزية (غالبًا نُسخ بالغلط).")
    if re.search(r"\s", k):
        out.append("المفتاح فيه مسافات داخله.")
    if k and not k.startswith("gsk_"):
        out.append("مفاتيح Groq تبدأ دائمًا بـ gsk_ وهذا لا يبدأ بها.")
    return out


def explain_error(e, source=""):
    src = f" (المفتاح المستخدم الآن مصدره: {source})" if source else ""
    if getattr(e, "status_code", None) == 413:
        m = re.search(r"Limit (\d+), Requested (\d+)", str(e))
        detail = f" (حد النموذج {m.group(1)} توكن، وطلبك {m.group(2)})" if m else ""
        return ("حجم الطلب أكبر من حد Groq للنموذج الحالي" + detail + ". الحل: قسّم الكود أو الرسالة "
                "لأجزاء أصغر، أو اضغط «محادثة جديدة» لمسح السجل، أو جرّب نموذجًا آخر (حدودها تختلف).")
    if isinstance(e, groq.AuthenticationError):
        return ("Groq رفضت المفتاح (401)" + src + ". افتح «حالة المفتاح» في الشريط الجانبي واضغط "
                "«اختبار المفتاح». لو المصدر Secrets فغيّر المفتاح من إعدادات التطبيق على Streamlit Cloud.")
    if isinstance(e, groq.NotFoundError):
        return "هذا النموذج غير متاح (ربما تم إيقافه). اختر نموذجًا آخر من الشريط الجانبي."
    if isinstance(e, groq.RateLimitError):
        return "وصلت للحد المسموح مؤقتًا. انتظر قليلًا أو جرّب نموذجًا آخر."
    if isinstance(e, groq.APIConnectionError):
        return "تعذر الاتصال بخدمة Groq. تحقق من الإنترنت ثم أعد المحاولة."
    if isinstance(e, groq.APIStatusError):
        return f"رفضت Groq الطلب (رمز الخطأ {e.status_code}). جرّب نموذجًا آخر."
    return f"حدث خطأ غير متوقع: {e}"


def test_key(key, source):
    try:
        data = Groq(api_key=key, timeout=20.0, max_retries=0).models.list().data
        return True, f"المفتاح مقبول من Groq، وفيه {len(data)} نموذج متاح."
    except Exception as e:
        return False, explain_error(e, source)


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_models(api_key):
    try:
        data = Groq(api_key=api_key, timeout=20.0, max_retries=1).models.list().data
        ids = sorted(m.id for m in data)
        ids = [i for i in ids if not any(h in i.lower() for h in NON_CHAT_HINTS)]
        if ids:
            return ids, True
    except Exception:
        pass
    return FALLBACK_MODELS, False


def order_models(ids):
    first = [m for m in FALLBACK_MODELS if m in ids]
    return first + [m for m in ids if m not in first]


# ------------------------------------------------------------------ الحفظ
def slugify(text):
    return re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_") or "chat"


def save_text(filename, text):
    try:
        OUTPUT_DIR.mkdir(exist_ok=True)
        path = OUTPUT_DIR / filename
        path.write_text(text, encoding="utf-8")
        return path
    except OSError:
        return None


def chat_transcript(title, messages, model):
    lines = [f"# {APP_TITLE} — {title}", f"- التاريخ: {datetime.now():%Y-%m-%d %H:%M}",
             f"- النموذج: {model}", ""]
    for m in messages:
        lines += ["## " + ("أنت" if m["role"] == "user" else "المساعد"), m["content"], ""]
    return "\n".join(lines)


# ------------------------------------------------------------------ الشريط الجانبي
def render_sidebar():
    with st.sidebar:
        st.markdown("## ⚡ Magdy AI Suite")
        workspace = st.radio("Choose Workspace:", list(WORKSPACES) + [CTE_NAME])
        st.divider()

        manual = ""
        key, source = resolve_key("")
        with st.expander("حالة المفتاح", expanded=not key):
            manual = st.text_input(
                "مفتاح مؤقت للتجربة (اختياري)", type="password",
                help="لو كتبت مفتاحًا هنا يُستخدم بدل مفتاح Secrets في هذه الجلسة فقط.")
            key, source = resolve_key(manual)
            if key:
                st.caption(f"المصدر: {source}")
                st.caption(f"البصمة: {mask_key(key)}")
                for p in key_problems(key):
                    st.warning(p)
                if st.button("اختبار المفتاح", use_container_width=True):
                    ok, msg = test_key(key, source)
                    (st.success if ok else st.error)(msg)
            else:
                st.caption("لم يتم العثور على أي مفتاح.")

        ctx = {"workspace": workspace, "key": key, "source": source, "client": None,
               "model": None, "temperature": 0.4, "autosave": True}
        if not key or key == PLACEHOLDER_KEY:
            return ctx

        ctx["client"] = Groq(api_key=key, timeout=60.0, max_retries=2)
        models, live = fetch_models(key)
        ctx["model"] = st.selectbox("النموذج", order_models(models))
        if not live:
            st.warning("تعذر جلب قائمة النماذج الحالية، فعرضت قائمة احتياطية.")
        st.button("تحديث قائمة النماذج", on_click=fetch_models.clear, use_container_width=True)
        ctx["temperature"] = st.slider("الإبداع (Temperature)", 0.0, 1.0, 0.4, 0.1)
        ctx["autosave"] = st.checkbox("حفظ تلقائي في مجلد outputs", value=True)
        st.caption("لا ترفع مفتاحك على GitHub. ضعه في Secrets فقط.")
    return ctx


def no_key_notice():
    st.info(
        "لم يتم العثور على مفتاح Groq. على Streamlit Cloud: افتح إعدادات التطبيق ← Secrets "
        "وأضف السطر  GROQ_API_KEY = \"gsk_...\"  (بعلامتي التنصيص). أو جرّب مفتاحًا مؤقتًا "
        "من «حالة المفتاح» في الشريط الجانبي."
    )


# ------------------------------------------------------------------ مساحات المحادثة
def trim_history(history, max_chars=MAX_CONTEXT_CHARS):
    """يحتفظ بأحدث الرسائل التي يتسع لها الحد، ودائمًا بآخر رسالة."""
    kept, total = [], 0
    for m in reversed(history[-MAX_HISTORY:]):
        total += len(m["content"])
        if kept and total > max_chars:
            break
        kept.append(m)
    return list(reversed(kept))


def stream_answer(ctx, system_prompt, history):
    recent = trim_history(history)
    if len(recent) < len(history[-MAX_HISTORY:]):
        st.caption("تم تجاهل الرسائل الأقدم عند الإرسال لتقليل حجم الطلب.")
    messages = [{"role": "system", "content": system_prompt}] + recent
    stream = ctx["client"].chat.completions.create(
        model=ctx["model"], messages=messages, temperature=ctx["temperature"], stream=True)
    status = st.empty()
    status.caption("جاري التفكير...")

    def tokens():
        first = True
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                if first:
                    status.empty()
                    first = False
                yield chunk.choices[0].delta.content
        status.empty()

    return st.write_stream(tokens())


def render_chat(ws, ctx):
    info = WORKSPACES[ws]
    st.subheader(ws)
    st.caption(info["desc"])
    if not ctx["client"]:
        no_key_notice()
        return

    msgs = st.session_state.chats.setdefault(ws, [])
    prompt = st.chat_input("اكتب رسالتك...")
    if not msgs and not prompt:
        st.markdown('<div style="height:26vh"></div>', unsafe_allow_html=True)
    for m in msgs:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    if prompt:
        msgs.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            try:
                answer = stream_answer(ctx, info["prompt"], msgs)
                if answer:
                    msgs.append({"role": "assistant", "content": answer})
                else:
                    st.warning("لم يصل رد من النموذج. أعد المحاولة أو اختر نموذجًا آخر.")
            except Exception as e:
                st.error(explain_error(e, ctx["source"]))

    if msgs:
        text = chat_transcript(ws, msgs, ctx["model"])
        fname = f"{PROJECT_NAME}_{slugify(ws)}_{st.session_state.stamp}.md"
        with st.sidebar:
            st.download_button("تحميل المحادثة", data=text, file_name=fname,
                               mime="text/markdown", use_container_width=True)
            if ctx["autosave"] and save_text(fname, text):
                st.caption(f"محفوظة في: outputs/{fname}")


# ------------------------------------------------------------------ Clear Thinking Engine
CTE_QUESTIONS_SYSTEM = (
    "You help a person who is stuck on a personal, study or career decision. Read it carefully and "
    "write 3 or 4 SHORT clarifying questions in simple Arabic that are specific to the CONTENT of "
    "this decision (for example: money needed, a skill they lack, time it takes, what is reversible, "
    "what they really want). Do not ask generic questions about mood or tiredness. One question per "
    "line, numbered. No introduction, no closing, no jargon."
)

CTE_RESULT_SYSTEM = """You are a calm, practical decision coach for an Arabic-speaking student or young adult.
Use ONLY the facts the person gave. If something important is missing, say so and state your assumption
explicitly. Never invent facts, statistics or sources. Write in simple, clear Arabic with short sentences.
No motivational fluff. No jargon in the main sections.

Output EXACTLY these sections, each starting with a level-2 markdown heading ("## ") with these exact titles:

## الخلاصة
(2-3 sentences: what the real decision is and what is actually blocking the person.)

## خطوتك الجاية
(ONE concrete action that takes under 15 minutes, specific to their situation.)

## تجربة صغيرة
(A cheap, reversible test they can run within a few days, and what result would mean yes or no.)

## انتبه لده
(1-2 ways their own thinking may be misleading them here, in plain words, tied to what they wrote.)

## تحليل أعمق
(Use "### " sub-headings: ### تفكيك المشكلة (First Principles), ### النتائج بعيدة المدى (Second-Order),
### مصفوفة القرار with a markdown table with columns: الخيار | المزايا | العيوب | مستوى المخاطرة
(منخفض/متوسط/مرتفع). Add one short Arabic explanation next to every English term. If no options were
given, infer 2-3 from the text and say that you inferred them.)"""


def parse_questions(text):
    qs = []
    for line in text.splitlines():
        m = re.match(r"^\s*(?:\d+\s*[\.\)\-:]|[-•*])\s*(.+)$", line.strip())
        if m:
            qs.append(m.group(1).replace("**", "").strip())
    if not qs:
        qs = [l.strip() for l in text.splitlines() if "؟" in l or "?" in l]
    return qs[:5]


def split_sections(md):
    parts = re.split(r"(?m)^##\s+", md)
    sections = []
    for p in parts[1:]:
        title, _, body = p.partition("\n")
        sections.append((title.strip(), body.strip()))
    return sections or [("", md.strip())]


def cte_call(ctx, system, user, temperature):
    r = ctx["client"].chat.completions.create(
        model=ctx["model"], temperature=temperature,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}])
    return (r.choices[0].message.content or "").strip()


def cte_reset():
    st.session_state.cte = {}
    for k in list(st.session_state.keys()):
        if k.startswith("cte_a_"):
            del st.session_state[k]
    for k in ("cte_problem", "cte_options", "cte_constraints"):
        st.session_state[k] = ""


def cte_back():
    """يرجع لمرحلة كتابة القرار مع استعادة النص الذي كتبه المستخدم."""
    s = st.session_state.cte
    st.session_state.cte_problem = s.get("problem", "")
    st.session_state.cte_options = s.get("options", "")
    st.session_state.cte_constraints = s.get("constraints", "")
    st.session_state.cte = {}
    for k in list(st.session_state.keys()):
        if k.startswith("cte_a_"):
            del st.session_state[k]


def cte_brief(s, answers=None):
    lines = [f"القرار/المشكلة: {s['problem']}"]
    if s.get("options"):
        lines.append(f"الخيارات المطروحة: {s['options']}")
    if s.get("constraints"):
        lines.append(f"القيود والسياق: {s['constraints']}")
    if answers:
        lines.append("أسئلة وإجابات:")
        for q, a in answers:
            lines.append(f"- س: {q}\n  ج: {a if a.strip() else '(لم يُجب)'}")
    return "\n".join(lines)


def render_cte(ctx):
    st.subheader(CTE_NAME + " — بوصلة التفكير الواضحة")
    st.caption("اكتب قرارك بكلامك. الأداة تسألك أسئلة تخص قرارك أنت، ثم تعطيك خطوة واحدة واضحة.")
    if not ctx["client"]:
        no_key_notice()
        return

    s = st.session_state.cte

    # المرحلة 0: كتابة القرار
    if not s.get("questions"):
        st.text_area("ما القرار أو المشكلة التي تشغل بالك؟", key="cte_problem", height=110,
                     placeholder="مثال: عندي خياران لمشروع التخرج ولا أستطيع الحسم بينهما...")
        st.text_area("الخيارات المطروحة (اختياري، سطر لكل خيار)", key="cte_options", height=80)
        st.text_input("قيود أو سياق (اختياري: الوقت، المال، ...)", key="cte_constraints")
        if st.button("ابدأ", type="primary"):
            problem = st.session_state.get("cte_problem", "").strip()
            if len(problem) < 10:
                st.warning("اكتب القرار بجملة أو جملتين على الأقل.")
                return
            new = {"problem": problem,
                   "options": st.session_state.get("cte_options", "").strip(),
                   "constraints": st.session_state.get("cte_constraints", "").strip()}
            with st.spinner("أقرأ قرارك وأجهّز أسئلة تخصه..."):
                try:
                    qs = parse_questions(cte_call(ctx, CTE_QUESTIONS_SYSTEM, cte_brief(new), 0.3))
                except Exception as e:
                    st.error(explain_error(e, ctx["source"]))
                    return
            if not qs:
                st.warning("لم أستطع تجهيز أسئلة. أعد الصياغة وجرّب مرة أخرى.")
                return
            new["questions"] = qs
            st.session_state.cte = new
            st.rerun()
        return

    # المرحلة 1: الأسئلة
    if not s.get("result"):
        with st.container(border=True):
            st.markdown("**قرارك:** " + s["problem"])
        st.markdown("جاوب باختصار (وتقدر تتخطى أي سؤال):")
        for i, q in enumerate(s["questions"]):
            st.text_input(q, key=f"cte_a_{i}")
        c1, c2 = st.columns([2, 1])
        if c1.button("حلّل قراري", type="primary", use_container_width=True):
            answers = [(q, st.session_state.get(f"cte_a_{i}", "")) for i, q in enumerate(s["questions"])]
            with st.spinner("أحلل قرارك..."):
                try:
                    s["result"] = cte_call(ctx, CTE_RESULT_SYSTEM, cte_brief(s, answers), 0.3)
                except Exception as e:
                    st.error(explain_error(e, ctx["source"]))
                    return
            s["answers"] = answers
            s["stamp"] = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.rerun()
        c2.button("تعديل القرار", on_click=cte_back, use_container_width=True)
        return

    # المرحلة 2: النتيجة
    for title, body in split_sections(s["result"]):
        if title.startswith("تحليل أعمق"):
            with st.expander("تحليل أعمق (للمهتم بالتفاصيل)"):
                st.markdown(body)
        else:
            with st.container(border=True):
                if title:
                    st.markdown(f"### {title}")
                st.markdown(body)

    report = "\n".join([
        f"# {APP_TITLE} — Clear Thinking Engine", f"- التاريخ: {datetime.now():%Y-%m-%d %H:%M}",
        f"- النموذج: {ctx['model']}", "", "## المدخلات", cte_brief(s, s.get("answers")), "",
        "## النتيجة", s["result"]])
    fname = f"{PROJECT_NAME}_ClearThinking_{s['stamp']}.md"
    st.download_button("تحميل النتيجة", data=report, file_name=fname, mime="text/markdown")
    st.button("قرار جديد", on_click=cte_reset)
    if ctx["autosave"] and save_text(fname, report):
        st.caption(f"محفوظة في: outputs/{fname}")


# ------------------------------------------------------------------ الرئيسية
def main():
    st.set_page_config(page_title=APP_TITLE, page_icon="⚡", layout="centered",
                       initial_sidebar_state="expanded")
    if not GROQ_AVAILABLE:
        st.error("مكتبة groq غير مثبتة. أضف السطر  groq  إلى ملف requirements.txt في المستودع.")
        st.stop()

    inject_css()
    st.session_state.setdefault("chats", {})
    st.session_state.setdefault("cte", {})
    st.session_state.setdefault("stamp", datetime.now().strftime("%Y%m%d_%H%M%S"))

    st.markdown(
        f'<div class="hero"><h1>{APP_TITLE}</h1>'
        "<p>منصتك الذكية لتحليل الأكواد وإدارة محتوى الذكاء الاصطناعي</p></div>",
        unsafe_allow_html=True)

    ctx = render_sidebar()
    if ctx["workspace"] == CTE_NAME:
        render_cte(ctx)
    else:
        render_chat(ctx["workspace"], ctx)


# صورة الخلفية الافتراضية (Lamborghini) مدمجة بصيغة Base64. لا حاجة لتعديلها.
BG_IMAGE_B64 = """
/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAMCAgMCAgMDAwMEAwMEBQgFBQQEBQoHBwYIDAoMDAsKCwsNDhIQDQ4RDgsLEBYQERMUFRUVDA8XGBYUGBIUFRT/
2wBDAQMEBAUEBQkFBQkUDQsNFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBT/wAARCALgBRwDASIAAhEBAxEB/8QA
HwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkK
FhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXG
x8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAEC
AxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOE
hYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD8qqKKKACi
iigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKd/FTaACil20MtAC/xVJHzUf8AFUqrtq4lxFooorU1CiiigAooooAKKKKACiii
gAooooAKKKKACiiiq6gHSilaocn0qJClLlJNwpN4qLaaNtR7xlzhupKdtFFPkJ5g/iptLtqTalFgIqKX+L5aNtZAJtNLzUlFK5PMR80q5p9FK4uYKKKKRIUU
UUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABSbRS0UAJtpdq0UUx3CiiikIKKKKACii
igAooooAKKKKACiiigAooooAKKKKACiiigAooooAKNzUUU7juG32pu2n7TRtNac4EW2jb70/FG2r92RVxtIrbaWk20SiVck3BqfUNOVsVMf7xrzEu6jdTFcC
nVoVzBRRRTGFFFFABRRRQAUUUUAFFFFABRRRQAbvmoaoclfrS+ZXPIUZiN3ptPZqT+KgzkNop38VNoICiiigAooooAKKKKACiiigAooooAKKKKACiiigAooo
oAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiineWfSgBu00YqTy6Xy6di+WRHto2mp/LpdtO0iuQh2n0pdhp+2lq+UXKR+WPSl2+1Poo5Yl8oVHItSt
TdopOISI1jqWn4plXFcocvKFFFFMYUUUUAFFFO/ioATdRupKTcKVhcw7dSbhTGb+7TKLEc5LuH96k3imYNGDVcpPOO8z2o8z2plFMXNIfvpvHrTvmo2+1RzR
FzDKKXbTqj2hAynbfalope0kO4bfal20lFS5SJFwKSiioELx60lFFIAooooAKKKKACiiigAooooAKKKKACiiimAUUUUAFFFFABRTttSbarlAhoqbaKj27fvU
coDaKdto21XIA2inbaNtLlAbRTttG2jkYDaKdto20cjAbRTttG2jkYDaKdto20cjAbRTttG2lygNop22jbT5ZDG0U7aKNtHIxDaKdtpafIAyinbaNvftRyAN
oqTy6d5Y9KnlAhoqTy2p/FDiBHRTvxp2w1fKK5BRU3ln+9S+SP71HKHMQUVN5dLsNHKHMQUVI0dR7fao5RhRRRUgFFFFIAooooAKKKKACiiigAooooAKKKKA
CiiigBWptLRWik4jG7aSn0U+crmGUU/atJtq4yiFwz70u5abtpK090rmJdwpahop9Sucn3Ubqh3H1pyt/epWK9oSbqN1N3ClqbF8wUUUUxhRRRQAjKGqFl21
YIpvFZyiRKJBtNG01NsFN20uUjlY5R8uKTZRtagntSKG+WaPLNSLS1fKPliQlStHPrU+OM03bUtByEFFKy0v8VQZDaKKKACiiigAooooAKKKKACiiigAoooo
AKKKKACiiigAooooAKKKKACiiigAoxTlXdT9vtTRfKCrtqX+Km0VtGPKahRRRTAKKKKACiiigAooooAKKKKACiiiq6gLuo3VGzUbmpW1M/aD6RpBUe00YNHK
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
Kv8AFUtFAFeilakqywqJl21LTG71cS4jKglj2/N/DU9Iy7lpy94Uo8xWqJqsSx7fmqFlH3qwM/hGUUUVZQUjLupaKAIqKkdaQLVl8xBuf7u2pKKKCgooooAk
WlpFpagyCiiigAqaolqWokRIVfvLVmqtWq2iXAKelMpVaqNSWiiisjIKfF9+mUq430AT0UUVBAVLu/i/hqKl3fJVxkMsJipKiX7lPVquRox1FFFQSTRVYgqr
E1Wrdv4aAJ6lt1+7UVSwf65aANOrdn/FVSrNqwV9v96gDQiWtCP7q1nxN89XomGz5aANKD7lXrVfnWqNrWha/wCsWgDQirSiXdtrNirSib7tAGtF1WtizjeT
yUjXfI2FX/eNY9v91a6bQ7iPS7O81aZti2cH7v8A66N8q1ZZj/Ev4lXfgW2j0bQ7qW0kgP7+6t32NJN/F8y/wjtXzn4t8aX+rXMk+oX1xe3DfxXEzP8A+hVc
8feKpLq5kZpGdsla8zurg3D7t1QQSXF48r7laq+7dSUUAFFFFABRRRQAUjUtMZqAIZfl2svybT96rEuzXIdkn7q+jHyt/eqGVgqNuqmzfOrK2xl+aNq1sEij
LJJA7Iy7JF+8tSRapLH91q0riNNZh/55XkY+b/arnZd8UzI3+srIDYj1y4WTd/EtakvjrULxVW8uJbtVHlr9odn2r/d+bNcjuo8z+GgvlNy4jtrz51j8pm/u
1Pofw/13xhqX9naFYvqt40Ms/wBnt/veXGu6RvwWuc8xl+7W74R8bar4J8Sabrmk3DW+oafOs8Ev+0P73+y3egOUr2Nvpa2cclzHqM9w33kiRfKrQXVbKz/4
9dPS3b+9JZtI3/jzV6x8afB8fibRbf4r+DbFofB+tH/iYWVn93RdR/5bQMq/cjZvmT/ZfbXiS30rbY2upUoINZvE1+8exdauoo2/hihZF/8AHazZZI7h902p
b2/6apJVhbO9ZNy3DPUMsN6r/M0rrQQQ7oV+7eW//j3/AMTR9oiX/l4if/vr/wCJprrdr/8AZVCzXf8AeX/vigsm+3xf89Fpv2yP/nov/fdRbrv0X/viomab
7rLH/wB8UBzFxbgN/Ev/AH3UysW+7t/77Ws2OFvvGOJv+AVJ5Jb/AJd4t1AcxpKsrfw/+PrUi28//POsfbKv/LGKneZIv3o1SgDa+xz/APPFqb9lm/54tWfb
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
5lG6ggdRRRQAbvepEao6N22gmUSWl3D+7Ue7bTd3vUByk3mf981J5m35duyq/mH1o8ygXvFjzvu07d935qrrMad5h+b+CrHzSJfM/wB6k87+9UPmUbv9qjmE
TNNu/hpu4f3aj3UeY1HMSTcN/wAs6GYf/YtUPmUbt1HMUSMy/e205pN38OyofM207zN3+7RzASbvn3bfu1N5hbbtVqqq395qk87+7Iz1fMBYXf8Ad205W/75
qn5gXd8tHnNvXcu/b/dqCy00n3fmo3fP93tVfd/e2/N/dpqyH/gNAFrd/e+SnLIdn3aotJt+6tOVgzN8zItAFxpD/FTfM/iVqr/aC3y7u38VN8wfd+4uKA5i
bzI5pv8AaX7tNutn2Zomj+aQ/wANQrjyWZpPmz93+KjaYkV/MXd97bQBjMpViG+8KbWhfxxs+9PlZj826qG2gBKKKKACiiigAooooAKKKKACiiigAooooAKK
KKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiig
AooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACnfxU2nx/L81AFqKFF2/LuapNx/u96q7pJd1WFkEsm/bs/wBlaAJvmoqP59lO
3BqAJGpaZu96KAHfJ/F/eo3Cm+1FAEn+792jn/gNR0UEkm6jzGpu6m7vegXKSLIaPMWo9zUbvegCbd/FR5p/u1Huo3UATeZ91duyjzDUO6jdQMm8z3o8wfpU
O6jcaBEjSH9aNwqPzD60eYP7tSHvDtwpu6m/LRVByjtw9KNw+9TabuFBfKOopu4UeZQA6mtTWmC/8CpvmBv4qsBzU3aFprSD7tN8wfNtoL5hzsy/7tNfP96j
zNv+9RuPzf7NQRINv8O7ZTdo/vUfL/7LRuLfxUEDljP95aNrt8u37tN8xm+Zv4abu/u0AO2nb93/AIFUdPV9u6l87/ZqB+6N3U5W281HRVxZBboqBW2v/vVI
s3975Kv3TeMh9FI0gT+Km+YlBfMPopNw2bqhab+7QRKRY2j+9TWqNZj/AHad5h/iWgIyJEam+cf7tRth/wCJaPu/dko90mUiZpNvy7Wo87/Zeo/M+9+8pvnH
f/rKCCx5n+y1HmD+7UPmH/np81O8z/pp/wCOVBY/zB/dak+0j+61R+YNn+sajzP+mjUASLcD+61OWQf3WqNpv7slCtufc0i7aCCTzB/DG26neZ/s1HuO/wC8
u2jcfvf3qCx26jzN3yrTWYrt+WjzE+7uoAk3e9G4bGXb8396ofOH8LVIsgb+KgB273p26o9wp24f3qAJlmC/7tDTbk21Csgo3J/eoAm3Cm+ZUe4LR5ib8bqC
OUk8w/Nt9Kb5h9aa0gV/7601ZN3O2gOUdu96NxX+Gmsyb13UecF+ZWoLJPu0bt3y1H5m59q/eo8wdN1AcpIuP4qJVCsy+XsbNR+Z8jN/dqi1w7fxUAFxJumY
1FTv4qbQAU7+Km0UALxRxSUUAO/iptFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAU
UUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAO/ipNp/u0v8AFSbj/eoA
X+Kk4pf4qTigA4oVttL/ABU2gB6yFd3+1To2H92oqXcVoAtW7eb96j7R/wDE7f7tRLL/AHl+al+0H/nmu6gCx9oG+jzvm+b5Fqukzr92nNMf7u2gOYsNMKd5
g+ba2/bVVZj/ABNR5jtt+agOYm84fe205ZP++ah+ff8Aep3mBv8AYVaA5iTzP71O8z5Pu1H50fzU793s3f3qC+Ydupvme1NVt33fSjj5vm+7QIk8xdjfL81N
8ymsyfwtTVk3v96rD3STzKPOWm7k/wBmjcn+zUEjt4/2qN49Hpv8ed1G07/9ZsoCQ7ePR6POC/w03cf+e1DN/wBNKsB32hP7r03zk/utTdxb5vMo/wC21QQO
8wN/C9N85P7r0bv+nijcP+e33qCxPOT+7S+cP+edR7R/fWnL/vf+OVXukA8g/hjpvmbuWVaHWm7T92plIA3UbqNpptQSKtKqmm0UAO2n+7S0m2jdTKBWP/Aa
GWjd/wDtUtacwDKKKKyJCiiigAooooAKKKKACiiigAooooAKKKKAFyaMmkooAduNNoooAKXJpKKACiiigAp+4f3f/HqZRQA7zP8AZoVh/EtNooHcduK9KPMP
rTaKBEnmNQshSo6KCuYk84/w01ZCr7qbRQK5J5jtQq7mZvuLSKxX7rfeG2m5NAXJfOdX+Vt602WYy/w1HRQFxy5p7y7v4VT/AHaiooC5IsndvSo2kP8AwKim
tVlIPMOzb/DSfxUfxU2goKKKKACiiigAp38VNooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooA
KKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAd/FSbqSi
gAooooAKKKKACiiigAp60ylVqAJKKM0bveoMgpvmH7v8NObvTdtMqJI2N3ytuptFFIkKXJpKKAFyaXcf71NooAKKKKACiiigApcmkooAXd2oyaSigAooooAV
WK0ZNJRQAuTS+Y396m0UALzSUUUAFFFFABRRRQAUUUUAFFFFABRRRQAinFLu96iyaMmrNLEtFM703JpWFyku5abupmTRk0wsP3UbqZk07IoHYfuWimd6bk1N
hcpLRu96iyaMmnYOUloqLJp3enyhyj6KbupPMPrU2Fyj6KTdRuoFZi0U3zKbuosPlJKKj3Uu80WDlH0Um6kyaBco6io91G6iw+UkoqPdQrGq5Q5SXJoyaZmj
JquQLDqKRTS1Mo8ogoopN1SFhaKbuo3UgsObvTSc0lFWUNooooKCiil3UAJRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFF
FABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQA
UUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQA7vSbjSUu6gA3UbqNxo3GgBaXcaONtJWsYxJHZpdy0yk4qZRiHKSbvejdtqLJoyaysHKSZFLu
WosmjJqh2JaKiyad3pWFyj6Kj3GjdSsLlJKKiyaMmnYfKS0VHuNG40rC5SSio91O3VXKHKOopu6jdT5GKw6io91G6osPlJKN3vUe40veiwco7Io3VHk0ZNUV
Yl3e9FRZNGTSsLlJaKiyaXcaLByklFM3mjeaVhco2iiiqLCiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigB38VH
8VNooAd/FSbqSigB2716UfxU2igBd1JRRQAUUUUAFO/iptFADv4qOP7tNooAd/FTaKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiii
gAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAK
KKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKd/FTaKAHfxU2iigAooooAKKKKACiiigAooooAKKKKACiiigApd1L/FTa
AJPvc5ptNoq+aQBRRRUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFF
ABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAU
UUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFF
ABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAU
UUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFF
ABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAU
UUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFF
ABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAU
UUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFF
ABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAU
UUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFF
ABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAU
UUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFF
ABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAU
UUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFF
ABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAU
UUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFF
ABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAU
UUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFF
ABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAU
UUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFF
ABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUU7+KgBtFFFABRRRQAUUUUAFFFFABRRR
QAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAF
FFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRR
QAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFS+c/leXu/d53bfeoqKACiiigAooooAKKKKACiiigAooooAKK
KKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigApzFdq8fN3ptFABUkrBtuF28Co6KACiiigAooooAKKKKACiiigAooooAKKKKACii
igAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooA
KKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACii
igAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooA
KKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKAP/Z
""".replace("\n", "")

if __name__ == "__main__":
    main()
