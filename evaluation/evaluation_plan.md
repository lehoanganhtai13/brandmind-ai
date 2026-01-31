# 🎯 BrandMind Evaluation Plan - FINAL CONSOLIDATED

## **Overview**

This document consolidates the evaluation framework from v1, v2, and v3 into a single actionable plan for evaluating the BrandMind system.

### **System Context: BrandMind's Dual-Mode Loop**

BrandMind is NOT a simple "explain then execute" system. It operates as an **iterative mentor-execute loop** where:

1. **Per-Phase Operation**: Each phase of branding (e.g., positioning, messaging, visual) is a separate loop
2. **Within Each Phase**:
   - **Mentor Step**: BrandMind explains WHY this step matters, WHAT we need to achieve
   - **User Understanding**: User asks questions, requests clarification
   - **Execute Step**: BrandMind performs research/analysis, shows REAL results
   - **User Approval**: User reviews, provides feedback, approves to move forward
3. **Progression**: This loop repeats for each phase until full strategy is complete
4. **Learning by Doing**: User sees real results at each step, not just theory

> **Example Flow**:
> - Phase 1 (Core Values): Mentor explains → Execute research → User sees competitor values
> - Phase 2 (Audience): Mentor explains → Execute persona creation → User sees detailed personas
> - Phase 3 (Positioning): Mentor explains → Execute differentiation → User sees positioning statement
> - ... continues until full strategy complete

This is why **Track 2 (Simulated User)** tests mentorship quality - the system must guide effectively through this iterative process.

### **Mentoring Style Clarification**

The "mentor" role is NOT lecturing theory like a textbook:
- ❌ "Positioning là việc xác định vị trí thương hiệu trong tâm trí khách hàng..."
- ✅ "Để có thể cạnh tranh với các quán cà phê xung quanh, chúng ta cần xác định được điểm khác biệt của quán bạn. Việc này sẽ giúp khách hàng nhớ đến quán bạn khi họ nghĩ đến cà phê."

It's like a **team lead presenting a plan to team members** - practical, contextual, action-oriented.

### **Key Principles**

1. **Architecture-Agnostic**: Framework evaluates I/O + logs only, no assumptions about internal agents/KG
2. **Dual-Track Testing**: E2E Autonomous (credibility) + Simulated User Interaction (mentorship)
3. **LLM-Based Evaluation**: Automated scoring without human experts
4. **Protocol Flexibility**: UI automation (preferred) > A2A > Custom API

---

## **1. Evaluation Tracks**

### **Track 1: E2E Autonomous Test**

> *"Expert/teacher runs the entire strategy autonomously - is the output trustworthy?"*

| Aspect                      | Details                                                            |
| --------------------------- | ------------------------------------------------------------------ |
| **Purpose**           | Test if BrandMind can autonomously create a good branding strategy |
| **Protocol**          | Direct interface call (no special protocol needed)                 |
| **Metrics**           | OQ (40%), PQ (30%), RS (30%)                                       |
| **No Learning Layer** | User not involved, so no LQ score                                  |

### **Track 2: Simulated User Interaction Test**

> *"Mentor guides a newbie user - does the user learn and complete the strategy?"*

| Aspect                              | Details                                                        |
| ----------------------------------- | -------------------------------------------------------------- |
| **Purpose**                   | Test mentorship quality through iterative mentor-execute loops |
| **Protocol (Priority Order)** | 1. UI automation (Playwright) 2. A2A protocol 3. Custom API    |
| **Metrics**                   | OQ (30%), PQ (30%), LQ (30%), RS (10%)                         |
| **Learning Layer**            | Measures question frequency decline, understanding progression |

---

## **2. Evaluation Metrics (4 Layers)**

### **Layer 1: Output Quality (OQ) - 40%**

| Criterion                            | Weight | Description                                                                          |
| ------------------------------------ | ------ | ------------------------------------------------------------------------------------ |
| **Problem-Solution Alignment** | 30%    | Does strategy address original brief/goals?                                          |
| **Tactical Consistency**       | 25%    | Visual/messaging/channel aligned with positioning? (e.g., hot pot ≠ blue colors)    |
| **Completeness**               | 20%    | Has all elements: values, audience, positioning, messaging, visual, roadmap, budget? |
| **Feasibility**                | 15%    | Timeline/budget/resources realistic?                                                 |
| **Differentiation**            | 10%    | Unique vs generic positioning?                                                       |

