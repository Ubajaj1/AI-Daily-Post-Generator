# Architecture Comparison

## BEFORE: Monolithic with Duplication ❌

```
┌─────────────────────────────────────────────────────────────────┐
│                         runner.py (267 lines)                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  STEP 1: INLINE RSS SCRAPING (~70 lines)                 │  │
│  │  - Import feedparser in loop                             │  │
│  │  - Parse RSS feeds                                       │  │
│  │  - Filter by date                                        │  │
│  │  - Check duplicates                                      │  │
│  │  - Insert into DB                                        │  │
│  │  - Extract markdown (sometimes)                          │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  STEP 2: PROCESSING                                      │  │
│  │  ✓ Calls: convert_url_to_markdown()                      │  │
│  │  ✓ Calls: fetch_article()                                │  │
│  │  ✓ Calls: summarize()                                    │  │
│  │  ✓ Calls: create_post_draft()                            │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  STEP 3: INLINE DIGEST BUILDING (~30 lines)              │  │
│  │  - Create NEW session (duplicate!)                       │  │
│  │  - Query processed articles                              │  │
│  │  - Format digest content                                 │  │
│  │  - (send_digest() commented out)                         │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
│ scrape_anthropic.py  │  │ scrape_arstechnica.py│  │  scrape_surgeai.py   │
│   (121 lines)        │  │     (120 lines)      │  │    (124 lines)       │
│ ┌──────────────────┐ │  │ ┌──────────────────┐ │  │ ┌──────────────────┐ │
│ │ DUPLICATE CODE   │ │  │ │ DUPLICATE CODE   │ │  │ │ DUPLICATE CODE   │ │
│ │ - Parse RSS      │ │  │ │ - Parse RSS      │ │  │ │ - Parse RSS      │ │
│ │ - Filter dates   │ │  │ │ - Filter dates   │ │  │ │ - Filter dates   │ │
│ │ - Insert DB      │ │  │ │ - Insert DB      │ │  │ │ - Insert DB      │ │
│ │ - Extract MD     │ │  │ │ - Extract MD     │ │  │ │ - Extract MD     │ │
│ └──────────────────┘ │  │ └──────────────────┘ │  │ └──────────────────┘ │
│  NEVER CALLED BY    │  │  NEVER CALLED BY    │  │  NEVER CALLED BY     │
│  RUNNER!            │  │  RUNNER!            │  │  RUNNER!             │
└──────────────────────┘  └──────────────────────┘  └──────────────────────┘

┌─────────────────────┐
│  email/sender.py    │
│   (34 lines)        │
│ ┌─────────────────┐ │
│ │ send_digest()   │ │
│ │ - Only sends    │ │
│ │ - No building   │ │
│ └─────────────────┘ │
└─────────────────────┘

PROBLEMS:
❌ 4x duplication of RSS logic (runner + 3 scrapers)
❌ Individual scrapers orphaned (not called by runner)
❌ Digest building in wrong place (runner vs email)
❌ Duplicate session in STEP 3
❌ Import in loop
❌ Tight coupling, hard to test
```

---

## AFTER: Modular with Orchestration ✅

```
┌─────────────────────────────────────────────────────────────────┐
│                    runner.py (172 lines)                        │
│                     CLEAN ORCHESTRATOR                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  STEP 1: FETCH                                           │  │
│  │  ✓ new_articles = fetch_all_sources(session, 48h)        │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  STEP 2: PROCESS                                         │  │
│  │  ✓ convert_url_to_markdown()                             │  │
│  │  ✓ fetch_article()                                       │  │
│  │  ✓ summarize()                                           │  │
│  │  ✓ create_post_draft()                                   │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  STEP 3: DIGEST                                          │  │
│  │  ✓ build_and_send_digest(session, logger)                │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                               │
                ┌──────────────┼──────────────┐
                │              │              │
                ▼              ▼              ▼
     ┌─────────────────┐  ┌─────────────┐  ┌──────────────────┐
     │ orchestrator.py │  │ sender.py   │  │ Other Modules    │
     │  (175 lines)    │  │ (Enhanced)  │  │ - llm/           │
     │  SINGLE SOURCE  │  │ (104 lines) │  │ - posts/         │
     │  OF TRUTH       │  │             │  │ - images/        │
     │ ┌─────────────┐ │  │ ┌─────────┐ │  └──────────────────┘
     │ │ Functions:  │ │  │ │send_    │ │
     │ │             │ │  │ │email()  │ │
     │ │ • ensure_   │ │  │ │         │ │
     │ │   source_   │ │  │ │build_   │ │
     │ │   registered│ │  │ │digest_  │ │
     │ │             │ │  │ │content()│ │
     │ │ • fetch_    │ │  │ │         │ │
     │ │   articles_ │ │  │ │build_   │ │
     │ │   from_rss  │ │  │ │and_send_│ │
     │ │   - Parse   │ │  │ │digest() │ │
     │ │   - Filter  │ │  │ └─────────┘ │
     │ │   - Insert  │ │  └─────────────┘
     │ │   - Extract │ │         ▲
     │ │     MD      │ │         │
     │ │             │ │    Complete digest
     │ │ • fetch_all_│ │    functionality
     │ │   sources   │ │
     │ └─────────────┘ │
     └────────┬────────┘
              │
              │ CALLED BY
              │
    ┌─────────┼──────────────────┐
    │         │                  │
    ▼         ▼                  ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│scrape_   │ │scrape_   │ │scrape_   │
│anthropic │ │arstechni-│ │surgeai   │
│   (53)   │ │ca  (52)  │ │  (52)    │
│ THIN     │ │ THIN     │ │ THIN     │
│ WRAPPERS │ │ WRAPPERS │ │ WRAPPERS │
└──────────┘ └──────────┘ └──────────┘

BENEFITS:
✅ Zero duplication - single source of truth
✅ Individual scrapers work AND called by runner
✅ Proper separation (scraping/email/orchestration)
✅ Efficient session management
✅ Modular, testable, maintainable
✅ Easy to add new sources
```

---

## Key Improvements

| Aspect | Before | After |
|--------|--------|-------|
| **RSS Logic** | Duplicated 4x | Unified in orchestrator |
| **runner.py** | 267 lines, monolithic | 172 lines, orchestrator |
| **Scrapers** | 120 lines each, orphaned | 52 lines each, wrappers |
| **Digest** | Mixed in runner | Owned by email module |
| **Testing** | Hard (tightly coupled) | Easy (modular) |
| **Maintenance** | Fix 4 places | Fix 1 place |
| **Session** | Duplicate in STEP 3 | Single session |
| **Imports** | In loop (4x) | At module level |
| **Total Code** | ~632 lines | ~574 lines (-58) |
| **Reusability** | Low | High |
