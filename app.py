import streamlit as st
import pdfplumber
import pandas as pd
import json
import io
import re
import time
from datetime import datetime
from groq import Groq

try:
    import google.generativeai as genai
    _GEMINI_OK = True
except ImportError:
    _GEMINI_OK = False

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CSE Pro Dual Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# PREMIUM CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp {
    background: linear-gradient(135deg, #0a0e1a 0%, #0d1526 50%, #0a1020 100%);
    min-height: 100vh;
}
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1a2e 0%, #0a1020 100%) !important;
    border-right: 1px solid rgba(99,179,237,0.15);
}
section[data-testid="stSidebar"] .block-container { padding-top: 2rem; }

.hero-header {
    background: linear-gradient(135deg, rgba(99,179,237,0.08) 0%, rgba(154,105,255,0.08) 100%);
    border: 1px solid rgba(99,179,237,0.2);
    border-radius: 20px;
    padding: 2.5rem 3rem;
    margin-bottom: 2rem;
    text-align: center;
    backdrop-filter: blur(10px);
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
}
.hero-title {
    font-size: 2.4rem; font-weight: 800; margin-bottom: 0.5rem;
    background: linear-gradient(135deg, #63b3ed 0%, #9a69ff 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
}
.hero-subtitle { color: rgba(160,174,192,0.8); font-size: 1rem; line-height: 1.8; }

.step-card {
    background: rgba(13,26,46,0.6);
    border: 1px solid rgba(99,179,237,0.1);
    border-radius: 14px;
    padding: 1.2rem;
    text-align: center;
    transition: all 0.3s ease;
}
.step-card:hover { border-color: rgba(99,179,237,0.3); transform: translateY(-2px); }

.metric-card {
    background: rgba(13,26,46,0.7);
    border: 1px solid rgba(99,179,237,0.12);
    border-radius: 14px;
    padding: 1.2rem 1.4rem;
    transition: all 0.3s ease;
}
.metric-card:hover { border-color: rgba(99,179,237,0.25); box-shadow: 0 4px 20px rgba(0,0,0,0.3); }
.metric-value { font-size: 1.5rem; font-weight: 700; color: #63b3ed; margin-bottom: 0.2rem; }
.metric-label { font-size: 0.72rem; color: rgba(160,174,192,0.6); text-transform: uppercase; letter-spacing: 1.5px; }

.section-label {
    font-size: 0.75rem; font-weight: 600; color: rgba(99,179,237,0.7);
    text-transform: uppercase; letter-spacing: 2px;
    margin: 1.5rem 0 0.8rem; padding-bottom: 0.5rem;
    border-bottom: 1px solid rgba(99,179,237,0.1);
}
.badge-buy   { background: rgba(72,187,120,0.15); color: #68d391; padding: 0.3rem 0.8rem; border-radius: 20px; font-weight: 600; font-size: 0.85rem; }
.badge-sell  { background: rgba(245,101,101,0.15); color: #fc8181; padding: 0.3rem 0.8rem; border-radius: 20px; font-weight: 600; font-size: 0.85rem; }
.badge-hold  { background: rgba(236,201,75,0.15);  color: #f6e05e; padding: 0.3rem 0.8rem; border-radius: 20px; font-weight: 600; font-size: 0.85rem; }

.info-box    { background: rgba(99,179,237,0.07); border: 1px solid rgba(99,179,237,0.15); border-radius: 12px; padding: 1rem 1.2rem; margin: 0.8rem 0; font-size: 0.85rem; line-height: 1.8; }
.success-box { background: rgba(72,187,120,0.08);  border: 1px solid rgba(72,187,120,0.2);  border-radius: 10px; padding: 0.6rem 1rem; font-size: 0.82rem; color: #68d391; }
.warning-box { background: rgba(236,201,75,0.08);  border: 1px solid rgba(236,201,75,0.2);  border-radius: 10px; padding: 0.6rem 1rem; font-size: 0.82rem; color: #f6e05e; }
.error-box   { background: rgba(245,101,101,0.08); border: 1px solid rgba(245,101,101,0.2); border-radius: 10px; padding: 0.8rem 1rem; font-size: 0.85rem; color: #fc8181; }

.groq-badge   { background: linear-gradient(135deg,#f97316,#fb923c); color:#fff; padding:0.28rem 0.8rem; border-radius:20px; font-size:0.78rem; font-weight:600; }
.gemini-badge { background: linear-gradient(135deg,#4285f4,#34a853); color:#fff; padding:0.28rem 0.8rem; border-radius:20px; font-size:0.78rem; font-weight:600; }

.sidebar-logo { text-align:center; margin-bottom:1.2rem; }
.sidebar-logo-text { font-size:1.2rem; font-weight:700; background:linear-gradient(135deg,#63b3ed,#9a69ff); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
.sidebar-section-title { font-size:0.7rem; font-weight:600; color:rgba(99,179,237,0.6); text-transform:uppercase; letter-spacing:2px; margin:1rem 0 0.4rem; }

.stButton > button {
    background: linear-gradient(135deg, #3182ce 0%, #9a69ff 100%) !important;
    color: white !important; border: none !important;
    border-radius: 12px !important; font-weight: 600 !important;
    padding: 0.6rem 1.5rem !important; font-size: 1rem !important;
    transition: all 0.3s ease !important;
}
.stButton > button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(99,179,237,0.3) !important; }
hr { border-color: rgba(99,179,237,0.1) !important; margin: 1.5rem 0 !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
COLUMN_ORDER = [
    "Company Name", "Time Period", "Sector",
    "EPS (Earnings Per Share)", "NAV (Net Asset Value per Share)",
    "PE Ratio (Price to Earnings)", "PBV (Price to Book Value)",
    "Dividend Yield (%)", "Dividend Payout Ratio (%)",
    "ROE (Return on Equity)", "ROA (Return on Assets)",
    "Net Profit Margin (%)", "CASA Ratio (%)",
    "Debt to Equity Ratio", "Debt to Assets Ratio",
    "Current Ratio", "Quick Ratio",
    "Business Summary & Future Plans", "Final Recommendation",
]

GROQ_MODELS = {
    "llama-3.3-70b-versatile  (best quality)": "llama-3.3-70b-versatile",
    "llama3-70b-8192          (fast & reliable)": "llama3-70b-8192",
    "llama3-8b-8192           (fastest / low quota)": "llama3-8b-8192",
    "mixtral-8x7b-32768       (great reasoning)": "mixtral-8x7b-32768",
}

MAX_CHARS_GROQ   = 30_000   # Groq: 30k per chunk, 6k token/min limit
MAX_CHARS_GEMINI = 100_000  # Gemini Pro: 1M token context — full report in one shot
INTER_CHUNK_DELAY = 12      # seconds between Groq chunks
MODEL_NAME = "llama-3.3-70b-versatile"  # default; overwritten by sidebar

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS — PDF + CHUNKING
# ─────────────────────────────────────────────────────────────────────────────
def extract_text_from_pdf(uploaded_file) -> str:
    text_parts = []
    with pdfplumber.open(uploaded_file) as pdf:
        total = len(pdf.pages)
        bar = st.progress(0, text="📄 Extracting text from PDF…")
        for i, page in enumerate(pdf.pages):
            t = page.extract_text()
            if t:
                text_parts.append(t)
            bar.progress((i + 1) / total, text=f"📄 Reading page {i + 1} / {total}…")
        bar.empty()
    return "\n".join(text_parts)


def chunk_text(text: str, max_chars: int) -> list:
    chunks, start = [], 0
    while start < len(text):
        end = start + max_chars
        if end < len(text):
            split = text.rfind("\n\n", start, end)
            if split == -1: split = text.rfind("\n", start, end)
            if split == -1: split = end
        else:
            split = len(text)
        chunk = text[start:split].strip()
        if chunk:
            chunks.append(chunk)
        start = split
    return chunks


def build_prompt(text_chunk: str, chunk_index: int, total_chunks: int,
                 is_merge: bool = False) -> str:
    keys_json = json.dumps(COLUMN_ORDER, ensure_ascii=False)
    if is_merge:
        return f"""You are a senior financial analyst for Sri Lanka's Colombo Stock Exchange (CSE).
Merge the following partial JSON analyses of the SAME report into ONE coherent JSON object.
Prefer the most specific/detailed value when there are conflicts.

Partial results:
{text_chunk}

Return ONLY a single valid JSON object with EXACTLY these keys:
{keys_json}"""

    chunk_note = f"(Part {chunk_index + 1} of {total_chunks})" if total_chunks > 1 else ""
    return f"""You are a senior financial analyst for Sri Lanka's Colombo Stock Exchange (CSE).
Analyse this company report excerpt {chunk_note} and extract the financial data.

REPORT TEXT:
---
{text_chunk}
---

Return a JSON object with EXACTLY these keys:
{keys_json}

FORMATTING RULES (mandatory):
- EPS, NAV: include currency (e.g. "LKR 12.50")
- PE Ratio, PBV, Debt ratios, Current/Quick Ratio: numeric with 'x' suffix (e.g. "14.2x")
- All % fields: include % symbol (e.g. "18.4%")
- ROE, ROA, margins, yields: use % symbol (e.g. "22.1%")
- CASA Ratio: banks/finance companies only; else "N/A"
- Business Summary: 2-4 sentences — business model + key future plans
- Final Recommendation: "Buy", "Hold", or "Sell" + 1-sentence reason
- Use "Not Disclosed" if a value cannot be found"""


def parse_json_from_response(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end   = text.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON object found in model response.")
    return json.loads(text[start:end])


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS — RATE LIMIT
# ─────────────────────────────────────────────────────────────────────────────
def _is_rate_limit(exc: Exception) -> bool:
    return "429" in str(exc) or "rate_limit" in str(exc).lower()


def _countdown(seconds: int, label: str) -> None:
    slot = st.empty()
    for remaining in range(seconds, 0, -1):
        slot.markdown(
            f'<div class="warning-box">⏳ {label} — retrying in <b>{remaining}s</b>…</div>',
            unsafe_allow_html=True,
        )
        time.sleep(1)
    slot.empty()


# ─────────────────────────────────────────────────────────────────────────────
# AI ENGINES
# ─────────────────────────────────────────────────────────────────────────────
def call_groq(api_key: str, prompt: str, retries: int = 4) -> str:
    client  = Groq(api_key=api_key)
    backoff = [15, 30, 60]
    for attempt in range(retries):
        try:
            resp = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": "You are a financial analyst. Respond with valid JSON only. No markdown, no explanation."},
                    {"role": "user",   "content": prompt},
                ],
                temperature=0.1,
                max_tokens=4096,
                response_format={"type": "json_object"},
            )
            return resp.choices[0].message.content
        except Exception as e:
            if attempt < retries - 1:
                if _is_rate_limit(e):
                    wait = backoff[min(attempt, len(backoff) - 1)]
                    st.warning(f"⚠️ Groq rate-limit (attempt {attempt + 1}/{retries}). Waiting {wait}s…")
                    _countdown(wait, f"Groq rate-limit back-off (attempt {attempt + 1})")
                else:
                    wait = 2 ** attempt
                    st.warning(f"⚠️ Groq error (attempt {attempt + 1}/{retries}): {e}. Retrying in {wait}s…")
                    time.sleep(wait)
            else:
                raise
    raise RuntimeError("call_groq: all retries exhausted.")


def call_gemini(api_key: str, prompt: str, retries: int = 3) -> str:
    if not _GEMINI_OK:
        raise ImportError("google-generativeai not installed. Run: pip install google-generativeai")
    genai.configure(api_key=api_key)
    model   = genai.GenerativeModel("gemini-1.5-pro")   # Pro = high accuracy, 1M token context
    backoff = [15, 30, 60]
    for attempt in range(retries):
        try:
            resp = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(temperature=0.1, max_output_tokens=4096),
            )
            return resp.text
        except Exception as e:
            if attempt < retries - 1:
                if _is_rate_limit(e):
                    wait = backoff[min(attempt, len(backoff) - 1)]
                    st.warning(f"⚠️ Gemini rate-limit (attempt {attempt + 1}/{retries}). Waiting {wait}s…")
                    _countdown(wait, f"Gemini rate-limit back-off")
                else:
                    wait = 2 ** attempt
                    st.warning(f"⚠️ Gemini error (attempt {attempt + 1}/{retries}): {e}. Retrying in {wait}s…")
                    time.sleep(wait)
            else:
                raise
    raise RuntimeError("call_gemini: all retries exhausted.")


# ─────────────────────────────────────────────────────────────────────────────
# ANALYSIS ORCHESTRATOR
# ─────────────────────────────────────────────────────────────────────────────
def analyse_report(api_key: str, full_text: str, engine: str) -> dict:
    """Route to correct engine. Gemini = single call. Groq = chunked."""

    if engine == "Gemini":
        # ── Gemini Pro: massive context — send full report in ONE call ──────
        text = full_text[:MAX_CHARS_GEMINI]
        if len(full_text) > MAX_CHARS_GEMINI:
            st.markdown(
                f'<div class="warning-box">✨ Report trimmed to {MAX_CHARS_GEMINI:,} chars for Gemini Pro '
                '(covers all financial statements in most CSE reports).</div>',
                unsafe_allow_html=True,
            )
        st.info("✨ Gemini Pro — full report sent in a single API call…")
        bar = st.progress(0, text="✨ Gemini Pro analysing…")
        raw = call_gemini(api_key, build_prompt(text, 0, 1))
        bar.progress(1.0, text="✨ Gemini Pro done!")
        bar.empty()
        return parse_json_from_response(raw)

    else:
        # ── Groq: chunk to stay within 6k token/min limit ──────────────────
        text = full_text
        if len(text) > MAX_CHARS_GROQ * 3:   # hard cap at 3 chunks max
            text = text[:MAX_CHARS_GROQ * 3]
            st.markdown(
                f'<div class="warning-box">⚠️ Very long report trimmed to {MAX_CHARS_GROQ * 3:,} chars.</div>',
                unsafe_allow_html=True,
            )

        chunks = chunk_text(text, MAX_CHARS_GROQ)
        n = len(chunks)

        if n == 1:
            st.info("⚡ Groq — fits in a single API call, analysing now…")
        else:
            st.info(
                f"⚡ Groq — split into **{n} chunk(s)**. "
                f"**{INTER_CHUNK_DELAY}s cooldown** between chunks (token-rate limit)."
            )

        partial_results = []
        bar = st.progress(0, text="⚡ Groq analysing…")

        for i, chunk in enumerate(chunks):
            bar.progress((i + 1) / n, text=f"⚡ Groq — chunk {i + 1} / {n}…")
            if i > 0:
                _countdown(INTER_CHUNK_DELAY, f"Cooldown before chunk {i + 1} / {n}")
            raw = call_groq(api_key, build_prompt(chunk, i, n))
            try:
                partial_results.append(parse_json_from_response(raw))
            except Exception as e:
                st.warning(f"⚠️ Could not parse chunk {i + 1}: {e}")
                partial_results.append({"_raw": raw})

        bar.empty()

        if len(partial_results) == 1:
            return partial_results[0]

        # Merge chunks
        _countdown(INTER_CHUNK_DELAY, "Cooldown before merge call…")
        merge_str = json.dumps(partial_results, indent=2, ensure_ascii=False)
        with st.spinner("🔀 Merging partial analyses…"):
            raw = call_groq(api_key, build_prompt(merge_str, 0, 1, is_merge=True))
            return parse_json_from_response(raw)


# ─────────────────────────────────────────────────────────────────────────────
# DATA + EXCEL HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _norm(key: str) -> str:
    return re.sub(r'[^a-z0-9]', '', key.lower())


def build_dataframe(data: dict) -> pd.DataFrame:
    norm_map = {_norm(k): v for k, v in data.items()}
    row = {}
    for col in COLUMN_ORDER:
        row[col] = data.get(col) or norm_map.get(_norm(col), "Not Disclosed")
    return pd.DataFrame([row])


def _make_watermark():
    try:
        from PIL import Image, ImageDraw, ImageFont
        img  = Image.new("RGBA", (900, 600), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        font_big = font_med = None
        for fp in ["C:/Windows/Fonts/calibrib.ttf", "C:/Windows/Fonts/arial.ttf",
                   "C:/Windows/Fonts/segoeui.ttf"]:
            try:
                font_big = ImageFont.truetype(fp, 110)
                font_med = ImageFont.truetype(fp, 42)
                break
            except OSError:
                pass
        if font_big is None:
            font_big = font_med = ImageFont.load_default()
        draw.text((60, 180), "NALAKA",               fill=(80, 120, 200, 52), font=font_big)
        draw.text((55, 310), "CSE REPORT ANALYZER",  fill=(80, 120, 200, 38), font=font_med)
        img = img.rotate(-28, resample=Image.BICUBIC, expand=False)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf
    except Exception:
        return None


def dataframe_to_excel_bytes(df: pd.DataFrame,
                              company: str = "", period: str = "",
                              engine_used: str = "") -> bytes:
    from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
    from openpyxl.drawing.image import Image as XLImage
    from openpyxl.utils import get_column_letter

    fill_title  = PatternFill("solid", fgColor="0D1526")
    fill_brand  = PatternFill("solid", fgColor="091020")
    fill_spacer = PatternFill("solid", fgColor="0A1322")
    fill_header = PatternFill("solid", fgColor="1A3A5C")
    fill_data   = PatternFill("solid", fgColor="EEF5FF")
    thin = Border(
        left=Side(style='thin', color='B0CCE8'), right=Side(style='thin', color='B0CCE8'),
        top=Side(style='thin', color='B0CCE8'),  bottom=Side(style='thin', color='B0CCE8'),
    )
    ncols = len(COLUMN_ORDER)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="CSE Analysis", startrow=3)
        ws = writer.sheets["CSE Analysis"]

        # Row 1 — Title
        ws.merge_cells(f"A1:{get_column_letter(ncols)}1")
        t = ws["A1"]
        t.value     = f"CSE Financial Analysis Report  ·  {company}  ·  {period}"
        t.font      = Font(bold=True, size=15, color="FFFFFF", name="Calibri")
        t.fill      = fill_title
        t.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[1].height = 38

        # Row 2 — Nalaka credit
        ws.merge_cells(f"A2:{get_column_letter(ncols)}2")
        c = ws["A2"]
        engine_tag = f"Groq AI ⚡" if "Groq" in engine_used else "Gemini Pro ✨"
        c.value     = f"Analyzed by Nalaka  |  CSE Report Analyzer  |  Powered by {engine_tag}  |  github.com/prasadhnalaka"
        c.font      = Font(italic=True, size=9, color="63B3ED", name="Calibri")
        c.fill      = fill_brand
        c.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[2].height = 22

        # Row 3 — Spacer
        ws.merge_cells(f"A3:{get_column_letter(ncols)}3")
        ws["A3"].fill = fill_spacer
        ws.row_dimensions[3].height = 5

        # Row 4 — Headers
        for cell in ws[4]:
            cell.fill      = fill_header
            cell.font      = Font(bold=True, color="FFFFFF", size=9, name="Calibri")
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border    = thin
        ws.row_dimensions[4].height = 42

        # Row 5 — Data
        for cell in ws[5]:
            cell.fill      = fill_data
            cell.font      = Font(size=9, name="Calibri")
            cell.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
            cell.border    = thin
        ws.row_dimensions[5].height = 130

        # Column widths
        col_w = {
            "Company Name": 22, "Time Period": 14, "Sector": 20,
            "EPS (Earnings Per Share)": 20, "NAV (Net Asset Value per Share)": 20,
            "PE Ratio (Price to Earnings)": 18, "PBV (Price to Book Value)": 18,
            "Dividend Yield (%)": 16, "Dividend Payout Ratio (%)": 18,
            "ROE (Return on Equity)": 18, "ROA (Return on Assets)": 18,
            "Net Profit Margin (%)": 18, "CASA Ratio (%)": 16,
            "Debt to Equity Ratio": 16, "Debt to Assets Ratio": 16,
            "Current Ratio": 14, "Quick Ratio": 14,
            "Business Summary & Future Plans": 55, "Final Recommendation": 45,
        }
        for i, col in enumerate(COLUMN_ORDER, 1):
            ws.column_dimensions[get_column_letter(i)].width = col_w.get(col, 22)

        # Print footer
        ws.oddFooter.left.text   = f"Generated: {datetime.now().strftime('%Y-%m-%d')}"
        ws.oddFooter.left.size   = 8
        ws.oddFooter.center.text = "Analyzed by Nalaka  |  CSE Report Analyzer  |  github.com/prasadhnalaka"
        ws.oddFooter.center.size = 8
        ws.oddFooter.right.text  = "Page &P of &N"
        ws.oddFooter.right.size  = 8

        ws.freeze_panes = "A5"
        ws.sheet_view.showGridLines  = False
        ws.sheet_properties.tabColor = "1A3A5C"

        # Watermark
        wm = _make_watermark()
        if wm:
            xl_img        = XLImage(wm)
            xl_img.width  = 480
            xl_img.height = 320
            xl_img.anchor = "E5"
            ws.add_image(xl_img)

    output.seek(0)
    return output.getvalue()


def recommendation_badge(text: str) -> str:
    u = text.upper()
    if "BUY"  in u: return f'<span class="badge-buy">🟢 {text}</span>'
    if "SELL" in u: return f'<span class="badge-sell">🔴 {text}</span>'
    return f'<span class="badge-hold">🟡 {text}</span>'


# ─────────────────────────────────────────────────────────────────────────────
# ───────────────────────────────  SIDEBAR  ───────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<div class="sidebar-logo">'
        '<span class="sidebar-logo-text">📊 CSE Pro Analyzer</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Engine selector ──────────────────────────────────────────────────────
    st.markdown('<div class="sidebar-section-title">🤖 AI Engine</div>', unsafe_allow_html=True)
    engine_choice = st.radio(
        "AI Engine",
        options=["⚡  Groq Cloud  (Ultra Fast · Free)", "✨  Gemini Pro  (High Accuracy · Free)"],
        index=0,
        label_visibility="collapsed",
        help="Groq = fastest, great for most reports | Gemini Pro = higher accuracy, handles 100k chars in 1 call",
    )
    USE_GROQ = engine_choice.startswith("⚡")

    if USE_GROQ:
        st.markdown(
            '<div style="text-align:center;margin:0.6rem 0 1rem;">'
            '<span class="groq-badge">⚡ Powered by Groq</span></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="text-align:center;margin:0.6rem 0 1rem;">'
            '<span class="gemini-badge">✨ Powered by Gemini Pro</span></div>',
            unsafe_allow_html=True,
        )

    # ── API Key ──────────────────────────────────────────────────────────────
    if USE_GROQ:
        st.markdown('<div class="sidebar-section-title">🔑 Groq API Key</div>', unsafe_allow_html=True)
        api_key = st.text_input(
            "groq_key", type="password", placeholder="gsk_…",
            label_visibility="collapsed",
            help="Get FREE key: https://console.groq.com/keys",
        )
        if api_key:
            st.markdown('<div class="success-box">✅ Groq key loaded</div>', unsafe_allow_html=True)
        else:
            st.markdown(
                '<div class="warning-box">⚠️ Enter your Groq API key.<br>'
                '<a href="https://console.groq.com/keys" target="_blank" style="color:#ffc107;">'
                'Get FREE key →</a></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="sidebar-section-title">🔑 Gemini API Key</div>', unsafe_allow_html=True)
        api_key = st.text_input(
            "gemini_key", type="password", placeholder="AIza…",
            label_visibility="collapsed",
            help="Get FREE key: https://aistudio.google.com/app/apikey",
        )
        if api_key:
            st.markdown('<div class="success-box">✅ Gemini key loaded</div>', unsafe_allow_html=True)
        else:
            st.markdown(
                '<div class="warning-box">⚠️ Enter your Gemini API key.<br>'
                '<a href="https://aistudio.google.com/app/apikey" target="_blank" style="color:#ffc107;">'
                'Get FREE key →</a></div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="sidebar-section-title">⚙️ Settings</div>', unsafe_allow_html=True)

    # ── Model (Groq only) ────────────────────────────────────────────────────
    if USE_GROQ:
        model_label = st.selectbox(
            "Model", options=list(GROQ_MODELS.keys()), index=0,
            help="All FREE on Groq. llama-3.3-70b gives best financial analysis.",
        )
        MODEL_NAME = GROQ_MODELS[model_label]
    else:
        st.markdown(
            '<div style="color:rgba(160,174,192,0.6);font-size:0.78rem;">'
            'Model: <b style="color:#4285f4;">gemini-1.5-pro</b><br>'
            '<span style="color:rgba(160,174,192,0.4);font-size:0.7rem;">100k chars · 1M token context</span>'
            '</div>', unsafe_allow_html=True)
        MODEL_NAME = "gemini-1.5-pro"

    # ── Info ─────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown('<div class="sidebar-section-title">ℹ️ Engine Comparison</div>', unsafe_allow_html=True)
    st.markdown("""
<div style="color:rgba(160,174,192,0.7);font-size:0.78rem;line-height:1.8;">
<b style="color:#fb923c;">⚡ Groq</b><br>
· Ultra-fast (3–8 sec)<br>
· 30k chars / call<br>
· 30 RPM free tier<br><br>
<b style="color:#4285f4;">✨ Gemini Pro</b><br>
· Higher accuracy<br>
· 100k chars in 1 call<br>
· 15 RPM free tier
</div>
""", unsafe_allow_html=True)

    # ── Nalaka card ──────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(f"""
<div style="
  background:rgba(99,179,237,0.05);
  border:1px solid rgba(99,179,237,0.12);
  border-radius:12px;
  padding:0.9rem 1rem;
  text-align:center;
">
  <div style="font-size:1rem;font-weight:700;
    background:linear-gradient(135deg,#63b3ed,#9a69ff);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
    background-clip:text;margin-bottom:0.3rem;">Nalaka</div>
  <div style="color:rgba(160,174,192,0.55);font-size:0.7rem;line-height:1.7;">
    Developer &amp; Analyst<br>
    CSE Report Analyzer<br>
    <a href="https://github.com/prasadhnalaka" target="_blank"
       style="color:#63b3ed;text-decoration:none;">github.com/prasadhnalaka</a><br>
    {datetime.now().strftime("%Y")} · Groq ⚡ + Gemini Pro ✨
  </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# ────────────────────────────────  MAIN  ─────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
engine_name  = "Groq"   if USE_GROQ else "Gemini"
engine_icon  = "⚡"     if USE_GROQ else "✨"
engine_label = "Groq Cloud" if USE_GROQ else "Gemini Pro"

# Hero
st.markdown(f"""
<div class="hero-header">
    <div class="hero-title">📊 CSE Pro Report Analyzer</div>
    <div class="hero-subtitle">
        Upload a Colombo Stock Exchange Annual / Quarterly Report PDF<br>
        and extract <b>19 key financial ratios</b> — powered by <b style="color:#fb923c;">{engine_icon} {engine_label}</b>
    </div>
</div>
""", unsafe_allow_html=True)

# Step tracker
c1, c2, c3, c4 = st.columns(4)
for col, icon, step, label in [
    (c1, "📤", "Step 1", "Upload PDF"),
    (c2, "📄", "Step 2", "Extract Text"),
    (c3, engine_icon, "Step 3", f"{engine_label} Analysis"),
    (c4, "📥", "Step 4", "Download Excel"),
]:
    col.markdown(f"""
<div class="step-card">
  <div style="font-size:1.5rem;margin-bottom:0.4rem;">{icon}</div>
  <div style="font-size:0.65rem;color:rgba(99,179,237,0.5);text-transform:uppercase;letter-spacing:1.5px;">{step}</div>
  <div style="font-size:0.85rem;font-weight:600;color:#e2e8f0;">{label}</div>
</div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Upload
st.markdown('<div class="section-label">📁 Upload Report</div>', unsafe_allow_html=True)
uploaded_file = st.file_uploader("Upload Annual/Quarterly Report (PDF)", type="pdf", label_visibility="collapsed")

if uploaded_file:
    st.markdown(f"""
<div class="info-box">
📄 <b>File:</b> {uploaded_file.name}<br>
📦 <b>Size:</b> {uploaded_file.size / 1024:.1f} KB<br>
🤖 <b>Engine:</b> {engine_icon} {engine_label}
</div>""", unsafe_allow_html=True)

run_btn = st.button(f"{engine_icon} Analyse Report", use_container_width=False,
                    disabled=not (uploaded_file and api_key))

if not api_key:
    st.markdown(
        f'<div class="warning-box">⚠️ Enter your {engine_label} API key in the sidebar to begin.</div>',
        unsafe_allow_html=True)

if uploaded_file and api_key and run_btn:

    # STEP 1 — Extract
    with st.status("📄 Extracting text from PDF…", expanded=True) as st1:
        full_text = extract_text_from_pdf(uploaded_file)
        st1.update(label=f"✅ Extracted {len(full_text):,} characters from PDF", state="complete")
    with st.expander("📋 Text preview (first 2 000 chars)", expanded=False):
        st.text(full_text[:2000] + ("…" if len(full_text) > 2000 else ""))

    # STEP 2 — AI Analysis
    with st.status(f"{engine_icon} Running {engine_label} Analysis…", expanded=True) as st2:
        try:
            t0 = time.time()
            result_json = analyse_report(api_key, full_text, engine=engine_name)
            elapsed = time.time() - t0
            st2.update(label=f"✅ {engine_label} analysis complete in {elapsed:.1f}s {engine_icon}", state="complete")
        except Exception as err:
            st2.update(label="❌ Analysis failed", state="error")
            err_str = str(err)
            if "429" in err_str:
                st.markdown(f"""
<div class="error-box">
<b>🚫 429 — Rate Limit Hit on {engine_label}</b><br><br>
✅ <b>Quick fixes:</b><br>
{"1️⃣  Switch to <b>Gemini Pro ✨</b> in the sidebar — separate quota<br>" if USE_GROQ else
 "1️⃣  Switch to <b>Groq ⚡</b> in the sidebar — separate quota<br>"}
2️⃣  Wait 60 seconds and retry<br>
3️⃣  {"Change Groq model (each has own quota bucket)<br>" if USE_GROQ else "Check Gemini quota at console.cloud.google.com<br>"}
4️⃣  Get key: <a href="{'https://console.groq.com/keys' if USE_GROQ else 'https://aistudio.google.com/app/apikey'}" target="_blank" style="color:#63b3ed;">
{'console.groq.com/keys' if USE_GROQ else 'aistudio.google.com'}</a>
</div>""", unsafe_allow_html=True)
            elif "401" in err_str or "invalid" in err_str.lower():
                st.markdown(f'<div class="error-box"><b>🔑 Invalid API Key</b><br>Check your {engine_label} key in the sidebar.</div>', unsafe_allow_html=True)
            else:
                st.error(f"❌ {engine_label} error: {err}")
            st.stop()

    # STEP 3 — Display results
    df = build_dataframe(result_json)

    st.markdown("---")

    # Top 4 summary cards
    m1, m2, m3, m4 = st.columns(4)
    m1.markdown(f"""<div class="metric-card">
  <div class="metric-value" style="font-size:1rem;">{result_json.get("Company Name","—")}</div>
  <div class="metric-label">Company</div></div>""", unsafe_allow_html=True)
    m2.markdown(f"""<div class="metric-card">
  <div class="metric-value" style="font-size:1.1rem;">{result_json.get("Time Period","—")}</div>
  <div class="metric-label">Period</div></div>""", unsafe_allow_html=True)
    m3.markdown(f"""<div class="metric-card">
  <div class="metric-value" style="font-size:0.95rem;">{result_json.get("Sector","—")}</div>
  <div class="metric-label">Sector</div></div>""", unsafe_allow_html=True)
    rec = result_json.get("Final Recommendation", "—")
    m4.markdown(f"""<div class="metric-card">
  <div style="margin-bottom:0.3rem;">{recommendation_badge(rec)}</div>
  <div class="metric-label">Recommendation</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 14 ratio grid (4 columns)
    RATIO_FIELDS = [
        ("EPS (Earnings Per Share)",       "💰"),
        ("NAV (Net Asset Value per Share)","📒"),
        ("PE Ratio (Price to Earnings)",   "📊"),
        ("PBV (Price to Book Value)",      "📐"),
        ("Dividend Yield (%)",             "💵"),
        ("Dividend Payout Ratio (%)",      "📤"),
        ("ROE (Return on Equity)",         "🏆"),
        ("ROA (Return on Assets)",         "🏗️"),
        ("Net Profit Margin (%)",          "📈"),
        ("CASA Ratio (%)",                 "🏦"),
        ("Debt to Equity Ratio",           "⚖️"),
        ("Debt to Assets Ratio",           "📉"),
        ("Current Ratio",                  "🔄"),
        ("Quick Ratio",                    "⚡"),
    ]
    st.markdown('<div class="section-label">📊 Key Financial Ratios</div>', unsafe_allow_html=True)
    rcols = st.columns(4)
    for idx, (field, icon) in enumerate(RATIO_FIELDS):
        val = result_json.get(field, "Not Disclosed")
        rcols[idx % 4].markdown(f"""
<div class="metric-card" style="margin-bottom:0.8rem;">
  <div style="font-size:1.2rem;margin-bottom:0.25rem;">{icon}</div>
  <div style="font-size:0.95rem;font-weight:700;color:#63b3ed;margin-bottom:0.2rem;">{val}</div>
  <div style="font-size:0.65rem;color:rgba(160,174,192,0.6);text-transform:uppercase;letter-spacing:1px;">{field}</div>
</div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Business summary + recommendation
    st.markdown('<div class="section-label">📋 Business Summary & Recommendation</div>', unsafe_allow_html=True)
    col_l, col_r = st.columns(2)
    with col_l:
        biz = result_json.get("Business Summary & Future Plans", "N/A")
        st.markdown(f"""
<div class="metric-card" style="text-align:left;height:100%;">
  <div style="font-size:0.7rem;color:rgba(99,179,237,0.6);text-transform:uppercase;letter-spacing:1.5px;margin-bottom:0.5rem;">💼 Business Summary & Future Plans</div>
  <div style="color:#e2e8f0;font-size:0.88rem;line-height:1.7;">{biz}</div>
</div>""", unsafe_allow_html=True)
    with col_r:
        rec_val = result_json.get("Final Recommendation", "N/A")
        st.markdown(f"""
<div class="metric-card" style="text-align:left;height:100%;">
  <div style="font-size:0.7rem;color:rgba(99,179,237,0.6);text-transform:uppercase;letter-spacing:1.5px;margin-bottom:0.5rem;">🎯 Final Recommendation</div>
  <div style="margin-bottom:0.5rem;">{recommendation_badge(rec_val)}</div>
  <div style="color:#e2e8f0;font-size:0.85rem;line-height:1.6;margin-top:0.4rem;">{rec_val}</div>
</div>""", unsafe_allow_html=True)

    with st.expander("🗂️ Raw DataFrame", expanded=False):
        st.dataframe(df, use_container_width=True)
    with st.expander("🔧 Raw JSON from AI", expanded=False):
        st.json(result_json)

    # STEP 4 — Download
    st.markdown("---")
    st.markdown("### 📥 Download Results")

    company = result_json.get("Company Name", "")
    period  = result_json.get("Time Period", "")
    excel_bytes = dataframe_to_excel_bytes(df, company=company, period=period, engine_used=engine_name)

    dl_col, info_col = st.columns([1, 2])
    with dl_col:
        st.download_button(
            label="📥 Download Excel Report",
            data=excel_bytes,
            file_name="CSE_Analysis_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with info_col:
        st.markdown(f"""
<div class="info-box" style="margin-top:0;">
📁 <b>File:</b> CSE_Analysis_Report.xlsx<br>
📊 <b>Rows:</b> 1 &nbsp;|&nbsp; 📋 <b>Columns:</b> {len(COLUMN_ORDER)}<br>
{engine_icon} <b>Engine:</b> {engine_label}<br>
💧 <b>Watermark:</b> NALAKA · CSE Report Analyzer
</div>""", unsafe_allow_html=True)

else:
    st.markdown(f"""
<div style="
    text-align:center; padding:4rem 2rem;
    background:rgba(13,26,46,0.4);
    border:1px dashed rgba(99,179,237,0.2);
    border-radius:20px; margin-top:1rem;
">
    <div style="font-size:4rem;margin-bottom:1rem;">📂</div>
    <div style="font-size:1.3rem;font-weight:600;color:#e2e8f0;margin-bottom:0.5rem;">
        Upload a CSE Report to Begin
    </div>
    <div style="color:rgba(160,174,192,0.6);font-size:0.9rem;max-width:440px;margin:0 auto;line-height:1.7;">
        Enter your <b style="color:#fb923c;">{engine_icon} {engine_label} API key</b> in the sidebar,
        upload your PDF, and click <b style="color:#9a69ff;">{engine_icon} Analyse Report</b>.<br><br>
        Switch engines anytime — <b style="color:#fb923c;">⚡ Groq</b> for speed,
        <b style="color:#4285f4;">✨ Gemini Pro</b> for larger reports!
    </div>
</div>
""", unsafe_allow_html=True)
