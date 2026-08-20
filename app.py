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

SAMPLE_POLICY = (
    "Implement a 10% tax on single-use plastic packaging sold by manufacturers "
    "and retailers. The revenue collected will fund recycling infrastructure "
    "and provide subsidies for businesses switching to biodegradable packaging. "
    "Small businesses with under $50,000 in annual revenue are exempt for the first two years."
)

# ---------------- Page Configuration ----------------
st.set_page_config(
    page_title="CivitasX - Policy Impact Simulator",
    page_icon="🏛️",
    layout="wide"
)

# ---------------- Custom Light Theme Styling ----------------
st.markdown("""
<style>
    /* Overall background - soft, easy-on-the-eyes off-white */
    .stApp {
        background: #f6f7fb;
        color: #1f2430 !important;
    }

    .stApp, .stApp p, .stApp span, .stApp label, .stMarkdown, .stCaption {
        color: #1f2430 !important;
    }

    /* Title - clean indigo/teal gradient, still pops on white */
    h1 {
        background: linear-gradient(90deg, #4f46e5, #0ea5e9);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
    }

    /* Metric cards */
    .stMetric {
        background: #ffffff;
        padding: 16px;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 2px 10px rgba(17, 24, 39, 0.06);
    }
    .stMetric label, .stMetric [data-testid="stMetricValue"] {
        color: #1f2430 !important;
    }

    /* Top header bar */
    header[data-testid="stHeader"] {
        background: #f6f7fb !important;
    }

    /* File uploader dropzone */
    [data-testid="stFileUploaderDropzone"] {
        background-color: #ffffff !important;
        border: 1.5px dashed #d1d5db !important;
    }
    [data-testid="stFileUploaderDropzone"] * {
        color: #1f2430 !important;
    }
    [data-testid="stFileUploaderDropzoneInstructions"] svg {
        fill: #4f46e5 !important;
    }

    /* File uploader - catch-all fix for any dark nested elements */
    [data-testid="stFileUploader"] {
        background-color: transparent !important;
    }
    [data-testid="stFileUploader"] section {
        background-color: #ffffff !important;
    }
    html body [data-testid="stFileUploaderFile"],
    html body [data-testid="stFileUploaderFile"] *,
    html body [data-testid="stFileUploaderFile"] div,
    html body [data-testid="stFileUploaderFile"] span,
    html body [data-testid="stFileUploaderFile"] small,
    html body .uploadedFileData,
    html body .uploadedFileData * {
        background-color: #eef0fb !important;
        color: #1f2430 !important;
        -webkit-text-fill-color: #1f2430 !important;
    }
    [data-testid="stFileUploaderFile"] {
        border-radius: 8px;
        padding: 4px 8px;
    }
    [data-testid="stFileUploaderFileIcon"] svg,
    [data-testid="stFileUploaderFile"] svg {
        fill: #4f46e5 !important;
    }
    [data-testid="baseButton-secondary"] {
        background-color: #ffffff !important;
        color: #1f2430 !important;
        border: 1px solid #d1d5db !important;
    }

    /* "Browse files" button inside uploader */
    [data-testid="stFileUploaderDropzone"] button {
        background-color: #4f46e5 !important;
        color: #ffffff !important;
        border: none !important;
    }
    [data-testid="stFileUploaderDropzone"] button p {
        color: #ffffff !important;
    }
    [data-testid="stFileUploaderDropzoneInstructions"] div,
    [data-testid="stFileUploaderDropzoneInstructions"] span,
    [data-testid="stFileUploaderDropzoneInstructions"] small {
        color: #1f2430 !important;
    }

    /* Selectbox - force every nested element to be light + readable, including the dropdown arrow icon */
    html body [data-testid="stSelectbox"],
    html body [data-testid="stSelectbox"] *,
    html body [data-baseweb="select"],
    html body [data-baseweb="select"] *,
    html body [data-baseweb="select"] div,
    html body [data-baseweb="select"] span {
        background-color: #ffffff !important;
        color: #1f2430 !important;
        fill: #1f2430 !important;
        -webkit-text-fill-color: #1f2430 !important;
        border-color: #d1d5db !important;
    }
    html body [data-baseweb="select"] svg {
        fill: #4f46e5 !important;
        background-color: transparent !important;
    }
    /* The little arrow/indicator box on the right edge of the dropdown */
    html body [data-baseweb="select"] [data-testid="stSelectboxVirtualDropdown"],
    html body [data-baseweb="select"] > div > div:last-child {
        background-color: #ffffff !important;
    }
    div[data-baseweb="popover"],
    div[data-baseweb="popover"] * {
        background-color: #ffffff !important;
        color: #1f2430 !important;
        -webkit-text-fill-color: #1f2430 !important;
    }
    div[data-baseweb="popover"] li:hover {
        background-color: #eef0fb !important;
    }

    /* Main block container */
    .block-container {
        background: #f6f7fb;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #e5e7eb;
    }
    section[data-testid="stSidebar"] * {
        color: #1f2430 !important;
    }

    /* Text areas / inputs */
    .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: #ffffff !important;
        color: #1f2430 !important;
        border: 1px solid #d1d5db !important;
    }

    /* Segmented / pill-style horizontal radio for input method */
    div[role="radiogroup"] {
        display: flex;
        gap: 8px;
        background: #f0f1f6;
        padding: 4px;
        border-radius: 10px;
    }
    div[role="radiogroup"] label {
        flex: 1;
        text-align: center;
        border-radius: 8px;
        padding: 6px 4px;
    }

    /* Submit button - primary indigo/sky */
    .stFormSubmitButton>button {
        background: linear-gradient(90deg, #4f46e5, #0ea5e9) !important;
        color: #ffffff !important;
        font-weight: bold !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.6em 1em !important;
        box-shadow: 0 4px 14px rgba(79, 70, 229, 0.25);
        transition: transform 0.15s ease-in-out;
    }
    .stFormSubmitButton>button * {
        color: #ffffff !important;
    }
    .stFormSubmitButton>button:hover {
        transform: scale(1.02);
    }

    /* Download button - teal/emerald, distinct from submit */
    .stDownloadButton>button {
        background: linear-gradient(90deg, #059669, #10b981) !important;
        color: #ffffff !important;
        font-weight: bold !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.6em 1em !important;
        box-shadow: 0 4px 14px rgba(5, 150, 105, 0.3);
        transition: transform 0.15s ease-in-out;
    }
    .stDownloadButton>button * {
        color: #ffffff !important;
    }
    .stDownloadButton>button:hover {
        transform: scale(1.02);
    }

    /* Sidebar quick-action buttons (Try Sample / Reset) - distinct colors */
    section[data-testid="stSidebar"] .stButton>button {
        font-weight: bold !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.5em 0.8em !important;
        transition: transform 0.15s ease-in-out;
    }
    section[data-testid="stSidebar"] .stButton>button * {
        color: #ffffff !important;
    }
    section[data-testid="stSidebar"] .stButton:nth-of-type(1)>button {
        background: linear-gradient(90deg, #f59e0b, #f97316) !important;
        box-shadow: 0 4px 14px rgba(249, 115, 22, 0.3);
    }
    section[data-testid="stSidebar"] .stButton:nth-of-type(2)>button {
        background: linear-gradient(90deg, #64748b, #475569) !important;
        box-shadow: 0 4px 14px rgba(71, 85, 105, 0.25);
    }
    section[data-testid="stSidebar"] .stButton>button:hover {
        transform: scale(1.02);
    }

    /* Secondary (outline-style) buttons */
    .secondary-btn button {
        background: #ffffff !important;
        color: #4f46e5 !important;
        border: 1.5px solid #4f46e5 !important;
        box-shadow: none !important;
    }

    /* Impact cards - clean white cards, soft shadow, colored top accent */
    .impact-box {
        background: #ffffff;
        border: 1px solid #eef0f5;
        border-radius: 14px;
        padding: 22px 20px;
        height: 100%;
        color: #1f2430 !important;
        box-shadow: 0 4px 16px rgba(17, 24, 39, 0.07);
    }
    .impact-box li {
        color: #374151 !important;
        margin-bottom: 10px;
        line-height: 1.55;
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
        width: 36px;
        height: 36px;
        border-radius: 10px;
        font-size: 17px;
        margin-bottom: 10px;
    }
    .impact-box h4 {
        margin: 0 0 14px 0;
        color: #1f2430 !important;
        font-size: 1.15rem;
    }
    .benefit-box { border-top: 4px solid #10b981; }
    .benefit-box .icon-badge { background: rgba(16, 185, 129, 0.12); }
    .risk-box { border-top: 4px solid #f97316; }
    .risk-box .icon-badge { background: rgba(249, 115, 22, 0.12); }
    .env-box { border-top: 4px solid #0ea5e9; }
    .env-box .icon-badge { background: rgba(14, 165, 233, 0.12); }

    /* Footer feature cards */
    .footer-box {
        background: #ffffff;
        border: 1px solid #eef0f5;
        border-radius: 14px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 16px rgba(17, 24, 39, 0.06);
    }
    .footer-box .emoji {
        font-size: 32px;
        margin-bottom: 8px;
    }

    /* Info / alert boxes */
    .stAlert p {
        color: #1f2430 !important;
        font-weight: 500;
    }

    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #d1d5db, transparent);
    }

    /* Subtle hover lift on impact/footer cards for a premium feel */
    .impact-box, .footer-box {
        transition: transform 0.18s ease, box-shadow 0.18s ease;
    }
    .impact-box:hover, .footer-box:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 24px rgba(17, 24, 39, 0.12);
    }

    /* Tighter, cleaner spacing for headings */
    h3 {
        letter-spacing: -0.01em;
    }

    /* Caption text a touch softer for hierarchy */
    .stCaption, [data-testid="stCaptionContainer"] p {
        color: #6b7280 !important;
    }

    /* Sidebar section spacing */
    section[data-testid="stSidebar"] .block-container {
        padding-top: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ---------------- Header ----------------
st.title("🏛️ CivitasX — AI Policy Impact Simulator")
st.markdown(
    """<div style="display:inline-block; background:#eef0fb; color:#4f46e5;
    padding:6px 14px; border-radius:20px; font-size:0.9rem; font-weight:600; margin-bottom:8px;">
    ✨ Turn any policy draft into clear, easy-to-read insights on its economic, social, and environmental impact.
    </div>""",
    unsafe_allow_html=True
)
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")

# ---------------- Sidebar ----------------
st.sidebar.markdown("## 📥 Input Policy Data")
st.sidebar.caption("Paste text or upload a PDF to get started 🚀")

# Quick-action buttons (outside the form, so they act instantly)
btn_col1, btn_col2 = st.sidebar.columns(2)
with btn_col1:
    load_sample = st.button("🎯 Try Sample", use_container_width=True)
with btn_col2:
    reset_clicked = st.button("🔄 Reset", use_container_width=True)

if load_sample:
    st.session_state["policy_text_input"] = SAMPLE_POLICY
if reset_clicked:
    st.session_state["policy_text_input"] = ""

with st.sidebar.form(key="policy_submission_form", clear_on_submit=False):
    user_text = st.text_area(
        "Paste policy draft here:",
        height=180,
        placeholder="Type or paste policy proposal...",
        key="policy_text_input"
    )
    st.caption("— or —")
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

    # If a PDF is uploaded, it takes priority; otherwise use the pasted text.
    if uploaded_file is not None:
        status_box = st.empty()
        status_box.info(f"📄 Received **{uploaded_file.name}** — reading file, please wait...")
        try:
            file_bytes = uploaded_file.getvalue()

            # Step 1: Try normal text extraction (fast, works for text-based PDFs)
            reader = PdfReader(uploaded_file)
            num_pages = len(reader.pages)
            status_box.info(f"📄 Found {num_pages} page(s) — extracting text...")

            extracted_pages = []
            for page in reader.pages:
                txt = page.extract_text()
                if txt and txt.strip():
                    extracted_pages.append(txt.strip())
            policy_text = "\n\n".join(extracted_pages)

            # Step 2: If empty, likely a scanned PDF -> OCR fallback
            if not policy_text:
                status_box.info("📄 No selectable text found — running OCR on scanned PDF (this can take a bit longer)...")
                images = convert_from_bytes(file_bytes)
                ocr_pages = []
                for idx, image in enumerate(images, start=1):
                    status_box.info(f"🔍 Running OCR on page {idx} of {len(images)}...")
                    ocr_text = pytesseract.image_to_string(image)
                    if ocr_text and ocr_text.strip():
                        ocr_pages.append(ocr_text.strip())
                policy_text = "\n\n".join(ocr_pages)

            if not policy_text:
                status_box.error("⚠️ Could not extract any text from this PDF, even with OCR. Try a clearer scan or paste the text directly.")
            else:
                status_box.success(f"✅ Text extracted successfully from {num_pages} page(s)! Running AI analysis...")
        except Exception as pdf_err:
            status_box.error(f"Error reading PDF file: {str(pdf_err)}")
    elif user_text.strip():
        policy_text = user_text.strip()
    else:
        st.error("⚠️ Please paste some policy text or upload a PDF first!")

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

                if data.get("_was_truncated"):
                    st.warning("⚠️ Ye document bohot lamba tha, is liye sirf shuru ka hissa analyze kiya gaya hai.")

                summary_html = f"""<div dir="{text_dir}" style="text-align:{text_align};
                    background: #ffffff;
                    border: 1px solid #eef0f5;
                    border-radius: 12px; padding: 18px; color:#1f2430; line-height:1.9;
                    box-shadow: 0 4px 16px rgba(17, 24, 39, 0.06);">
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
                    env_html = "".join(f"<li>🔵 {e}</li>" for e in data.get("environmental_impact", []))
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
                    range_y=[0, 100], template="plotly_white",
                    color_discrete_sequence=["#4f46e5", "#0ea5e9", "#10b981", "#f97316"]
                )
                fig.update_traces(textposition="outside", textfont_color="#1f2430")
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#1f2430",
                    legend_font_color="#1f2430",
                    xaxis=dict(color="#1f2430", title_font_color="#1f2430", tickfont_color="#1f2430"),
                    yaxis=dict(color="#1f2430", title_font_color="#1f2430", tickfont_color="#1f2430"),
                )
                st.plotly_chart(fig, use_container_width=True)

                # Download report as a text file
                report_text = (
                    f"CivitasX Policy Analysis\n\n"
                    f"Title: {data.get('policy_title', '')}\n\n"
                    f"Summary:\n{data.get('summary', '')}\n\n"
                    f"Benefits:\n" + "\n".join(f"- {b}" for b in data.get("benefits", [])) + "\n\n"
                    f"Risks:\n" + "\n".join(f"- {r}" for r in data.get("risks", [])) + "\n\n"
                    f"Environmental Impact:\n" + "\n".join(f"- {e}" for e in data.get("environmental_impact", [])) + "\n\n"
                    f"Scores: {scores}\n"
                )
                st.download_button(
                    "📥 Download Full Report (.txt)",
                    data=report_text,
                    file_name=f"{data.get('policy_title', 'policy_analysis')}.txt",
                    use_container_width=True
                )

            except Exception as e:
                err_text = str(e)
                if "RESOURCE_EXHAUSTED" in err_text or "429" in err_text:
                    st.error(
                        "⚠️ Filhal bohot zyada log ye app use kar rahe hain, ya document "
                        "bohot bada hai. Meherbani kar ke 1 minute wait kar ke dobara try karein."
                    )
                elif "API_KEY" in err_text or "PERMISSION_DENIED" in err_text or "401" in err_text:
                    st.error("⚠️ App ki API key mein masla hai. App owner se rabta karein.")
                else:
                    st.error("⚠️ Kuch masla ho gaya hai analysis run karte waqt. Dobara try karein, ya chota document use karein.")

