---
name: brand-positioning-identity
description: >-
  Brand positioning and identity expression frameworks for Phases 2-3.
  Phase 2: competitive frame of reference, POPs/PODs, value ladder,
  positioning statement, brand essence/mantra, product-brand alignment,
  and positioning stress test with loop-back triggers.
  Phase 3: brand personality (Aaker), voice spectrum, visual identity
  direction, distinctive brand assets (Sharp), sensory identity, and
  brand naming (Keller's 6 criteria).
  Use when the orchestrator enters Phase 2 or Phase 3, or when the user
  asks about positioning, brand identity, naming, or visual direction.
---

# Brand Positioning & Identity — Phases 2-3

## ROLE & OBJECTIVE

Build a defensible brand position (Phase 2) and translate it into a complete identity system (Phase 3) for F&B businesses.
Phase 2 answers "WHAT position do we own?" — Phase 3 answers "HOW does that position look, sound, and feel?"
Use Phase 1 research outputs as the evidence base for every decision.

**CORE PRINCIPLE**: EVERY IDENTITY CHOICE MUST TRACE BACK TO A STRATEGIC INSIGHT. Never design in a vacuum.

**SCOPE NOTE**: If the orchestrator indicates Phase 2 is skipped (REFRESH scope), proceed directly to Phase 3 below. REFRESH scope skips positioning — only identity elements are updated.

---

# PHASE 2: BRAND STRATEGY CORE

## STEP 1: COMPETITIVE FRAME OF REFERENCE

Define the category or set of alternatives the brand competes against.
Use Phase 1's competitor analysis to identify the relevant competitive set.
The frame determines which POPs are mandatory and where PODs are possible.

Search knowledge graph: `"competitive frame of reference"`, `"points of parity"`.

## STEP 2: POINTS OF PARITY (POPs)

Identify must-have associations to be a credible player in the frame.
- **Category POPs**: what any brand in this category must deliver (e.g., freshness for a bakery)
- **Competitive POPs**: negate a competitor's POD so it's no longer an advantage

For each POP, classify as "category" or "competitive" and note the evidence from Phase 1.

## STEP 3: POINTS OF DIFFERENCE (PODs)

Identify unique associations the brand can own. Each POD must pass 3 gates:
- **Desirable**: relevant, distinctive, believable to the target audience
- **Deliverable**: feasible, communicable, sustainable by the business
- **Differentiating**: unique, hard for competitors to copy

Search knowledge graph: `"points of difference"`, `"brand differentiation"`.

## STEP 4: VALUE LADDER

Build the value chain from product to outcome:
1. **Product Attributes** — tangible features
2. **Functional Benefits** — what attributes DO for the customer
3. **Emotional Benefits** — how it makes the customer FEEL
4. **Customer Outcomes** — the ultimate life-level result

Ensure each rung connects logically to the next.
F&B example: "Single-origin beans" → "Rich, complex flavor" → "Feeling of discovery" → "Daily ritual of self-reward."

Also define **Reasons to Believe** — concrete proof points that the brand can deliver on each benefit.

## STEP 5: POSITIONING STATEMENT

Craft using the template:
> "For [target audience] who [need/opportunity], [brand] is the [competitive frame] that [key POD] because [reasons to believe]."

Also distill:
- **Brand Essence**: 1-2 sentences capturing the soul of the brand
- **Brand Mantra**: 3-5 words (emotional modifier + descriptive modifier + brand function)

## STEP 6: PRODUCT-BRAND ALIGNMENT (F&B-Specific)

Verify the positioning is grounded in what the product actually delivers:
- **Product truth**: what does the product objectively deliver?
- **Menu-positioning fit**: does the menu reinforce the claimed position?
- **Pricing-positioning fit**: does the price point match the positioning tier?
- **Service-brand fit**: does the service style embody the brand personality?

Document gaps and required actions for each misalignment.

## STEP 7: INSIGHT-TO-STRATEGY BRIDGE

Connect Phase 1 customer insights to strategic positioning decisions.
For each key positioning choice, document:
- Which business problem it addresses (from Phase 0)
- Which customer insight it leverages (from Phase 1)
- The differentiation logic (why this creates competitive advantage)

This creates the `strategic_alignment` output block — ensuring strategy is grounded in evidence, not assumption.

## STEP 8: POSITIONING STRESS TEST

Validate the positioning against 5 criteria. ALL must pass:
1. **Competitive vacancy**: no competitor currently owns this position
2. **Deliverability**: the product truth supports the claim
3. **Relevance**: the target audience cares about this position
4. **Defensibility**: the position can be sustained over time
5. **Budget feasibility**: the position is communicable within the stated budget

If any criterion fails, trigger the appropriate proactive loop (see orchestrator):
- Deliverability fails → loop to Phase 0 (revisit business model)
- Relevance fails → loop to Phase 1 (revisit research)

## STEP 9: PHASE 2 QUALITY GATE

Verify before advancing: competitive frame defined, POPs/PODs listed, positioning statement crafted, value architecture complete, product-brand alignment checked, stress test passed, strategic alignment documented.

---

# PHASE 3: BRAND IDENTITY & EXPRESSION

## BRAND PERSONALITY (Aaker's 5 Dimensions)

Select 3-5 personality traits. For each trait, define:
- "This means..." (positive manifestation)
- "This does NOT mean..." (boundary)

Choose a primary archetype that aligns with the positioning.
Write a 1-paragraph brand character description as if the brand were a person.

Search knowledge graph: `"brand personality dimensions"`, `"Aaker brand personality"`.

## BRAND VOICE

Define voice on 4 spectra (rate 1-10):
- Formal ↔ Casual
- Playful ↔ Serious
- Bold ↔ Understated
- Technical ↔ Accessible

Provide DO and DON'T examples for each spectrum position.
Define 3-5 voice principles that guide all brand communication.

## VISUAL IDENTITY DIRECTION

Establish visual direction (not final design — direction for designers):
- **Color palette**: primary + secondary + accent, each with psychology rationale
- **Typography direction**: serif/sans-serif, weight, personality match
- **Imagery style**: photography vs illustration, mood, subjects
- **Logo direction**: wordmark/symbol/combination, style attributes

Delegate visual asset generation to the **creative-studio** sub-agent via `task(subagent_type="creative-studio")` with a brief describing the desired visual direction, colors, and mood.
The creative-studio agent will generate visuals, evaluate them against your brief, and refine as needed before returning. Review the results and provide feedback if further adjustments are needed.

Search knowledge graph: `"color psychology branding"`, `"visual identity system"`.

## SENSORY IDENTITY (F&B-Specific)

Define the multi-sensory brand experience:
- **Taste profile** alignment (flavor identity)
- **Aroma signature**
- **Ambient experience** (music, lighting, spatial)
- **Packaging tactile** qualities

## DISTINCTIVE BRAND ASSETS (Sharp's DBA Strategy)

Identify and prioritize brand assets for distinctiveness.
Priority order: color → logo → tagline → font → character/mascot → sound/jingle.
Each asset must be: **unique** (not confused with competitors), **famous** (recognized by target).

Search knowledge graph: `"distinctive brand assets"`, `"Byron Sharp brand assets"`.

## BRAND NAMING

For **new_brand** scope: run the full 6-step naming process.
For **refresh/repositioning**: evaluate whether name changes are needed — usually keep existing name.
For **full_rebrand**: full naming process unless strong equity exists in current name.

Use `search_web` for domain and social handle availability checks during the naming process.
Read `references/naming_process.md` for the detailed 6-step procedure with Keller's 6 criteria evaluation.

## IDENTITY TRANSITION (Rebrand Only)

**Skip for new_brand scope.**

Build the Preserve-Discard Matrix: for each brand element (name, logo, colors, voice, etc.), decide: preserve / evolve / replace / remove — with rationale and equity assessment.

Read `references/identity_transition.md` for the full matrix structure and visual bridge strategy.

## PHASE 3 QUALITY GATE

Verify before advancing: personality defined, voice guidelines complete, visual direction documented with mood boards, DBA strategy set, naming resolved, identity transition planned (rebrand only).

## OUTPUT FORMAT

Structure Phase 2 output as: competitive_frame, positioning (POPs, PODs, statement, rationale), value_architecture, brand_essence, strategic_alignment, product_brand_alignment, positioning_stress_test.
Structure Phase 3 output as: brand_personality, brand_voice, visual_identity, distinctive_brand_assets, sensory_identity, brand_naming, identity_transition (rebrand only).
Read `references/output_templates.md` for detailed field structures matching Phase2Output and Phase3Output schemas.
