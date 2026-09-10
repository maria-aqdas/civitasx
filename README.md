# 🏛️ CivitasX    AI Policy Impact Simulator

**Turn any policy draft into clear, easy-to-read insights on its economic, social, and environmental impact.**

CivitasX is an AI-powered tool that helps citizens, students, and policymakers understand what a public policy actually *means* — in plain, simple language, before it's passed. Paste a policy proposal or upload a PDF, and CivitasX breaks it down into benefits, risks, environmental effects, and easy-to-read impact scores.

Built for the **Build Beyond Hackathon**.
 
---

## ✨ Features

- **📄 Flexible Input** — Paste policy text directly, or upload a PDF document.
- **🔍 Smart PDF Reading** — Automatically extracts text from PDFs, with built-in OCR fallback for scanned/image-based documents.
- **🤖 AI-Powered Analysis** — Uses Google Gemini to analyze the policy and generate:
  - A plain-language summary (length scales with document detail)
  - Key **Benefits**
  - Key **Risks & Drawbacks**
  - **Environmental Impact**
  - Impact scores (Economic, Social Equity, Environmental, Public Sentiment) out of 100
- **🌐 Multi-Language Output** — Get results in English, Urdu, Hindi, Arabic, French, Spanish, Chinese, Turkish, Bengali, or Pashto — including proper right-to-left formatting for Urdu/Arabic/Pashto.
- **🔊 Voice Playback** — Listen to the summary out loud in the selected language.
- **📊 Visual Dashboard** — Interactive score charts powered by Plotly.
- **📥 Downloadable Report** — Export the full analysis as a text file.

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Frontend / UI | [Streamlit](https://streamlit.io) |
| AI Engine | Google Gemini API (`google-genai`) |
| PDF Parsing | `pypdf` |
| OCR (scanned PDFs) | `pytesseract` + `pdf2image` (Tesseract OCR + Poppler) |
| Text-to-Speech | `gTTS` |
| Charts | `plotly` |

---

## 🚀 Getting Started (Local Setup)

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/civitasx.git
cd civitasx
```

### 2. Create a virtual environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. System dependencies (for scanned PDF / OCR support)
This app needs **Tesseract OCR** and **Poppler** installed on your system:
- **Tesseract**: [Windows installer](https://github.com/UB-Mannheim/tesseract/wiki)
- **Poppler**: [Windows binaries](https://github.com/oschwartz10612/poppler-windows/releases)

(On Streamlit Community Cloud, these are installed automatically via `packages.txt`.)

### 5. Add your Gemini API key
Create a `.env` file in the project root:
```
GEMINI_API_KEY=your_actual_api_key_here
```
Get a free key from [Google AI Studio](https://aistudio.google.com).

### 6. Run the app
```bash
streamlit run app.py
```

---

## ☁️ Deployment (Streamlit Community Cloud)

This app is deployed on Streamlit Community Cloud. To deploy your own copy:

1. Push this repo to your GitHub account.
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **New app**, select this repo, and set the main file to `app.py`.
4. Under **Advanced settings → Secrets**, add:
   ```toml
   GEMINI_API_KEY = "your_actual_api_key_here"
   ```
5. Click **Deploy**.

The included `packages.txt` file automatically installs `poppler-utils` and `tesseract-ocr` on the cloud server.

---

## 📁 Project Structure

```
civitasx/
├── .streamlit/
│   └── config.toml       # Light theme configuration
├── app.py                # Streamlit UI and app logic
├── analyzer.py            # Gemini API integration & prompt logic
├── requirements.txt        # Python dependencies
├── packages.txt            # System-level dependencies (Streamlit Cloud)
└── README.md
```

---

## 📌 Notes

- The `.env` file is intentionally excluded from version control — never commit your API key.
- Summary length and number of benefit/risk/environmental points automatically scale with how detailed the input document is.

---

## 🏆 Built For

**Build Beyond Hackathon** — an open-ended hackathon where creativity has no limits.

---

## 📄 License

This project was built for hackathon submission purposes.