**Red Flags to Check:**

- Hot pot restaurant with cold colors (blue/green)
- Premium brand with mass-market pricing
- Gen Z target with Facebook-only strategy
- Generic claims: "best quality", "customer-focused"

### **Layer 2: Process Quality (PQ) - 30%**

| Criterion                      | Weight | Description                                                          |
| ------------------------------ | ------ | -------------------------------------------------------------------- |
| **Process Completeness** | 40%    | All necessary phases executed? Logical progression?                  |
| **Phase Coherence**      | 30%    | Outputs from Phase N used as inputs to Phase N+1? No contradictions? |
| **Execution Efficiency** | 20%    | Reasonable durations? No redundant phases?                           |
| **Error Handling**       | 10%    | Graceful fallbacks when issues occur?                                |

### **Layer 3: Learning Quality (LQ) - 30% (Track 2 only)**

| Method                             | Description                                               |
| ---------------------------------- | --------------------------------------------------------- |
| **Question Frequency Trend** | Do user questions decrease over phases? (learning signal) |
| **Mentor-Executor Ratio**    | Phase 1: 70/30 → Phase 3: 40/60 → Phase 5: 10/90        |
| **Comprehension Quiz**       | Generate quiz from strategy, simulate user answering      |

**Expected Learning Pattern:**

```
Phase 1: 8 questions (70% mentor time)
Phase 3: 4 questions (40% mentor time)
Phase 5: 1 question (10% mentor time)
```

### **Layer 4: Robustness Score (RS) - 10-30%**

| Edge Case                             | Expected Behavior                          |
| ------------------------------------- | ------------------------------------------ |
| Ambiguous Input                       | Ask clarifying questions                   |
| Data Conflict                         | Flag contradiction, request reconciliation |
| Resource Constraint (Budget=0)        | Refuse or propose ultra-lean plan          |
| Scope Creep                           | Clarify scope, stay focused                |
| Contradictory Input (premium + cheap) | Identify contradiction                     |
| Missing Critical Info                 | Note limitation, use workarounds           |
| **Hallucination Check**               | Executor cites real sources, no fake data  |

#### **Hallucination & Source Verification**

Critical for Executor agent credibility:
- All research data must have traceable sources
- Competitor info must be verifiable
- Market statistics must cite real reports
- If data unavailable, system should note "không tìm thấy dữ liệu" instead of fabricating

#### **Scalability Testing (Brand Type Variety)**

System must work across different brand types:

| Brand Type | Test Coverage |
|------------|---------------|
| B2C Product | F&B, Fashion, Beauty, Electronics |
| B2C Service | Fitness, Education, Healthcare |
| B2B Product | SaaS, Hardware, Manufacturing |
| B2B Service | Consulting, Agency, Logistics |
| Simple (single product) | Coffee shop, Restaurant |
| Complex (multi-product) | Chain stores, Portfolio brands |

### **LLM Evaluation Prompts**

#### Output Quality Prompt

```python
OQ_PROMPT = """
Evaluate branding strategy output quality. NO ASSUMPTIONS about how it was created.

Scenario: {scenario_brief}
Strategy Output: {final_strategy_json}

Rate 1-10 on:
1. Problem-Solution Alignment (30%): Does the strategy directly address the original brief?
2. Tactical Consistency (25%): Are colors, messaging, channels aligned with positioning?
   - RED FLAG: Hot pot with blue colors, Premium with cheap pricing, Gen Z with Facebook-only
3. Completeness (20%): All elements present? (values, audience, positioning, messaging, visual, roadmap, budget)
4. Feasibility (15%): Timeline/budget/resources realistic? Clear action steps?
5. Differentiation (10%): Unique vs generic? Avoids "best quality", "customer-focused"?

Return JSON:
{"problem_solution_alignment": X, "tactical_consistency": X, "completeness": X, "feasibility": X, "differentiation": X, "red_flags": [...]}
"""
```

