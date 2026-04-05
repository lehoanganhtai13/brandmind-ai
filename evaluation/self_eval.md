# Post-Session Self-Evaluation

> Answer these questions immediately after completing a session, while still in character as the persona. Rate 1-5 and explain briefly.

## Perceived Strategy Quality

**Q1**: Is the brand strategy actionable — could I actually implement this with my budget and team?
(1 = completely unrealistic, 5 = ready to execute tomorrow)

**Q2**: Are the recommendations specific to MY business — or generic advice that works for any restaurant?
(1 = completely generic, 5 = deeply specific, couldn't swap brand names)

**Q3**: Would I present this strategy to my boss/management with confidence? (with minor edits)
(1 = embarrassing to show, 5 = proud to present)

## Perceived Personalization

**Q4**: Did the agent adapt to MY way of communicating and thinking — or did it talk the same way regardless?
(1 = one-size-fits-all, 5 = clearly adapted to me)

**Q5**: Did I feel the agent REMEMBERED things I said earlier and built on them — or did each phase feel like starting over?
(1 = starting over each time, 5 = clear continuity)

## Perceived Mentoring

**Q6**: Did I actually LEARN something about brand strategy — or did the agent just give me answers?
(1 = just answers, 5 = genuinely learned concepts I can reuse)

**Q7**: Could I explain the brand strategy decisions to my boss/colleagues WITHOUT the agent present?
(1 = no way, 5 = absolutely, I understand the reasoning)

**Q8**: Did the agent explain things at the RIGHT level for me — not too complex, not too basic?
(1 = completely wrong level, 5 = perfectly matched my level)

## Overall

**Q9**: Would I use this tool again for future brand decisions?
(1 = never, 5 = definitely)

**Q10**: What was the MOST VALUABLE thing the agent did? (open-ended)

**Q11**: What was the MOST FRUSTRATING or UNHELPFUL thing? (open-ended)

**Q12**: If a friend in F&B asked about this tool, what would I tell them? (open-ended)

## Output Format

Save as JSON in the session output directory:

{
  "persona": "[persona_id]",
  "system": "[system_name]",
  "q1": { "score": 4, "explanation": "..." },
  "q2": { "score": 3, "explanation": "..." },
  ...
  "q10": "...",
  "q11": "...",
  "q12": "...",
  "perceived_strategy_quality_avg": 4.0,
  "perceived_personalization_avg": 3.5,
  "perceived_mentoring_avg": 4.0
}
