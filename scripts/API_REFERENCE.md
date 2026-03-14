# API Reference for Live Data

## HubSpot
- API Key: stored at ~/.config/hubspot/api_key
- Portal: 48782903
- Pipeline ID: 828940659
- Contacts endpoint: GET https://api.hubapi.com/crm/v3/objects/contacts
- Deals endpoint: GET https://api.hubapi.com/crm/v3/objects/deals
- Owner IDs: Harry=77594415, Elliot=2419conversionID, Rye=2507780714
- Key deal stages: Booked DC, DC Completed, Closed, Agreement Form, W1 Started

## Stripe
- API Key: stored at ~/.config/stripe/api_key  
- MRR: calculate from active subscriptions
- Endpoint: GET https://api.stripe.com/v1/subscriptions?status=active

## Meta Ads
- Token: stored at ~/.config/meta/api_key
- Ad Account: act_1631004910795417
- Endpoint: GET https://graph.facebook.com/v22.0/act_1631004910795417/insights

## Supabase
- Config: ~/.config/supabase/config.json
- URL: https://ltpkeddkkrexynlhgxal.supabase.co
- Has mentor session data, member data

## Google Calendar (pending API enable)
- Account: admin@bluesandgreens.com.au
- CLI: gog
- Calendar events: gog calendar list --from today --to tomorrow