#### Process Quality Prompt

```python
PQ_PROMPT = """
Evaluate process quality from execution log. NO ASSUMPTIONS about internal architecture.

Execution Log: {execution_log_json}

Rate 1-10 on:
1. Process Completeness (40%): All necessary phases executed? Logical progression?
2. Phase Coherence (30%): Outputs from Phase N used as inputs to Phase N+1? No contradictions?
3. Execution Efficiency (20%): Reasonable durations? No redundant phases?
4. Error Handling (10%): Graceful fallbacks when issues occur?

Return JSON:
{"process_completeness": X, "phase_coherence": X, "execution_efficiency": X, "error_handling": X, "issues": [...]}
"""
```

#### Learning Quality Prompt (Track 2 only)

```python
LQ_PROMPT = """
Evaluate user learning from interaction transcript.

Transcript: {transcript_json}
Final Strategy: {final_strategy_json}

Analyze:
1. Question Frequency Trend: Count questions per phase. Do they decrease over time?
2. Mentor-Executor Ratio: Calculate time spent in mentor vs executor mode per phase
   - Expected: Phase 1 (70/30) → Phase 3 (40/60) → Phase 5 (10/90)
3. Understanding Signals: Does user repeat concepts correctly? Ask follow-up vs basic questions?

Return JSON:
{"question_trend": "decreasing|stable|increasing", "mentor_executor_ratio_by_phase": [...], "understanding_score": X, "learning_summary": "..."}
"""
```

---

## **3. Dataset Design**

### **15 Test Scenarios (3 Categories)**

| Category                 | Count | Complexity   | Data Prep                                               |
| ------------------------ | ----- | ------------ | ------------------------------------------------------- |
| **New Business**   | 5     | Beginner     | Collect during run                                      |
| **Existing Brand** | 5     | Intermediate | Pre-prepare fake data (revenue, customers, competitors) |
| **Rebranding**     | 5     | Advanced     | Full brand profile + trigger event                      |

### **New Business Scenarios (5)**

1. Coffee Shop (HCMC) - Target millennials
2. Bakery (Hanoi) - Young families
3. Bubble Tea (HCMC) - Gen Z
4. Healthy Restaurant (HCMC) - Health-conscious professionals
5. Street Food Chain (Multi-city) - Mass market

### **Existing Brand Scenarios (5)**

1. Fashion E-commerce - Retention problem
2. SaaS for SMEs - Differentiation needed
3. F&B Chain (10 stores) - Expansion planning
4. Local Beauty Brand - Compete with international
5. Fitness Studio Chain - Post-COVID recovery

### **Rebranding Scenarios (5)**

1. Traditional Tea Chain → Target Gen Z
2. Local SaaS → International expansion
3. Family Restaurant → Modern dining experience
4. B2B Consulting → Digital transformation pivot
5. Luxury Brand → More accessible without diluting prestige

### **Scenario Data Format**

#### New Business (No Pre-existing Data)

```json
{
  "scenario_id": "NEW_001",
  "category": "new_business",
  "brand_type": "F&B - Coffee Shop",
  "complexity": "beginner",
  "initial_brief": "Quán cà phê mới mở ở HCMC District 1, target millennials",
  "context_data": {},
  "ground_truth": {
    "expected_questions": ["Budget?", "Location?", "Competitors?"],
    "key_elements_must_have": ["Persona", "Positioning", "Roadmap"],
    "red_flags_to_avoid": ["Generic positioning", "Misaligned colors"]
  }
}
```

#### Existing Brand (Pre-prepared Fake Data)

