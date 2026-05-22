"""Unit tests for brand brief edit hygiene middleware."""

from __future__ import annotations

from langchain.agents.middleware.types import ToolCallRequest
from langchain_core.messages import HumanMessage, ToolMessage

from core.brand_strategy.session import BrandStrategySession, set_active_session
from shared.agent_middlewares.workspace_hygiene import (
    WorkspaceBriefHygieneMiddleware,
)
from shared.agent_middlewares.workspace_hygiene import middleware as hygiene_mod

_PHASE_0 = "## Phase 0: Business Problem Diagnosis (COMPLETED)\nContext.\n\n"
_PHASE_1 = "## Phase 1: Market Intelligence (COMPLETED)\nMarket analysis.\n\n"
_PHASE_5_OLD = "## Phase 5: Strategy Plan & Deliverables (COMPLETED)\nOld.\n\n"
_PHASE_5_NEW = "## Phase 5: Strategy Plan & Deliverables (COMPLETED)\nNew.\n\n"


def _edit_request(
    old_string: str,
    new_string: str,
    messages: list[object] | None = None,
    file_path: str = "/workspace/brand_brief.md",
) -> ToolCallRequest:
    return ToolCallRequest(
        tool_call={
            "name": "edit_file",
            "args": {
                "file_path": file_path,
                "old_string": old_string,
                "new_string": new_string,
            },
            "id": "call_1",
        },
        tool=None,
        state={"messages": messages or []},
        runtime=None,  # type: ignore[arg-type]
    )


def _profile_edit_request(
    user_texts: list[str],
    new_string: str = "## Identity\n- Role: [Chủ doanh nghiệp F&B]",
) -> ToolCallRequest:
    return ToolCallRequest(
        tool_call={
            "name": "edit_file",
            "args": {
                "file_path": "/user/profile.md",
                "old_string": "## Identity\n- Role: [To be discovered]",
                "new_string": new_string,
            },
            "id": "call_profile",
        },
        tool=None,
        state={"messages": [HumanMessage(content=text) for text in user_texts]},
        runtime=None,  # type: ignore[arg-type]
    )


def test_blocks_edit_that_removes_existing_phase_heading() -> None:
    middleware = WorkspaceBriefHygieneMiddleware()
    old_string = "### P - What's next\n## Phase 1: Market Intelligence (COMPLETED)"
    new_string = "### P - What's next\n## Phase 4: Communication Framework"
    handler_called = False

    def handler(request: ToolCallRequest) -> ToolMessage:
        nonlocal handler_called
        handler_called = True
        return ToolMessage("ran", tool_call_id=request.tool_call["id"])

    result = middleware.wrap_tool_call(_edit_request(old_string, new_string), handler)

    assert isinstance(result, ToolMessage)
    assert handler_called is False
    assert "preserve existing phase heading" in str(result.content)
    assert "`## Phase 1`" in str(result.content)


def test_blocks_unverified_hypothesis_in_objective_findings() -> None:
    middleware = WorkspaceBriefHygieneMiddleware()
    old_string = "### O — What we found\n_Research data._"
    new_string = (
        "### O — What we found\n"
        "- Hậu tố Signature thường ám chỉ một phiên bản cao cấp hơn.\n\n"
        "### A — What we concluded\n"
        "- Cần xác nhận đây là brand mới hay tái định vị."
    )
    handler_called = False

    def handler(request: ToolCallRequest) -> ToolMessage:
        nonlocal handler_called
        handler_called = True
        return ToolMessage("ran", tool_call_id=request.tool_call["id"])

    result = middleware.wrap_tool_call(_edit_request(old_string, new_string), handler)

    assert isinstance(result, ToolMessage)
    assert handler_called is False
    assert "`O — What we found`" in str(result.content)
    assert "hypotheses" in str(result.content)
    assert "market-research" in str(result.content)


