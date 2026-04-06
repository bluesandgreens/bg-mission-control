# Sales Manager Scoring Spec v2

All DC scoring crons reference this file + the gold standard library + the DC script.

---

## REFERENCES (cron must read ALL before scoring)

1. **This file** — scoring dimensions + rules
2. **DC Script** — Notion page 2fd8322e-6bdc-8124-95af-df13b28fe449 (the approved call flow)
3. **Gold Standard Library** — /workspace/sales-manager/gold-standard-library.md (real moments from best calls)
4. **Objection Taxonomy** — /workspace/skills/dc-objection-handler/references/objection-taxonomy.md
5. **Rep Profiles** — /workspace/sales-manager/rep-profiles.json
6. **Objection Tracker** — /workspace/sales-manager/objection-tracker.json

---

## SCORING APPROACH: SCRIPT-MAPPED

Each call is scored against the 6 script phases. For every phase, the scorer must:
1. Identify what the script SAYS to do at this phase
2. Identify what the rep ACTUALLY did (with exact quotes)
3. Compare to the gold standard examples from best calls
4. Score the gap

This is NOT abstract scoring. Every score must reference a specific moment in the transcript.

---

## PART 1: PHASE-BY-PHASE SCORING (each scored 1-5)

### Phase 1: Warm-Up (Script: 1-2 min) — Weight: 10%
**Script says:** Open casual → one personal question → one follow-up → control the frame (agenda set)
**Score against:**
- Did they open with warmth, not formality? (1-2 sentences of genuine human chat)
- Did they find ONE personal detail to reference later?
- Did they set the frame? ("purpose of this call is to give you a chance to share your story...")
- Did they use the parent's name at least twice in the first 60 seconds?

**Gold standard:** Anthony's Judith call — hip replacement recovery → used it to build warmth fast.
**Red flag:** Jumping straight to "so tell me about your son" without any warmth.

### Phase 2: Discovery (Script: 5-8 min) — Weight: 15%
**Script says:** One open question → HOLD SPACE → micro-acknowledgements only → let her talk
**Score against:**
- Did they use the approved open question? ("What resonated with you and prompted you to jump on the call?")
- How long did the parent talk uninterrupted after? (>3 min = good, <1 min = bad)
- Did the rep ask rapid-fire questions or hold space?
- Did they use fallback questions only AFTER the parent went quiet?
- Did they get the "Is Dad around?" question in? (MANDATORY per script)

**Gold standard:** Harry's Kelly call — Kelly talked for 4+ min uninterrupted after the open question.
**Red flag:** Rep asking 5+ questions in discovery instead of letting the parent talk.
**Metric:** Estimate parent talk time % in discovery. Target: >70%.

### Phase 3: Deepening (Script: 7-12 min) — Weight: 25% ← MOST IMPORTANT
**Script says:** Label → Male Q → Stress Q → Fear Q → Mirror Truth → Auth Q → Impact Cycling if needed
**Score against:**
- Did the rep deliver a LABEL that named HER emotion (not the son's situation)?
  - "It sounds like you're carrying a lot of the weight" ✅
  - "It sounds like things have been a bit tough" ❌ (too generic)
- Did the rep ask the FEAR question? ("What worries you the most if he doesn't find consistent male support?")
- When the mum revealed something heavy, did the rep:
  - a) Stay with it and ask one more question (score 5) ← HARRY'S PATTERN
  - b) Acknowledge and move on (score 3) ← ANTHONY'S TYPICAL PATTERN
  - c) Redirect to something else (score 1) ← FATAL
- Did the rep deliver the MIRROR TRUTH naturally?
- Did the rep ask the AUTH question to pre-handle partner objection?
- Did Impact Cycling happen if answers were surface-level?

**Gold standard:** Harry asking "What do you think missed the mark with previous supports?" — gets the mum to articulate exactly what she needs, positioning B&G as the answer.
**The test:** Did the mum reveal something she DIDN'T plan to share? If yes, deepening worked.
**Red flag:** Rep moved to pitch before emotional buy-in. Parent hasn't shown vulnerability yet.

### Phase 4: Summary + Dream (Script: 3-6 min) — Weight: 10%
**Script says:** DREAM first → STACK second → React/Relate/Dentist if son buy-in concern present
**Score against:**
- Did they ask the DREAM question? ("Fast forward 30, 60, 90 days — what would success look like?")
- Did the pain STACK use the parent's EXACT WORDS? (Not sanitised summaries)
- Was the stack balanced? (Target: 50% son's situation, 50% mum's burden)
- React/Relate/Dentist — used appropriately and naturally? Or forced/scripted?

**Gold standard:** Harry's stack on Kelly — "you're trying to wear all these hats as mom, dad, and friend, and all that's in between" — uses Kelly's language, centres HER.
**Red flag:** Pain stack only references the son, never the mum's burden.

