"""
Core logic tests for TodoWrite functionality without LangChain dependencies.

This module tests the core validation and reminder generation logic
independently of the LangChain framework.
"""

import json
from typing import Any, Dict, List, Literal, TypedDict


class TodoItem(TypedDict):
    """
    Represents a structured todo item with all mandatory fields.
    """

    content: str
    status: Literal["pending", "in_progress", "completed"]
    activeForm: str
    priority: Literal["high", "medium", "low"]


def validate_todos(todos: List[TodoItem]) -> Dict[str, Any]:
    """
    Validate todo list with mandatory activeForm and business rules.

    Enforces:
    - Single in_progress rule (max_in_progress = 1)
    - Mandatory activeForm field
    - Required field validation
    - Status value validation
    """
    if not todos:
        return {"valid": True, "error": None}

    # Single in_progress rule (fixed at 1)
    in_progress = [t for t in todos if t.get("status") == "in_progress"]
    if len(in_progress) > 1:
        return {
            "valid": False,
            "error": f"Too many tasks in_progress ({len(in_progress)}). "
            f"Only 1 task allowed at a time.",
        }

    # Mandatory field validation
    for i, todo in enumerate(todos):
        # Check required content field
        if not todo.get("content", "").strip():
            return {"valid": False, "error": f"Todo at index {i} has empty content"}

        # Check mandatory activeForm field
        if not todo.get("activeForm", "").strip():
            return {
                "valid": False,
                "error": f"Todo at index {i} has empty activeForm field",
            }

        # Check valid status values
        if todo.get("status") not in ["pending", "in_progress", "completed"]:
            return {
                "valid": False,
                "error": f"Todo at index {i} has invalid status "
                f"'{todo.get('status')}'. "
                f"Must be one of: pending, in_progress, completed",
            }

        # Check valid priority values
        if todo.get("priority") not in ["high", "medium", "low"]:
            return {
                "valid": False,
                "error": f"Todo at index {i} has invalid priority "
                f"'{todo.get('priority')}'. "
                f"Must be one of: high, medium, low",
            }

    return {"valid": True, "error": None}


def generate_reminder(todos: List[TodoItem]) -> str:
    """
    Generate reminders based on todo state.

    Covers all edge cases:
    - Empty list (initial or post-completion)
    - State changes (any update)
    """
    try:
        # Case A: Empty list reminder
        if not todos:
            return """
<system-reminder>
This is a reminder that your todo list is currently empty. DO NOT mention this explicitly to the user because they are already aware. If you are working on tasks that would benefit from a todo list please use the TodoWrite tool to create one. If not, please feel free to ignore. Again do not mention this to the user.
</system-reminder>"""

        # Case B: State change reminder with placeholder
        todos_json = json.dumps(
            [
                {
                    "content": todo["content"],
                    "status": todo["status"],
                    "activeForm": todo["activeForm"],
                }
                for todo in todos
            ],
            indent=2,
        )

        reminder_template = """
<system-reminder>
Your todo list has changed. DO NOT mention this explicitly to the user. Here are the latest contents of your todo list:
{{todos_json}}. Continue on with the tasks that you have to complete.
</system-reminder>"""

        return reminder_template.replace("{{todos_json}}", todos_json)

    except Exception as e:
        print(f"Warning: Reminder generation failed: {e}")
        return ""


