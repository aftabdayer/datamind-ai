# 🧠 DataMind AI — Streamlit Prototype (Archived)

> ⚠️ **This is the original prototype.** The live app has moved to the full-stack Next.js + FastAPI version.
>
> 👉 **[Live App](https://datamind-ai-frontend.vercel.app/)** &nbsp;|&nbsp; 🖥️ **[Current Frontend](https://github.com/aftabdayer/datamind-frontend)** &nbsp;|&nbsp; ⚙️ **[Current Backend](https://github.com/aftabdayer/datamind-backend)**

---

## What This Was

This repo is the original single-file Streamlit proof-of-concept for DataMind AI — built to validate the core idea before rebuilding it as a production full-stack app.

It demonstrates the same core functionality: upload a CSV/Excel → get AI-written analysis, auto-generated charts, linear regression forecast, anomaly detection, and a PDF export.

**The Streamlit live app is no longer running.** This repo is preserved as a record of the prototype stage.

---

## Evolution

| Stage | Stack | Status |
|-------|-------|--------|
| v1 — This repo | Python · Streamlit · Groq · ReportLab | Archived (prototype) |
| v2 — Production | Next.js · FastAPI · Plotly · Groq · ReportLab | ✅ Live |

The jump from v1 to v2 involved: separating frontend and backend, replacing Streamlit with Next.js + TypeScript, building a proper REST API with FastAPI, and deploying on Vercel + Render with CI/CD.

---

## Running Locally (if you want to explore the prototype)

```bash
git clone https://github.com/aftabdayer/datamind-ai.git
cd datamind-ai
pip install -r requirements.txt
streamlit run app.py
```

Get a free Groq API key at [console.groq.com](https://console.groq.com).

---

## Author

**Aftab Dayer** · [LinkedIn](https://linkedin.com/in/aftabdayer) · [GitHub](https://github.com/aftabdayer)  
NIT Hamirpur 2025 · IEEE Published · Microsoft Power BI Certified (PL-300)
