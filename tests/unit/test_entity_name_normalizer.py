"""
Test script for Entity Name Normalization module.

This script tests the entity name normalizer according to test cases
defined in task_30.md.
"""

import asyncio
import sys
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "src" / "core" / "src"))
sys.path.insert(0, str(project_root / "src" / "shared" / "src"))

from core.knowledge_graph.curator.entity_name_normalizer import (
    PASCAL_CASE_PATTERN,
    EntityToNormalize,
    NormalizationResult,
    batch_normalize_names,
)


def test_case_1_detection_accuracy():
    """
    Test Case 1: Detection Accuracy
    Purpose: Verify regex correctly identifies PascalCase
    """
    print("\n" + "=" * 60)
    print("Test Case 1: Detection Accuracy")
    print("=" * 60)

    test_cases = [
        # (input, should_match)
        ("BrandEquity", True),           # PascalCase - should match
        ("Brand Equity", False),         # Has space - should NOT match
        ("iPhone", False),               # Brand name - should NOT match
        ("AI", False),                   # Single word acronym - should NOT match
        ("ConsumerBehavior", True),      # PascalCase - should match
        ("MarketSegmentation", True),    # PascalCase - should match
        ("Google", False),               # Single word - should NOT match
        ("StrategicBrandManagement", True),  # Long PascalCase - should match
        ("MacBookPro", True),            # PascalCase - should match
        ("macOS", False),                # camelCase with lowercase start - should NOT match
        ("ROI", False),                  # All caps acronym - should NOT match
        ("B2B", False),                  # Mixed with number - should NOT match
        ("LinkedInMarketing", True),     # PascalCase - should match
    ]

    passed = 0
    failed = 0

    for name, expected in test_cases:
        result = bool(PASCAL_CASE_PATTERN.match(name))
        status = "✅" if result == expected else "❌"
        if result == expected:
            passed += 1
        else:
            failed += 1
        print(f"  {status} '{name}': Expected {expected}, Got {result}")

    print(f"\nResult: {passed}/{len(test_cases)} passed")
    return failed == 0


async def test_case_2_llm_normalization():
    """
    Test Case 2: LLM Normalization
    Purpose: Verify LLM correctly normalizes PascalCase
    """
    print("\n" + "=" * 60)
    print("Test Case 2: LLM Normalization")
    print("=" * 60)

    # Create test entities
    test_entities = [
        EntityToNormalize(
            entity_id="test-1",
            entity_type="MarketingConcept",
            current_name="BrandEquity",
            description="A concept related to brand value",
        ),
        EntityToNormalize(
            entity_id="test-2",
            entity_type="MarketingConcept",
            current_name="MarketSegmentation",
            description="Dividing market into segments",
        ),
        EntityToNormalize(
            entity_id="test-3",
            entity_type="Product",
            current_name="ConsumerBehavior",
            description="How consumers make decisions",
        ),
    ]

    print("Input entities:")
    for e in test_entities:
        print(f"  - {e.current_name}")

    try:
        # Call LLM to normalize
        name_mapping = await batch_normalize_names(test_entities, batch_size=10)

        print("\nLLM Normalization Results:")
        for old_name, new_name in name_mapping.items():
            print(f"  ✅ '{old_name}' -> '{new_name}'")

        # Verify expected transformations
        expected = {
            "BrandEquity": "Brand Equity",
            "MarketSegmentation": "Market Segmentation",
            "ConsumerBehavior": "Consumer Behavior",
        }

        all_passed = True
        print("\nValidation:")
        for old, expected_new in expected.items():
            actual = name_mapping.get(old, old)
            if actual == expected_new:
                print(f"  ✅ '{old}' correctly normalized to '{actual}'")
            else:
                print(f"  ❌ '{old}': Expected '{expected_new}', Got '{actual}'")
                all_passed = False

        return all_passed

    except Exception as e:
        print(f"  ❌ Error during LLM call: {e}")
        return False


def test_case_3_data_models():
    """
    Test Case 3: Data Models
    Purpose: Verify Pydantic models work correctly
    """
    print("\n" + "=" * 60)
    print("Test Case 3: Data Models")
    print("=" * 60)

    # Test EntityToNormalize
    try:
        entity = EntityToNormalize(
            entity_id="uuid-123",
            entity_type="MarketingConcept",
            current_name="TestEntity",
            description="A test entity",
        )
        print(f"  ✅ EntityToNormalize created: {entity.current_name}")
    except Exception as e:
        print(f"  ❌ EntityToNormalize failed: {e}")
        return False

    # Test NormalizationResult
    try:
        result = NormalizationResult(
            normalized_count=5,
            skipped_count=2,
            failed_count=1,
            name_mapping={"OldName": "New Name"},
            skipped_names=["iPhone", "Google"],
            errors=["Test error"],
        )
        print(f"  ✅ NormalizationResult created:")
        print(f"     Normalized: {result.normalized_count}")
        print(f"     Skipped: {result.skipped_count}")
        print(f"     Failed: {result.failed_count}")
    except Exception as e:
        print(f"  ❌ NormalizationResult failed: {e}")
        return False

    # Test default values
    try:
        default_result = NormalizationResult()
        assert default_result.normalized_count == 0
        assert default_result.name_mapping == {}
        print(f"  ✅ Default values work correctly")
    except Exception as e:
        print(f"  ❌ Default values failed: {e}")
        return False

    return True


def test_case_4_edge_cases():
    """
    Test Case 4: Edge Cases
    Purpose: Test regex with edge cases
    """
    print("\n" + "=" * 60)
    print("Test Case 4: Edge Cases")
    print("=" * 60)

    edge_cases = [
        # Edge cases that might be tricky
        ("Ab", False),                   # Too short
        ("ABc", False),                  # Starts with consecutive caps
        ("aBC", False),                  # Starts lowercase
        ("AbC", False),                  # Single letter word after
        ("AbCd", True),                  # Minimal valid PascalCase
        ("A", False),                    # Single letter
        ("", False),                     # Empty string
        ("123", False),                  # Numbers only
        ("Test123Name", False),          # Numbers in middle
        ("TestName123", False),          # Numbers at end
        ("TESTNAME", False),             # All caps
        ("testname", False),             # All lowercase
        ("TestNameHere", True),          # Valid 3-word PascalCase
    ]

    passed = 0
    failed = 0

    for name, expected in edge_cases:
        result = bool(PASCAL_CASE_PATTERN.match(name))
        status = "✅" if result == expected else "❌"
        if result == expected:
            passed += 1
        else:
            failed += 1
        print(f"  {status} '{name}': Expected {expected}, Got {result}")

    print(f"\nResult: {passed}/{len(edge_cases)} passed")
    return failed == 0


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Entity Name Normalization - Test Suite")
    print("=" * 60)

    results = []

    # Test 1: Detection Accuracy
    results.append(("Test Case 1: Detection Accuracy", test_case_1_detection_accuracy()))

    # Test 3: Data Models (run before LLM to catch basic errors)
    results.append(("Test Case 3: Data Models", test_case_3_data_models()))

    # Test 4: Edge Cases
    results.append(("Test Case 4: Edge Cases", test_case_4_edge_cases()))

    # Test 2: LLM Normalization (requires API call)
    print("\n⚠️  Test Case 2 requires LLM API call. Running...")
    results.append(
        ("Test Case 2: LLM Normalization", await test_case_2_llm_normalization())
    )

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed. Please review.")

    return all_passed


if __name__ == "__main__":
    asyncio.run(main())
