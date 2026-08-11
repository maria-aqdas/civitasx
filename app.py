import streamlit as st
import plotly.express as px
import pandas as pd
from pypdf import PdfReader
from analyzer import analyze_policy
from io import BytesIO
from gtts import gTTS

# OCR fallback for scanned PDFs
import pytesseract
from pdf2image import convert_from_bytes

# Map dropdown language names to gTTS language codes for voice playback
TTS_LANG_CODES = {
    "English": "en",
    "Urdu": "ur",
    "Hindi": "hi",
    "Arabic": "ar",
    "French": "fr",
    "Spanish": "es",
    "Chinese": "zh-CN",
    "Turkish": "tr",
    "Bengali": "bn",
    "Pashto": "ps",
}

# Languages that read right-to-left and need mirrored text alignment
RTL_LANGUAGES = {"Urdu", "Arabic", "Pashto"}

# ---------------- Page Configuration ----------------
st.set_page_config(
    page_title="CivitasX - Policy Impact Simulator",
    page_icon="🏛️",
    layout="wide"
)

# ---------------- Custom Modern Dashboard Styling ----------------
st.markdown("""
<style>
    /* Overall background - clean dark slate/charcoal */
    .stApp {
        background: #0d1117;
        color: #e6edf3 !important;
    }

    /* Force readable light text everywhere by default */
    .stApp, .stApp p, .stApp span, .stApp label, .stMarkdown, .stCaption {
        color: #e6edf3 !important;
    }

    /* Title - clean indigo/teal gradient */
    h1 {
        background: linear-gradient(90deg, #38bdf8, #6366f1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
    }

    /* Metric cards */
    .stMetric {
        background: #161b22;
        padding: 16px;
        border-radius: 12px;
        border: 1px solid #30363d;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
    .stMetric label, .stMetric [data-testid="stMetricValue"] {
        color: #e6edf3 !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #0a0d12;
        border-right: 1px solid #21262d;
    }
    section[data-testid="stSidebar"] * {
        color: #e6edf3 !important;
    }

    /* Text areas / inputs */
    .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: #161b22 !important;
        color: #e6edf3 !important;
        border: 1px solid #30363d !important;
    }

    /* Submit button */
    .stButton>button, .stFormSubmitButton>button {
        background: linear-gradient(90deg, #6366f1, #38bdf8) !important;
        color: #ffffff !important;
        font-weight: bold !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.6em 1em !important;
        box-shadow: 0 4px 14px rgba(99, 102, 241, 0.4);
        transition: transform 0.15s ease-in-out;
    }
    .stButton>button:hover, .stFormSubmitButton>button:hover {
        transform: scale(1.02);
    }

    /* Modern minimal impact cards */
    .impact-box {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 14px;
        padding: 22px 20px;
        height: 100%;
        color: #e6edf3 !important;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.3);
    }
    .impact-box li {
        color: #c9d1d9 !important;
        margin-bottom: 10px;
        line-height: 1.5;
    }
    .impact-box ul {
        list-style: none;
        margin: 0;
        padding: 0;
    }
    .impact-box .icon-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 34px;
        height: 34px;
        border-radius: 10px;
        font-size: 16px;
        margin-bottom: 10px;
    }
    .impact-box h4 {
        margin: 0 0 14px 0;
        color: #ffffff !important;
        font-size: 1.15rem;
    }
    .benefit-box { border-top: 3px solid #34d399; }
    .benefit-box .icon-badge { background: rgba(52, 211, 153, 0.15); }
    .risk-box { border-top: 3px solid #f87171; }
    .risk-box .icon-badge { background: rgba(248, 113, 113, 0.15); }
    .env-box { border-top: 3px solid #38bdf8; }
    .env-box .icon-badge { background: rgba(56, 189, 248, 0.15); }

    /* Info / success / error boxes text */
    .stAlert p {
        color: #0d1117 !important;
        font-weight: 500;
    }

    /* Section divider */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #30363d, transparent);
    }
</style>
""", unsafe_allow_html=True)

# ---------------- Header ----------------
st.title("🏛️ CivitasX — AI Policy Impact Simulator")
st.caption("✨ Turn any policy draft into clear, easy-to-read insights on its economic, social, and environmental impact.")
st.markdown("---")

# ---------------- Sidebar Form ----------------
st.sidebar.markdown("## 📥 Input Policy Data")
st.sidebar.caption("Paste text or upload a PDF to get started 🚀")

with st.sidebar.form(key="policy_submission_form", clear_on_submit=False):
    input_option = st.radio("Choose Input Method:", ("📝 Paste Text Proposal", "📄 Upload Policy PDF"))
    user_text = st.text_area("Paste policy draft here:", height=180, placeholder="Type or paste policy proposal...")
    uploaded_file = st.file_uploader("Upload Policy PDF Document", type=["pdf"])
    selected_language = st.selectbox(
        "🌐 Output Language",
        list(TTS_LANG_CODES.keys()),
        index=0
    )
    submit_button = st.form_submit_button(label="✅ Submit & Run Simulation", use_container_width=True)

