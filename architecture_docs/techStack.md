# Technology Stack

## Core Technologies

### Backend Framework
- **Flask** - Python web framework for the REST API
  - Chosen for simplicity and ease of deployment
  - Handles all HTTP endpoints for printer control
  - Runs on port 5001

### Hardware Integration
- **python-escpos (3.1)** - ESC/POS printer library
  - Communicates with thermal printer over network
  - Supports text formatting, alignment, and paper cutting
  - Connected to printer at IP: `192.168.2.134`

### Task Management
- **TickTick API** - Task management integration
  - OAuth2 authentication for secure access
  - REST API for fetching tasks, projects, and tags
  - Client library: ticktick-py (2.0.0)

### Data Sources
- **feedparser (6.0.12)** - RSS feed parsing
  - Fetches news from Heidelberg News (RNZ) and Tagesschau
- **requests** - HTTP client for API calls
  - TickTick API communication
  - Sunrise/sunset data from sunrise-sunset.org

## Key Dependencies

### Python Packages (from requirements.in)
```
feedparser
python-dotenv
python-escpos
Flask
ticktick-py
qrcode
yfinance
python-barcode
```

### Environment Variables (stored in .env)
- `TICKTICK_CLIENT_ID` - TickTick OAuth2 client ID
- `TICKTICK_CLIENT_SECRET` - TickTick OAuth2 client secret
- `TICKTICK_REDIRECT_URI` - OAuth2 callback URL
- `TICKTICK_USERNAME` - TickTick account username
- `TICKTICK_PASSWORD` - TickTick account password

## Architecture Decisions

### Authentication Strategy
**Decision:** Use OAuth2 for TickTick with token storage in local files
- Tokens stored in `.tt_token_full` (full response) and `.tt_token` (token only)
- Fallback to username/password authentication if OAuth fails
- **Rationale:** Provides secure access while maintaining offline token reuse

### Tag Recognition
**Decision:** Extract tags from TickTick's `tags` array field, with fallback to hashtags in text
- Primary: TickTick's native tags array
- Fallback: Regex search for #hashtags in title/description
- **Rationale:** TickTick stores tags separately; hashtags provide backward compatibility

### Quote System
**Decision:** Use local Marc Aurel text file with deterministic daily selection
- Replaced external zenquotes.io API
- Deterministic selection based on date ensures same quote throughout the day
- **Rationale:** Offline operation, no API rate limits, philosophical content

### Printer Communication
**Decision:** Direct network connection to ESC/POS printer
- Printer accessed via Network() class with IP address
- **Rationale:** Simple, reliable, no driver installation required

## Technical Debt

### Configuration Management
- **Issue:** Printer IP and other settings are hardcoded
- **Impact:** Requires code changes for different environments
- **Proposed Solution:** Move to configuration file or environment variables

### Error Handling
- **Issue:** Limited error recovery and user notification
- **Impact:** Silent failures may go unnoticed
- **Proposed Solution:** Implement comprehensive logging and error notifications

### Testing
- **Issue:** No automated tests
- **Impact:** Manual testing required for changes
- **Proposed Solution:** Add unit tests for core functions

### Service Management
- **Issue:** Manual server startup required
- **Impact:** Not persistent across reboots
- **Proposed Solution:** Implement systemd service (escposprinter.service exists but needs configuration)

## Deployment

### Current Setup
- Development server using Flask's built-in server
- Runs on `0.0.0.0:5001` for network access
- Debug mode enabled for development

### Recommended Production Setup
- Use production WSGI server (gunicorn or uwsgi)
- Implement systemd service for automatic startup
- Add systemd timer for scheduled printing
- Consider containerization with Docker

## Integration Points

### External Services
1. **TickTick API** (api.ticktick.com)
   - Tasks, projects, and tags
   - OAuth2 authentication

2. **Sunrise-Sunset API** (api.sunrise-sunset.org)
   - Daily sunrise/sunset times for Heidelberg

3. **RSS Feeds**
   - RNZ Heidelberg: https://www.rnz.de/feed/139-RL_Heidelberg_free.xml
   - Tagesschau: https://www.tagesschau.de/inland/index~rss2.xml

### Local Resources
- `data/marc_aurel.txt` - German philosophical quotes
- `morgenjournal_fragen.json` - Morning journal questions
- `.tt_token_full` - TickTick OAuth tokens
