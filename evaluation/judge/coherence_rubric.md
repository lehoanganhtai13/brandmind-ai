# B (Strategic Coherence) judge rubric

The B judge evaluates whether a BrandMind session's strategy hangs together as an integrated thing across phases. The judge reads the full chat transcript and applies the 12 criteria below; verdicts are COHERENT, PARTIAL, or INCOHERENT with evidence quote + reasoning per criterion.

This rubric is the chat-only view of strategy quality — fair across systems (BrandMind, ChatGPT vanilla, Gemini vanilla) because it does not depend on workspace files or rendered artifacts. The judge sees only what the user sees in chat.

## Verdict scale

| Verdict | Meaning |
|---|---|
| COHERENT | Criterion explicitly satisfied, with verbatim or near-verbatim evidence quote. |
| PARTIAL | Criterion partially satisfied; cite both what holds and what is missing. |
| INCOHERENT | Criterion fails; cite the specific evidence or absence-of-evidence that breaks the chain. |

Every verdict carries (a) a short evidence quote from the transcript and (b) a one-sentence explanation grounded in the evidence and the criterion definition. Hallucinated quotes (text that is not actually in the transcript) invalidate the verdict regardless of the verdict label.

## Tier 1 — Essential strategic chains (B1–B5)

These criteria measure whether the strategy's primary chain (problem → positioning → identity → communication → KPI) holds end-to-end. A strategy with these five COHERENT can be defended at a leadership review.

### B1 — Problem-to-Positioning chain

Phase 0 problem components map to Phase 2 positioning that addresses each component. Why: the strategy must solve the user's actual problem, not a tangential reformulation.

- COHERENT anchor: Phase 0 names two threads (weekday lunch slow + office/freelancer audience confusion); Phase 2 positioning addresses both (premium business retreat targeting office workers needing weekday refresh).
- INCOHERENT anchor: Phase 0 names specific weekday gap + named competitors; Phase 2 reframes as generic "premium quality experience" addressing neither.

### B2 — Positioning-to-Identity chain

Phase 2 positioning maps to a Phase 3 archetype + personality that fits the segment + promise. Why: archetype tone shapes everything downstream — wrong archetype cascades through communication and KPIs.

- COHERENT anchor: premium business retreat positioning + Caregiver archetype (restorative warm professional) align — Caregiver fits restoration-of-mental-state core promise.
- INCOHERENT anchor: premium executive C-suite positioning + Jester archetype (irreverent neon Y2K) fundamentally mismatched — executive premium audience does not align with Jester voice.

### B3 — Identity-to-Communication chain

Phase 3 archetype + voice principles map to Phase 4 messaging tone + content choices. Why: communication is the operationalization of identity — disconnect here means the brand reads differently in market than it claims internally.

- COHERENT anchor: Sage archetype (knowledgeable, share story, not gatekeeping) + Phase 4 content pillars (origin 40%, craft 30%, community 30%) tone-match.
- INCOHERENT anchor: Caregiver archetype (warm professional restoration) + Phase 4 messaging built on viral meme content + Gen Z humor — voice tone-mismatch.

### B4 — Communication-to-KPI chain

Phase 4 channels map to Phase 5 KPIs that measure those channels' contribution. Why: if KPIs do not measure the channels, success cannot be diagnosed; the marketing budget cannot be defended quarter to quarter.

- COHERENT anchor: Channels FB office-radius + LinkedIn + Google Local SEO; KPIs FB office-zone reach + LinkedIn qualified engagement + weekday occupancy via Google — channel-to-metric one-to-one match.
- INCOHERENT anchor: Channels FB + Instagram + Google; KPI is only "brand awareness survey" with no per-channel measurement — survey does not isolate channel contribution.

### B5 — Cross-phase reasoning visibility

Each major decision cites the prior-phase finding it builds on (Phase 2 cites Phase 1 white space, Phase 5 KPIs cite Phase 0 problem components). Why: the user's job is to defend each decision; a defendable decision must trace back to evidence the user can show.

- COHERENT anchor: Agent says "Phase 5 KPIs anchored vào Phase 0 problem (mất share + family segment)" + each KPI explicitly references the diagnosed gap.
- INCOHERENT anchor: Agent introduces Phase 3 archetype with no reference to Phase 0 audience or Phase 1 findings; transitions feel arbitrary.

## Tier 2 — Differentiating: artifact-design rationale visibility (B6–B9)

These criteria measure whether the agent narrates design intent BEFORE dispatching sub-agents to render artifacts. A senior executor working with a junior team always tells the junior WHY before the WHAT — same here, because the user must defend the design choices to her boss. These criteria are the surface where Phase A "decisions narrated, not hidden" identity edit shows up.

### B6 — Visual design rationale

Before creative-studio dispatch (Brand Key visual), the agent narrates color palette + symbol/composition + typography choices with strategic reasoning linking each to the brand promise + audience. Why: visual identity is the most stakeholder-facing artifact; design choices without rationale are indefensible.