else:
    st.info("👈 Upload a PDF or paste your policy text in the sidebar, then click **'Submit & Run Simulation'**. Or hit **'Try Sample'** for a quick demo!")

    # ---------------- Footer / "How it works" section (fills empty space) ----------------
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("---")
    st.subheader("✨ How CivitasX Works")

    f1, f2, f3 = st.columns(3)
    with f1:
        st.markdown(
            """<div class="footer-box">
            <div class="emoji">📄</div>
            <h4>1. Provide a Policy</h4>
            <p>Paste text or upload a PDF — even scanned documents work with built-in OCR.</p>
            </div>""",
            unsafe_allow_html=True
        )
    with f2:
        st.markdown(
            """<div class="footer-box">
            <div class="emoji">🤖</div>
            <h4>2. AI Analyzes It</h4>
            <p>Google Gemini breaks it down into benefits, risks, and environmental effects.</p>
            </div>""",
            unsafe_allow_html=True
        )
    with f3:
        st.markdown(
            """<div class="footer-box">
            <div class="emoji">📊</div>
            <h4>3. Get Clear Insights</h4>
            <p>See simple scores, charts, and even listen to the summary out loud.</p>
            </div>""",
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.caption("🏛️ CivitasX — Built for smarter, safer governance. Made with Streamlit + Google Gemini.")
