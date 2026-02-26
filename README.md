

Ось README.md у markdown-форматі без згадки про PYTHONPATH:

---

# Parking Space AI Chatbot

## Installation & Setup

### 1. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set environment variables

Create a `.env` file in the project root with the following content (replace `<your-api-key>`):

```
OPENAI_API_KEY=<your-api-key>
DB_URL=sqlite:///./app/db/parking.db
PINECONE_API_KEY=<your-api-key>
PINECONE_INDEX=parking-static
```

---

## Usage

### 1. Run the chat interface

```bash
python -m streamlit run app/main.py
```

### 2. Run system performance evaluation

```bash
python -m app.evaluation.performance
```

### 3. Run unit tests

```bash
pytest -v
```

---

## Notes

- Make sure your Pinecone index
 is created and your API keys are valid.
- The database will be initialized automatically on first run.
- If you encounter import errors, ensure you are running commands from the project root directory.

---

## Project Structure

- `app/` — main application code
- `app/db/` — database models and logic
- `app/llm/` — LLM integration
- `app/agents/` — agents and business logic
- `app/gui/` — Streamlit interface
- `app/evaluation/` — performance evaluation scripts
- `tests/` — unit tests

---
