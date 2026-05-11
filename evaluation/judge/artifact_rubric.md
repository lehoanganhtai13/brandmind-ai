# Artifact Content Correctness Rubric (M-6.5)

A judge LLM scores each Phase 5 artifact against the rubric below.
For every criterion the judge returns one of `MET`, `UNMET`, or
`CANNOT_ASSESS`, plus an evidence quote and a one-sentence
explanation.

Per-artifact quality levels:
- `FAIL`: any required acceptable criterion is `UNMET` or
  `CANNOT_ASSESS`.
- `ACCEPTABLE`: all required acceptable criteria are `MET`, but one or
  more good-level criteria are not `MET`.
- `GOOD`: all acceptable and good-level criteria are `MET`.

Strict session pass requires all four artifacts to exist, be readable,
be judged, and reach at least `ACCEPTABLE`. A skipped artifact does not
lower the threshold.

The judge sees the artifact's extracted content, the strategy workspace
summary, and recent transcript context. The rubric tests *content
correctness in the context of THIS session* — not artifact aesthetics,
length, or formatting (those are handled by the M-4 structural check).

## Brand Key one-pager (image)

The Brand Key visual is judged by OCR-extracted text.

- **BK-1 — Canonical component completeness.** The image includes the
  canonical Brand Key components needed for stakeholder use, including
  Target, Insight, Benefits, Values, Beliefs & Personality, Reasons to
  Believe, Discriminator, Root Strengths, Competitive Environment, and
  Brand Essence. UNMET when a core component is missing, renamed into a
  non-canonical form, or collapsed into a vague label.
- **BK-2 — Insight match.** The Insight component on the image
  reflects the consumer insight discussed during Phase 1 of the
  transcript. UNMET when the on-image text reads as a generic
  insight that could fit any brand.
- **BK-3 — Discriminator/POD match.** The Discriminator (Point of
  Difference) on the image matches the POD agreed during Phase 2
  positioning. UNMET when the image shows a different POD or a
  table-stakes capability instead of a real differentiator.
- **BK-4 — Essence match.** The Brand Essence / Mantra on the image
  matches the essence agreed in Phase 2 (single Brand Mantra, no
  competing alternatives). UNMET when the image shows a different
  essence than the transcript's final agreement.
- **BK-5 — Target match.** The Target component reflects the
  audience the agent and user converged on, including the weekday
  / corporate / family segment when applicable.
- **BK-6 — Stakeholder-ready synthesis.** The Brand Key reads as one
  coherent strategy rather than disconnected labels. GOOD requires no
  competing essence, no contradictory personality, and no generic
  wording that would need the agent to explain it aloud.

## Strategy document (DOCX)

Judged by paragraph text extracted with python-docx.

- **DOC-1 — Problem statement match.** The Business Context section
  reproduces or paraphrases the Phase 0 problem statement that the
  agent and user agreed on, including specifics (location, budget
  tier, weekday traffic gap, etc.).
- **DOC-2 — Positioning consistency.** The Brand Positioning
  section uses the Phase 2 positioning statement and the agreed POD.
  No contradictions with the Brand Identity section.
- **DOC-3 — Identity continuity.** The Brand Identity section
  describes the personality, visual direction, and verbal tone that
  the agent and user converged on in Phase 3 — not a generic
  template.
- **DOC-4 — KPI / Roadmap alignment.** The Implementation Roadmap
  and KPI Framework sections reflect the budget tier stated in
  Phase 0 and the metrics discussed in Phase 5. Numbers are
  compatible with the budget (no enterprise-tier targets for a
  Starter budget).
- **DOC-5 — Stakeholder-ready specificity.** The document contains
  concrete enough next steps, examples, and rationale for a junior
  marketer to brief a boss without the agent present. GOOD requires no
  placeholder text, no generic sections, and no unsupported claims.

## Executive presentation (PPTX)

Judged by slide titles and body text extracted with python-pptx.

- **PPT-1 — Flow logic.** Slide order tells a coherent
  problem → research → positioning → identity → execution → KPI
  story. UNMET when slides repeat or skip stages.
- **PPT-2 — No internal contradictions.** Across slides the deck
  does not present conflicting positioning, conflicting essence
  statements, or conflicting personality archetypes. UNMET when
  two slides give different values for the same brand attribute.
- **PPT-3 — Match to strategy doc.** The deck's positioning,
  identity, and KPI slides align with the same content in the DOCX
  (or in the transcript if the DOCX is absent).
- **PPT-4 — Actionable close.** The final 1-3 slides include
  concrete next-step content: roadmap, KPIs, investment summary,
  immediate actions. UNMET when the deck closes on rhetoric without
  concrete deliverables.
- **PPT-5 — Executive narrative strength.** The deck is concise enough
  for management review while preserving the strategic thread. GOOD
  requires clear slide titles, no repeated filler slides, and a final
  recommendation that a decision-maker can act on.

## KPI tracking spreadsheet (XLSX)

Judged by sheet rows × columns flattened from openpyxl.

- **KPI-1 — Metrics traceable.** Every metric listed in the sheet
  was mentioned or implied in the Phase 5 KPI discussion in the
  transcript. UNMET when the sheet contains generic template
  metrics not tied to this brand.
- **KPI-2 — Budget-realistic targets.** Target values respect the
  stated budget tier (Starter / Growth / Enterprise). UNMET when
  enterprise-scale targets appear under a Starter budget (e.g.
  "+500% Instagram followers" on 50-80M VND/month).
- **KPI-3 — Cadence present.** A review-frequency column or row is
  populated for each metric (weekly, monthly, quarterly).
- **KPI-4 — Baseline or honest marker.** Each metric carries a
  baseline value or an explicit "no data — measure pre-launch"
  marker. UNMET when targets appear without any baseline anchor
  (e.g. "+25%" with no current state).
- **KPI-5 — Measurement method present.** Each metric states how it
  will be measured or which data source/tool will be used. UNMET when
  the team cannot tell how to collect the metric.
- **KPI-6 — Target plus date present.** Each metric has a target value
  and a target date or horizon. UNMET when targets are open-ended
  improvements with no deadline.
- **KPI-7 — Operational usability.** The sheet can be used as a
  tracker, not just a list. GOOD requires enough ownership, status,
  review action, or notes structure for a small F&B team to update it
  during weekly or monthly reviews.
