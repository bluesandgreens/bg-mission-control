# Mission Control V6 — Live Data + Navigation Brief

## What Needs to Change

The current dashboard has HARDCODED data. It needs to pull LIVE from APIs and support day/week/month navigation.

## Architecture

### 1. Data Layer (`scripts/generate-data.py`)
Create a Python script that:
- Pulls from HubSpot API (key at ~/.config/hubspot/api_key)
- Pulls from Stripe API (key at ~/.config/stripe/api_key)  
- Pulls from Windsor AI (key at ~/.config/windsor/api_key, endpoint https://connectors.windsor.ai/facebook)
- Outputs to `data/live-data.json`

Data to pull:
- **HubSpot:** New leads today/this week/this month, DCs booked, DCs completed, deals closed, W1 starts, active members count, pipeline by stage, rep attribution
- **Stripe:** Active subscriptions (count + MRR), failed payments, new subs today/week/month, cancelled subs, revenue by period
- **Windsor AI:** CPBC (cost per booked call) by day, ad spend by day, booked calls by day. Use endpoint: https://connectors.windsor.ai/facebook with params: api_key, date_preset or date_from/date_to, fields=campaign,date,spend,source, _filter_action_type=Booked Call (HS)

### 2. Dashboard Updates (`index.html`)
Update the Live Dashboard view to:
- **Load data from `data/live-data.json`** on page load (fetch)
- **Auto-refresh** every 5 minutes (setInterval)
- **Day/Week/Month navigation** with LEFT and RIGHT arrows:
  - Day view: show single day, arrows move ±1 day
  - Week view: show week range (Mon-Sun), arrows move ±1 week  
  - Month view: show full month, arrows move ±1 month
  - Current period highlighted differently from historical
  - Data filters based on selected date range
- **All 6 sub-tabs must work with the date navigation:**
  - Overview (leads, DCs, closes, W1s, revenue, CPBC)
  - DCs (by rep, close rates, pipeline)
  - DC→W1 (conversion, pending families, time-to-W1)
  - Mentors (capacity, sessions, active mentors)
  - Program (active members, satisfaction, sessions completed)
  - Unit Economics (CAC, LTV, CAC:LTV ratio, CPBC trend)

### 3. Auto-Deploy Cron
After building, create a shell script `scripts/refresh-and-deploy.sh` that:
1. Runs generate-data.py
2. Commits data/live-data.json
3. Pushes to GitHub (triggers GitHub Pages deploy)
This will be run via cron every 30 minutes.

## Design Requirements
- Keep the existing dark theme and styling EXACTLY as is
- Navigation arrows should be clean, minimal — small < > buttons next to the period label
- Current period label shows: "Sunday, March 15" (day) / "Mar 10 - Mar 16" (week) / "March 2026" (month)
- When viewing historical data, show a subtle "Historical" badge
- Loading state while data fetches
- Error state if data.json is stale (>1 hour old)

## API Details

### HubSpot
- Base: https://api.hubapi.com
- Auth: Bearer token from ~/.config/hubspot/api_key
- Contacts: GET /crm/v3/objects/contacts (search with filters for date ranges)
- Deals: GET /crm/v3/objects/deals (search with filters)
- Deal stages: appointmentscheduled (DC Booked), qualifiedtobuy (DC Completed), closedwon (Closed), etc.
- Use the search endpoint POST /crm/v3/objects/deals/search with date filters

### Stripe
- Auth: Basic auth with API key
- Subscriptions: GET /v1/subscriptions?status=active
- Balance transactions: GET /v1/balance_transactions?type=charge&created[gte]=TIMESTAMP
- Customers: GET /v1/customers

### Windsor AI (for CPBC)
- Endpoint: GET https://connectors.windsor.ai/facebook
- Params: api_key=KEY&date_preset=last_7d OR date_from=YYYY-MM-DD&date_to=YYYY-MM-DD
- Returns: campaign-level data with spend and conversion actions
- Filter for action_type containing "Booked Call" to get CPBC

## File Structure
```
bg-mission-control/
├── index.html          (updated with live data loading + navigation)
├── data/
│   └── live-data.json  (generated, gitignored for local but committed for Pages)
├── scripts/
│   ├── generate-data.py
│   ├── refresh-and-deploy.sh
│   └── API_REFERENCE.md
└── REBUILD-BRIEF.md
```

## IMPORTANT
- Do NOT break existing views (Agent HQ, Team Office, Advisory Board, Feed)
- Only modify the Live Dashboard view
- The data.json should have a "generated_at" timestamp
- Handle API errors gracefully — if one source fails, still show data from others
- All amounts in AUD
- Read API keys from files, never hardcode them
