# Evaluation Methodology Summary
## Luận văn Thạc sĩ Ứng dụng

**Đề tài:** Personalized Multi-Agent Mentor for Brand Strategy Development cho F&B in SME

**Target user:** Junior marketer làm trong F&B của SME — người thiếu kinh nghiệm, không nắm quy trình tổng quát, dù có nhiều AI tools nhưng không biết dùng cái nào cho cái nào.

**Core concept:** Agent cùng user phát triển brand strategy theo hướng mentor — hướng dẫn user đến khi nắm rõ toàn bộ quy trình, có thể tự làm hoàn toàn, lúc đó agent chuyển thành executor.

**3 trục đánh giá chính:** Strategy Quality, Mentor Quality, Personalization.

---

## 1. Baselines

### External Baselines
- **ChatGPT (vanilla):** Không trang bị thêm skills/plugins, đại diện cho cách phổ biến nhất mà SME hiện tại tiếp cận AI.
- **Gemini (vanilla):** Tương tự, không trang bị thêm gì.
- **Framing:** Đây là "vanilla LLM baselines" — đại diện cho trải nghiệm thực tế phổ biến nhất, không phải cố tình nerf baseline.

### Ablation Baselines (variants của chính system)
- **System không có mentoring:** Chỉ generate strategy thẳng, không hướng dẫn user.
- **System không có personalization:** Mọi user nhận cùng một cách mentor và cùng flow.
- Mục đích: Chứng minh từng component (mentoring, personalization) thực sự đóng góp.

### Tổng cộng bảng kết quả: 5 dòng
| # | System | Mục đích so sánh |
|---|--------|-----------------|
| 1 | Full system (của mình) | — |
| 2 | System không mentor | Ablation: giá trị của mentoring |
| 3 | System không personalize | Ablation: giá trị của personalization |
| 4 | ChatGPT vanilla | External baseline |
| 5 | Gemini vanilla | External baseline |

---

## 2. Evaluation Framework — 2 tầng

### Tầng 1: Quantitative — Simulation

**Simulated User: Claude Code**
- Đóng vai junior marketer với persona được define cực kỳ chi tiết (tên, tuổi, background, level kiến thức, cách nói chuyện, mức độ hiểu biết marketing).
- Tương tác trực tiếp với cả 4 system (system của mình + ChatGPT + Gemini + ablation variants) qua interface bằng Playwright.
- Chạy nhiều scenario đa dạng (3-5 persona khác nhau, mỗi persona 2-3 lần).
- Sau mỗi session, Claude Code tự đánh giá **perceived personalization** và **mentor experience** từ góc first-person — vì chỉ user trực tiếp trải nghiệm mới đánh giá được.

**Third-person Judges: 3 SOTA models từ 3 providers**
- Claude Sonnet 4.6, Gemini 3.1 Pro, GPT 5.4.
- Đọc conversation logs sau khi simulation hoàn tất.
- Chấm **objective metrics** theo cùng một rubric cố định:
  - Strategy quality: đủ component không, logic không, actionable không...
  - Mentor quality: có scaffolding đúng kỹ thuật không, có hỏi lại khi user mơ hồ không...
  - Objective personalization: có adapt ngôn ngữ/độ khó theo level user không, có nhớ context không...
- Tính inter-rater agreement giữa 3 judges (Fleiss' Kappa hoặc Krippendorff's Alpha).
- Nếu 3 judges cho kết quả tương đồng → kết quả đáng tin. Nếu bất đồng → finding thú vị để discuss.

**Tại sao tách user và judge:**
- Claude Code (user): đánh giá perceived/subjective experience — thứ chỉ người trải nghiệm mới cảm nhận được.
- 3 SOTA models (judges): đánh giá objective metrics từ log — loại bỏ bias vì 3 providers khác nhau cross-validate.

### Tầng 2: Qualitative — Real User Case Study (nếu mời được)

**Participants:**
- Participant A: Marketing executive, ít kinh nghiệm brand strategy (junior level).
- Participant B: Assistant brand manager tại công ty FMCG (có nền tảng hơn).
- 2 người khác level → test khả năng personalization của system.

**Quy trình:**
- Cả hai dùng system của mình (không cần test cả 4 system) với cùng một brief (ví dụ: phát triển brand strategy cho một quán F&B giả định).
- Quan sát quá trình tương tác: system mentor khác nhau thế nào giữa 2 người.
- Phỏng vấn sâu 20-30 phút sau khi dùng xong.

**Điểm cần chứng minh:**
- Participant A (junior) → system mentor nhiều hơn, giải thích kỹ, dẫn dắt từng bước.
- Participant B (có nền tảng) → system adapt, ít giải thích cơ bản, đi sâu hơn.
- → Bằng chứng sống cho personalization.

**Về danh tính:**
- Không cần ghi tên thật, ẩn danh hoàn toàn.
- Mô tả profile đủ để hiểu: "Participant A — marketing executive, 2 năm kinh nghiệm, chưa từng làm brand strategy hoàn chỉnh."
- Chuẩn bị consent form đơn giản (đồng ý tham gia, dữ liệu ẩn danh), hai bên ký, giữ lại phòng hội đồng hỏi.

**Nếu không mời được real user:**
- Chỉ có simulation vẫn ổn cho thạc sĩ ứng dụng.
- Acknowledge trong phần Limitation rằng future work sẽ validate với real user.
- Có real user thì nâng từ "tốt" lên "rất tốt", không có thì không rớt.

---

## 3. Lưu ý quan trọng

### Rubric
- Phải design xong TRƯỚC khi chạy experiment.
- Càng cụ thể và measurable càng tốt (không phải "strategy tốt không" mà "có cover đủ X component không").

### Reproducibility
- Ghi rõ exact model version, ngày test, temperature setting cho tất cả models.
- Dùng API nếu có thể để kiểm soát parameter.

### ToS
- Check Terms of Service của OpenAI và Google xem automated interaction qua web interface (Playwright) có vi phạm không.
- Nếu vi phạm → chuyển sang dùng API.

### Scenarios
- Define trước 3-5 persona đa dạng (beginner mở quán mới, người muốn rebrand, người có chút kiến thức...).
- Mỗi persona chạy 2-3 lần để có variance.
- Số lượng và danh sách persona phải fix trước khi chạy.

---

## 4. Cách justify với hội đồng

> "Vì chưa có work nào giải quyết đồng thời cả 3 khía cạnh (multi-agent + mentoring + personalization cho brand strategy), baselines được thiết kế bằng cách degrade từng khía cạnh (bỏ multi-agent, bỏ mentoring, bỏ personalization) kết hợp với vanilla LLM baselines đại diện cho cách tiếp cận phổ biến nhất hiện tại của SME."

> "Evaluation sử dụng simulated user cho quantitative comparison ở quy mô lớn, cross-validated bởi 3 SOTA models từ 3 providers độc lập, bổ sung bởi exploratory case study với real users để validate perceived experience."