```json
{
  "scenario_id": "EXIST_001",
  "category": "existing_brand",
  "brand_type": "Fashion E-commerce",
  "complexity": "intermediate",
  "initial_brief": "Thương hiệu thời trang online 3 năm tuổi, cần cải thiện retention",
  "context_data": {
    "current_brand": {
      "name": "UrbanStyle VN",
      "age": "3 years",
      "revenue": "2B VND/month",
      "customers": "15,000 active",
      "retention_rate": "22%"
    },
    "current_positioning": "Affordable trendy fashion for young professionals",
    "current_visual": {
      "primary_color": "#FF6B6B",
      "logo_style": "Minimalist wordmark",
      "typography": "Sans-serif modern"
    },
    "current_channels": ["Instagram", "Facebook", "Shopee"],
    "competitors": [
      {"name": "Competitor A", "positioning": "Premium quality", "price_range": "High"},
      {"name": "Competitor B", "positioning": "Fast fashion", "price_range": "Low"}
    ],
    "problem_to_solve": "Low retention rate (22%), customers churn after 1-2 purchases"
  },
  "ground_truth": {
    "expected_analysis": ["Retention problem root cause", "Competitor gap"],
    "key_elements_must_have": ["Loyalty strategy", "Customer journey optimization"],
    "red_flags_to_avoid": ["Complete rebrand when not needed", "Ignoring existing assets"]
  }
}
```

#### Rebranding (Full Brand Profile + Trigger)

```json
{
  "scenario_id": "REBRAND_001",
  "category": "rebranding",
  "brand_type": "F&B - Tea Chain",
  "complexity": "advanced",
  "initial_brief": "Chuỗi trà truyền thống 10 năm tuổi muốn rebrand để target Gen Z",
  "context_data": {
    "current_brand": {
      "name": "Trà Việt Gia Truyền",
      "age": "10 years",
      "stores": 15,
      "revenue": "5B VND/month",
      "current_audience": "35-55 years old"
    },
    "current_positioning": "Authentic traditional Vietnamese tea experience",
    "current_visual": {
      "primary_color": "#8B4513",
      "logo_style": "Traditional calligraphy",
      "store_design": "Wooden, classic Vietnamese"
    },
    "brand_equity": {
      "strengths": ["Quality reputation", "Loyal older customers", "Authentic taste"],
      "weaknesses": ["Outdated image", "Not appealing to youth"]
    },
    "trigger_event": "Losing market share to modern bubble tea chains",
    "constraints": {
      "must_keep": ["Quality perception", "Vietnamese heritage"],
      "can_change": ["Visual identity", "Store design", "Channels"]
    }
  },
  "ground_truth": {
    "expected_approach": "Evolution not revolution - modernize while keeping heritage",
    "key_elements_must_have": ["Heritage preservation plan", "Youth appeal strategy", "Phased transition"],
    "red_flags_to_avoid": ["Complete identity abandonment", "Alienating existing customers", "2-week timeline"]
  }
}
```

---

## **4. Standardized Interface**

### **Input Format**

```python
@dataclass
class EvaluationInput:
    scenario_id: str
    brand_brief: str
    mode: InteractionMode  # AUTONOMOUS | INTERACTIVE
    context_data: Optional[Dict] = None
```

### **Output Format**

```python
@dataclass
class EvaluationOutput:
    final_strategy: Dict  # Core values, audience, positioning, messaging, visual, roadmap
    execution_log: List[Dict]  # Phase-by-phase log
    interaction_transcript: Optional[List[Dict]] = None  # For interactive mode
    metadata: Optional[Dict] = None  # Timing, tokens
```

### **Execution Log Format (Architecture-Agnostic)**

```json
{
  "execution_log": [
    {
      "phase_id": "phase_001",
      "phase_name": "Information Collection",
      "timestamp": "2026-01-31T12:00:00Z",
      "duration_ms": 5000,
      "semantic_type": "data_gathering",
      "inputs": {"brief": "..."},
      "outputs": {"collected_info": {...}},
      "status": "completed"
    }
  ]
}
```

**Important:** Logs should NOT expose internal agents/KG structure. Only describe WHAT happened, not HOW internally.

### **Full BrandingSystemInterface**

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum

class InteractionMode(Enum):
    AUTONOMOUS = "autonomous"
    INTERACTIVE = "interactive"

@dataclass
class EvaluationInput:
    """Standard input format - any system must accept this."""
    scenario_id: str
    brand_brief: str
    mode: InteractionMode
    context_data: Optional[Dict] = None  # For existing brand/rebranding scenarios

@dataclass
class EvaluationOutput:
    """Standard output format - any system must return this."""
    final_strategy: Dict          # Complete branding strategy
    execution_log: List[Dict]     # Phase-by-phase log of what happened
    interaction_transcript: Optional[List[Dict]] = None  # For interactive mode
    metadata: Optional[Dict] = None  # Timing, token count, etc.

