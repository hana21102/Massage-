# Massage Therapist Finder (Streamlit)

This is a deploy-ready Streamlit app that filters a list of massage therapist candidates by city, price, rating, modalities, languages, availability, and more.

## Files
- `massage_filter_app.py` — the Streamlit app
- `massage_filter.py` — optional CLI tool
- `massage_candidates_sample.csv` — sample data schema
- `requirements.txt` — Python dependencies
- `Procfile` — for Heroku deployment
- `Dockerfile` — for containerized deployment
- `setup.sh` — small helper script for Heroku
- `README_DEPLOY.md` — this guide

---

## Option A — Deploy on Streamlit Community Cloud (fastest, free)
1. Create a **public GitHub repo** and add these files.
2. Go to https://share.streamlit.io/ (Streamlit Community Cloud).
3. Click **New app** → select your repo, branch (e.g., `main`), and app file: `massage_filter_app.py`.
4. Click **Deploy**.
5. Once live, upload your CSV/Excel and filter away.

Notes:
- If your dataset is big, consider making the repo private and using Streamlit Cloud paid plan, or deploy via Docker on a VPS.
- Streamlit Cloud may sleep the app when idle.

## Option B — Deploy on Heroku
1. Install Heroku CLI and log in:
   ```bash
   heroku login
   ```
2. Create the app and push the code:
   ```bash
   heroku create your-app-name
   git init
   git add .
   git commit -m "Initial commit"
   heroku git:remote -a your-app-name
   git push heroku HEAD:main
   ```
   (If your default branch is `main`, you can also use `git push heroku main`)

3. Scale the web dyno:
   ```bash
   heroku ps:scale web=1
   ```
4. Open:
   ```bash
   heroku open
   ```

## Option C — Docker (any cloud: Fly.io, Render, AWS, GCP, Azure, etc.)
1. Build image:
   ```bash
   docker build -t massage-filter .
   ```
2. Run locally:
   ```bash
   docker run -p 8501:8501 massage-filter
   ```
3. Deploy the image to your preferred platform’s container service.

## Option D — Local run
```bash
pip install -r requirements.txt
streamlit run massage_filter_app.py
```

## Tips
- Keep `massage_candidates_sample.csv` outside your repo if it contains personal data. Upload the file at runtime in the app.
- You can customize filters or defaults inside `massage_filter_app.py` (e.g., default city, rating min).
- For BC insurance reimbursement, look for `Credentials` containing `RMT`.