# ---------------- Main Processing ----------------
if submit_button:
    policy_text = ""

    if input_option == "📝 Paste Text Proposal":
        policy_text = user_text.strip()
    else:
        if uploaded_file is not None:
            try:
                file_bytes = uploaded_file.getvalue()

                # Step 1: Try normal text extraction (fast, works for text-based PDFs)
                reader = PdfReader(uploaded_file)
                extracted_pages = []
                for page in reader.pages:
                    txt = page.extract_text()
                    if txt and txt.strip():
                        extracted_pages.append(txt.strip())
                policy_text = "\n\n".join(extracted_pages)

                # Step 2: If empty, likely a scanned PDF -> OCR fallback
                if not policy_text:
                    with st.spinner("📄 No selectable text found — running OCR on scanned PDF..."):
                        images = convert_from_bytes(file_bytes)
                        ocr_pages = []
                        for image in images:
                            ocr_text = pytesseract.image_to_string(image)
                            if ocr_text and ocr_text.strip():
                                ocr_pages.append(ocr_text.strip())
                        policy_text = "\n\n".join(ocr_pages)

                if not policy_text:
                    st.error("⚠️ Could not extract any text from this PDF, even with OCR. Try a clearer scan or paste the text directly.")
            except Exception as pdf_err:
                st.error(f"Error reading PDF file: {str(pdf_err)}")
        else:
            st.error("⚠️ Please select a PDF file first before submitting!")

    if policy_text:
        with st.spinner("⚡ Running AI simulation on policy content..."):
            try:
                data = analyze_policy(policy_text, language=selected_language)
                is_rtl = selected_language in RTL_LANGUAGES
                text_dir = "rtl" if is_rtl else "ltr"
                text_align = "right" if is_rtl else "left"

                # Executive Overview
                title_html = f"""<div dir="{text_dir}" style="text-align:{text_align};">
                    <h3>📋 Analysis: {data.get('policy_title', 'Policy Analysis')}</h3>
                </div>"""
                st.markdown(title_html, unsafe_allow_html=True)

                summary_html = f"""<div dir="{text_dir}" style="text-align:{text_align};
                    background: #161b22;
                    border: 1px solid #30363d;
                    border-radius: 12px; padding: 16px; color:#e6edf3; line-height:1.9;">
                    <b>Summary:</b> {data.get('summary', 'No summary available.')}
                    </div>"""
                st.markdown(summary_html, unsafe_allow_html=True)

                # Voice / Text-to-Speech playback of the summary
                try:
                    tts_lang_code = TTS_LANG_CODES.get(selected_language, "en")
                    tts_text = data.get("summary", "")
                    if tts_text:
                        tts = gTTS(text=tts_text, lang=tts_lang_code)
                        audio_buffer = BytesIO()
                        tts.write_to_fp(audio_buffer)
                        audio_buffer.seek(0)
                        st.audio(audio_buffer, format="audio/mp3")
                except Exception:
                    st.caption("🔇 Voice playback is not available for this language right now.")

                st.markdown("---")

                # Impact Scores
                st.subheader("📊 Policy Impact Ratings (Out of 100)")
                scores = data.get("scores", {})
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("💰 Economic Impact", f"{scores.get('economic_impact', 0)}/100")
                m2.metric("⚖️ Social Equity", f"{scores.get('social_equity', 0)}/100")
                m3.metric("🌱 Environmental Benefit", f"{scores.get('environmental_benefit', 0)}/100")
                m4.metric("📣 Public Sentiment", f"{scores.get('public_sentiment', 0)}/100")

                st.markdown("<br>", unsafe_allow_html=True)

                # 3 Core Impact Boxes (colorful HTML cards)
                st.subheader("🎯 Detailed Impact Breakdown")
                col_benefit, col_risk, col_env = st.columns(3)

                with col_benefit:
                    benefits_html = "".join(f"<li>🟢 {b}</li>" for b in data.get("benefits", []))
                    st.markdown(
                        f"""<div class="impact-box benefit-box" dir="{text_dir}" style="text-align:{text_align};">
                        <div class="icon-badge">✅</div>
                        <h4>Benefits</h4>
                        <ul>{benefits_html}</ul>
                        </div>""",
                        unsafe_allow_html=True
                    )

                with col_risk:
                    risks_html = "".join(f"<li>🟠 {r}</li>" for r in data.get("risks", []))
                    st.markdown(
                        f"""<div class="impact-box risk-box" dir="{text_dir}" style="text-align:{text_align};">
                        <div class="icon-badge">⚠️</div>
                        <h4>Risks &amp; Drawbacks</h4>
                        <ul>{risks_html}</ul>
                        </div>""",
                        unsafe_allow_html=True
                    )

                with col_env:
                    env_html = "".join(f"<li>🟣 {e}</li>" for e in data.get("environmental_impact", []))
                    st.markdown(
                        f"""<div class="impact-box env-box" dir="{text_dir}" style="text-align:{text_align};">
                        <div class="icon-badge">🌿</div>
                        <h4>Environmental Impact</h4>
                        <ul>{env_html}</ul>
                        </div>""",
                        unsafe_allow_html=True
                    )

                st.markdown("---")

                # Visual Chart
                st.subheader("📈 Multi-Dimensional Score Breakdown")
                df = pd.DataFrame({
                    "Dimension": ["💰 Economic", "⚖️ Social Equity", "🌱 Environmental", "📣 Sentiment"],
                    "Score": [
                        scores.get("economic_impact", 0),
                        scores.get("social_equity", 0),
                        scores.get("environmental_benefit", 0),
                        scores.get("public_sentiment", 0)
                    ]
                })
                fig = px.bar(
                    df, x="Dimension", y="Score", color="Dimension", text="Score",
                    range_y=[0, 100], template="plotly_dark",
                    color_discrete_sequence=["#6366f1", "#38bdf8", "#34d399", "#f87171"]
                )
                fig.update_traces(textposition="outside")
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.error(f"Error executing analysis: {str(e)}")

else:
    st.info("👈 Upload a PDF or paste your policy text in the sidebar, then click **'Submit & Run Simulation'**.")
