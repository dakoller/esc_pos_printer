# Codebase Summary

## Project Structure

```
esc_pos_printer/
├── run.py                          # Main Flask application
├── image.py                        # Image handling utilities
├── yf1.py                          # Yahoo Finance integration (unused)
├── requirements.in                 # Python dependencies
├── requirements.txt                # Locked dependencies
├── .env                           # Environment variables (not in git)
├── .tt_token_full                 # TickTick OAuth tokens (not in git)
├── escposprinter.service          # systemd service file
├── data/
│   └── marc_aurel.txt            # Marc Aurel philosophical quotes
├── morgenjournal_fragen.json     # Morning journal questions
└── architecture_docs/             # Project documentation
    ├── projectRoadmap.md
    ├── currentTask.md
    ├── techStack.md
    └── codebaseSummary.md
```

## Key Components

### run.py (Main Application)
The core Flask application containing all endpoints and printing logic.

**Flask Endpoints:**
- `GET /` - API information and available endpoints
- `GET /print_news` - Print daily news, quotes, and journal prompts
- `GET /print_tasks` - Print tasks grouped by tags with date info
- `GET /print_text` - Print custom text with optional headline
- `GET /print_journal` - Print journal prompts only
- `GET /due_tasks` - Return JSON of due tasks from TickTick
- `GET /ticktick_auth` - Get TickTick OAuth URL
- `GET /ticktick_callback` - Handle TickTick OAuth callback
- `GET /test_ticktick` - Test TickTick integration

**Core Functions:**
- `print_rss_feed()` - Parse and print RSS news feeds
- `print_daily_basics()` - Print date and sunrise/sunset times
- `print_daily_quote()` - Print Marc Aurel quote
- `print_journal_items()` - Print random journal questions
- `print_due_tasks()` - Print tasks with due dates (legacy)
- `get_ticktick_tasks()` - Fetch tasks from TickTick API
- `get_daily_marc_aurel_quote()` - Select daily quote deterministically
- `count_due_overdue_tasks()` - Count tasks by status

### Data Flow

#### Task Printing Flow
```
User Request → /print_tasks
    ↓
Fetch sunrise/sunset data
    ↓
GET /due_tasks → TickTick API
    ↓
Filter: overdue & due today
    ↓
Group by tags (from TickTick tags array + hashtags)
    ↓
Filter #sap on weekends
    ↓
Sort groups alphabetically
    ↓
Print to ESC/POS printer
```

#### News Printing Flow
```
User Request → /print_news
    ↓
Print date & sunrise/sunset
    ↓
Print Marc Aurel quote
    ↓
Print RSS feeds (Heidelberg, Tagesschau)
    ↓
Print journal questions
    ↓
Cut paper
```

## Component Interactions

### TickTick Integration
1. **Authentication:** OAuth2 flow stores tokens in `.tt_token_full`
2. **Data Fetching:** REST API calls with Bearer token
3. **Projects:** Fetches from inbox + all user projects
4. **Tasks:** Extracts tasks with due dates, including tags array
5. **Tag Recognition:** Combines TickTick tags + hashtag parsing

### Printer Communication
1. **Connection:** Network socket to printer at `192.168.2.134`
2. **Formatting:** ESC/POS commands for text styling
3. **Operations:** Print, set alignment, bold, double-height, cut paper

### External APIs
1. **TickTick:** OAuth2 + REST API for task management
2. **Sunrise-Sunset:** Public API for Heidelberg coordinates
3. **RSS Feeds:** RNZ and Tagesschau news feeds

## Recent Significant Changes

### 2026-01-17: Tag Recognition Fix
**Problem:** Tasks with TickTick tags weren't being recognized
**Solution:** Updated to extract tags from TickTick's `tags` array field
**Files Modified:** `run.py`
- `/due_tasks` endpoint now includes `tags` field
- `print_tasks` checks both tags array and hashtags
- Added tag-based grouping and alphabetical sorting
- Implemented weekday filtering for #sap tasks

### Previous: Marc Aurel Quote System
**Change:** Replaced zenquotes.io API with local text file
**Rationale:** Offline operation, no rate limits, philosophical content
**Implementation:** Deterministic selection based on date

## External Dependencies

### Python Packages
- **Flask:** Web framework
- **python-escpos:** Printer control
- **feedparser:** RSS parsing
- **requests:** HTTP client
- **ticktick-py:** TickTick API client
- **python-dotenv:** Environment variable management

### External Services
- **TickTick API:** Task management (api.ticktick.com)
- **Sunrise-Sunset API:** Solar times (api.sunrise-sunset.org)
- **RSS Feeds:** News sources

### Local Resources
- **data/marc_aurel.txt:** German philosophical text
- **morgenjournal_fragen.json:** Journal prompts with scales
- **.tt_token_full:** OAuth tokens (gitignored)

## User Feedback Integration

### Current Implementation
- Tag-based task grouping requested and implemented
- Weekday filtering for work tasks (#sap) added
- Alphabetical sorting of tag groups implemented

### Pending Feedback
- Configuration file for custom filters
- Task priority display
- Scheduled automatic printing

## Development Notes

### Testing
- Manual testing via Flask endpoints
- No automated tests currently
- Test endpoints available (`/test_ticktick`, `/test_due_tasks`)

### Deployment
- Currently runs with Flask dev server
- `escposprinter.service` file exists but not configured
- Needs production WSGI server (gunicorn/uwsgi)

### Configuration
- Printer IP hardcoded in `run.py`
- TickTick credentials in `.env`
- No configuration file for runtime settings

## Future Considerations

### Scalability
- Single-user design, no multi-tenancy
- Direct printer connection limits to one printer
- Could be extended with printer pools

### Maintainability
- Well-organized single-file application
- Clear function separation
- Documentation now in place
- Needs unit tests for critical functions

### Performance
- Synchronous API calls could be async
- No caching of TickTick data
- RSS feeds fetched on every request
