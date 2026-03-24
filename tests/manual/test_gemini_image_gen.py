"""Manual test: Gemini 3 Pro Image — generate + edit via generate_content.

Run: uv run python tests/manual/test_gemini_image_gen.py

Tests:
1. Text-to-image generation
2. Image viewing (load generated image back)
3. Image editing (send image + edit prompt → refined image)
"""

from __future__ import annotations

import base64
import sys
from pathlib import Path

from google import genai
from google.genai import types

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "config"))
from system_config import SETTINGS  # noqa: E402

OUTPUT_DIR = Path(__file__).parent.parent.parent / "brandmind-output" / "test_images"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL = "gemini-3-pro-image-preview"


def _save_image_from_response(
    response: types.GenerateContentResponse,
    filename: str,
) -> Path | None:
    """Extract and save first image from generate_content response."""
    if not response.candidates:
        print("  No candidates in response")
        return None

    for part in response.candidates[0].content.parts:
        if part.inline_data and part.inline_data.mime_type.startswith("image/"):
            img_bytes = part.inline_data.data
            ext = part.inline_data.mime_type.split("/")[-1]
            path = OUTPUT_DIR / f"{filename}.{ext}"
            path.write_bytes(img_bytes)
            print(f"  Saved: {path} ({len(img_bytes)} bytes)")
            return path

    # Check if response has text instead (safety block, etc.)
    for part in response.candidates[0].content.parts:
        if part.text:
            print(f"  Model returned text instead: {part.text[:200]}")
    return None


def test_1_generate_image():
    """Test 1: Text-to-image generation."""
    print("\n=== Test 1: Text-to-Image Generation ===")

    client = genai.Client(api_key=SETTINGS.GEMINI_API_KEY)

    response = client.models.generate_content(
        model=MODEL,
        contents="Generate an image: A minimalist logo for a Vietnamese specialty coffee shop called 'Sương Mai'. Clean lines, earthy tones, flat design, white background.",
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(
                aspect_ratio="1:1",
            ),
        ),
    )

    path = _save_image_from_response(response, "test1_generate")
    assert path is not None, "Failed to generate image"
    assert path.stat().st_size > 1000, "Image too small"
    print("  PASSED")
    return path


def test_2_generate_with_text_response():
    """Test 2: Generate image + get text description back."""
    print("\n=== Test 2: Generate Image + Text ===")

    client = genai.Client(api_key=SETTINGS.GEMINI_API_KEY)

    response = client.models.generate_content(
        model=MODEL,
        contents="Generate an image of a mood board for a luxury F&B brand: dark wood, gold accents, specialty coffee, artisan pastries. Also describe the visual direction briefly.",
        config=types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
            image_config=types.ImageConfig(
                aspect_ratio="16:9",
            ),
        ),
    )

    if not response.candidates:
        print("  No candidates")
        return None

    text_parts = []
    image_saved = False

    for part in response.candidates[0].content.parts:
        if part.text:
            text_parts.append(part.text)
        if part.inline_data and part.inline_data.mime_type.startswith("image/"):
            img_bytes = part.inline_data.data
            ext = part.inline_data.mime_type.split("/")[-1]
            path = OUTPUT_DIR / f"test2_mood_board.{ext}"
            path.write_bytes(img_bytes)
            print(f"  Image saved: {path} ({len(img_bytes)} bytes)")
            image_saved = True

    if text_parts:
        print(f"  Text response: {' '.join(text_parts)[:200]}...")

    assert image_saved, "No image in response"
    print("  PASSED")


def test_3_edit_image(source_path: Path):
    """Test 3: Image editing — load existing image + edit prompt."""
    print("\n=== Test 3: Image Editing (image + text → refined image) ===")

    client = genai.Client(api_key=SETTINGS.GEMINI_API_KEY)

    # Load the image from Test 1
    image_bytes = source_path.read_bytes()
    mime = "image/png" if source_path.suffix == ".png" else "image/jpeg"

    print(f"  Input image: {source_path} ({len(image_bytes)} bytes)")

    # Send image + edit instruction
    response = client.models.generate_content(
        model=MODEL,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=mime),
            types.Part.from_text(text=
                "Edit this logo: make the color palette warmer with terracotta and cream tones, add a subtle coffee leaf motif, keep the minimalist style."
            ),
        ],
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(
                aspect_ratio="1:1",
            ),
        ),
    )

    path = _save_image_from_response(response, "test3_edited")
    assert path is not None, "Failed to edit image"
    assert path.stat().st_size > 1000, "Edited image too small"
    print("  PASSED")
    return path


def test_4_multi_turn_editing(source_path: Path):
    """Test 4: Multi-turn editing — simulate agent iteration loop."""
    print("\n=== Test 4: Multi-turn Editing (2 rounds) ===")

    client = genai.Client(api_key=SETTINGS.GEMINI_API_KEY)

    image_bytes = source_path.read_bytes()
    mime = "image/png" if source_path.suffix == ".png" else "image/jpeg"

    # Round 1: Simplify
    print("  Round 1: Simplify design...")
    response_1 = client.models.generate_content(
        model=MODEL,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=mime),
            types.Part.from_text(text=
                "Simplify this logo further: reduce to 2 colors only, remove any detailed textures, make it work at small sizes like a favicon."
            ),
        ],
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio="1:1"),
        ),
    )

    path_1 = _save_image_from_response(response_1, "test4_round1")
    if path_1 is None:
        print("  Round 1 failed, skipping round 2")
        return

    # Round 2: Color adjustment on round 1 output
    print("  Round 2: Adjust colors...")
    round1_bytes = path_1.read_bytes()
    round1_mime = "image/png" if path_1.suffix == ".png" else "image/jpeg"

    response_2 = client.models.generate_content(
        model=MODEL,
        contents=[
            types.Part.from_bytes(data=round1_bytes, mime_type=round1_mime),
            types.Part.from_text(text=
                "Change the primary color to deep forest green (#2D5016), keep the secondary color as cream (#F5F0E8)."
            ),
        ],
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio="1:1"),
        ),
    )

    path_2 = _save_image_from_response(response_2, "test4_round2")
    assert path_2 is not None, "Round 2 editing failed"
    print("  PASSED — 2 rounds of editing completed")


if __name__ == "__main__":
    print(f"Model: {MODEL}")
    print(f"Output: {OUTPUT_DIR}")

    # Test 1: Generate
    generated_path = test_1_generate_image()

    # Test 2: Generate + text
    test_2_generate_with_text_response()

    # Test 3: Edit
    if generated_path:
        edited_path = test_3_edit_image(generated_path)

        # Test 4: Multi-turn
        if edited_path:
            test_4_multi_turn_editing(edited_path)

    print("\n=== All tests completed ===")