def test_blocks_unsourced_external_findings_in_objective_section() -> None:
    middleware = WorkspaceBriefHygieneMiddleware()
    old_string = "### O — What we found\n_Research data._"
    new_string = (
        "### O — What we found\n"
        "- Brand has two branches in District 1.\n\n"
        "### A — What we concluded\n"
        "- Repositioning may be the right path."
    )
    handler_called = False

    def handler(request: ToolCallRequest) -> ToolMessage:
        nonlocal handler_called
        handler_called = True
        return ToolMessage("ran", tool_call_id=request.tool_call["id"])

    result = middleware.wrap_tool_call(_edit_request(old_string, new_string), handler)

    assert isinstance(result, ToolMessage)
    assert handler_called is False
    assert "current public market facts" in str(result.content)


def test_allows_sourced_objective_findings() -> None:
    middleware = WorkspaceBriefHygieneMiddleware()
    old_string = "### O — What we found\n_Research data._"
    new_string = (
        "### O — What we found\n"
        '- [O1] Source: market-research returned "official listing for the brand".\n\n'
        "### A — What we concluded\n"
        "- Use this verified fact to frame the next question."
    )
    messages = [
        ToolMessage(
            "The research pass found an official listing for the brand.",
            tool_call_id="research_1",
        )
    ]
    handler_called = False

    def handler(request: ToolCallRequest) -> ToolMessage:
        nonlocal handler_called
        handler_called = True
        return ToolMessage("ran", tool_call_id=request.tool_call["id"])

    result = middleware.wrap_tool_call(
        _edit_request(old_string, new_string, messages),
        handler,
    )

    assert handler_called is True
    assert isinstance(result, ToolMessage)
    assert result.content == "ran"


def test_blocks_fabricated_source_marker_in_objective_section() -> None:
    middleware = WorkspaceBriefHygieneMiddleware()
    old_string = "### O — What we found\n_Research data._"
    new_string = (
        "### O — What we found\n"
        "- Source: market-research task found a premium branch.\n\n"
        "### A — What we concluded\n"
        "- Treat this as repositioning."
    )
    messages = [
        ToolMessage("KG result: Signature is a naming cue.", tool_call_id="kg_1")
    ]
    handler_called = False

    def handler(request: ToolCallRequest) -> ToolMessage:
        nonlocal handler_called
        handler_called = True
        return ToolMessage("ran", tool_call_id=request.tool_call["id"])

    result = middleware.wrap_tool_call(
        _edit_request(old_string, new_string, messages),
        handler,
    )

    assert isinstance(result, ToolMessage)
    assert handler_called is False
    assert "Do not fabricate source labels" in str(result.content)


def test_allows_objective_section_that_records_no_verified_evidence_yet() -> None:
    middleware = WorkspaceBriefHygieneMiddleware()
    old_string = "### O — What we found\n_Research data._"
    new_string = (
        "### O — What we found\n"
        "- No external evidence verified yet.\n\n"
        "### A — What we concluded\n"
        "- Keep the opening interpretation tentative."
    )
    handler_called = False

    def handler(request: ToolCallRequest) -> ToolMessage:
        nonlocal handler_called
        handler_called = True
        return ToolMessage("ran", tool_call_id=request.tool_call["id"])

    result = middleware.wrap_tool_call(_edit_request(old_string, new_string), handler)

    assert handler_called is True
    assert isinstance(result, ToolMessage)
    assert result.content == "ran"


