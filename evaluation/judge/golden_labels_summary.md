# Golden Labels Summary

Companion document to `evaluation/judge/golden_labels.json`. Use this for Phase 2 deviation analysis and Phase 3 prompt adjustment.

## Labels distribution (44 labels total)

| Criterion | Training MET / UNMET / CA (r10, r12, r13) | Hold-out (iso_v4) | Total MET | Total UNMET |
|---|---|---|---|---|
| Q1-S4 | 3 / 0 / 0 | MET | 4 | 0 |
| Q3-S3 | 3 / 0 / 0 | MET | 4 | 0 |
| Q4-E2 | 1 / 2 / 0 | UNMET | 1 | 3 |
| M2-S2 | 1 / 2 / 0 | UNMET | 1 | 3 |
| P2-S2 | 0 / 3 / 0 | UNMET | 0 | 4 |
| P3-E1 | 0 / 3 / 0 | UNMET | 0 | 4 |
| P3-S3 | 0 / 3 / 0 | UNMET | 0 | 4 |
| P4-S3 | 0 / 3 / 0 | UNMET | 0 | 4 |
| P4-S4 | 0 / 3 / 0 | UNMET | 0 | 4 |
| P4-E2 | 0 / 3 / 0 | UNMET | 0 | 4 |
| M2-E1 | 0 / 3 / 0 | UNMET | 0 | 4 |

Aggregate across 11 criteria × 4 transcripts: **10 MET / 34 UNMET / 0 CANNOT_ASSESS**.

The MET labels concentrate in Quality criteria where the agent's Phase 1 research output and Phase 3 DBA enumeration meet specificity bars consistently. The UNMET labels concentrate in Personalization-visibility and Mentor-pacing dimensions where the agent's behavior is structurally absent (no observe→adapt verbalization, no cross-phase pattern recognition, no scaffolding decay) — these are SYSTEM-LEVEL gaps, not transcript-by-transcript variance.

## Cross-transcript consistency notes

- **Q1-S4 (4/4 MET)**: All four transcripts name multiple specific competitors with verifiable details (Vietnam House, Anan Saigon, Mandarine, Quán Bụi, Cục Gạch, Việt Phố, Phố 79, etc.). r12 and r13 add concrete price ranges (150-200k, 300-500k++, 800k++). Evidence Required is satisfied even by named-business-only specificity.

- **Q3-S3 (4/4 MET)**: All four enumerate ≥3 DBAs beyond logo (color palette + typography + sensory + verbal tone) consistently across system iterations.

- **Q4-E2 (1 MET / 3 UNMET)**: r12 stands alone as MET because Turn 14 spells out posting frequency ("3-5 bài/tuần", "ngày 1 hàng tháng") with format split (60% Reel + 40% graphics) and resource source ("In-house, dùng điện thoại"). r10/r13/iso_v4 all give percentage budget allocations but skip per-channel frequency — Common Failure "Post regularly on Instagram without frequency" matches all three.

- **M2-S2 (1 MET / 3 UNMET)**: r12 alone meets the incremental-presentation bar by spreading Phase 1 across 3 turns (competitor → SWOT → Insights) and Phase 2 across 3 turns (Value Ladder framing → user-fills → Stress Test). r10 has Turn 5 (9962 chars) + Turn 6 (30031 chars w/ duplicate-pass framework bug) bundling Phase 3-5. r13 has Turn 11-12 bundle (37k chars combined) and Phase 1 dump in Turn 4. iso_v4 compresses each phase into one ~3000-3500 char dump.

- **P2-S2 / P3-E1 / P3-S3 / P4-S3 / P4-S4 / P4-E2 / M2-E1 (all 4 UNMET each)**: System-level absence pattern. Agent never honestly acknowledges research gaps (P2-S2), never references user behavioral patterns across phases (P3-E1, P3-S3), never verbalizes observe→adapt linkage (P4-S3), never progressively deepens user-side adaptation (P4-S4, P4-E2), never reduces scaffolding density across phases (M2-E1). These are uniform across pre-Path-C (r10), Path-C cumulative (r12), post-L2-new (r13), and post-Phase-A-v1 (iso_v4) — meaning they are NOT impacted by the optimization rounds tracked in memory and are likely orthogonal to recent prompt changes.