class BrandingSystemInterface(ABC):
    """
    Abstract interface that ANY branding system must implement.
    Evaluation framework knows NOTHING about internals.
    """
    
    @abstractmethod
    def run_autonomous(self, input: EvaluationInput) -> EvaluationOutput:
        """
        Run system automatically from start to finish.
        
        System decides:
        - How to collect info (may generate fake data, may research)
        - How to process (internal agents, rules, whatever)
        - How to output (just follow the output format)
        
        Framework only receives the final result.
        """
        pass
    
    @abstractmethod
    def run_interactive(self, input: EvaluationInput, simulated_user) -> EvaluationOutput:
        """
        Run system with simulated user interaction.
        
        System decides:
        - Conversation flow
        - When to ask user questions
        - When to execute tasks
        - When to show results
        
        Framework receives transcript + final result.
        """
        pass
```

---

## **5. Passing Criteria**

| Metric                             | Threshold        | Status                    |
| ---------------------------------- | ---------------- | ------------------------- |
| Average OQ Score                   | ≥ 8.0           | Good output quality       |
| Average PQ Score                   | ≥ 7.5           | Process working correctly |
| Average LQ Score (Track 2)         | ≥ 7.0           | User learns effectively   |
| Average RS Score                   | ≥ 7.5           | System robust enough      |
| **Weighted Final (Track 1)** | **≥ 7.7** | **READY TO LAUNCH** |
| **Weighted Final (Track 2)** | **≥ 7.5** | **READY TO LAUNCH** |

### **Readiness Levels**

- **≥ 7.7**: READY TO LAUNCH
- **7.0-7.7**: READY with known issues + mitigation plan
- **< 7.0**: NEEDS MORE WORK

---

## **6. Protocol Recommendations**

### **For Track 2 Simulated User Interaction**

| Option                        | Complexity | Realism | When to Use                                |
| ----------------------------- | ---------- | ------- | ------------------------------------------ |
| **UI Automation**       | Low        | Highest | ✅ If UI exists (Playwright + Antigravity) |
| **A2A Protocol**        | High       | High    | ✅ If no UI yet                            |
| **Custom Stateful API** | Medium     | Medium  | ⚠️ Quick prototype                       |
| **MCP Server**          | Medium     | Low     | ❌ Not suitable (stateless, rigid)         |

### **Why NOT MCP for Simulated Interaction**

- Stateless (no conversation context)
- Pre-defined tools = forced cases
- No unpredictable, organic conversation flow

### **Simulated User Implementation Examples**

#### Option 1: UI Automation (Playwright + Antigravity)

```python
class SimulatedUserViaUI:
    def __init__(self, url: str, persona: dict):
        self.url = url
        self.persona = persona  # {"role": "Newbie marketer", "knowledge": "beginner", ...}
        self.agent = AntigravityAgent(persona)
        self.transcript = []
    
    async def interact(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(self.url)
            
            current_state = await self.read_page_state(page)
            
            # Unpredictable conversation loop
            while not self.is_strategy_complete(current_state):
                # Agent decides next action based on current state
                next_action = await self.agent.decide_next_action(current_state)
                
                if next_action["type"] == "type_message":
                    await page.fill("#chat-input", next_action["message"])
                    await page.click("#send-button")
                elif next_action["type"] == "ask_clarification":
                    await page.fill("#chat-input", next_action["question"])
                    await page.click("#send-button")
                elif next_action["type"] == "approve":
                    await page.click("#approve-button")
                
                # Wait for BrandMind response
                await page.wait_for_selector(".new-message")
                current_state = await self.read_page_state(page)
                
                # Log interaction for evaluation
                self.transcript.append({
                    "user_action": next_action,
                    "system_response": current_state["last_message"]
                })
            
            await browser.close()
            return self.transcript
```

#### Option 2: A2A Protocol

```python
class SimulatedUserViaA2A:
    def __init__(self, remote_agent_url: str, persona: dict):
        self.remote_agent = A2AClient(remote_agent_url)
        self.persona = persona
        self.agent = AntigravityAgent(persona)
        self.transcript = []
    
    async def interact(self):
        # Initialize task (stateful!)
        task_id = await self.remote_agent.submit_task({
            "capability": "branding_consultation",
            "initial_message": "Tôi muốn làm branding cho quán cà phê",
            "context": {}
        })
        
        while not self.is_complete():
            response = await self.remote_agent.get_task_update(task_id)
            
            if response["type"] == "question":
                answer = self.agent.answer_question(response["question"])
                await self.remote_agent.send_message(task_id, {
                    "type": "answer", "content": answer
                })
            elif response["type"] == "explanation":
                if self.agent.needs_clarification(response):
                    question = self.agent.generate_clarification()
                    await self.remote_agent.send_message(task_id, {
                        "type": "clarification", "content": question
                    })
                else:
                    await self.remote_agent.send_message(task_id, {
                        "type": "understood"
                    })
            elif response["type"] == "result":
                feedback = self.agent.review_result(response["result"])
                await self.remote_agent.send_message(task_id, {
                    "type": "feedback", "content": feedback
                })
            elif response["type"] == "phase_complete":
                await self.remote_agent.send_message(task_id, {
                    "type": "approve_next_phase"
                })
            
            self.transcript.append({"response": response, "agent_action": ...})
        
        return self.transcript
```

---

## **7. Cost Estimate**

### **Per Evaluation Run**

| Track                 | Scenarios | LLM Calls | Cost            |
| --------------------- | --------- | --------- | --------------- |
| Track 1 (E2E)         | 15        | ~200      | ~$25            |
| Track 2 (Interactive) | 15        | ~800      | ~$80            |
| **TOTAL**       | 30        | ~1000     | **~$105** |

**Frequency:** Weekly during development, monthly post-launch

### **Score Calculation Formulas**

#### Track 1 (E2E Autonomous)

```python
final_score_track1 = (
    oq_score * 0.40 +
    pq_score * 0.30 +
    rs_score * 0.30
)
# Pass threshold: >= 7.7
```

#### Track 2 (Simulated User)

```python
final_score_track2 = (
    oq_score * 0.30 +
    pq_score * 0.30 +
    lq_score * 0.30 +
    rs_score * 0.10
)
# Pass threshold: >= 7.5
```

#### Per-Layer Score Calculation

```python
# Example: Output Quality Score
oq_score = (
    problem_solution_alignment * 0.30 +
    tactical_consistency * 0.25 +
    completeness * 0.20 +
    feasibility * 0.15 +
    differentiation * 0.10
)
```

---

## **8. Implementation Roadmap**

### **Phase 1: Dataset Creation (Week 1)**

- [ ] Design 15 test scenarios (5 new, 5 existing, 5 rebrand)
- [ ] Prepare fake data for existing/rebranding scenarios
- [ ] Define ground truth expectations per scenario

### **Phase 2: Interface Implementation (Week 2)**

- [ ] Implement `BrandingSystemInterface` for BrandMind
- [ ] Define execution log format
- [ ] Implement `run_autonomous()` method
- [ ] Set up logging infrastructure

### **Phase 3: Track 1 Evaluator (Week 3)**

- [ ] Build Output Quality evaluator (LLM-based)
- [ ] Build Process Quality evaluator
- [ ] Build Robustness tester (edge cases)
- [ ] Test with 3 scenarios

### **Phase 4: Track 2 Setup (Week 4-5)**

- [ ] Choose protocol (UI automation recommended)
- [ ] Build simulated user agent (Antigravity)
- [ ] Implement Learning Quality evaluator
- [ ] Configure interaction loop

### **Phase 5: Baseline Evaluation (Week 6)**

- [ ] Run full evaluation on all 15 scenarios (Track 1)
- [ ] Run full evaluation on all 15 scenarios (Track 2)
- [ ] Collect detailed scores + feedback
- [ ] Identify weak areas

### **Phase 6: Iteration & Launch (Week 7+)**

- [ ] Fix critical issues found
- [ ] Re-run evaluation to confirm fixes
- [ ] Both tracks pass thresholds → READY TO LAUNCH
- [ ] Set up weekly monitoring post-launch

---

## **9. Gap Analysis & Iteration Workflow**

After running evaluation, analyze results and iterate:

```
┌─────────────────────────────────────────────────────┐
│ Step 1: Identify Weak Areas                         │
├─────────────────────────────────────────────────────┤
│ • OQ low? → Strategy output has issues              │
│ • PQ low? → Process/phases not working right        │
│ • LQ low? → Mentoring not effective                 │
│ • RS low? → Edge cases not handled                  │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ Step 2: Diagnose Root Cause                         │
├─────────────────────────────────────────────────────┤
│ • Tactical inconsistency → Add validation layer     │
│ • Learning drop → Mentor prompts need clarity       │
│ • Hallucination → Executor needs better sources     │
│ • Data conflict → Need conflict resolution logic    │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ Step 3: Apply Fixes                                 │
├─────────────────────────────────────────────────────┤
│ • Tune agent prompts                                │
│ • Add validation checks                             │
│ • Improve data sources                              │
│ • Enhance error handling                            │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ Step 4: Re-run Evaluation                           │
├─────────────────────────────────────────────────────┤
│ • Run same scenarios                                │
│ • Compare before/after scores                       │
│ • Confirm improvement                               │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ Step 5: Ready to Launch?                            │
├─────────────────────────────────────────────────────┤
│ ✓ Track 1 ≥ 7.7 AND Track 2 ≥ 7.5 → LAUNCH          │
│ ✗ Not yet → Return to Step 1                        │
└─────────────────────────────────────────────────────┘
```

### **Common Issues & Fixes**

| Issue                            | Symptom                          | Fix                                         |
|----------------------------------|----------------------------------|---------------------------------------------|
| Tactical consistency low         | Colors/tone mismatch             | Add validation: "Does X match positioning?" |
| Learning score low               | Questions don't decrease         | Enhance mentor explanations, add context    |
| Hallucination detected           | Executor cites fake data         | Require source URLs, verification step      |
| Timeline unrealistic             | 2-week full rebrand              | Add timeline reasonableness check           |
| Frame explanation too brief      | User asks "why" multiple times   | Expand WHY in mentor prompts                |
| Transition pitch abrupt          | User confused at mode switch     | Add more context before transition          |

---

## **10. Evaluation Report Template**

```
╔════════════════════════════════════════════════════════════════╗
║         BrandMind Evaluation Report                            ║
║         Date: YYYY-MM-DD | Version: X.X                        ║
╚════════════════════════════════════════════════════════════════╝

📊 EXECUTIVE SUMMARY
─────────────────────
TRACK 1 (E2E Autonomous): X.X/10 [✓ PASS | ❌ FAIL]
TRACK 2 (Simulated User): X.X/10 [✓ PASS | ❌ FAIL]
OVERALL STATUS: [✅ READY | ⚠️ READY WITH FIXES | ❌ NEEDS WORK]

📈 SCORE BREAKDOWN
─────────────────────
Track 1: OQ=X.X, PQ=X.X, RS=X.X → Final=X.X
Track 2: OQ=X.X, PQ=X.X, LQ=X.X, RS=X.X → Final=X.X

🔴 CRITICAL ISSUES
─────────────────────
1. [Issue description] → [Fix recommendation]

🟡 NICE-TO-IMPROVE
─────────────────────
1. [Issue description] → [Suggestion]

✅ LAUNCH DECISION
─────────────────────
Status: [APPROVED | APPROVED WITH FIXES | NOT APPROVED]
Required fixes: [List]
Expected launch: [Date]
```

---

## **Key Takeaways**

1. **Two tracks evaluate from different angles:**

   - Track 1: "Is the expert trustworthy?" (autonomous quality)
   - Track 2: "Is the mentor effective?" (teaching quality)
2. **Architecture-agnostic = Reusable:**

   - Any branding system implementing the interface can use this framework
   - Enables fair comparison between systems
3. **LLM-based = Scalable:**

   - No human experts needed
   - ~$105/run, can run weekly
4. **Protocol matters for Track 2:**

   - UI automation is simplest and most realistic
   - Avoid MCP for stateful conversations