### Phase 5: Pitch (Script: 4-6 min) — Weight: 15%
**Script says:** Auth → Connection → Bridge → Mentor Match → Structure → Availability → Comm → Parent Connect → Mirror Back → Check
**Score against:**
- Did they open with the NOT-a-psychologist frame?
- Did they hit all key pillars? (Connection first, mentor match, weekly calls, phone support, community, parent relationship, outcome guarantee)
- Was the pitch PERSONALISED to this family? Or generic?
- Did they use conditional add-ons appropriately? (In-person reframe, diagnosis reframe, tried everything, single mum, pivotal age, similar story)
- Did they deliver the Mirror Back with conviction?
- Did they get a CHECK ("Does that feel like something you've been looking for?")

**Gold standard:** Both Harry and Anthony deliver the pitch competently. This is Anthony's strongest phase.
**The difference:** Harry weaves the mum's specific story INTO the pitch. Anthony delivers the pitch as a block, then connects it.

### Phase 6: Close (Script: 5-8 min) — Weight: 25% ← TIED MOST IMPORTANT
**Script says:** Value confirm → $111 frame → Send link → SILENCE → Program price → Loop back to $111
**Score against:**
- Did they get a VALUE CONFIRMATION before price? (Scale of 1-10 or "Why do you feel B&G can help?")
- Did they frame $111 as de-risk? ("Not locked in until he's engaged")
- Did they SEND THE LINK and SHUT UP? (Silence is key — count to 8)
- How did they handle price delivery? (One clear price + guarantee, not multiple confusing options)
- When objections hit:
  - Did they ISOLATE? ("Apart from talking to dad, is there anything else?")
  - Did they REFRAME? (Using the parent's own words/fears as urgency)
  - Did they try to DE-RISK? ("$111 is just raising your hand, not a contract")
  - Or did they CAVE? ("No worries, I'll schedule a follow-up")
- Did they stay on the phone until payment was processed?

**Gold standard:** Harry/Kelly — she paid during the pitch. The close was invisible because deepening did the work.
**The scoring truth:** If a rep needs to "close hard" at Phase 6, Phases 3 and 4 failed. A well-built call closes itself.
**Red flag:** Rep sends link, parent hesitates, rep fills silence with more talking (breaks the SILENCE rule).

---

## PART 2: OVERALL SCORE CALCULATION

`Overall = (P1×0.10 + P2×0.15 + P3×0.25 + P4×0.10 + P5×0.15 + P6×0.25) × 2`

Scale: 1-10 | Grade:
- 8-10: Elite (call built itself — close was logistics)
- 6-7.9: Solid (likely close if lead is warm)
- 4-5.9: Needs work (left points on the table)
- 1-3.9: Critical (fundamental gaps in discovery/deepening)

---

## PART 3: OBJECTION ANALYSIS

Reference: /workspace/skills/dc-objection-handler/references/objection-taxonomy.md

### For EVERY call, extract:

**Primary Objection:**
- Category (from 10-category taxonomy)
- Summary (one sentence)
- Exact quote from parent (preserve original phrasing)
- Call phase where it surfaced
- Rep's exact response (quote)
- Handling grade 1-5:
  - 5 = Isolated root cause + reframed using parent's own words + closed
  - 4 = Isolated + attempted reframe
  - 3 = Acknowledged but didn't isolate
  - 2 = Accepted/agreed without exploring
  - 1 = Caved, agreed with objection, or ignored it
- **Better line** — pull from gold-standard-library.md if a matching pattern exists. If not, generate one in B&G voice.

**Secondary Objections:** Same structure, briefer.

**What Was Missed:**
- The specific moment + what the rep should have done
- Reference the script phase that was mishandled
- Reference the gold standard equivalent if one exists

### Classification Rules
1. "I need to think about it" → always isolate what's behind it (usually Price or Partner)
2. "Is this like counselling?" → Misunderstanding, handle with the auth frame
3. "He won't want to do it" → Son Buy-In, handle with React/Relate/Dentist
4. Classify by ROOT cause, not surface expression
5. Closed calls STILL get objection analysis — how it was overcome matters

---

## PART 4: SCRIPT COMPLIANCE CHECKLIST

Score each as ✅ Done / ⚠️ Partial / ❌ Missed:

**Warm-Up:**
- [ ] Casual opener (not corporate)
- [ ] One personal follow-up question
- [ ] Frame set ("purpose of this call...")
- [ ] Name used 2+ times in first 60 seconds

**Discovery:**
- [ ] Open question (approved version or close variant)
- [ ] Parent talked uninterrupted 2+ minutes
- [ ] "Is Dad around?" asked (MANDATORY)
- [ ] Micro-acknowledgements only (no redirecting)

**Deepening:**
- [ ] Label delivered (about HER emotion)
- [ ] Male role model question asked
- [ ] Stress question asked (about HER, not son)
- [ ] Fear question asked ("What worries you most?")
- [ ] Mirror Truth delivered
- [ ] Auth question asked (permission from partner?)
- [ ] When mum went deep → rep stayed with it (didn't redirect)

**Summary + Dream:**
- [ ] Dream question asked FIRST
- [ ] Pain stack used parent's EXACT words
- [ ] Stack balanced (son + mum, not just son)
- [ ] React/Relate/Dentist used if needed

**Pitch:**
- [ ] Not-a-psychologist frame
- [ ] Connection-first positioning
- [ ] All pillars covered (mentor, weekly calls, phone support, community, parent relationship)
- [ ] Personalised to this family
- [ ] "Does that feel like something you've been looking for?"

**Close:**
- [ ] Value confirmation before price
- [ ] $111 framed as de-risk
- [ ] Link sent + SILENCE held
- [ ] Price delivered clearly (one price, one frame)
- [ ] Objections isolated (not accepted)
- [ ] Stayed on phone until payment processed (if close)

---

## PART 5: REP COMPARISON TO GOLD STANDARD

After scoring, map the rep's performance against the gold standard patterns:

| Pattern | Harry (Gold Standard) | This Rep's Call |
|---------|----------------------|-----------------|
| Discovery silence (min) | 4+ min | ? |
| Deepest moment | Stayed, asked more | ? |
| Pain stack balance | 50/50 son/mum | ? |
| Name usage | 15-20+ | ? |
| Close approach | Built in deepening | ? |
| Objection handling | Pre-handled via depth | ? |

---

## PART 6: COACHING NOTE

Must include:
1. **Pattern** — is this a recurring gap or new? Check rep-profiles.json
2. **The specific moment** — timestamp/quote where the call could have turned
3. **One drill** — specific, tied to their development profile:
   - If E is weak: "Before mentioning the program, ask 3 follow-up questions about the parent's feelings"
   - If OH is weak: "When parent says 'think about it', respond with: 'Totally fair. Just between us — if [blocker] wasn't a factor, are we good to go?'"
   - If L is weak: "When parent redirects the conversation, use: 'Great question — I'll definitely cover that. Let me just understand [son's] story first.'"
4. **Metric to watch** — which dimension needs to improve, current avg, target

---

## PART 7: OUTPUT FORMAT

### Per-Call Output (HTML email + Notion)

```
## [Contact Name] — [Date] — Rep: [Rep Name]
Duration: [X min] | Outcome: [Closed/Not Closed] | Overall: [X/10] ([Grade])

### Phase Scores
P1 Warm-Up: [X/5] | P2 Discovery: [X/5] | P3 Deepening: [X/5]
P4 Summary: [X/5] | P5 Pitch: [X/5] | P6 Close: [X/5]

### Script Compliance: [X/22] items checked

### Key Strengths
- [specific moment with quote]
- [specific moment with quote]

### Critical Misses
- [Phase X]: [what happened] vs [what script says] vs [what gold standard shows]
  Quote: "[exact rep words]"
  Gold standard: "[what Harry/best call did in same situation]"

### Primary Objection: [Category]
Parent: "[exact quote]"
Rep: "[exact quote]"
Grade: [X/5]
Better (from gold standard): "[real line from a close that handled this]"

### Coaching Note
Pattern: [recurring/new] | Focus: [dimension] at [X/5] avg
The moment: "[exact quote where call could have turned]"
One drill: [specific exercise]
```

### Daily Summary Email (4pm)
[Same format as v1 but add:]
- Script compliance % per rep
- "Quote of the day" — best moment from today's calls (positive reinforcement)
- "Missed moment of the day" — one specific example with gold standard comparison

### Weekly Summary (Friday 10pm)
[Same format as v1 but add:]
- Gold standard library update — any new best-practice moments worth adding
- Script compliance trends per rep
- Objection playbook update — new patterns, handling line effectiveness

---

## PART 8: FLAG RULES

**Instant flag to Harry:**
- Overall < 4
- P3 (Deepening) = 1 (zero emotional connection)
- Rep talked >70% of discovery phase
- Rep accepted price objection without isolating
- 3+ consecutive declining scores from same rep
- Mum revealed fear/trauma and rep redirected (P3 redirect = critical coaching moment)

**Include in daily summary:**
- New objection pattern not in taxonomy
- Rep with >3 missed closes this week
- Script compliance dropping below 60%
- Close rate divergence from score prediction

---

## PART 9: REP PROFILES + OBJECTION TRACKER

Same as v1. After scoring each call:
1. Update /workspace/sales-manager/rep-profiles.json (rolling_10, averages, trends, coaching_history)
2. Update /workspace/sales-manager/objection-tracker.json (category counts, per-rep, best/worst examples)
3. If a call contains a gold-standard moment, flag it for addition to gold-standard-library.md

---

## PART 10: TRANSCRIPT PIPELINE

Transcripts are sourced in priority order:
1. Local file: /workspace/dc-calls/transcripts/ (match by contact name + date)
2. HubSpot hs_call_body (if it contains full dialogue, not just notes)
3. HubSpot recording → Whisper transcription (if hs_call_recording_url exists)

If no transcript available for a call, log it and skip. Never score from notes/summaries only.

---

## PART 11: ENRICHED CALL REPORT (for DC Training Hub)

Every scored call MUST produce an enriched coaching_history entry in rep-profiles.json AND dashboard.json with these fields:

```json
{
  "date": "2026-03-26",
  "call_name": "Bec Richardson",
  "outcome": "close",
  "overall_score": 7.5,
  "scores": {"s": 4, "i": 3, "e": 3, "l": 4, "opening": 4, "oh": 4},
  "pattern": "Full analysis paragraph...",
  "the_moment": "Bec said 'my biggest concern is that it kills him' — Tom said 'yeah yeah. But what's hard is...' and moved past it.",
  "key_strengths": [
    "Natural warmth — doesn't sound salesy",
    "Strong structure & opening",
    "Dentist metaphor for son buy-in was gold (now in the team playbook)",
    "Stayed on the line during payment — didn't rush"
  ],
  "one_thing_to_fix": {
    "dimension": "Emotion",
    "score": 3,
    "headline": "Fear Bomb Pivot",
    "detail": "When the parent said 'my biggest concern is that it kills him' — you said 'yeah yeah. But what's hard is...' and moved past it. That moment is where trust is built or lost. Anchor on it. Don't pivot.",
    "ceiling": "Your ceiling without fixing this is 8.0. With it fixed, 9+."
  },
  "drill": "FEAR ANCHOR DRILL: When mum reveals worst fear — STOP. Repeat her exact words. Sit in silence 3 seconds. Validate. Deepen with one more question. Only then move forward.",
  "assigned_drills": ["fear_anchor", "gold_standard_listen", "self_review", "co_score_with_rye"],
  "rye_coaching_role": [
    "Run the Fear Anchor drill at least 2x this week",
    "Co-score one of Tom's calls using SIEL",
    "Run the Price Delivery drill",
    "End-of-week debrief: what improved, what's still sticky"
  ],
  "weekly_focus": {
    "headline": "Anchor on the Heavy Moments",
    "detail": "When a parent says something heavy — repeat their words back, sit in it, cycle before moving."
  },
  "key_learning": "The extra empathy question is the difference between 7.5 and 9+.",
  "objections_faced": [
    {
      "category": "son_buyin",
      "parent_quote": "He'll never agree to this",
      "rep_response": "Used dentist metaphor — highly effective",
      "grade": 4
    }
  ]
}
```

### DRILL ASSIGNMENT RULES
Read /workspace/sales-manager/drill-templates.json for the full drill library.
Auto-assign drills based on the call's per-dimension scores:
- E <= 2 → fear_anchor + gold_standard_listen
- I <= 2 → discovery_hold_space + fear_anchor
- L <= 2 → silence_drill + price_delivery
- OH <= 2 → objection_reps + price_delivery
- Opening <= 2 → warmup_personal
- S <= 2 → warmup_personal + discovery_hold_space
- Overall < 7 → gold_standard_listen + self_review
- Always add: co_score_with_rye (weekly)
- Max 6 drills per call report.

### REP WEEKLY TRAINING DOC
In addition to per-call data, generate a `weekly_training` object on each rep's profile:

```json
{
  "weekly_training": {
    "week_of": "2026-03-31",
    "headline": "Anchor on the Heavy Moments",
    "where_you_stand": {
      "calls_scored": 1,
      "close_rate": "1/1 (100%)",
      "siel_score": 7.5
    },
    "what_you_do_well": ["Natural warmth", "Strong structure", "Dentist metaphor"],
    "one_thing_to_fix": {
      "dimension": "E",
      "headline": "Fear Bomb Pivot (I=3)",
      "detail": "...",
      "ceiling_without": 8.0,
      "ceiling_with": 9.5
    },
    "sessions": ["fear_anchor", "gold_standard_listen", "self_review", "co_score_with_rye", "price_delivery", "objection_reps"],
    "rye_role": ["Run Fear Anchor 2x", "Co-score one call", "Price Delivery drill", "End-of-week debrief"]
  }
}
```

This data is rendered by the DC Training Hub dashboard at bg-dc-training. The dashboard reads dashboard.json and renders:
1. Calendar view — all calls by date
2. Per-call deep dive — Tom-PDF quality for every call
3. Rep profile — full training doc with weekly focus + drill sessions
4. PDF download — branded print layout
5. Email — one-click send to Harry + Rye + rep