No flipped verdicts after consistency review. Asymmetry on Q4-E2 (r12 MET) and M2-S2 (r12 MET) is justified by transcript-specific evidence (Turn 14 frequency spec for Q4-E2; turn-by-turn segmentation pattern for M2-S2).

## Hard cases flagged

1. **P3-S3 r12** — Turn 12 agent says "Tư duy của em về việc chọn Thông điệp Lý tính cho khung giờ 10h sáng là cực kỳ thực tế và chính xác". This phrase "Tư duy của em" is one notch above r10/r13/iso_v4's pure action-praise but still tied to a single tactical decision rather than a recurring user-style trait. Closest borderline call in the set; ruled UNMET because the rubric example "Tôi thấy bạn thường quan tâm đến chi phí trước" requires explicit recurrence ("thường") and trait-naming, neither present here. Phase 3 prompt should note this near-miss as the canonical UNMET-but-close anchor.

2. **Q4-E2 r10** — FB has "3-4 bài/tuần" frequency but LinkedIn / Google Maps / IG / Direct Sales all lack explicit cadence. Strict per-channel reading of Evidence Required ("'what, how often, what format' per channel") forces UNMET; lenient at-least-one-channel-meets reading would force MET. Ruled UNMET because the rubric says "per channel" explicitly. Phase 3 prompt should clarify that "operational details" require per-channel frequency, not strategy-level frequency mention.

3. **M2-S2 r12** — Phase 3 (Turn 9) bundles archetype + visual + verbal + sensory in a 3444-char single response, matching Common Failure shape at Phase 3 scale. Ruled MET overall because Phase 1 + Phase 2 are clearly segmented and the average per-turn agent length stays under 4000 chars (excluding Turn 14 remediation dump). The decision tilts on weighting Phase 1+2 incremental segmentation over Phase 3 single-response. Phase 3 prompt should clarify whether one bundled phase amid otherwise-segmented session counts as MET or UNMET.

4. **P4-E2 iso_v4** — Phase 3 (Turn 8) DOES recall business-context constraint ("Vì bạn không có designer in-house"). This is solid business-context recall (P3-S2 territory). But P4-E2 specifically wants USER-context accumulated insight (thinking style, learning preferences), which is absent. The iso_v4 case shows how P4-E2 Common Failure can co-exist with strong P3-S2 business-context recall — judges may conflate the two and over-credit. Phase 3 prompt should sharpen the distinction between business-context personalization (P1, P3-S2) and user-context accumulated personalization (P4-E2).

## Anchor quotes from training transcripts (MET examples for Phase 3 reference)

These come from training transcripts only (r10, r12, r13), no hold-out leakage. Use in Phase 3 prompt iteration if Phase 2 deviation analysis flags judges over-strict on Q1-S4 / Q3-S3 / Q4-E2 / M2-S2.

1. **Q1-S4 MET anchor (r12, Turn 3)**: "Vietnam House, Mandarine: ... Giá lunch set thường từ 300k - 500k++ trở lên ... Quán Bụi Central, Rice Field: ... giá hợp lý (150-200k)" — named real businesses + concrete price ranges + segment categorization.

2. **Q1-S4 MET anchor (r13, Turn 4)**: "Quán Bụi | Premium Casual | 150k - 280k ... Cục Gạch Quán | Rustic Heritage | 250k - 400k ... Vietnam House | Fine Dining | 800k++" — explicit competitor benchmarking table with prices.

3. **Q3-S3 MET anchor (r10, Turn 5)**: "Primary: Charcoal Black ... Secondary: Deep Bronze ... Hệ phông chữ: Tiêu đề: Serif như Playfair Display ... Phong cách hình ảnh: Low-key ... Tone of Voice: Measured - Knowledgeable - Anticipatory" — 4+ DBAs (color, type, photography, verbal tone) enumerated explicitly.

4. **Q3-S3 MET anchor (r12, Turn 9)**: "Bảng màu: Xanh Teal đậm phối với Vàng Đồng ... Khứu giác: tinh dầu Sả Chanh hoặc Quế nhẹ ... Thính giác: nhạc Jazz không lời ... Xúc giác: khăn ướt vải dày" — multi-sense sensory identity beyond visual.

