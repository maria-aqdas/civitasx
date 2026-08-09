import streamlit as st
import plotly.express as px
import pandas as pd
from pypdf import PdfReader
from analyzer import analyze_policy

# OCR fallback for scanned PDFs
import pytesseract
from pdf2image import convert_from_bytes

# ---------------- Page Configuration ----------------
st.set_page_config(
    page_title="CivitasX - Policy Impact Simulator",
    page_icon="🏛️",
    layout="wide"
)

# ---------------- Custom "VIP" Styling ----------------
st.markdown("""
<style>
    /* Overall background gradient */
    .stApp {
        background: linear-gradient(160deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    }

    /* Title glow */
    h1 {
        background: linear-gradient(90deg, #00d4ff, #a259ff, #ff5da2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
    }

    /* Metric cards */
    .stMetric {
        background: linear-gradient(145deg, #1e1b3a, #2a2550);
        padding: 16px;
        border-radius: 14px;
        border: 1px solid rgba(0, 212, 255, 0.35);
        box-shadow: 0 4px 15px rgba(162, 89, 255, 0.15);
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1533, #0f0c29);
        border-right: 1px solid rgba(255,255,255,0.08);
    }

    /* Submit button */
    .stButton>button, .stFormSubmitButton>button {
        background: linear-gradient(90deg, #a259ff, #00d4ff) !important;
        color: white !important;
        font-weight: bold !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.6em 1em !important;
        box-shadow: 0 4px 14px rgba(162, 89, 255, 0.45);
        transition: transform 0.15s ease-in-out;
    }
    .stButton>button:hover, .stFormSubmitButton>button:hover {
        transform: scale(1.02);
    }

    /* Colorful impact boxes */
    .impact-box {
        border-radius: 14px;
        padding: 18px;
        height: 100%;
    }
    .benefit-box {
        background: linear-gradient(145deg, #0d3b2e, #114b3b);
        border: 1px solid #10b981;
    }
    .risk-box {
        background: linear-gradient(145deg, #4a1d1d, #5c2323);
        border: 1px solid #ef4444;
    }
    .env-box {
        background: linear-gradient(145deg, #1e3a8a, #234a9e);
        border: 1px solid #3b82f6;
    }
    .impact-box h4 {
        margin-top: 0;
    }

    /* Section divider glow */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #a259ff, transparent);
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
                data = analyze_policy(policy_text)

                # Executive Overview
                st.subheader(f"📋 Analysis: {data.get('policy_title', 'Policy Analysis')}")
                st.info(f"**Summary:** {data.get('summary', 'No summary available.')}")
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
                    benefits_html = "".join(f"<li>✅ {b}</li>" for b in data.get("benefits", []))
                    st.markdown(
                        f"""<div class="impact-box benefit-box">
                        <h4>🟢 Benefits</h4>
                        <ul>{benefits_html}</ul>
                        </div>""",
                        unsafe_allow_html=True
                    )

                with col_risk:
                    risks_html = "".join(f"<li>⚠️ {r}</li>" for r in data.get("risks", []))
                    st.markdown(
                        f"""<div class="impact-box risk-box">
                        <h4>🔴 Risks & Drawbacks</h4>
                        <ul>{risks_html}</ul>
                        </div>""",
                        unsafe_allow_html=True
                    )

                with col_env:
                    env_html = "".join(f"<li>🌍 {e}</li>" for e in data.get("environmental_impact", []))
                    st.markdown(
                        f"""<div class="impact-box env-box">
                        <h4>🌿 Environmental Impact</h4>
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
                    color_discrete_sequence=["#00d4ff", "#a259ff", "#10b981", "#ff5da2"]
                )
                fig.update_traces(textposition="outside")
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.error(f"Error executing analysis: {str(e)}")

else:
    st.info("👈 Upload a PDF or paste your policy text in the sidebar, then click **'Submit & Run Simulation'**.")