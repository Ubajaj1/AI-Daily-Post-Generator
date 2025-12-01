# AI News Aggregator: Technical Deep Dive & Interview Guide

## 1. Project Overview
**AI News Aggregator** is an automated pipeline that monitors key AI news sources, uses a Large Language Model (LLM) to analyze and summarize articles, and delivers a curated daily digest via email.

**Core Problem Solved:** Keeping up with the fast-paced AI industry is difficult. This tool automates the "read, summarize, and draft" workflow, saving hours of manual research time.

---

## 2. System Architecture

The system follows a **ETL (Extract, Transform, Load)** pattern, enhanced with Generative AI.

```mermaid
graph TD
    subgraph "Extraction Layer (Scraping)"
        RSS[RSS Feeds] -->|Fetch XML| Orch[Orchestrator]
        Orch -->|Check History| DB[(PostgreSQL)]
        Orch -->|Extract Content| Docling[Docling/Markdown]
        Docling -->|Save Raw Article| DB
    end

    subgraph "Transformation Layer (AI Processing)"
        Runner[Runner Script] -->|Poll New Articles| DB
        Runner -->|Send Content| OpenAI[OpenAI API (GPT-4o)]
        OpenAI -->|Structured JSON| Pydantic[Pydantic Validation]
        Pydantic -->|Save Drafts| DB
    end

    subgraph "Delivery Layer (Notification)"
        Email[Email Sender] -->|Query Recent Drafts| DB
        Email -->|Format HTML| SMTP[Gmail SMTP]
        SMTP -->|Send| User((User))
    end
```

---

## 3. Key Technical Concepts & Implementation

### A. Pydantic (Data Validation & Schema)
**What it is:** A library for data validation using Python type hints.
**How we used it:**
In `app/llm/schemas.py`, we defined the `ArticleAnalysis` class.
```python
class ArticleAnalysis(BaseModel):
    key_concept: str = Field(..., description="The core technical idea...")
    post_content: str = Field(..., description="LinkedIn post content...")
    # ...
```
**Why it matters:**
When we call OpenAI, we don't just ask for "text". We force the LLM to output JSON that matches this exact schema. Pydantic guarantees that if the function returns, the data types are correct (e.g., `key_concept` is definitely a string). This prevents the pipeline from crashing due to "hallucinated" or malformed API responses.

### B. Docker & Docker Compose
**What it is:** A platform for developing, shipping, and running applications in containers.
**How we used it:**
We used `docker/docker-compose.yml` to run our **PostgreSQL database**.
```yaml
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: ai_news
      # ...
```
**Why it matters:**
Instead of installing PostgreSQL directly on your Mac (which is messy and hard to clean up), we spin it up in an isolated container. `docker-compose up -d` starts the DB, and `docker-compose down` stops it. It ensures your development environment is clean and reproducible.

### C. SQLAlchemy (ORM - Object Relational Mapping)
**What it is:** A toolkit that lets you interact with databases using Python classes instead of writing raw SQL queries.
**How we used it:**
In `app/models.py`, we defined classes like `Article` and `PostDraft` that inherit from `Base`.
```python
class Article(Base):
    __tablename__ = "articles"
    id = Column(String, primary_key=True, ...)
    url = Column(String, unique=True, ...)
```
**Why it matters:**
*   **Abstraction:** We write `session.add(article)` instead of `INSERT INTO articles...`.
*   **Safety:** It automatically handles SQL injection protection.
*   **Portability:** If we switched from PostgreSQL to SQLite, we wouldn't need to rewrite our queries.

### D. GitHub Actions (CI/CD & Automation)
**What it is:** A CI/CD platform that allows you to automate your build, test, and deployment pipeline.
**How we used it:**
We created `.github/workflows/run-pipeline.yml`.
*   **Trigger:** `schedule` (cron job running every 2 days).
*   **Environment:** It spins up a Linux server (runner), installs Python, installs dependencies, and runs our script.
*   **Secrets:** It securely injects your API keys (`OPENAI_API_KEY`, `DATABASE_URL`) from GitHub Secrets into the runtime environment.

---

## 4. Code Walkthrough (The "Life of a Request")

### 1. The Entry Point: `app/runner.py`
This is the "manager". It coordinates the entire process.
*   **Step 1:** Calls `fetch_all_sources()` to get new data.
*   **Step 2:** Loops through new articles and calls `analyze_article()` (the AI).
*   **Step 3:** Saves the AI results to the DB.
*   **Step 4:** Calls `build_and_send_digest()` to email the results.

### 2. The Scraper: `app/scrapers/orchestrator.py`
This component handles the "Extract" phase.
*   **Anti-Backcrawl Logic:**
    *   It checks: "Do we have *any* articles from this source in the DB?" (`source_has_history`).
    *   **If Yes:** It assumes we are up-to-date and only fetches *new* items from the RSS feed.
    *   **If No:** It fetches the 2 most recent articles to populate the DB (the "fallback").
    *   **Why?** This prevents the system from re-processing old news every time it runs.

### 3. The AI Brain: `app/llm/client.py`
This interacts with OpenAI.
*   It uses the `client.beta.chat.completions.parse` method.
*   It passes the `ArticleAnalysis` Pydantic model as the `response_format`.
*   **Prompt Engineering:** We explicitly instructed the model in `app/llm/prompts.py` to use a **Third-Person Perspective** ("They announced...") to ensure the posts sound like an industry analyst, not a company employee.

### 4. The Courier: `app/email/sender.py`
*   It queries the `post_drafts` table for items with `status="draft"`.
*   **Sorting:** It joins with the `articles` table to sort by `published_at` (newest first).
*   It constructs an HTML email using Python f-strings.
*   It uses `smtplib` to connect to Gmail's SMTP server and send the email.

---

## 5. Interview Q&A Prep

**Q: Why did you choose PostgreSQL over a simpler file-based storage like JSON or CSV?**
**A:** I chose PostgreSQL for data integrity and scalability. The `UniqueConstraint` on the `url` column prevents duplicate articles at the database level, which is a critical reliability feature. Also, using an ORM (SQLAlchemy) allows me to easily query relationships (like joining Drafts with Articles) which would be complex with flat files.

**Q: How do you handle "hallucinations" from the AI?**
**A:** I use **Structured Outputs** with Pydantic. By enforcing a strict schema (`ArticleAnalysis`), the AI is constrained to provide exactly the fields I need. If the AI generates malformed data, the validation layer catches it before it corrupts my database.

**Q: How is this deployed?**
**A:** It follows a serverless, scheduled architecture. The code is hosted on GitHub, and a **GitHub Actions** workflow runs the pipeline every 48 hours. The database is hosted on **Railway** (cloud PostgreSQL). This separation allows the compute (GitHub) to be ephemeral and free, while the state (Railway) is persistent.

**Q: How do you ensure you don't scrape the same article twice?**
**A:** I implemented a multi-layer check.
1.  **Database Constraint:** The `url` column is unique.
2.  **Application Logic:** The orchestrator checks if a URL exists before attempting to process it.
3.  **Anti-Backcrawl:** I track if a source has history; if it does, I strictly only look for new items in the RSS feed.

---

## 6. Future Improvements (Talking Points)
*   **OAuth Integration:** Replacing the manual LinkedIn copy-paste with the LinkedIn API to auto-post.
*   **Vector Database:** Adding a vector store (like Pinecone) to search for "similar past articles" to provide context.
*   **Frontend:** Building a Next.js dashboard to view and edit drafts before they are emailed.
