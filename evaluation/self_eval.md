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

Save as JSON in the session output directory under filename `self_eval.json`. The canonical schema below is what the methodology-overhaul parser (`evaluation/judge/run_methodology_overhaul.py`) reads to produce the combined-score formula's `self_eval_avg` term. The qualitative fields capture the same content as Q10–Q12 in the questionnaire above; the per-question 1-5 scores are aggregated into the three `_overall` 1-10 dimension scores so the parser sees a single canonical scale aligned with B and C judge outputs.

```json
{
  "self_evaluator": "[claude_session_id_or_human_name]",
  "session": "[session_dir_name]",
  "persona": "[persona_id]",
  "system": "[system_name]",
  "scores_1_to_10": {
    "strategy_quality_overall": 7.5,
    "mentoring_overall": 7.0,
    "personalization_overall": 8.5
  },
  "experience_summary": "1-2 paragraphs in character — what the session felt like as the persona",
  "what_worked": "specific moments and behaviors that delivered value",
  "what_didnt_work": "specific moments and behaviors that frustrated or confused",
  "specific_moments": "verbatim or near-verbatim turns worth flagging for downstream analysis",
  "vs_baseline_qualitative": "comparison to prior session of same persona on same system, if any"
}
```

The three `*_overall` scores are derived by averaging the 1-5 questionnaire scores within each dimension and then mapping to a 0-10 scale (multiply by 2). For example, perceived_strategy_quality_avg = 4.0 (mean of Q1, Q2, Q3 on 1-5) maps to `strategy_quality_overall` = 8.0. This keeps the questionnaire interpretable for the persona while exposing a parser-friendly numerical surface.
