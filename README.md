<h1 align="center">GenAI Analyst</h1>

<p align="center">
  AI-assisted data analysis with upload, profiling, visualizations, Q&A, and exportable reports.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Frontend-React%2019-61DAFB?style=for-the-badge&logo=react&logoColor=0b1020" alt="React 19" />
  <img src="https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/AI-Groq-F55036?style=for-the-badge" alt="Groq" />
  <img src="https://img.shields.io/badge/Charts-Plotly-3F4F75?style=for-the-badge&logo=plotly&logoColor=white" alt="Plotly" />
  <img src="https://img.shields.io/badge/Reports-PDF%20%26%20Markdown-7C3AED?style=for-the-badge" alt="Reports" />
</p>

---

## Overview

GenAI Analyst is a full-stack application for exploring tabular datasets with a workflow that feels closer to an analyst assistant than a raw dashboard. You can upload a CSV or Excel file, inspect the dataset, generate charts, ask questions in natural language, and export an AI-assisted report in Markdown or PDF.

## What It Does

| Area | Capability |
| --- | --- |
| Upload | Accepts CSV and Excel datasets |
| Overview | Shows dataset metadata, preview rows, and summary analysis |
| Visualizations | Generates charts from the uploaded data |
| AI Insights | Produces narrative insights from dataset summaries |
| Q&A | Answers natural-language questions about the dataset |
| Reports | Exports Markdown and PDF reports |

## Stack

### Frontend

- React 19
- Vite
- Axios
- Plotly / React Plotly

### Backend

- FastAPI
- Pandas
- Plotly
- Groq API
- fpdf2

## Project Layout

```text
backend/
  main.py
  requirements.txt
  routers/
  services/
frontend/
  src/
  public/
  package.json
sample_data.csv
```

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/muddaBTW/genai-analyst.git
cd genai-analyst
```

### 2. Set up the backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Create `backend/.env`:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Start the backend:

```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

### 3. Set up the frontend

In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend default URL: `http://localhost:5173`

## Workflow

1. Upload a dataset from the `Upload` section.
2. The backend stores the dataframe in memory for the current session.
3. Analysis, charts, and AI insights are generated after upload.
4. You can inspect the dataset, ask questions, and export a report.

## Report Generation

The exported report is a mix of:

- data-derived summary content from the uploaded dataset
- AI-generated narrative sections and insights
- backend-defined report formatting and PDF layout

## API Surface

The backend exposes routes under `/api` for:

- `upload`
- `analysis`
- `visualizations`
- `insights`
- `query`
- `report`

## Notes

> The current implementation uses in-memory dataset storage, which keeps the app simple for local use and single-user workflows.

> A valid `GROQ_API_KEY` is required for AI insights, natural-language Q&A, and report generation.

## License

No license file is currently included in this repository.
