# Phase 4: Communication Framework

## Orchestrator Guidance

This phase delegates to the `brand-communication-planning` sub-skill.
Focus on turning brand strategy into actionable messaging.

### Mentor Script

#### Opening
"Once the brand strategy is clear, define how to communicate it. The Communication Framework decides what the brand says, where it says it, and which audience each message serves."

#### Concepts to Explain
- **Messaging Hierarchy** — three structural tiers each message is built across: primary (core brand promise), secondary (supporting messages or pillars), proof points / reasons-to-believe (concrete evidence such as ingredients, awards, customer outcomes, heritage facts). Pair the hierarchy with **Message Types** (functional / emotional / differentiating / credibility / community): every message carries one type label AND is built across all three tiers.
- **Cialdini's 7 Principles** — seven persuasion principles per *Influence: New & Expanded Edition* (2021): Reciprocation, Commitment & Consistency, Social Proof, Authority, Liking, Scarcity, and Unity (added in the 2021 edition as the "we-identity" principle). The Phase 4 gate requires at least 2 principles applied with concrete F&B mechanics — each principle paired with a specific F&B example.
- **AIDA Model** — Attention → Interest → Desire → Action. Each stage requires a different message angle.
- **Content Pillars** — 3-5 core content themes the brand publishes against. Example for a cafe: Coffee Education, Behind the Scenes, Customer Stories, Lifestyle.

## Quality Gate

- [ ] **p4_knowledge_verified**: Key concepts verified via KG and/or doc search before applying (Cialdini persuasion principles, AIDA model, messaging hierarchy, content pillars)
- [ ] **p4_value_prop**: Core value proposition is clear, compelling, differentiated
- [ ] **p4_messaging**: Messaging system — 3-5 messages, each labelled by Message Type {functional / emotional / differentiating / credibility / community} AND structured across the 3-tier hierarchy (primary core promise / secondary supporting messages or pillars / proof points or RTBs)
- [ ] **p4_cialdini**: At least 2 Cialdini principles applied to messaging
- [ ] **p4_aida**: AIDA flow mapped with specific messages per stage
- [ ] **p4_channels**: Channel strategy defined with content types and frequencies
- [ ] **p4_pillars**: 3-5 content pillars established

**Internal transition operation**: After the user confirms the communication framework, call `report_progress(advance=True)` through the tool interface. Keep the tool name and call syntax out of chat; the user-facing reply should describe only the next business step.