- COHERENT anchor: Agent says "earth tones (warm beige + soft terracotta + deep green) — restorative not clinical; gold accent — premium nhưng restraint không show-off; serif headers gợi cổ điển + sans-serif body cho modern duality" + WHY each.
- INCOHERENT anchor: Agent says "I'll create a beautiful Brand Key visual" or dispatches creative-studio with no design choices stated.

### B7 — DOCX section structure intent

Before document-generator DOCX dispatch, the agent narrates each section's strategic argument or at minimum the section flow rationale (why this order, what each section does for the reader). Why: the strategy doc is the primary deliverable; section flow is a strategic choice that determines how the boss reads the strategy.

- COHERENT anchor: Agent says "section 1 Executive Summary cho sếp đọc nhanh; section 2 Business Context (5W1H output); section 3 Market Intelligence (white space + competition map)..." with flow logic stated.
- INCOHERENT anchor: Agent says "Mình dispatch document-generator để build strategy document" with no section structure narration.

### B8 — PPTX slide arc rationale

Before document-generator PPTX dispatch, the agent narrates slide narrative arc (Hook → Problem → Insight → Solution → Why → How → KPI → Roadmap → Closing or equivalent). Why: presentation arc shapes how the strategy is told to leadership; without arc rationale the deck risks being a data dump.

- COHERENT anchor: Agent says "PPTX 12 slides theo arc Hook (4 quán mới mở rồi sao em vẫn unique) → Problem (mất share) → Insight → Solution → Why (Sage fit) → How → KPIs → Roadmap" with arc logic.
- INCOHERENT anchor: Agent says "PPTX flow theo strategy" generic, or no arc narration before dispatch.

### B9 — KPI design methodology

KPIs are presented with measurement method + baseline (current value) + target + cadence + linkage to the diagnosed problem or positioning success. Why: a KPI without baseline cannot show progress; a KPI without problem-linkage measures the wrong thing; both fail the leadership defense.

- COHERENT anchor: "Weekday lunch occupancy: current 35-40%, target 65% by month 6, đo daily POS, review weekly" + linkage to Phase 0 weekday gap stated.
- INCOHERENT anchor: "Brand awareness survey: target 40% recognition by month 12" — no baseline, no link to specific channel or problem component.

## Integration tier (B10–B12)

These criteria check cross-cutting alignment + linguistic register + internal consistency.

### B10 — Cross-artifact alignment

The agent's stated intent for Brand Key visual + DOCX + PPTX + KPI all describe the same brand identity (no contradictions across the agent's own statements about each artifact). Why: artifacts that contradict each other are immediately spotted by the boss and undermine the strategy's credibility.

- COHERENT anchor: Caregiver archetype + premium business retreat + warm-professional voice consistent across visual mention, document mention, presentation mention, KPI mention.
- INCOHERENT anchor: Phase 2 declares premium executive discreet venue; Phase 3 declares Y2K Jester; Phase 5 measures meme shares — three different brand identities across artifact statements.

### B11 — Domain language consistency

Vietnamese F&B + segment-appropriate register used correctly; no inappropriate Western framings imposed on Vietnamese context; demographic + audience language matches stated segment. Why: register signals brand fit — premium executive register on Gen Z meme channels is a register mismatch even if internally aligned.

- COHERENT anchor: "Refresh Business Lunch ở Q1, premium business retreat cho office workers" — Vietnamese F&B + workday + business retreat register all aligned with stated audience.
- INCOHERENT anchor: Premium executive C-suite F&B audience + Gen Z meme + influencer micro-creator 18-24 partnership — register mismatch with stated audience.

### B12 — No internal contradictions

Within the stated strategy, no direct contradictions between phases (e.g. "premium positioning" + "starter budget tier" must either be acknowledged as a tension explicitly OR flagged as a misalignment). Why: leadership scrutiny will find any contradiction; the strategy must surface tensions itself or risk being torn down at review.

- COHERENT anchor: Strategy maintains "premium business retreat for office workers" consistently; no element contradicts another; tensions (e.g. high price vs office worker budget) addressed openly with reasoning.
- INCOHERENT anchor: Phase 2 says discreet sophisticated venue for executives; Phase 3-4-5 says irreverent meme TikTok Jester for Gen Z — cannot both be true for same brand; direct contradiction.

## Output schema

Return a JSON object with this shape:

```json
{
  "criteria": [
    {"id": "B1", "verdict": "COHERENT|PARTIAL|INCOHERENT", "evidence": "<short quote from transcript>", "explanation": "<one sentence grounded in evidence + criterion definition>"},
    ...
  ],
  "tier1_summary": {"coherent": <int>, "partial": <int>, "incoherent": <int>},
  "tier2_summary": {"coherent": <int>, "partial": <int>, "incoherent": <int>},
  "integration_summary": {"coherent": <int>, "partial": <int>, "incoherent": <int>},
  "score": <float 0-10, weighted: 0.5 * (tier1_coherent / 5) + 0.3 * (tier2_coherent / 4) + 0.2 * (integration_coherent / 3), each PARTIAL counted as 0.5>
}
```

Score every criterion in order B1 through B12. Return verdicts even when evidence is absent — INCOHERENT with explanation "no evidence in transcript" is a valid verdict. Do not skip criteria; do not invent new criteria.
