# interview_langgraph
Hr Resume Screening Chatbot

## Run locally

```bash
pip install -r requirements.txt
export OPENAI_API_KEY="your-api-key"
streamlit run main.py
```

On Windows PowerShell, set the API key with:

```powershell
$env:OPENAI_API_KEY="your-api-key"
streamlit run main.py
```

## Deploy on Streamlit Community Cloud

1. Push this repository to GitHub.
2. Create a Streamlit app and select `main.py`.
3. In app **Settings > Secrets**, add:

```toml
OPENAI_API_KEY = "your-api-key"
```
