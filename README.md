# AI Daily Post Generator

Automated daily aggregator that scrapes AI news from curated sources, generates social media posts using OpenAI, and delivers them via email digest.

## Features

- 🔍 **Smart Scraping**: Fetches articles from RSS feeds (Anthropic, Ars Technica, Surge AI)
- 🤖 **AI-Powered Content**: Generates LinkedIn posts, X/Twitter posts, and layman explanations
- 📧 **Email Digest**: Delivers top 5 recent articles via Gmail SMTP
- 🛡️ **Anti-Backcrawl**: Prevents duplicate fetching of older articles
- 📝 **Professional Tone**: Uses third-person perspective for reporting

## Setup

1. **Clone and Install**
   ```bash
   git clone https://github.com/Ubajaj1/AI-Daily-Post-Generator.git
   cd AI-Daily-Post-Generator
   uv sync
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials:
   # - DATABASE_URL (PostgreSQL)
   # - OPENAI_API_KEY
   # - SENDER_EMAIL, GMAIL_APP_PASSWORD, RECIPIENT_EMAIL
   ```

3. **Start Database**
   ```bash
   docker-compose -f docker/docker-compose.yml up -d
   ```

4. **Initialize Schema**
   ```bash
   .venv/bin/python scripts/drop_and_recreate_tables.py
   ```

## Usage

**Run the pipeline:**
```bash
.venv/bin/python -m app.runner
```

This will:
1. Fetch new articles from all sources
2. Generate posts using OpenAI (GPT-4o-mini)
3. Send email digest with the 5 most recent articles

**Email includes:**
- LinkedIn post (professional, third-person)
- X/Twitter post (under 260 chars)
- Layman explanation (with analogy)
- Publication date and article link

## Tech Stack

- **Python 3.13** with `uv` package manager
- **PostgreSQL** for article storage
- **OpenAI API** for structured content generation
- **Docling** for markdown extraction
- **Gmail SMTP** for email delivery

## Gmail App Password Setup

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable 2-Step Verification
3. Search for "App passwords"
4. Generate password for "Mail"
5. Add to `.env` as `GMAIL_APP_PASSWORD`

## License

MIT