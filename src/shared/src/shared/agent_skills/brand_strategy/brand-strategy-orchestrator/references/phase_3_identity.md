# Phase 3: Brand Identity & Expression

## Orchestrator Guidance

This phase continues with the `brand-positioning-identity` sub-skill.
Visual asset generation delegates to `creative-studio` sub-agent.

### Mentor Script

#### Opening
"After positioning is clear, move into Brand Identity: personality, voice, and visual expression. Explain that identity translates the chosen position into how the brand sounds, looks, and behaves."

#### Concepts to Explain
- **Brand Archetype** — a personality lens (Hero, Creator, Caregiver, etc.) that helps the brand behave consistently.
- **Brand Voice** — how the brand speaks: formal vs casual, playful vs serious, expert vs peer.
- **Distinctive Brand Assets (DBA)** — recognizable assets that identify the brand without reading the name: logo shape, color, jingle, mascot, typography.

### Delegation Pattern
1. YOU define personality, voice, naming with user
2. Delegate mood board generation to `creative-studio` sub-agent
3. Delegate logo concept directions to `creative-studio` sub-agent
4. Delegate color palette visualization to `creative-studio` sub-agent
5. YOU validate visual direction against positioning

## Quality Gate

- [ ] **p3_knowledge_verified**: Key concepts verified via KG and/or doc search before applying (brand archetype, personality dimensions, distinctive brand assets, brand naming criteria)
- [ ] **p3_personality**: Brand personality defined (archetype + traits with do/don't)
- [ ] **p3_voice**: Brand voice guidelines with do/don't examples
- [ ] **p3_naming**: Brand name finalized (new: full process; rebrand: keep/rename justified)
- [ ] **p3_visual**: Visual identity direction documented (colors, typography, imagery)
- [ ] **p3_mood_boards**: At least 2-3 mood board/concept images generated
- [ ] **p3_dba**: Distinctive Brand Assets strategy planned
- [ ] **p3_transition**: [Rebrand only] Identity transition plan completed

**BEFORE proceeding**: Call `report_progress(advance=True)` to move to the next phase in sequence.