def test_validation_logic():
    """Test validation logic with various scenarios."""
    print("Testing validation logic...")

    # Test 1: Valid single todo
    valid_todos = [
        {
            "content": "Test task",
            "status": "pending",
            "activeForm": "Will test",
            "priority": "high",
        }
    ]
    result = validate_todos(valid_todos)
    assert result["valid"], f"Expected valid, got: {result}"
    print("✅ Valid single todo test passed")

    # Test 2: Valid multiple todos with single in_progress
    valid_multiple = [
        {
            "content": "Task 1",
            "status": "completed",
            "activeForm": "Completed task 1",
            "priority": "high",
        },
        {
            "content": "Task 2",
            "status": "in_progress",
            "activeForm": "Working on task 2",
            "priority": "medium",
        },
        {
            "content": "Task 3",
            "status": "pending",
            "activeForm": "Will start task 3",
            "priority": "low",
        },
    ]
    result = validate_todos(valid_multiple)
    assert result["valid"], f"Expected valid for multiple todos, got: {result}"
    print("✅ Valid multiple todos test passed")

    # Test 3: Invalid - multiple in_progress
    invalid_multiple = [
        {
            "content": "Task 1",
            "status": "in_progress",
            "activeForm": "Working on task 1",
            "priority": "high",
        },
        {
            "content": "Task 2",
            "status": "in_progress",
            "activeForm": "Working on task 2",
            "priority": "medium",
        },
    ]
    result = validate_todos(invalid_multiple)
    assert not result[
        "valid"
    ], f"Expected invalid for multiple in_progress, got: {result}"
    assert "Too many tasks in_progress" in result["error"]
    print("✅ Multiple in_progress validation test passed")

    # Test 4: Invalid - empty content
    invalid_content = [
        {"content": "", "status": "pending", "activeForm": "Task", "priority": "high"}
    ]
    result = validate_todos(invalid_content)
    assert not result["valid"], f"Expected invalid for empty content, got: {result}"
    assert "empty content" in result["error"]
    print("✅ Empty content validation test passed")

    # Test 5: Invalid - empty activeForm
    invalid_active_form = [
        {"content": "Task", "status": "pending", "activeForm": "", "priority": "high"}
    ]
    result = validate_todos(invalid_active_form)
    assert not result["valid"], f"Expected invalid for empty activeForm, got: {result}"
    assert "empty activeForm" in result["error"]
    print("✅ Empty activeForm validation test passed")

    # Test 6: Invalid - invalid status
    invalid_status = [
        {
            "content": "Task",
            "status": "invalid_status",
            "activeForm": "Task",
            "priority": "high",
        }
    ]
    result = validate_todos(invalid_status)
    assert not result["valid"], f"Expected invalid for invalid status, got: {result}"
    assert "invalid status" in result["error"]
    print("✅ Invalid status validation test passed")

    # Test 7: Invalid - invalid priority
    invalid_priority = [
        {
            "content": "Task",
            "status": "pending",
            "activeForm": "Task",
            "priority": "invalid_priority",
        }
    ]
    result = validate_todos(invalid_priority)
    assert not result["valid"], f"Expected invalid for invalid priority, got: {result}"
    assert "invalid priority" in result["error"]
    print("✅ Invalid priority validation test passed")

    # Test 8: Empty list
    result = validate_todos([])
    assert result["valid"], f"Expected valid for empty list, got: {result}"
    print("✅ Empty list validation test passed")


def test_reminder_generation():
    """Test reminder generation logic."""
    print("Testing reminder generation...")

    # Test 1: Empty list reminder
    reminder = generate_reminder([])
    assert "todo list is currently empty" in reminder.lower()
    print("✅ Empty list reminder test passed")

    # Test 2: Todos reminder
    test_todos = [
        {
            "content": "Test task 1",
            "status": "in_progress",
            "activeForm": "Working on test 1",
            "priority": "high",
        },
        {
            "content": "Test task 2",
            "status": "pending",
            "activeForm": "Will start test 2",
            "priority": "medium",
        },
    ]
    reminder = generate_reminder(test_todos)
    assert "Test task 1" in reminder
    assert "in_progress" in reminder
    assert "Working on test 1" in reminder
    print("✅ Todos reminder test passed")

    # Test 3: Reminder format
    assert "<system-reminder>" in reminder
    assert "</system-reminder>" in reminder
    print("✅ Reminder format test passed")


if __name__ == "__main__":
    """Run all core logic tests."""
    print("🧪 Running TodoWrite core logic tests...")
    print("=" * 50)

    try:
        test_validation_logic()
        print()
        test_reminder_generation()
        print()
        print("🎉 All core logic tests passed successfully!")
        print()
        print("✅ Core TodoWrite functionality is working correctly!")
        print("✅ Validation logic properly enforces business rules!")
        print("✅ Reminder generation works for all scenarios!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