def test_blocks_memory_candidate_without_exact_evidence_quote() -> None:
    middleware = WorkspaceBriefHygieneMiddleware()
    old_string = "## Memory Candidates\n- Candidate:\n- Evidence quote:\n"
    new_string = (
        "## Memory Candidates\n"
        "- Candidate: Brand operates in HCMC with a premium fusion concept.\n"
        "- Type: project_context\n"
        "- Evidence quote: mentioned by user + research.\n"
        "- Confidence: high\n"
        "- Stability: durable\n"
        "- Promotion decision: promote to brand_brief.\n"
    )
    messages = [HumanMessage(content="Chuyện Ba Bữa Signature")]
    handler_called = False

    def handler(request: ToolCallRequest) -> ToolMessage:
        nonlocal handler_called
        handler_called = True
        return ToolMessage("ran", tool_call_id=request.tool_call["id"])

    result = middleware.wrap_tool_call(
        _edit_request(
            old_string,
            new_string,
            messages,
            file_path="/workspace/working_notes.md",
        ),
        handler,
    )

    assert isinstance(result, ToolMessage)
    assert handler_called is False
    assert "without source evidence" in str(result.content)


def test_allows_memory_candidate_with_exact_evidence_quote() -> None:
    middleware = WorkspaceBriefHygieneMiddleware()
    old_string = "## Memory Candidates\n- Candidate:\n- Evidence quote:\n"
    new_string = (
        "## Memory Candidates\n"
        "- Candidate: User asked for Chuyện Ba Bữa Signature strategy.\n"
        "- Type: project_context\n"
        '- Evidence quote: User said "Chuyện Ba Bữa Signature".\n'
        "- Confidence: medium\n"
        "- Stability: project_scoped\n"
        "- Promotion decision: keep here.\n"
    )
    messages = [HumanMessage(content="Chuyện Ba Bữa Signature")]
    handler_called = False

    def handler(request: ToolCallRequest) -> ToolMessage:
        nonlocal handler_called
        handler_called = True
        return ToolMessage("ran", tool_call_id=request.tool_call["id"])

    result = middleware.wrap_tool_call(
        _edit_request(
            old_string,
            new_string,
            messages,
            file_path="/workspace/working_notes.md",
        ),
        handler,
    )

    assert handler_called is True
    assert isinstance(result, ToolMessage)
    assert result.content == "ran"


def test_blocks_project_scoped_profile_fact_even_with_exact_quote() -> None:
    middleware = WorkspaceBriefHygieneMiddleware()
    new_string = (
        "## Constraints\n"
        "- Current project budget: 30-40 triệu for Chuyện Ba Bữa Signature.\n"
        '- Evidence quote: User said "ngân sách có khoảng 30-40 triệu thôi á".\n'
    )
    messages = [
        HumanMessage(
            content=(
                "Tôi muốn làm brand strategy cho Chuyện Ba Bữa Signature; "
                "ngân sách có khoảng 30-40 triệu thôi á"
            )
        )
    ]
    handler_called = False

    def handler(request: ToolCallRequest) -> ToolMessage:
        nonlocal handler_called
        handler_called = True
        return ToolMessage("ran", tool_call_id=request.tool_call["id"])

    result = middleware.wrap_tool_call(
        _profile_edit_request([messages[0].content], new_string),
        handler,
    )

    assert isinstance(result, ToolMessage)
    assert handler_called is False
    assert "project-scoped details" in str(result.content)
    assert "`/workspace/working_notes.md`" in str(result.content)


def test_allows_abstracted_durable_profile_fact_with_project_quote() -> None:
    middleware = WorkspaceBriefHygieneMiddleware()
    new_string = (
        "## Identity\n"
        "- Role: Marketing Executive.\n"
        '- Evidence quote: User said "tôi là marketing executive của nhà hàng đó á".\n'
    )
    messages = [HumanMessage(content="tôi là marketing executive của nhà hàng đó á")]
    handler_called = False

    def handler(request: ToolCallRequest) -> ToolMessage:
        nonlocal handler_called
        handler_called = True
        return ToolMessage("ran", tool_call_id=request.tool_call["id"])

    result = middleware.wrap_tool_call(
        _profile_edit_request([messages[0].content], new_string),
        handler,
    )

    assert handler_called is True
    assert isinstance(result, ToolMessage)
    assert result.content == "ran"