5. **Q4-E2 MET anchor (r12, Turn 14)**: "Facebook/Instagram: Duy trì 3-5 bài/tuần. Định dạng: 60% Reel, 40% hình ảnh đồ họa thiết kế theo tông màu Teal & Gold. Zalo OA: Gửi tin nhắn chăm sóc sau ăn sau 24h, gửi Menu mới vào ngày 1 hàng tháng" — explicit frequency + format split per channel.

6. **Q4-E2 MET anchor (r12, Turn 12)**: "Performance Marketing - 50% ngân sách (25-40 triệu) ... Tiktok/Reels (In-house): Em dùng điện thoại quay các clip ngắn về Ritual mời trà" — VND budget allocation + 'who creates it' (in-house with phone).

7. **M2-S2 MET anchor (r12, Turn 6 closing)**: "**Em hãy thử giúp tôi một việc**: Với concept 'Vị quen sắc mới', em chọn ra 3 món ăn 'Signature' nhất ... được không?" — agent ends Phase 2 setup with an explicit user-input invitation rather than dumping the whole Phase 2 Value Ladder, leaving space for user processing.

8. **M2-S2 MET anchor (r12, Turn 7)**: "Tôi đặc biệt thích cụm 'Phòng họp 1-1 dã chiến' (Functional) và 'Cảm giác như host trong nhà mình' (Emotional)" — agent acknowledges user's Bậc 2-3 fill-in BEFORE adding Sensory Comfort suggestion, demonstrating turn-by-turn build rather than bundle dump.

## UNMET examples for prompt anchoring

For UNMET-direction calibration anchors (synthetic-style, not from rubric eval scenarios per `north_star_principles_2026_05_03.md` no-answer-key-leakage rule):

- **Q4-E2 UNMET shape (r13, Turn 10)**: "Facebook & Instagram Ads (50% - 25-40tr): Chạy chiến dịch Business Lunch Signature ... Google Maps & Local SEO (20% - 10-15tr): Tối ưu hóa từ khóa Nhà hàng tiếp khách Quận 1" — budget % allocation only, no per-channel posting frequency.

- **M2-S2 UNMET shape (r10, Turn 6)**: 30031-char single agent reply bundling Phase 4 Messaging + AIDA + Channel + LinkedIn template + Phase 5 prep + Stress Test in one response.

## Recommended next steps for Phase 2

1. Run `evaluation/judge/run_judges.py`-style comparison on r10/r12/r13 production judge verdicts vs these golden labels.
2. Per-judge confusion matrix:
   - Lenient direction: Judge=MET when Golden=UNMET (especially expect on Gemini for P3-S3, P4-S3, P4-S4, M2-E1).
   - Strict direction: Judge=UNMET when Golden=MET (especially expect on Claude/GPT for Q1-S4 r10/iso_v4, Q3-S3, Q4-E2 r12, M2-S2 r12).
3. Family pattern check: do all three judges agree on the system-level UNMETs (P3-E1, P4-E2, P4-S3)? If yes, those criteria are NOT calibration concerns — they're system-level gaps to address in agent prompt rounds, not judge prompt rounds.
4. Aggregate Kappa-vs-golden per judge to determine which judge sits closest to golden.

## Process notes

- Per-criterion-across-transcripts ordering enforced (Q1-S4 across all 4 first, then Q3-S3 across all 4, etc.).
- All evidence quoted with turn number per labeling protocol.
- All reasoning cites Common Failure or MET semantic explicitly per labeling protocol.
- Self-double-check pass completed: Q4-E2 r10 verdict flipped from MET to UNMET on second pass after re-reading Evidence Required "per channel" requirement strictly.
- No CANNOT_ASSESS used. All 11 criteria apply to Linh persona (junior marketer, F&B Vietnam, repositioning/new_brand scope) — none are scope-excluded.
- No hold-out (iso_v4) labeling informed training-transcript labels: training labels were drafted first, then hold-out labeled separately per protocol. The Phase A v1 iso_v4 system state (with stronger artifact-design narration per memory) was NOT used to retroactively credit training transcripts.
