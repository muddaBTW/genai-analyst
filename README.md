# GenAI Analyst

GenAI Analyst is a full-stack data analysis app that lets you upload a CSV or Excel file, inspect the dataset, generate visualizations, ask natural-language questions, and export an AI-assisted report in Markdown or PDF.

## Features

- Upload CSV and Excel datasets
- View dataset metadata, preview rows, and summary analysis
- Generate visualizations from the uploaded data
- Generate AI insights from dataset summaries
- Ask dataset questions in natural language
- Export reports as Markdown or PDF

## Tech Stack

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

## Project Structure

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

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/muddaBTW/genai-analyst.git
cd genai-analyst
```

### 2. Backend setup

Create and activate a virtual environment, then install dependencies:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file inside `backend/`:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Start the backend:

```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

### 3. Frontend setup

In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend runs on `http://localhost:5173` by default.

## How It Works

1. Upload a dataset from the `Upload` section.
2. The app stores the dataset in memory on the backend.
3. Analysis, charts, and AI insights are generated after upload.
4. You can inspect dataset details, ask questions, and export a report.

## Report Generation

The exported report combines:

- Data-derived summary content from the uploaded dataset
- AI-generated insights and report narrative
- PDF formatting and section layout defined in backend code

## API Overview

The backend exposes routes under `/api` for:

- upload
- analysis
- visualizations
- insights
- query
- report

## Notes

- The backend currently uses in-memory dataset storage for a simple single-user workflow.
- A valid Groq API key is required for AI insights, Q&A, and report generation.

## License

No license file is currently included in this repository.
