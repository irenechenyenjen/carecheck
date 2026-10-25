# CareCheck

CareCheck is an older-adult-friendly health-information risk checker. It helps people pause before believing or forwarding questionable health advice.

## Run locally

1. Create a virtual environment: `python -m venv .venv`
2. Activate it.
3. Install dependencies: `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` if using model-backed analysis.
5. Run: `python app.py`
6. Open `http://127.0.0.1:8050`.

The app checks its own `.env` first and then the parent folder's `.env`, matching the course testing setup. Never commit `.env` or real API keys.

## Course testing setup

The app supports both approved key names: `PORTKEY_API_KEY` and `OPENAI_API_KEY`. It first looks for `.env` inside this repository and then looks one folder above the repository, where the course testing setup may place the teaching staff's `.env` file. The course key must be used with `gpt-6-luna` only. Do not commit `.env`, `PORTKEY_API_KEY`, or `OPENAI_API_KEY`.

## Fresh-clone test

1. Clone this repository.
2. Confirm the course `.env` is either in the repository folder or one folder above it.
3. From the repository folder, create and activate a virtual environment.
4. Run `pip install -r requirements.txt`.
5. Run `python app.py`.
6. Open `http://127.0.0.1:8050`.

The app is designed to run locally without a database or additional service. If no API key is available, its local fallback still renders the interface and provides a limited safety-screening response.

## Submission documents

- `report.html` — report draft with confirmed product details and clearly marked `[TO COMPLETE]` evidence fields.
- `slides.html` — ten-slide Reveal.js presentation draft.

Before submission, replace every `[TO COMPLETE]` item with real screenshots, testing evidence, user feedback, cost/token records, names, dates, and links. Do not invent evidence.