def test_blocks_user_interaction_pattern_without_source_quote() -> None:
    middleware = WorkspaceBriefHygieneMiddleware()
    old_string = (
        "## User Interaction Patterns\n"
        "_Observations about how this user works._\n"
        "- Learning speed: [Fast/Medium/Slow at grasping concepts]\n"
    )
    new_string = (
        "## User Interaction Patterns\n"
        "- User quan tâm đến phân khúc Premium/Signature.\n"
        "- Thích cách tiếp cận trực diện.\n"
    )
    messages = [
        HumanMessage(
            content="Tôi muốn làm brand strategy cho nhà hàng Chuyện Ba Bữa Signature á"
        )
    ]
    handler_called = False

    def handler(request: ToolCallRequest) -> ToolMessage:
        nonlocal handler_called
        handler_called = True
        return ToolMessage("ran", tool_call_id=request.tool_call["id"])

    result = middleware.wrap_tool_call(
        _edit_request(
            old_string,
            new_string,
            messages,
            file_path="/workspace/working_notes.md",
        ),
        handler,
    )

    assert isinstance(result, ToolMessage)
    assert handler_called is False
    assert "inferred user interaction patterns" in str(result.content)
    assert "Memory Candidates" in str(result.content)


def test_allows_user_interaction_pattern_with_exact_source_quote() -> None:
    middleware = WorkspaceBriefHygieneMiddleware()
    old_string = "## User Interaction Patterns\n_Observations._"
    new_string = (
        "## User Interaction Patterns\n"
        "- Candidate: User asked for Chuyện Ba Bữa Signature strategy.\n"
        '- Evidence quote: User said "Chuyện Ba Bữa Signature".\n'
    )
    messages = [HumanMessage(content="Chuyện Ba Bữa Signature")]
    handler_called = False

    def handler(request: ToolCallRequest) -> ToolMessage:
        nonlocal handler_called
        handler_called = True
        return ToolMessage("ran", tool_call_id=request.tool_call["id"])

    result = middleware.wrap_tool_call(
        _edit_request(
            old_string,
            new_string,
            messages,
            file_path="/workspace/working_notes.md",
        ),
        handler,
    )

    assert handler_called is True
    assert isinstance(result, ToolMessage)
    assert result.content == "ran"


def test_blocks_unsourced_public_market_facts_in_working_notes() -> None:
    middleware = WorkspaceBriefHygieneMiddleware()
    old_string = "## Inbox\n_Empty._"
    new_string = (
        "## Inbox\n"
        "- [Market Fact] Existing location in District 1, HCMC.\n"
        "- [Market Fact] TripAdvisor rating is 5.0.\n"
    )
    handler_called = False

    def handler(request: ToolCallRequest) -> ToolMessage:
        nonlocal handler_called
        handler_called = True
        return ToolMessage("ran", tool_call_id=request.tool_call["id"])

    result = middleware.wrap_tool_call(
        _edit_request(
            old_string,
            new_string,
            file_path="/workspace/working_notes.md",
        ),
        handler,
    )

    assert isinstance(result, ToolMessage)
    assert handler_called is False
    assert "current public market facts" in str(result.content)
    assert "market-research" in str(result.content)
    assert "Do not retry the same edit unchanged" in str(result.content)
    assert "Ideas & Hypotheses" in str(result.content)
    assert "Evidence Gaps" in str(result.content)


def test_blocks_unsourced_public_listing_observations_in_working_notes() -> None:
    middleware = WorkspaceBriefHygieneMiddleware()
    old_string = "## Inbox\n_Empty._"
    new_string = (
        "## Inbox & Observations\n"
        '- Brand "Chuyện Ba Bữa" exists as a modern Saigonese concept.\n'
        '- "Chuyện Ba Bữa Signature" appears as a premium extension in '
        "public listings.\n"
    )
    handler_called = False

    def handler(request: ToolCallRequest) -> ToolMessage:
        nonlocal handler_called
        handler_called = True
        return ToolMessage("ran", tool_call_id=request.tool_call["id"])

    result = middleware.wrap_tool_call(
        _edit_request(
            old_string,
            new_string,
            file_path="/workspace/working_notes.md",
        ),
        handler,
    )

    assert isinstance(result, ToolMessage)
    assert handler_called is False
    assert "current public market facts" in str(result.content)


