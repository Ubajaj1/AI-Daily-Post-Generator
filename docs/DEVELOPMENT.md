# Development Notes — AI News Aggregator

This document tracks what we build, why each file exists, and contains beginner-friendly explanations of the coding concepts used. I'll append this file as we progress so you have a single reference.

--

## Summary of what was scaffolded

Files added (brief):
- `app/__init__.py` — marks `app` as a Python package.
- `app/config.py` — pydantic `Settings` that load environment variables from `.env`.
- `app/db.py` — SQLAlchemy `engine` and `SessionLocal` for DB access.
- `app/models.py` — SQLAlchemy declarative models: `Source` and `Article`.
- `app/sources/registry.py` — a small list of example sources (OpenAI, Anthropic, Perplexity, and example YouTube channels).
- `app/scrapers/youtube.py` — fetches items from YouTube RSS feeds using `feedparser`.
- `app/scrapers/blog.py` — fetches and extracts article content using `httpx` + `BeautifulSoup`.
- `app/llm/client.py` — a small wrapper around OpenAI for summarization with a safe console fallback.
- `app/email/sender.py` — SendGrid-based email sending with a console fallback.
- `app/runner.py` — a simple `run_once()` entrypoint that ties the flow together (create tables, fetch, dedupe, summarize, create digest, send/print).
- `docker/docker-compose.yml` — minimal Postgres service for local development.
- `.env.example` — example environment variables for local testing.

## Why these files exist (high-level)
- `config.py`: keeps secrets and configurable values out of source code. We read them from a `.env` file so you can change settings per environment.
- `db.py`: centralizes database connection setup. Any part of the app that needs DB access imports `SessionLocal` or `engine` from here.
- `models.py`: defines the structure of the data we store in the database. SQLAlchemy maps these Python classes to database tables.
- `scrapers/*`: encapsulate logic to fetch and parse data from different source types (RSS vs HTML). Keeping scrapers modular makes it easy to add new source types.
- `llm/client.py`: isolates the LLM API logic so other code calls `summarize(text)` without knowing API details.
- `email/sender.py`: isolates email provider implementation. Right now it supports SendGrid, but we can add SMTP or other providers easily.
- `runner.py`: orchestration code — small and synchronous for learning. Later we can convert it to async for higher throughput.

## Beginner-friendly explanations

- Python package / module: any folder with an `__init__.py` is a package; files inside are modules. You can import like `from app import config`.
- Function: a named block of code that performs a task. Example: `summarize(text)` — pass text in, get a summary back.
- Class: a blueprint for objects. In `models.py`, `Source` and `Article` are classes where each instance represents one row in the DB.
- SQLAlchemy declarative model: you define a Python class with attributes mapped to database columns. SQLAlchemy handles SQL for you.
- Pydantic Settings: `BaseSettings` reads environment variables and validates types. This prevents magic strings spread around your code.
- Virtual environment (`.venv` managed by `uv`): isolates project packages from system Python; use `uv` commands or `source .venv/bin/activate` to work inside it.
- Docker Compose: runs services (like Postgres) locally in containers so you don't need to install them locally.

## How the runner works (step-by-step)
1. `Base.metadata.create_all(bind=engine)` creates DB tables if they don't exist (good for dev).
2. Ensure each `Source` from `app/sources/registry.py` exists in the `sources` table.
3. For each source:
   - If `youtube`: fetch items from the channel's RSS feed and insert new `Article` rows for unseen URLs.
   - If `blog`: either parse RSS entries or fetch the page and extract main content.
