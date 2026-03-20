#!/usr/bin/env python3
"""
generate-data.py
Pull live data from HubSpot, Stripe, Meta Ads, and Supabase APIs and output
consolidated JSON to data/dashboard-data.json.

Usage:
    python scripts/generate-data.py
    python scripts/generate-data.py --period yesterday
    python scripts/generate-data.py --period 2026-03-15 --output data/custom.json
"""

import argparse
import calendar
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone

try:
    import requests
except ImportError:
    print("ERROR: 'requests' library is required. Install with: pip install requests", file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

HUBSPOT_OWNERS = {
    "75967744": "Harry",
    "86194016": "Elliot",
    "87029276": "Anthony",
    "88035516": "Bailey",
    "86488316": "Rye",
    "86750401": "Brodie",
}

META_AD_ACCOUNT = "act_1631004910795417"
# CRITICAL: When using 'conversions' field (not 'actions'), the action_type
# uses the EVENT NAME not the numeric pixel ID.
# 'actions' field uses: offsite_conversion.fb_pixel_custom.956033550334742
# 'conversions' field uses: offsite_conversion.fb_pixel_custom.Booked Call (HS)
# We use 'conversions' because it breaks out individual events properly.
# DO NOT change this back to the numeric ID -- it won't match.
META_PIXEL_ACTION = "offsite_conversion.fb_pixel_custom.Booked Call (HS)"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def log(msg: str):
    """Print progress to stderr so stdout stays clean."""
    print(f"[generate-data] {msg}", file=sys.stderr)


def read_key(path: str) -> str:
    """Read an API key from a file, stripping whitespace."""
    expanded = os.path.expanduser(path)
    try:
        with open(expanded, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        log(f"WARNING: Key file not found: {expanded}")
        return ""


def date_to_ms(dt: datetime) -> int:
    """Convert a datetime to milliseconds since epoch (UTC midnight)."""
    return int(dt.replace(hour=0, minute=0, second=0, microsecond=0,
                          tzinfo=timezone.utc).timestamp() * 1000)


def date_to_unix(dt: datetime) -> int:
    """Convert a datetime to unix timestamp (seconds)."""
    return int(dt.replace(hour=0, minute=0, second=0, microsecond=0,
                          tzinfo=timezone.utc).timestamp())


def end_of_day_ms(dt: datetime) -> int:
    """End-of-day timestamp in milliseconds (23:59:59.999 UTC)."""
    return int(dt.replace(hour=23, minute=59, second=59, microsecond=999999,
                          tzinfo=timezone.utc).timestamp() * 1000)


def end_of_day_unix(dt: datetime) -> int:
    """End-of-day timestamp in seconds (23:59:59 UTC)."""
    return int(dt.replace(hour=23, minute=59, second=59, microsecond=0,
                          tzinfo=timezone.utc).timestamp())


def monday_of(dt: datetime) -> datetime:
    """Return the Monday of the week containing dt."""
    return dt - timedelta(days=dt.weekday())


def parse_period(period_str: str) -> datetime:
    """Parse a --period value into a date. Uses AEDT (UTC+11) for 'today'."""
    import zoneinfo
    try:
        aedt = zoneinfo.ZoneInfo("Australia/Melbourne")
        today = datetime.now(aedt).date()
    except Exception:
        today = datetime.utcnow().date()
    if period_str == "today":
        return datetime(today.year, today.month, today.day)
    elif period_str == "yesterday":
        d = today - timedelta(days=1)
        return datetime(d.year, d.month, d.day)
    else:
        d = datetime.strptime(period_str, "%Y-%m-%d")
        return d


# ---------------------------------------------------------------------------
# Supabase helpers
# ---------------------------------------------------------------------------

SUPABASE_URL = "https://ltpkeddkkrexynlhgxal.supabase.co"


def load_supabase_key() -> str:
    """Read Supabase service_role_key from ~/.config/supabase/config.json."""
    config_path = os.path.expanduser("~/.config/supabase/config.json")
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        return config.get("service_role_key", "")
    except Exception as e:
        log(f"WARNING: Could not load Supabase config: {e}")
        return ""


def supabase_get(supabase_url: str, supabase_key: str, table: str, params: str = "") -> list:
    """Make a GET request to Supabase REST API. Returns list of rows or empty list."""
    if not supabase_key:
        return []
    url = f"{supabase_url}/rest/v1/{table}"
    if params:
        url = f"{url}?{params}"
    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        log(f"Supabase error ({table}): {e}")
        return []


def fetch_supabase_cache(supabase_url: str, supabase_key: str, cache_key: str) -> dict:
    """Fetch a hubspot_cache entry by cache_key. Returns the data field or empty dict."""
    try:
        rows = supabase_get(
            supabase_url, supabase_key,
            "hubspot_cache",
            f"cache_key=eq.{cache_key}&select=data,updated_at",
        )
        if rows and isinstance(rows, list) and len(rows) > 0:
            return rows[0].get("data", {}) or {}
        return {}
    except Exception as e:
        log(f"Supabase cache fetch error ({cache_key}): {e}")
        return {}


# ---------------------------------------------------------------------------
# HubSpot helpers
# ---------------------------------------------------------------------------

HUBSPOT_SEARCH_URL = "https://api.hubapi.com/crm/v3/objects/contacts/search"


def hubspot_headers(api_key: str) -> dict:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def hubspot_search_count(api_key: str, filters: list, properties: list = None) -> int:
    """Run a HubSpot CRM search and return the total count."""
    if not api_key:
        return 0
    body = {
        "filterGroups": [{"filters": filters}],
        "limit": 1,
    }
    if properties:
        body["properties"] = properties
    try:
        resp = requests.post(HUBSPOT_SEARCH_URL, headers=hubspot_headers(api_key),
                             json=body, timeout=30)
        resp.raise_for_status()
        return resp.json().get("total", 0)
    except Exception as e:
        log(f"HubSpot search error: {e}")
        return 0


def hubspot_search_contacts(api_key: str, filters: list, properties: list,
                            max_results: int = 200) -> list:
    """Run a HubSpot CRM search and return contact records (paginated)."""
    if not api_key:
        return []
    results = []
    after = None
    while True:
        body = {
            "filterGroups": [{"filters": filters}],
            "properties": properties,
            "limit": 100,
        }
        if after:
            body["after"] = after
        try:
            resp = requests.post(HUBSPOT_SEARCH_URL, headers=hubspot_headers(api_key),
                                 json=body, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            results.extend(data.get("results", []))
            paging = data.get("paging", {})
            next_page = paging.get("next", {})
            after = next_page.get("after")
            if not after or len(results) >= max_results:
                break
        except Exception as e:
            log(f"HubSpot search error: {e}")
            break
    return results[:max_results]


def hubspot_date_filter(prop: str, start_ms: int, end_ms: int) -> list:
    """Build HubSpot date-range filters for a property."""
    return [
        {"propertyName": prop, "operator": "GTE", "value": str(start_ms)},
        {"propertyName": prop, "operator": "LTE", "value": str(end_ms)},
    ]


def hubspot_date_filter_with_owner(prop: str, start_ms: int, end_ms: int,
                                   owner_id: str) -> list:
    """Date-range filters plus owner filter."""
    return hubspot_date_filter(prop, start_ms, end_ms) + [
        {"propertyName": "hubspot_owner_id", "operator": "EQ", "value": owner_id},
    ]


def hubspot_has_property(prop: str) -> dict:
    """Filter: property has any value."""
    return {"propertyName": prop, "operator": "HAS_PROPERTY"}


def hubspot_not_has_property(prop: str) -> dict:
    """Filter: property has no value."""
    return {"propertyName": prop, "operator": "NOT_HAS_PROPERTY"}


# ---------------------------------------------------------------------------
# Section A: Pulse Metrics
# ---------------------------------------------------------------------------

PULSE_METRICS = [
    ("new_leads", "createdate"),
    ("booked_calls", "date_dc_was_booked"),
    ("dcs_completed", "discovery_call_completed_on"),
    ("closes", "onboarding_call_scheduled"),
    ("w1_starts", "week_1_complete"),
    ("agreement_forms", "agreement_form_signed_time"),
]


def fetch_pulse(api_key: str, target: datetime) -> dict:
    """Fetch pulse metrics for today, week-to-date, and month-to-date."""
    log("Fetching pulse metrics...")

    day_start = date_to_ms(target)
    day_end = end_of_day_ms(target)

    week_start_dt = monday_of(target)
    week_start = date_to_ms(week_start_dt)

    month_start_dt = target.replace(day=1)
    month_start = date_to_ms(month_start_dt)

    result = {"today": {}, "wtd": {}, "mtd": {}}

    for metric_name, hs_prop in PULSE_METRICS:
        # Today
        count_today = hubspot_search_count(api_key,
                                           hubspot_date_filter(hs_prop, day_start, day_end))
        # WTD
        count_wtd = hubspot_search_count(api_key,
                                         hubspot_date_filter(hs_prop, week_start, day_end))
        # MTD
        count_mtd = hubspot_search_count(api_key,
                                         hubspot_date_filter(hs_prop, month_start, day_end))

        result["today"][metric_name] = count_today
        result["wtd"][metric_name] = count_wtd
        result["mtd"][metric_name] = count_mtd
        log(f"  {metric_name}: today={count_today}, wtd={count_wtd}, mtd={count_mtd}")

    return result


# ---------------------------------------------------------------------------
# Section B: Rep Breakdown
# ---------------------------------------------------------------------------

def fetch_reps(api_key: str, target: datetime) -> list:
    """Per-rep breakdown of leads, DCs, closes, close rate, W1 starts."""
    log("Fetching rep breakdown...")

    day_start = date_to_ms(target)
    day_end = end_of_day_ms(target)
    week_start = date_to_ms(monday_of(target))
    month_start = date_to_ms(target.replace(day=1))

    periods = {
        "today": (day_start, day_end),
        "wtd": (week_start, day_end),
        "mtd": (month_start, day_end),
    }

    rep_metrics = [
        ("leads", "createdate"),
        ("dcs_taken", "discovery_call_completed_on"),
        ("closes", "onboarding_call_scheduled"),
        ("w1_starts", "week_1_complete"),
    ]

    reps = []
    for owner_id, name in HUBSPOT_OWNERS.items():
        log(f"  Rep: {name} ({owner_id})")
        rep = {"name": name, "owner_id": owner_id}
        for period_key, (start, end) in periods.items():
            data = {}
            for metric_name, hs_prop in rep_metrics:
                filters = hubspot_date_filter_with_owner(hs_prop, start, end, owner_id)
                data[metric_name] = hubspot_search_count(api_key, filters)
            # Close rate
            dcs = data.get("dcs_taken", 0)
            closes = data.get("closes", 0)
            data["close_rate"] = round(closes / dcs, 2) if dcs > 0 else 0.0
            rep[period_key] = data
        reps.append(rep)

    return reps


# ---------------------------------------------------------------------------
# Section C: Meta Ads
# ---------------------------------------------------------------------------

def fetch_meta_insights(api_key: str, since: str, until: str) -> dict:
    """Fetch Meta Ads insights for a date range. Returns dict with spend, booked_calls, cpbc."""
    if not api_key:
        return {"spend": 0, "booked_calls": 0, "cpbc": 0}

    # CRITICAL: Use 'conversions' field, NOT 'actions'.
    # 'actions' lumps ALL pixel events together = wrong number.
    # 'conversions' breaks out individual custom pixel events so we can
    # isolate Booked Call (HS) specifically.
    # This was debugged on March 14 and March 18 2026 -- do NOT revert.
    url = f"https://graph.facebook.com/v22.0/{META_AD_ACCOUNT}/insights"
    params = {
        "fields": "spend,conversions,cost_per_conversion",
        "time_range": json.dumps({"since": since, "until": until}),
        "level": "account",
        "access_token": api_key,
    }
    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json().get("data", [])
        if not data:
            return {"spend": 0, "booked_calls": 0, "cpbc": 0}

        row = data[0]
        spend = float(row.get("spend", 0))
        booked_calls = 0
        cpbc_from_api = 0

        # Extract booked calls from conversions (NOT actions)
        for conv in row.get("conversions", []):
            if conv.get("action_type") == META_PIXEL_ACTION:
                booked_calls = int(conv.get("value", 0))
                break

        # Try to get CPBC directly from cost_per_conversion
        for cpc in row.get("cost_per_conversion", []):
            if cpc.get("action_type") == META_PIXEL_ACTION:
                cpbc_from_api = float(cpc.get("value", 0))
                break

        # Fall back to manual calc if API doesn't return cost_per_conversion
        cpbc = cpbc_from_api if cpbc_from_api > 0 else (round(spend / booked_calls, 2) if booked_calls > 0 else 0)
        return {"spend": round(spend, 2), "booked_calls": booked_calls, "cpbc": round(cpbc, 2)}
    except Exception as e:
        log(f"Meta Ads error: {e}")
        return {"spend": 0, "booked_calls": 0, "cpbc": 0}


def fetch_meta(api_key: str, target: datetime) -> dict:
    """Fetch Meta Ads data for today, WTD, MTD."""
    log("Fetching Meta Ads data...")

    day_str = target.strftime("%Y-%m-%d")
    week_start_str = monday_of(target).strftime("%Y-%m-%d")
    month_start_str = target.replace(day=1).strftime("%Y-%m-%d")

    result = {
        "today": fetch_meta_insights(api_key, day_str, day_str),
        "wtd": fetch_meta_insights(api_key, week_start_str, day_str),
        "mtd": fetch_meta_insights(api_key, month_start_str, day_str),
    }

    for period in ("today", "wtd", "mtd"):
        d = result[period]
        log(f"  {period}: spend=${d['spend']}, booked={d['booked_calls']}, cpbc=${d['cpbc']}")

    return result


# ---------------------------------------------------------------------------
# Section D: Stripe
# ---------------------------------------------------------------------------

def stripe_headers(api_key: str) -> dict:
    return {"Authorization": f"Bearer {api_key}"}


def stripe_get(api_key: str, endpoint: str, params: dict = None) -> dict:
    """Make a GET request to Stripe API."""
    if not api_key:
        return {}
    url = f"https://api.stripe.com/v1{endpoint}"
    try:
        resp = requests.get(url, headers=stripe_headers(api_key), params=params or {},
                            timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        log(f"Stripe error ({endpoint}): {e}")
        return {}


def count_stripe_paginated(api_key: str, endpoint: str, params: dict) -> int:
    """Count all items from a paginated Stripe list endpoint."""
    if not api_key:
        return 0
    total = 0
    has_more = True
    current_params = dict(params)
    current_params["limit"] = 100

    while has_more:
        data = stripe_get(api_key, endpoint, current_params)
        items = data.get("data", [])
        total += len(items)
        has_more = data.get("has_more", False)
        if has_more and items:
            current_params["starting_after"] = items[-1]["id"]
        else:
            break
    return total


def fetch_stripe(api_key: str, target: datetime) -> dict:
    """Fetch Stripe data: active subs, MRR, failed payments, new subs, cancellations."""
    log("Fetching Stripe data...")

    result = {
        "active_subscriptions": 0,
        "mrr": 0,
        "failed_payments": 0,
        "new_subscriptions": 0,
        "recent_cancellations": [],
    }

    if not api_key:
        log("  Skipping Stripe (no API key)")
        return result

    # Active subscriptions + MRR
    log("  Counting active subscriptions and computing MRR...")
    active_subs = []
    params = {"status": "active", "limit": 100}
    has_more = True
    while has_more:
        data = stripe_get(api_key, "/subscriptions", params)
        items = data.get("data", [])
        active_subs.extend(items)
        has_more = data.get("has_more", False)
        if has_more and items:
            params["starting_after"] = items[-1]["id"]
        else:
            break

    result["active_subscriptions"] = len(active_subs)

    mrr_cents = 0
    for sub in active_subs:
        # Handle both single-plan and multi-item subscriptions
        sub_items = sub.get("items", {}).get("data", [])
        for item in sub_items:
            price = item.get("price", {}) or item.get("plan", {})
            amount = price.get("unit_amount", 0) or price.get("amount", 0)
            interval = price.get("recurring", {}).get("interval", "month") if "recurring" in price else price.get("interval", "month")
            interval_count = price.get("recurring", {}).get("interval_count", 1) if "recurring" in price else price.get("interval_count", 1)
            quantity = item.get("quantity", 1)

            # Normalise to monthly
            if interval == "year":
                monthly = (amount * quantity) / (12 * interval_count)
            elif interval == "week":
                monthly = (amount * quantity * 52) / (12 * interval_count)
            elif interval == "day":
                monthly = (amount * quantity * 365) / (12 * interval_count)
            else:  # month
                monthly = (amount * quantity) / interval_count

            mrr_cents += monthly

    result["mrr"] = round(mrr_cents / 100, 2)
    log(f"  Active subs: {result['active_subscriptions']}, MRR: ${result['mrr']}")

    # Failed payments in period
    day_start_unix = date_to_unix(target)
    day_end_unix = end_of_day_unix(target)
    log("  Counting failed payments...")
    failed_count = count_stripe_paginated(api_key, "/charges", {
        "created[gte]": day_start_unix,
        "created[lte]": day_end_unix,
    })
    # We filter for failed status client-side since the Stripe charges endpoint
    # doesn't have a status filter directly - we need to check each charge.
    # Actually, let's just count by fetching with limit and checking status.
    failed_charges = []
    params_fc = {"created[gte]": day_start_unix, "created[lte]": day_end_unix, "limit": 100}
    has_more = True
    while has_more:
        data = stripe_get(api_key, "/charges", params_fc)
        for charge in data.get("data", []):
            if charge.get("status") == "failed":
                failed_charges.append(charge)
        has_more = data.get("has_more", False)
        items = data.get("data", [])
        if has_more and items:
            params_fc["starting_after"] = items[-1]["id"]
        else:
            break
    result["failed_payments"] = len(failed_charges)
    log(f"  Failed payments (today): {result['failed_payments']}")

    # Failed payments in last 7 days
    log("  Counting failed payments (7d)...")
    seven_days_ago_unix = date_to_unix(target - timedelta(days=7))
    failed_7d = []
    params_7d = {"created[gte]": seven_days_ago_unix, "created[lte]": day_end_unix, "limit": 100}
    has_more = True
    while has_more:
        data = stripe_get(api_key, "/charges", params_7d)
        for charge in data.get("data", []):
            if charge.get("status") == "failed":
                failed_7d.append({
                    "name": (charge.get("billing_details") or {}).get("name", ""),
                    "email": charge.get("receipt_email", ""),
                    "amount_aud": round(charge.get("amount", 0) / 100, 2),
                })
        has_more = data.get("has_more", False)
        items = data.get("data", [])
        if has_more and items:
            params_7d["starting_after"] = items[-1]["id"]
        else:
            break
    result["failed_payments_7d"] = len(failed_7d)
    result["failed_payments_7d_total"] = round(sum(f["amount_aud"] for f in failed_7d), 2)
    result["failed_payments_7d_list"] = failed_7d[:20]
    log(f"  Failed payments (7d): {result['failed_payments_7d']} (${result['failed_payments_7d_total']})")

    # Past due subscriptions
    log("  Fetching past due subscriptions...")
    past_due_subs = []
    pd_params = {"status": "past_due", "limit": 100, "expand[]": "data.customer"}
    pd_data = stripe_get(api_key, "/subscriptions", pd_params)
    for sub in pd_data.get("data", []):
        cust = sub.get("customer", {})
        items_data = sub.get("items", {}).get("data", [])
        amt = items_data[0].get("price", {}).get("unit_amount", 0) if items_data else 0
        interval = items_data[0].get("price", {}).get("recurring", {}).get("interval", "?") if items_data else "?"
        past_due_subs.append({
            "name": cust.get("name", cust.get("email", "Unknown")),
            "amount_aud": round(amt / 100, 2),
            "interval": interval,
        })
    result["past_due_count"] = len(past_due_subs)
    result["past_due_list"] = past_due_subs
    log(f"  Past due: {result['past_due_count']}")

    # New subscriptions in period
    log("  Counting new subscriptions...")
    new_sub_count = count_stripe_paginated(api_key, "/subscriptions", {
        "created[gte]": day_start_unix,
        "created[lte]": day_end_unix,
    })
    result["new_subscriptions"] = new_sub_count
    log(f"  New subscriptions: {new_sub_count}")

    # Recent cancellations (last 30 days)
    log("  Fetching recent cancellations...")
    thirty_days_ago = date_to_unix(target - timedelta(days=30))
    cancel_params = {
        "status": "canceled",
        "created[gte]": thirty_days_ago,
        "limit": 100,
    }
    cancellations = []
    has_more = True
    while has_more:
        data = stripe_get(api_key, "/subscriptions", cancel_params)
        for sub in data.get("data", []):
            cancellations.append({
                "id": sub.get("id"),
                "canceled_at": sub.get("canceled_at"),
                "customer": sub.get("customer"),
            })
        has_more = data.get("has_more", False)
        items = data.get("data", [])
        if has_more and items:
            cancel_params["starting_after"] = items[-1]["id"]
        else:
            break
    result["recent_cancellations"] = cancellations
    log(f"  Recent cancellations: {len(cancellations)}")

    # Upcoming renewals (next 10 days, excluding weekly billing)
    log("  Fetching upcoming renewals (next 10 days, non-weekly)...")
    upcoming = []
    now_unix = int(datetime.now(timezone.utc).timestamp())
    ten_days_unix = now_unix + (10 * 86400)
    for sub in active_subs:
        period_end = sub.get("current_period_end", 0)
        if now_unix < period_end <= ten_days_unix:
            sub_items = sub.get("items", {}).get("data", [])
            for item in sub_items:
                price = item.get("price", {}) or item.get("plan", {})
                interval = price.get("recurring", {}).get("interval", "month") if "recurring" in price else price.get("interval", "month")
                if interval == "week":
                    continue  # Skip weekly
                amount = price.get("unit_amount", 0) or price.get("amount", 0)
                interval_count = price.get("recurring", {}).get("interval_count", 1) if "recurring" in price else price.get("interval_count", 1)
                cust_id = sub.get("customer", "")
                # Try to get customer name
                cust_name = ""
                try:
                    cust_data = stripe_get(api_key, f"/customers/{cust_id}", {})
                    cust_name = cust_data.get("name", cust_data.get("email", cust_id))
                except Exception:
                    cust_name = cust_id
                upcoming.append({
                    "name": cust_name,
                    "customer_id": cust_id,
                    "renewal_date": period_end,
                    "amount": round(amount / 100, 2),
                    "interval": f"{interval_count} {interval}{'s' if interval_count > 1 else ''}",
                    "status": sub.get("status", "active"),
                    "subscription_id": sub.get("id"),
                })
    upcoming.sort(key=lambda x: x["renewal_date"])
    result["upcoming_renewals"] = upcoming
    log(f"  Upcoming renewals (non-weekly, 10d): {len(upcoming)}")

    return result


# ---------------------------------------------------------------------------
# Section E: Activation Pipeline
# ---------------------------------------------------------------------------

ACTIVATION_PROPERTIES = [
    "firstname", "lastname",
    "onboarding_call_scheduled", "agreement_form_signed_time",
    "mentor_allocated_time", "week_1_scheduled_for", "new_week_1_scheduled",
    "week_1_complete", "w1_activation_stage",
]

# Stage order from earliest to latest
ACTIVATION_STAGE_ORDER = [
    "deposit_paid",
    "agreement_signed",
    "mentor_allocated",
    "w1_scheduled",
    "w1_complete",
]


def fetch_activation_pipeline(api_key: str) -> dict:
    """
    Fetch activation pipeline contacts.
    Contacts in activation = closed (onboarding_call_scheduled set) but week_1_complete NOT set.
    Bucket by furthest stage reached using actual property presence.
    """
    log("Fetching activation pipeline...")

    result = {stage: [] for stage in ACTIVATION_STAGE_ORDER}

    if not api_key:
        log("  Skipping activation pipeline (no API key)")
        return result

    # Find contacts who closed but haven't done W1 yet
    filters = [
        hubspot_has_property("onboarding_call_scheduled"),
        hubspot_not_has_property("week_1_complete"),
    ]

    contacts = hubspot_search_contacts(api_key, filters, ACTIVATION_PROPERTIES, max_results=200)
    log(f"  Found {len(contacts)} contacts in activation pipeline")

    for contact in contacts:
        props = contact.get("properties", {})
        name = f"{props.get('firstname', '')} {props.get('lastname', '')}".strip() or "Unknown"
        w1_stage = props.get("w1_activation_stage", "")

        # Determine stage by checking properties in reverse order (highest first)
        if props.get("week_1_scheduled_for") or props.get("new_week_1_scheduled"):
            stage = "w1_scheduled"
            date_val = props.get("week_1_scheduled_for") or props.get("new_week_1_scheduled", "")
        elif props.get("mentor_allocated_time"):
            stage = "mentor_allocated"
            date_val = props.get("mentor_allocated_time", "")
        elif props.get("agreement_form_signed_time"):
            stage = "agreement_signed"
            date_val = props.get("agreement_form_signed_time", "")
        else:
            stage = "deposit_paid"
            date_val = props.get("onboarding_call_scheduled", "")

        result[stage].append({
            "name": name,
            "date": date_val,
            "w1_activation_stage": w1_stage,
        })

    for stage in ACTIVATION_STAGE_ORDER:
        log(f"  {stage}: {len(result[stage])} contacts")

    return result


# ---------------------------------------------------------------------------
# Section F: Retention Data
# ---------------------------------------------------------------------------

def fetch_retention(api_key: str, target: datetime) -> dict:
    """
    Fetch retention data:
    - Members at session 7+
    - Payment resets in next 30 days
    """
    log("Fetching retention data...")

    result = {
        "session_7_plus": [],
        "payment_resets_30d": [],
        "_notes": [],
    }

    if not api_key:
        log("  Skipping retention (no API key)")
        return result

    # Session 7+ members
    try:
        filters = [
            {"propertyName": "mentor_session_number", "operator": "GTE", "value": "7"},
        ]
        contacts = hubspot_search_contacts(
            api_key, filters,
            ["firstname", "lastname", "mentor_session_number", "payment_reset_date"],
            max_results=200,
        )
        for c in contacts:
            props = c.get("properties", {})
            name = f"{props.get('firstname', '')} {props.get('lastname', '')}".strip()
            result["session_7_plus"].append({
                "name": name or "Unknown",
                "session_count": props.get("mentor_session_number", ""),
                "payment_reset_date": props.get("payment_reset_date", ""),
            })
        log(f"  Session 7+ members: {len(result['session_7_plus'])}")
    except Exception as e:
        log(f"  mentor_session_number property may not exist: {e}")
        result["_notes"].append("mentor_session_number property may not exist in HubSpot")

    # Payment resets in next 30 days
    try:
        future_start = date_to_ms(target)
        future_end = date_to_ms(target + timedelta(days=30))
        filters = hubspot_date_filter("payment_reset_date", future_start, future_end)
        contacts = hubspot_search_contacts(
            api_key, filters,
            ["firstname", "lastname", "payment_reset_date"],
            max_results=200,
        )
        for c in contacts:
            props = c.get("properties", {})
            name = f"{props.get('firstname', '')} {props.get('lastname', '')}".strip()
            result["payment_resets_30d"].append({
                "name": name or "Unknown",
                "payment_reset_date": props.get("payment_reset_date", ""),
            })
        log(f"  Payment resets in 30d: {len(result['payment_resets_30d'])}")
    except Exception as e:
        log(f"  payment_reset_date property may not exist: {e}")
        result["_notes"].append("payment_reset_date property may not exist in HubSpot")

    if not result["session_7_plus"] and not result["payment_resets_30d"]:
        result["_notes"].append(
            "Retention properties (session_count, payment_reset_date) may not exist. "
            "Returning empty arrays."
        )

    return result


# ---------------------------------------------------------------------------
# Section G: Mentor Data
# ---------------------------------------------------------------------------

def fetch_mentors(api_key: str) -> dict:
    """
    Fetch mentor data. Searches for contacts/owners who are mentors.
    Uses mentor_name or mentor_allocated property to determine assignments.
    """
    log("Fetching mentor data...")

    result = {
        "active_count": 0,
        "members_per_mentor": [],
        "at_capacity": 0,
        "_notes": [],
    }

    if not api_key:
        log("  Skipping mentors (no API key)")
        return result

    try:
        # Find all active members with a mentor assigned
        filters = [
            hubspot_has_property("mentor_name1"),
            hubspot_has_property("week_1_complete"),
        ]
        contacts = hubspot_search_contacts(
            api_key, filters,
            ["firstname", "lastname", "mentor_name1", "mentor_session_number"],
            max_results=500,
        )

        # Group by mentor
        mentor_counts = {}
        for c in contacts:
            mentor = c.get("properties", {}).get("mentor_name1", "Unknown")
            if mentor:
                mentor_counts[mentor] = mentor_counts.get(mentor, 0) + 1

        result["active_count"] = len(mentor_counts)
        result["members_per_mentor"] = [
            {"mentor": m, "count": cnt} for m, cnt in sorted(mentor_counts.items())
        ]
        # Consider "at capacity" as mentors with 10+ members (heuristic)
        result["at_capacity"] = sum(1 for cnt in mentor_counts.values() if cnt >= 10)

        log(f"  Active mentors: {result['active_count']}")
        log(f"  At capacity: {result['at_capacity']}")

    except Exception as e:
        log(f"  Mentor data fetch failed: {e}")
        result["_notes"].append(
            "Mentor properties may not exist in HubSpot. Returning placeholder data."
        )

    if not result["members_per_mentor"]:
        result["_notes"].append(
            "No mentor data found. The mentor_allocated property may not be populated."
        )

    return result


# ---------------------------------------------------------------------------
# Section H: Supabase Data Pulls
# ---------------------------------------------------------------------------

def fetch_portal_stats(supabase_url: str, supabase_key: str) -> dict:
    """Fetch portal stats from admin_dashboard_stats cache key."""
    try:
        data = fetch_supabase_cache(supabase_url, supabase_key, "admin_dashboard_stats")
        if not data:
            return {}
        return {
            "active_users": data.get("active_users", 0),
            "active_mentors": data.get("active_mentors", 0),
            "unassigned_count": data.get("unassigned_count", 0),
            "parent_nps_score": data.get("parent_nps_score", 0),
            "safeguarding_flags": data.get("safeguarding_flags", 0),
            "support_requests_open": data.get("support_requests_open", 0),
            "parent_escalations_open": data.get("parent_escalations_open", 0),
            "activation_pipeline_total": data.get("activation_pipeline_total", 0),
        }
    except Exception as e:
        log(f"fetch_portal_stats error: {e}")
        return {}


def fetch_overdue_w1s(supabase_url: str, supabase_key: str) -> list:
    """Fetch overdue Week 1 sessions from activation_pipeline cache."""
    try:
        data = fetch_supabase_cache(supabase_url, supabase_key, "activation_pipeline")
        if not data:
            return []

        members = data if isinstance(data, list) else data.get("members", data.get("contacts", []))
        if not isinstance(members, list):
            return []

        today = datetime.utcnow().date()
        overdue = []
        for m in members:
            w1_date_str = m.get("week_1_scheduled_for", "")
            w1_complete = m.get("week_1_complete", "") or m.get("w1_complete", "")
            if not w1_date_str or w1_complete:
                continue
            # Skip withdrawn or inactive members
            onboarding_stage = (m.get("onboarding_stage") or "").lower()
            member_status = (m.get("member_status") or "").lower()
            if "withdrew" in onboarding_stage or member_status in ("inactive", "churn"):
                continue
            try:
                w1_date = datetime.strptime(str(w1_date_str)[:10], "%Y-%m-%d").date()
            except (ValueError, TypeError):
                continue
            if w1_date < today:
                days_overdue = (today - w1_date).days
                name = m.get("son_name") or f"{m.get('firstname', '')} {m.get('lastname', '')}".strip() or "Unknown"
                overdue.append({
                    "name": name,
                    "w1_scheduled_date": str(w1_date_str)[:10],
                    "days_overdue": days_overdue,
                    "activation_stage": m.get("w1_activation_stage", ""),
                    "mentor": m.get("mentor_name1") or m.get("associated_mentor_name", ""),
                })
        return overdue
    except Exception as e:
        log(f"fetch_overdue_w1s error: {e}")
        return []


def fetch_dc_closes(supabase_url: str, supabase_key: str, hubspot_key: str = None) -> list:
    """Fetch recent DC closes from HubSpot directly (with rep names)."""
    if not hubspot_key:
        return _fetch_dc_closes_supabase(supabase_url, supabase_key)
    try:
        fourteen_days_ago_ms = int((datetime.now(timezone.utc) - timedelta(days=14)).timestamp() * 1000)
        payload = {
            "filterGroups": [{
                "filters": [{
                    "propertyName": "onboarding_call_scheduled",
                    "operator": "GTE",
                    "value": str(fourteen_days_ago_ms)
                }]
            }],
            "properties": ["firstname", "lastname", "onboarding_call_scheduled",
                           "discovery_call_taken_by", "discovery_call_outcome", "member_status"],
            "limit": 100
        }
        headers = {"Authorization": f"Bearer {hubspot_key}", "Content-Type": "application/json"}
        resp = requests.post("https://api.hubapi.com/crm/v3/objects/contacts/search",
                             headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        results = resp.json().get("results", [])
        closes = []
        for r in results:
            p = r.get("properties", {})
            name = f"{p.get('firstname', '')} {p.get('lastname', '')}".strip() or "Unknown"
            close_date = str(p.get("onboarding_call_scheduled", ""))[:10]
            closes.append({
                "name": name,
                "close_date": close_date,
                "rep": p.get("discovery_call_taken_by", ""),
                "status": p.get("member_status", p.get("discovery_call_outcome", "")),
            })
        closes.sort(key=lambda x: x.get("close_date", ""), reverse=True)
        return closes
    except Exception as e:
        log(f"fetch_dc_closes HubSpot error: {e}")
        return _fetch_dc_closes_supabase(supabase_url, supabase_key)


def _fetch_dc_closes_supabase(supabase_url: str, supabase_key: str) -> list:
    """Fallback: fetch closes from Supabase pipeline_members cache."""
    try:
        data = fetch_supabase_cache(supabase_url, supabase_key, "pipeline_members")
        if not data:
            return []
        members = data if isinstance(data, list) else data.get("members", data.get("contacts", []))
        if not isinstance(members, list):
            return []
        return [{"name": f"{m.get('firstname','')} {m.get('lastname','')}".strip() or "Unknown",
                 "close_date": "", "rep": "", "status": ""} for m in members]
    except Exception as e:
        log(f"fetch_dc_closes supabase error: {e}")
        return []


def fetch_perf_flags(supabase_url: str, supabase_key: str) -> list:
    """Build performance flags from leaderboard and team_health cache keys."""
    try:
        leaderboard = fetch_supabase_cache(supabase_url, supabase_key, "leaderboard")
        team_health = fetch_supabase_cache(supabase_url, supabase_key, "team_health")
        flags = []

        # Process leaderboard data
        if leaderboard:
            mentors_lb = leaderboard if isinstance(leaderboard, list) else leaderboard.get("mentors", [])
            if isinstance(mentors_lb, list):
                for mentor in mentors_lb:
                    mentor_name = mentor.get("name", "Unknown")

                    # No-shows this week
                    no_shows = mentor.get("noShows", {})
                    no_shows_week = no_shows.get("week", []) if isinstance(no_shows, dict) else []
                    if isinstance(no_shows_week, list) and len(no_shows_week) > 0:
                        flags.append({
                            "type": "no_show",
                            "detail": f"{len(no_shows_week)} no-show(s) this week",
                            "mentor": mentor_name,
                            "severity": "high",
                        })

                    # Wellbeing flags from leaderboard
                    wellbeing = mentor.get("wellbeing", {})
                    wellbeing_week = wellbeing.get("week", []) if isinstance(wellbeing, dict) else []
                    if isinstance(wellbeing_week, list) and len(wellbeing_week) > 0:
                        flags.append({
                            "type": "wellbeing",
                            "detail": f"{len(wellbeing_week)} wellbeing flag(s) this week",
                            "mentor": mentor_name,
                            "severity": "high",
                        })

        # Process team_health data
        if team_health:
            members_th = team_health if isinstance(team_health, list) else team_health.get("members", [])
            if isinstance(members_th, list):
                for member in members_th:
                    mentor_name = member.get("mentor", member.get("name", "Unknown"))

                    # Low session consistency
                    consistency = member.get("avgSessionConsistency", 1.0)
                    try:
                        if float(consistency) < 0.6:
                            flags.append({
                                "type": "low_consistency",
                                "detail": f"Session consistency {consistency}",
                                "mentor": mentor_name,
                                "severity": "medium",
                            })
                    except (ValueError, TypeError):
                        pass

                    # Overdue sessions
                    days_since = member.get("daysSinceSession", 0)
                    try:
                        if int(days_since) > 14:
                            flags.append({
                                "type": "overdue_session",
                                "detail": f"{days_since} days since last session",
                                "mentor": mentor_name,
                                "severity": "high" if int(days_since) > 21 else "medium",
                            })
                    except (ValueError, TypeError):
                        pass

            # Wellbeing flags from team_health flaggedCount
            flagged_count = team_health.get("flaggedCount", 0)
            try:
                if int(flagged_count) > 0:
                    flags.append({
                        "type": "wellbeing",
                        "detail": f"{flagged_count} flagged in team health",
                        "mentor": "team",
                        "severity": "high",
                    })
            except (ValueError, TypeError):
                pass

        return flags
    except Exception as e:
        log(f"fetch_perf_flags error: {e}")
        return []


def fetch_mentor_leaderboard(supabase_url: str, supabase_key: str) -> list:
    """Fetch mentor leaderboard from leaderboard cache key."""
    try:
        data = fetch_supabase_cache(supabase_url, supabase_key, "leaderboard")
        if not data:
            return []

        mentors = data if isinstance(data, list) else data.get("mentors", [])
        if not isinstance(mentors, list):
            return []

        result = []
        for m in mentors:
            sessions = m.get("sessions", {})
            wins = m.get("wins", {})
            no_shows = m.get("noShows", {})
            result.append({
                "name": m.get("name", "Unknown"),
                "tier": m.get("tier", ""),
                "active_members": m.get("activeMembers", m.get("active_members", 0)),
                "sessions_week": sessions.get("week", 0) if isinstance(sessions, dict) else 0,
                "sessions_month": sessions.get("month", 0) if isinstance(sessions, dict) else 0,
                "wins_week": wins.get("week", 0) if isinstance(wins, dict) else 0,
                "retention_pct": m.get("retentionPct", m.get("retention_pct", 0)),
                "avg_parent_nps": m.get("avgParentNps", m.get("avg_parent_nps", 0)),
                "no_shows_week": len(no_shows.get("week", [])) if isinstance(no_shows, dict) and isinstance(no_shows.get("week"), list) else 0,
                "capacity": m.get("capacity", m.get("mentor_capacity_target", None)),
            })
        return result
    except Exception as e:
        log(f"fetch_mentor_leaderboard error: {e}")
        return []


def fetch_trend_14d(supabase_url: str, supabase_key: str, hubspot_key: str, target: datetime) -> list:
    """
    Build 14-day trend from HubSpot daily counts.
    Queries new_leads, booked_calls, and closes for each of the last 14 days.
    """
    trend = []
    if not hubspot_key:
        return trend
    try:
        for i in range(13, -1, -1):
            day = target - timedelta(days=i)
            day_start = date_to_ms(day)
            day_end = end_of_day_ms(day)

            leads = hubspot_search_count(hubspot_key, hubspot_date_filter("createdate", day_start, day_end))
            booked = hubspot_search_count(hubspot_key, hubspot_date_filter("discovery_call_booked", day_start, day_end))
            closes = hubspot_search_count(hubspot_key, hubspot_date_filter("onboarding_call_scheduled", day_start, day_end))

            trend.append({
                "date": day.strftime("%Y-%m-%d"),
                "new_leads": leads,
                "booked_calls": booked,
                "closes": closes,
            })

        return trend
    except Exception as e:
        log(f"fetch_trend_14d error: {e}")
        return trend


def fetch_surround_sound(supabase_url: str, supabase_key: str) -> list:
    """Fetch members needing team touches from surround_sound cache."""
    try:
        data = fetch_supabase_cache(supabase_url, supabase_key, "surround_sound")
        if not data:
            return []

        members = data if isinstance(data, list) else data.get("members", data.get("contacts", []))
        if not isinstance(members, list):
            return []

        result = []
        for m in members:
            mentor_touch = m.get("surround_mentor", m.get("mentor_touch", ""))
            dcrep_touch = m.get("surround_dcrep", m.get("dcrep_touch", ""))
            norri_touch = m.get("surround_norri", m.get("norri_touch", ""))
            brodie_touch = m.get("surround_brodie", m.get("brodie_touch", ""))

            # Include if any touch is missing
            touches = [mentor_touch, dcrep_touch, norri_touch, brodie_touch]
            if any(not t or t.lower() == "no" for t in touches):
                name = m.get("name") or f"{m.get('firstname', '')} {m.get('lastname', '')}".strip() or "Unknown"
                result.append({
                    "name": name,
                    "mentor_touch": mentor_touch or "No",
                    "dcrep_touch": dcrep_touch or "No",
                    "norri_touch": norri_touch or "No",
                    "brodie_touch": brodie_touch or "No",
                })
        return result
    except Exception as e:
        log(f"fetch_surround_sound error: {e}")
        return []


def fetch_unassigned(supabase_url: str, supabase_key: str) -> list:
    """Fetch unassigned members from admin_unassigned_default cache."""
    try:
        data = fetch_supabase_cache(supabase_url, supabase_key, "admin_unassigned_default")
        if not data:
            return []

        # Check multiple possible keys for the member list
        if isinstance(data, list):
            members = data
        elif isinstance(data, dict):
            members = (data.get("unassignedMembers") or
                       data.get("members") or
                       data.get("contacts") or [])
        else:
            return []

        if not isinstance(members, list):
            return []

        result = []
        for m in members:
            name = m.get("name") or f"{m.get('firstname', '')} {m.get('lastname', '')}".strip() or "Unknown"
            result.append({
                "name": name,
                "son_name": m.get("son_name", ""),
                "program": m.get("program", ""),
                "status": m.get("status", ""),
            })

        # Also pull admin_unassigned_matching for broader unassigned count
        try:
            matching_data = fetch_supabase_cache(supabase_url, supabase_key, "admin_unassigned_matching")
            if matching_data and isinstance(matching_data, dict):
                matching_members = matching_data.get("unassignedMembers", [])
                existing_names = {r["name"] for r in result}
                for m in matching_members:
                    name = m.get("name") or f"{m.get('firstname', '')} {m.get('lastname', '')}".strip() or "Unknown"
                    if name not in existing_names:
                        result.append({
                            "name": name,
                            "son_name": m.get("son_name", ""),
                            "program": m.get("program", ""),
                            "status": m.get("status", "matching"),
                        })
        except Exception:
            pass

        return result
    except Exception as e:
        log(f"fetch_unassigned error: {e}")
        return []


def enrich_activation_from_supabase(supabase_url: str, supabase_key: str,
                                     activation_data: dict) -> dict:
    """
    Enrich existing activation pipeline data with Supabase cache data.
    Fills in mentor_allocated and w1_complete arrays if they're empty.
    """
    try:
        data = fetch_supabase_cache(supabase_url, supabase_key, "activation_pipeline")
        if not data:
            return activation_data

        members = data if isinstance(data, list) else data.get("members", data.get("contacts", []))
        if not isinstance(members, list):
            return activation_data

        # If mentor_allocated is empty, populate from Supabase
        if not activation_data.get("mentor_allocated"):
            for m in members:
                has_mentor = m.get("has_associated_mentor") or m.get("associated_mentor_name")
                w1_complete = m.get("week_1_complete") or m.get("w1_complete")
                w1_scheduled = m.get("week_1_scheduled_for")
                if has_mentor and not w1_scheduled and not w1_complete:
                    name = m.get("son_name") or f"{m.get('firstname', '')} {m.get('lastname', '')}".strip() or "Unknown"
                    activation_data["mentor_allocated"].append({
                        "name": name,
                        "date": m.get("mentor_allocated_time", ""),
                        "w1_activation_stage": m.get("w1_activation_stage", ""),
                        "mentor": m.get("associated_mentor_name", ""),
                    })

        # If w1_complete is empty, populate from Supabase
        if not activation_data.get("w1_complete"):
            for m in members:
                w1_complete = m.get("week_1_complete") or m.get("w1_complete")
                if w1_complete:
                    name = m.get("son_name") or f"{m.get('firstname', '')} {m.get('lastname', '')}".strip() or "Unknown"
                    activation_data["w1_complete"].append({
                        "name": name,
                        "date": str(w1_complete)[:10] if w1_complete else "",
                        "w1_activation_stage": m.get("w1_activation_stage", ""),
                    })

        return activation_data
    except Exception as e:
        log(f"enrich_activation_from_supabase error: {e}")
        return activation_data


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Pull live data from HubSpot, Stripe, and Meta Ads into dashboard JSON."
    )
    parser.add_argument(
        "--period", default="today",
        help="Date period: 'today' (default), 'yesterday', or YYYY-MM-DD",
    )
    parser.add_argument(
        "--output", default="data/dashboard-data.json",
        help="Output file path relative to repo root (default: data/dashboard-data.json)",
    )
    args = parser.parse_args()

    # Resolve target date
    target = parse_period(args.period)
    target_str = target.strftime("%Y-%m-%d")
    week_start = monday_of(target)
    month_start = target.replace(day=1)

    log(f"Target date: {target_str}")
    log(f"Week start (Monday): {week_start.strftime('%Y-%m-%d')}")
    log(f"Month start: {month_start.strftime('%Y-%m-%d')}")

    # Load API keys
    log("Loading API keys...")
    hubspot_key = read_key("~/.config/hubspot/api_key")
    stripe_key = read_key("~/.config/stripe/api_key")
    meta_key = read_key("~/.config/meta/api_key")

    if hubspot_key:
        log("  HubSpot key loaded")
    else:
        log("  WARNING: HubSpot key missing")
    if stripe_key:
        log("  Stripe key loaded")
    else:
        log("  WARNING: Stripe key missing")
    if meta_key:
        log("  Meta key loaded")
    else:
        log("  WARNING: Meta key missing")

    # Load Supabase config
    supabase_key = load_supabase_key()
    supabase_url = SUPABASE_URL
    if supabase_key:
        log("  Supabase key loaded")
    else:
        log("  WARNING: Supabase key missing — Supabase data pulls will be skipped")

    # Fetch all sections
    pulse = fetch_pulse(hubspot_key, target)
    reps = fetch_reps(hubspot_key, target)
    meta_ads = fetch_meta(meta_key, target)
    stripe_data = fetch_stripe(stripe_key, target)
    activation = fetch_activation_pipeline(hubspot_key)
    retention = fetch_retention(hubspot_key, target)
    mentors = fetch_mentors(hubspot_key)

    # Supabase data pulls
    log("Fetching Supabase data...")
    overdue_w1s = fetch_overdue_w1s(supabase_url, supabase_key)
    log(f"  Overdue W1s: {len(overdue_w1s)}")
    dc_closes = fetch_dc_closes(supabase_url, supabase_key, hubspot_key)
    log(f"  DC closes: {len(dc_closes)}")
    perf_flags = fetch_perf_flags(supabase_url, supabase_key)
    log(f"  Perf flags: {len(perf_flags)}")
    trend_14d = fetch_trend_14d(supabase_url, supabase_key, hubspot_key, target)
    log(f"  Trend 14d entries: {len(trend_14d)}")
    portal_stats = fetch_portal_stats(supabase_url, supabase_key)
    log(f"  Portal stats: {'loaded' if portal_stats else 'empty'}")
    surround_sound = fetch_surround_sound(supabase_url, supabase_key)
    log(f"  Surround sound: {len(surround_sound)}")
    unassigned = fetch_unassigned(supabase_url, supabase_key)
    log(f"  Unassigned: {len(unassigned)}")
    mentor_leaderboard = fetch_mentor_leaderboard(supabase_url, supabase_key)
    log(f"  Mentor leaderboard: {len(mentor_leaderboard)}")

    # Enrich activation pipeline with Supabase data
    activation = enrich_activation_from_supabase(supabase_url, supabase_key, activation)

    # Add leaderboard to mentors
    mentors["leaderboard"] = mentor_leaderboard

    # Assemble output
    output = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "period": {
            "today": target_str,
            "week_start": week_start.strftime("%Y-%m-%d"),
            "month_start": month_start.strftime("%Y-%m-%d"),
        },
        "pulse": pulse,
        "reps": reps,
        "meta_ads": meta_ads,
        "stripe": stripe_data,
        "activation_pipeline": activation,
        "retention": retention,
        "mentors": mentors,
        "overdue_w1s": overdue_w1s,
        "dc_closes": dc_closes,
        "perf_flags": perf_flags,
        "trend_14d": trend_14d,
        "portal_stats": portal_stats,
        "surround_sound": surround_sound,
        "unassigned": unassigned,
    }

    # Write output
    output_path = os.path.join(REPO_ROOT, args.output)
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    log(f"Output written to {output_path}")
    log("Done.")


if __name__ == "__main__":
    main()