def test_allows_public_market_facts_with_exact_tool_quote() -> None:
    middleware = WorkspaceBriefHygieneMiddleware()
    old_string = "## Inbox\n_Empty._"
    new_string = (
        '## Inbox\n- Source: market-research returned "TripAdvisor rating is 5.0".\n'
    )
    messages = [
        ToolMessage(
            "The market-research pass found: TripAdvisor rating is 5.0.",
            tool_call_id="research_1",
        )
    ]
    handler_called = False

    def handler(request: ToolCallRequest) -> ToolMessage:
        nonlocal handler_called
        handler_called = True
        return ToolMessage("ran", tool_call_id=request.tool_call["id"])

    result = middleware.wrap_tool_call(
        _edit_request(
            old_string,
            new_string,
            messages,
            file_path="/workspace/working_notes.md",
        ),
        handler,
    )

    assert handler_called is True
    assert isinstance(result, ToolMessage)
    assert result.content == "ran"


def test_blocks_public_market_fact_with_unrelated_evidence_quote() -> None:
    middleware = WorkspaceBriefHygieneMiddleware()
    old_string = "## Inbox\n_Empty._"
    new_string = (
        "## Inbox\n"
        '- Initial research suggests "Chuyện Ba Bữa Signature" operates in '
        "Ho Chi Minh City with a fusion concept.\n\n"
        "## Memory Candidates\n"
        "- Candidate: User asked for Chuyện Ba Bữa Signature strategy.\n"
        "- Type: project_context\n"
        '- Evidence quote: User said "Chuyện Ba Bữa Signature".\n'
        "- Confidence: medium\n"
        "- Stability: project_scoped\n"
        "- Promotion decision: keep here.\n"
    )
    messages = [HumanMessage(content="Chuyện Ba Bữa Signature")]
    handler_called = False

    def handler(request: ToolCallRequest) -> ToolMessage:
        nonlocal handler_called
        handler_called = True
        return ToolMessage("ran", tool_call_id=request.tool_call["id"])

    result = middleware.wrap_tool_call(
        _edit_request(
            old_string,
            new_string,
            messages,
            file_path="/workspace/working_notes.md",
        ),
        handler,
    )

    assert isinstance(result, ToolMessage)
    assert handler_called is False
    assert "current public market facts" in str(result.content)