4. For new articles, fetch (or use existing) content and call `summarize()`; store `summary` and mark as `processed`.
5. Build a short daily digest from processed articles in the last 24 hours and email it (or print it to console if SendGrid isn't configured).

## Commands to run locally (copy + paste)
1. Verify Python and `uv` environment:
```bash
uv run python --version
uv run python -m pip freeze
```

2. Create your `.env` (copy from `.env.example`) and edit values:
```bash
cp .env.example .env
# edit .env with an editor and fill keys
```

3. Start Postgres locally (optional):
```bash
docker compose -f docker/docker-compose.yml up -d
```

4. Run a single processing cycle:
```bash
uv run python -m app.runner
```

If everything is configured with no OpenAI key, summaries will be truncated placeholders and digest will be printed to your terminal.

## What to change next (suggested learning steps)
1. Inspect `app/runner.py` and add `print()` statements to see the flow and the data being processed.
2. Add a real YouTube channel ID to `app/sources/registry.py` and re-run to fetch real updates.
3. Learn about Alembic and create migrations instead of `create_all()` for real projects.
4. Replace the simple `summarize()` with chunking + map-reduce for long articles.

## Notes about ongoing updates
I will append this file each time I scaffold or change files so it becomes your living developer guide. You can keep this project file under version control and track changes as we iterate.

---

If you want, I can (next):
- add Alembic configuration and an initial migration, or
- update README with run instructions and deployment notes, or
- implement chunked summarization (map-reduce) for long articles.

Tell me which next step you'd like and I'll update this file again to reflect it.

## Concepts Explained — Layman's Terms & Analogies

Below are friendly explanations (with analogies) for the main concepts used in this project. Keep this as a quick reference while you learn.

### Overall architecture (short)
- The app is split into small pieces with single responsibilities: configuration, database, data models, scrapers (fetching), LLM helpers (summaries and post generation), image fetching, runner (the coordinator), and email sending.
- Analogy: imagine a tiny newspaper: reporters (scrapers) gather stories, the archive (DB) stores them, an editor (LLM) writes a short piece and a layman explanation, and a publishing manager (runner) sends you the draft.

### Run flow (what happens when you run the app)
1. The runner ensures tables exist (dev convenience).
2. Sources are loaded from `app/sources/registry.py`.
3. For each source, fetch new items (RSS or HTML), skip duplicates, and insert new `Article` rows.
4. For each new article: fetch content → summarize using the LLM → store the summary.
5. Generate a `PostDraft` with an engaging LinkedIn post, a layman's explanation, and a suggested image.
6. Email (or print) the draft for review.

### What is SQLAlchemy (in plain language)
- SQLAlchemy is an ORM (Object-Relational Mapper). Instead of writing raw SQL, you define Python classes that represent tables. SQLAlchemy handles converting your Python actions into SQL commands that talk to the database.
- Analogy: the database is a set of spreadsheets (tables). SQLAlchemy gives you a friendly app to create and edit rows by manipulating Python objects (rows become objects you can inspect and modify).

### Key SQLAlchemy parts in the code
- `Base = declarative_base()` — a factory used to declare table classes. Each class inheriting from `Base` becomes a database table.
- `Column(...)` — defines a column (field) in the table, with a data type and optional constraints.
- `create_engine(DATABASE_URL)` — creates the connection to the real database (Postgres, sqlite, etc.).
- `SessionLocal()` — creates a session (a working area / transaction). Use sessions to add, query, and commit changes.

### What `relationship("Source")` does (simple)
- In `Article` we have `source_id = Column(..., ForeignKey("sources.id"))` and `source = relationship("Source")`.
- `source_id` is a raw reference (the ID of the source). `relationship("Source")` is a Python convenience that lets you access the full `Source` object directly from an `Article` instance: `article.source.name`.
- Analogy: `source_id` is like a note saying "belongs to shelf #3", and `relationship` is like having a ladder that goes to that shelf so you can pick up the full source record.

### Classes vs Instances (blueprint vs object)
- Class: a blueprint (like the recipe or mold). Example: `class Article(Base): ...` defines the shape of an article.
- Instance: a real object created from the blueprint. `a = Article(title="Hi")` is an instance representing a single article.
- When you `session.add(a)` and `session.commit()`, that instance is saved as a row in the database table.

### Concrete mini examples
- Create and save a source & article:
```python
from app.db import SessionLocal
from app.models import Source, Article

with SessionLocal() as session:
   src = Source(name="My Blog", type="blog", url="https://example.com", feed_url="https://example.com/rss")
   session.add(src)
   session.commit()   # src.id now available

   art = Article(source_id=src.id, url="https://example.com/post1", title="Hello")
   session.add(art)
   session.commit()
```
- Access related source from an article:
```python
with SessionLocal() as session:
   art = session.query(Article).filter_by(title="Hello").first()
   print(art.source.name)  # thanks to relationship("Source")
```

### Sessions and transactions (why use them)
- A `Session` groups database operations. You can add many changes and then `commit()` once. If something goes wrong, you can `rollback()` and prevent partial updates.
- Analogy: a Session is a transaction folder where you collect edits; committing seals the folder and writes changes to the official archive.

### `create_all()` vs migrations
- `Base.metadata.create_all(bind=engine)` inspects your models and creates missing tables. It's quick for prototyping.
- For real projects, use migrations (Alembic). Migrations record every schema change (like adding columns) and let you apply them safely to existing databases.

### Common pitfalls (and how to avoid them)
- Forgetting to `commit()` after `session.add()` — nothing gets saved to DB.
- Accessing a lazy-loaded relationship (like `article.source`) outside an active session — either keep the session alive or eager-load the relationship when querying.
- Changing model definitions after tables exist — prefer migrations rather than dropping tables and re-creating them.

### Suggested next step for learning
- (A) Walk through `app/runner.py` line-by-line with me. I'll explain each block and you can ask questions. This is the recommended next step because runner ties everything together.
- (B) Run the runner locally and paste the output; I will explain the results and show the DB rows.

Pick (A) or (B) and I'll proceed step-by-step.


## Change of objective — LinkedIn post generation

You asked to change the app objective: instead of (only) creating a daily digest summary, we will now generate an "engaging LinkedIn post" for each relevant article. Each post will:

- Focus on one key concept from the article (clear single takeaway). 
- Be written in an engaging, conversational LinkedIn style (hook, value, CTA). 
- Include a short "Layman's explanation" section so you can learn the concept in plain language. 
- Include a relevant image (prefer `og:image` from the article, else fallback to an image search like Unsplash); store the image URL and its source/attribution.
- Be saved as a draft in the DB (`PostDraft`) and emailed to you for review. Later we will add a LinkedIn integration so you (or the app) can post directly.

### Why this changes the architecture

- We will add a new `PostDraft` model/table to store the post, explanation, image info, and status (draft/sent/posted). This keeps drafts separate from raw `Article` data. 
- The LLM prompts need to be extended with templates for: (A) extracting the single key concept, (B) producing a short LinkedIn post (hook + 2–4 lines), and (C) writing a layman's explanation. We'll store those templates in `app/llm/prompts.py` so they're easy to adjust.
- We'll add an `images` helper to extract `og:image` or perform an image search and format attribution data.
- The runner will be updated to, for each new processed article, create a `PostDraft` (call LLM for the post and the layman explanation, call image-fetcher, store results) and then email the draft to you. This keeps the daily digest behavior but adds a per-article deliverable.

### Minimal prompt designs (initial)

- Extract key concept (system prompt): "Read the article and return the single most important idea, in one short sentence." 
- LinkedIn post (system prompt): "Write an engaging LinkedIn post (max 3 short paragraphs) that: starts with a hook, explains the key idea briefly, includes one concrete example or implication, ends with a one-line question or CTA. Keep length ~100–180 words." 
- Layman's explanation (system prompt): "Explain the same key idea to a non-technical reader in 3–5 sentences, using analogies if helpful." 

These templates will be adjustable and versioned in the DB (we'll record the prompt version used in `PostDraft`).

### Environment variables to add to `.env.example`

- `UNSPLASH_ACCESS_KEY` — optional, if you want to search Unsplash for images.
- `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET` — placeholders for later OAuth.

### Next actions (I will implement these when you confirm)

1. Add `app/posts/generator.py` to implement LLM-based post + layman explanation generation and a small function `create_post_draft(article)`.
2. Update `app/models.py` with a `PostDraft` model and migrate the DB (or keep `create_all()` for now and add Alembic later).
3. Add `app/images/fetcher.py` that extracts `og:image` or uses an image search API fallback.
4. Update `app/llm/client.py` and add `app/llm/prompts.py` to hold templates.
5. Modify `app/runner.py` so that after an article is summarized it calls `create_post_draft()` and emails the draft.

When you're ready I can begin implementing these changes step-by-step. I will append this file with code notes and examples as I add each new module so you have a running guide.