def test_normalizes_duplicate_phases_after_allowed_edit(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(hygiene_mod, "BRANDMIND_HOME", tmp_path)
    workspace = tmp_path / "projects" / "abc123" / "workspace"
    workspace.mkdir(parents=True)
    brief = workspace / "brand_brief.md"
    brief.write_text("# Brand\n\n" + _PHASE_0 + _PHASE_5_OLD + _PHASE_1, "utf-8")

    middleware = WorkspaceBriefHygieneMiddleware()
    request = _edit_request(_PHASE_1, _PHASE_5_NEW + _PHASE_1)
    session = BrandStrategySession(session_id="abc123")
    set_active_session(session)

    def handler(request: ToolCallRequest) -> ToolMessage:
        brief.write_text(
            "# Brand\n\n" + _PHASE_0 + _PHASE_5_OLD + _PHASE_1 + _PHASE_5_NEW,
            "utf-8",
        )
        return ToolMessage("ran", tool_call_id=request.tool_call["id"])

    try:
        result = middleware.wrap_tool_call(request, handler)
    finally:
        set_active_session(None)

    persisted = brief.read_text("utf-8")
    assert isinstance(result, ToolMessage)
    assert result.content == "ran"
    assert "Old." not in persisted
    assert "New." in persisted
    assert _PHASE_1 in persisted


def test_recovers_stale_full_brief_template_replace(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(hygiene_mod, "BRANDMIND_HOME", tmp_path)
    workspace = tmp_path / "projects" / "abc123" / "workspace"
    workspace.mkdir(parents=True)
    brief = workspace / "brand_brief.md"
    brief.write_text("# Brand Brief\n\n" + _PHASE_0, "utf-8")

    old_string = "# Brand Strategy Brief: [Brand Name]\n\n## Phase 0\n"
    new_string = "\n\n".join(
        [
            "# Brand Strategy Brief: Cà Phê Cũ",
            "## Phase 0: Business Problem Diagnosis\nDone.",
            "## Phase 0.5: Brand Equity Audit\nDone.",
            "## Phase 1: Market Intelligence\nDone.",
            "## Phase 2: Brand Positioning\nDone.",
            "## Phase 3: Brand Identity\nDone.",
            "## Phase 4: Communication Framework\nDone.",
            "## Phase 5: Strategy Plan & Deliverables\nDone.",
        ]
    )

    middleware = WorkspaceBriefHygieneMiddleware()
    session = BrandStrategySession(session_id="abc123")
    set_active_session(session)

    def handler(request: ToolCallRequest) -> ToolMessage:
        return ToolMessage("Error: String not found in file", tool_call_id="call_1")

    try:
        result = middleware.wrap_tool_call(
            _edit_request(old_string, new_string), handler
        )
    finally:
        set_active_session(None)

    persisted = brief.read_text("utf-8")
    assert isinstance(result, ToolMessage)
    assert "Recovered `/workspace/brand_brief.md`" in str(result.content)
    assert "# Brand Strategy Brief: Cà Phê Cũ" in persisted
    assert "## Phase 0.5: Brand Equity Audit" in persisted
    assert "## Phase 5: Strategy Plan & Deliverables" in persisted


def test_recovers_placeholder_full_brief_with_nested_phases_and_syncs_handoff(
    tmp_path,
    monkeypatch,
) -> None:
    import core.brand_strategy.session as sess_mod

    monkeypatch.setattr(hygiene_mod, "BRANDMIND_HOME", tmp_path)
    monkeypatch.setattr(sess_mod, "BRANDMIND_HOME", tmp_path)
    workspace = tmp_path / "projects" / "abc123" / "workspace"
    workspace.mkdir(parents=True)
    brief = workspace / "brand_brief.md"
    brief.write_text(
        "# Brand Brief\n\n## Phase 0: Business Problem Diagnosis\nOld.",
        "utf-8",
    )

    old_string = "# Brand Brief\n(Empty or placeholder content)\n"
    new_string = "\n\n".join(
        [
            "# Brand Brief - Cà Phê Cũ",
            "## 3. Chi tiết các giai đoạn",
            "### Phase 0: Business Problem Diagnosis\nDone.",
            "### Phase 0.5: Brand Equity Audit\nDone.",
            "### Phase 1: Market Intelligence\nDone.",
            "### Phase 2: Brand Positioning\nDone.",
            "### Phase 3: Brand Identity\nDone.",
            "### Phase 4: Communication Framework\nDone.",
            "### Phase 5: Strategy Plan & Deliverables\nReady.",
        ]
    )

    request = _edit_request(old_string, new_string)
    request.state["messages"] = [
        HumanMessage(
            content=(
                "Làm giúp tôi bộ tài liệu cuối gồm file chiến lược, "
                "bộ slide, bảng KPI và trang tóm tắt thương hiệu."
            )
        )
    ]
    middleware = WorkspaceBriefHygieneMiddleware()
    session = BrandStrategySession(
        session_id="abc123",
        scope="repositioning",
        current_phase="phase_0_5",
        completed_phases=["phase_0"],
    )
    set_active_session(session)

    def handler(request: ToolCallRequest) -> ToolMessage:
        return ToolMessage("Error: String not found in file", tool_call_id="call_1")

    try:
        result = middleware.wrap_tool_call(request, handler)
    finally:
        set_active_session(None)

    persisted = brief.read_text("utf-8")
    assert isinstance(result, ToolMessage)
    assert "Recovered `/workspace/brand_brief.md`" in str(result.content)
    assert "phase: phase_0_5 → phase_5" in str(result.content)
    assert session.current_phase == "phase_5"
    assert "### Phase" not in persisted
    assert "## Phase 2: Brand Positioning" in persisted
    assert "## Phase 5: Strategy Plan & Deliverables" in persisted


def test_intercepts_broad_replace_all_as_phase_section_upsert(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(hygiene_mod, "BRANDMIND_HOME", tmp_path)
    workspace = tmp_path / "projects" / "abc123" / "workspace"
    workspace.mkdir(parents=True)
    brief = workspace / "brand_brief.md"
    brief.write_text("# Brand Brief\n\n" + _PHASE_0 + _PHASE_1, "utf-8")

    new_string = "\n\n".join(
        [
            "---",
            "## Phase 2: Brand Positioning\nPositioning summary.",
            "## Phase 3: Brand Identity\nIdentity summary.",
        ]
    )
    request = _edit_request("---", new_string)
    request.tool_call["args"]["replace_all"] = True
    middleware = WorkspaceBriefHygieneMiddleware()
    session = BrandStrategySession(session_id="abc123")
    set_active_session(session)
    handler_called = False

    def handler(request: ToolCallRequest) -> ToolMessage:
        nonlocal handler_called
        handler_called = True
        return ToolMessage("ran", tool_call_id=request.tool_call["id"])

    try:
        result = middleware.wrap_tool_call(request, handler)
    finally:
        set_active_session(None)

    persisted = brief.read_text("utf-8")
    assert handler_called is False
    assert isinstance(result, ToolMessage)
    assert "upserting the supplied phase section" in str(result.content)
    assert "## Phase 0: Business Problem Diagnosis" in persisted
    assert "## Phase 1: Market Intelligence" in persisted
    assert "## Phase 2: Brand Positioning" in persisted
    assert "## Phase 3: Brand Identity" in persisted


def test_recovers_ambiguous_separator_edit_as_phase_section_upsert(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(hygiene_mod, "BRANDMIND_HOME", tmp_path)
    workspace = tmp_path / "projects" / "abc123" / "workspace"
    workspace.mkdir(parents=True)
    brief = workspace / "brand_brief.md"
    brief.write_text("# Brand Brief\n\n" + _PHASE_0, "utf-8")

    new_string = "---\n\n## Phase 2: Brand Positioning\nPositioning summary."
    middleware = WorkspaceBriefHygieneMiddleware()
    session = BrandStrategySession(session_id="abc123")
    set_active_session(session)

    def handler(request: ToolCallRequest) -> ToolMessage:
        return ToolMessage(
            "Error: String '---' appears 3 times in file.",
            tool_call_id=request.tool_call["id"],
        )

    try:
        result = middleware.wrap_tool_call(_edit_request("---", new_string), handler)
    finally:
        set_active_session(None)

    persisted = brief.read_text("utf-8")
    assert isinstance(result, ToolMessage)
    assert "upserting the supplied phase section" in str(result.content)
    assert "## Phase 0: Business Problem Diagnosis" in persisted
    assert "## Phase 2: Brand Positioning" in persisted


def test_ignores_non_brand_brief_edits() -> None:
    middleware = WorkspaceBriefHygieneMiddleware()
    request = ToolCallRequest(
        tool_call={
            "name": "edit_file",
            "args": {
                "file_path": "/workspace/working_notes.md",
                "old_string": "## Phase 1",
                "new_string": "## Phase 4",
            },
            "id": "call_1",
        },
        tool=None,
        state={},
        runtime=None,  # type: ignore[arg-type]
    )

    result = middleware.wrap_tool_call(
        request,
        lambda req: ToolMessage("ran", tool_call_id=req.tool_call["id"]),
    )

    assert isinstance(result, ToolMessage)
    assert result.content == "ran"


def test_blocks_sparse_first_turn_profile_inference() -> None:
    middleware = WorkspaceBriefHygieneMiddleware()
    request = _profile_edit_request(
        ["Tôi muốn làm brand strategy cho nhà hàng Chuyện Ba Bữa Signature á"]
    )
    handler_called = False

    def handler(request: ToolCallRequest) -> ToolMessage:
        nonlocal handler_called
        handler_called = True
        return ToolMessage("ran", tool_call_id=request.tool_call["id"])

    result = middleware.wrap_tool_call(request, handler)

    assert isinstance(result, ToolMessage)
    assert handler_called is False
    assert "Cannot edit `/user/profile.md` without source evidence" in str(
        result.content
    )
    assert "memory candidate" in str(result.content)
    assert "continue the user-facing flow" in str(result.content)


def test_blocks_keyword_profile_update_without_source_quote() -> None:
    middleware = WorkspaceBriefHygieneMiddleware()
    request = _profile_edit_request(
        ["Tôi là founder, ngân sách dự kiến khoảng 80 triệu cho launch."]
    )
    handler_called = False

    def handler(request: ToolCallRequest) -> ToolMessage:
        nonlocal handler_called
        handler_called = True
        return ToolMessage("ran", tool_call_id=request.tool_call["id"])

    result = middleware.wrap_tool_call(request, handler)

    assert handler_called is False
    assert isinstance(result, ToolMessage)
    assert "without source evidence" in str(result.content)


def test_blocks_project_budget_profile_update_even_with_exact_source_quote() -> None:
    middleware = WorkspaceBriefHygieneMiddleware()
    request = _profile_edit_request(
        ["Tôi là founder, ngân sách dự kiến khoảng 80 triệu cho launch."],
        new_string=(
            "## Identity\n"
            "- Role: Founder\n"
            '- Source: User said "Tôi là founder".\n'
            "## Constraints\n"
            "- Budget: khoảng 80 triệu cho launch\n"
            '- Evidence: User said "ngân sách dự kiến khoảng 80 triệu".'
        ),
    )
    handler_called = False

    def handler(request: ToolCallRequest) -> ToolMessage:
        nonlocal handler_called
        handler_called = True
        return ToolMessage("ran", tool_call_id=request.tool_call["id"])

    result = middleware.wrap_tool_call(request, handler)

    assert handler_called is False
    assert isinstance(result, ToolMessage)
    assert "project-scoped details" in str(result.content)


def test_blocks_ephemeral_project_context_after_multiple_user_turns() -> None:
    middleware = WorkspaceBriefHygieneMiddleware()
    request = _profile_edit_request(
        [
            "Tôi muốn làm brand strategy cho một nhà hàng.",
            "Tôi là founder, đang cần bản trình sếp tuần này.",
        ],
        new_string=(
            "## Identity\n"
            "- Role: Founder\n"
            '- Evidence: User said "Tôi là founder".\n'
            "## Working Context\n"
            "- Needs a boss-facing deck this week\n"
            '- Evidence: User said "đang cần bản trình sếp tuần này".'
        ),
    )
    handler_called = False

    def handler(request: ToolCallRequest) -> ToolMessage:
        nonlocal handler_called
        handler_called = True
        return ToolMessage("ran", tool_call_id=request.tool_call["id"])

    result = middleware.wrap_tool_call(request, handler)

    assert handler_called is False
    assert isinstance(result, ToolMessage)
    assert "project-scoped details" in str(result.content)
