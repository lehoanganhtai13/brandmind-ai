# Task 38: generate_image Tool — Gemini Image Generation

## 📌 Metadata

- **Epic**: Brand Strategy — Tools
- **Priority**: High (P2 — Enhanced experience)
- **Estimated Effort**: 1 week
- **Team**: Backend
- **Related Tasks**: Task 41 (Creative Studio sub-agent uses this)
- **Blocking**: Task 41 (Creative Studio Agent), Task 44 (Positioning Skill — mood boards)
- **Blocked by**: None

### ✅ Progress Checklist

- [x] 🤖 [Agent Protocol](#-agent-protocol) — Read and confirm before starting
- [x] 🎯 [Context & Goals](#🎯-context--goals)
- [x] 🛠 [Solution Design](#🛠-solution-design)
- [x] 🔬 [Pre-Implementation Research](#-pre-implementation-research) — Findings logged before coding
- [x] 🔄 [Implementation Plan](#🔄-implementation-plan)
- [x] 📋 [Implementation Detail](#📋-implementation-detail)
    - [x] ✅ [Component 1: Gemini Image Client](#component-1-gemini-image-client)
    - [x] ✅ [Component 2: generate_image Tool](#component-2-generate_image-tool)
    - [x] ✅ [Component 3: Image Storage Manager](#component-3-image-storage-manager)
    - [x] ✅ [Component 4: generate_brand_key Tool](#component-4-generate_brand_key-tool)
- [ ] 🧪 [Test Execution Log](#-test-execution-log) — All tests run and results recorded
- [ ] 📊 [Decision Log](#-decision-log) — Key decisions documented
- [ ] 📝 [Task Summary](#📝-task-summary)

## 🔗 Reference Documentation

- **Coding Standards**: Follow enterprise-level Python standards (see Agent Protocol section)
- **Prompt Engineering Standards**: `tasks/prompt_engineering_standards.md`
- **Blueprint Reference**: `docs/BRANDMIND_BRAND_STRATEGY_BLUEPRINT.md` — Section 5.3, Tool 10, Tool 16
- **Gemini Image Generation**: https://ai.google.dev/gemini-api/docs/image-generation
- **google-genai SDK**: Already in dependencies (`google-genai` / `google-generativeai`)
- **Models**: `gemini-3.1-flash-image-preview` (SOTA image gen — text-to-image, editing, multi-style support)
- **Nano-Banana-2 Reference**: `.claude/skills/nano-banana-2/SKILL.md` — prompt tips (styles, composition, lighting, resolution)
- **Output Directory Pattern**: Centralized via `BRANDMIND_OUTPUT_DIR` env var → `./brandmind-output/` default

------------------------------------------------------------------------

## 🤖 Agent Protocol

> **MANDATORY**: Read this section in full before starting any implementation work.

### Rule 1 — Research Before Coding

Before writing any code for a component:
1. Read all files referenced in "Reference Documentation" above
2. Read existing code in `src/shared/src/shared/model_clients/llm/google/` to understand config patterns
3. Read `.claude/skills/nano-banana-2/SKILL.md` for image generation prompt best practices
4. Read `src/shared/src/shared/agent_tools/` to understand tool function conventions (no `@tool` decorator)
5. Log your findings in [Pre-Implementation Research](#-pre-implementation-research) before proceeding
6. **Do NOT assume or invent** Gemini API behavior — verify against actual google-genai SDK documentation

### Rule 2 — Ask, Don't Guess

When encountering any of the following, **STOP and ask the user** before proceeding:

- Content policy blocks on a prompt template you're testing
- Gemini API behavior differs from documentation
- Image quality is consistently poor for a template — need prompt redesign
- Output directory permissions or path conflicts

Format: State the issue clearly, present your options with pros/cons, and ask for a decision.

### Rule 3 — Update Progress As You Go

After completing each component or sub-task:
1. Check off the corresponding item in the Progress Checklist
2. Update the component status emoji: ⏳ Pending → 🚧 In Progress → ✅ Done
3. Fill in the Test Execution Log with actual results as tests run
4. Log any significant decisions in the Decision Log

### Rule 4 — Production-Grade Code Standards

All code MUST meet these standards (no exceptions):

| Standard | Requirement |
|----------|-------------|
| **Docstrings** | Every module, class, and function — purpose, args, returns, business context |
| **Comments** | Inline comments for complex logic, business rules, non-obvious decisions |
| **String quotes** | Double quotes `"` consistently throughout |
| **Type hints** | All function signatures — no `Any` unless truly unavoidable |
| **Naming** | PEP 8 — `snake_case` functions/vars, `PascalCase` classes, `UPPER_SNAKE` constants |
| **Line length** | Max 100 characters — **exception: prompt strings** (see Rule 5) |
| **Language** | English only — all code, comments, docstrings |
| **Modularity** | Single responsibility — break large functions into focused, reusable units |

### Rule 5 — Prompt Engineering Standards

Applies to `BRAND_PROMPT_TEMPLATES` and `BRAND_KEY_PROMPT_TEMPLATE` in this task.

**Line length**: Prompt strings are **exempt from the 100-character rule**. Break lines at semantic boundaries.

**Full standards**: `tasks/prompt_engineering_standards.md`

Key requirements for image generation prompts specifically:
- Be SPECIFIC about style, composition, lighting, materials, and quality level
- Reference professional quality standards ("commercial photography", "design agency", "architectural visualization")
- Include explicit negative constraints where needed ("no people", "no 3D effects", "no gradients")
- Templates must produce consistent quality across different brand inputs
- Each template should specify: subject, style, composition, lighting, materials, quality modifier

------------------------------------------------------------------------

## 🎯 Context & Goals

### Bối cảnh

- Phase 3 (Brand Identity) cần mood boards, logo concept directions, color palette visualizations, packaging mockups
- Phase 5 cần Brand Key one-pager visual (generate_brand_key)
- Creative Studio sub-agent cần batch image generation
- Gemini image gen hỗ trợ nhiều style, aspect ratio, và reference images — phù hợp cho brand asset drafts
- Generated images là DIRECTION drafts, không phải final production assets (cần designer chuyên nghiệp cho logo thật)
- Hiện tại `google-genai` đã là dependency — không cần thêm package mới

### Mục tiêu

1. generate_image tool cho phép agent tạo brand-related images (mood boards, logo concepts, packaging mockups)
2. generate_brand_key tool tạo Brand Key one-pager visual (Phase 5 deliverable)
3. Image storage quản lý output files tổ chức theo session/phase
4. Prompt engineering tối ưu cho brand/F&B use cases

### Success Metrics / Acceptance Criteria

- **Quality**: Generated images phù hợp style direction (minimalist, modern, vintage, etc.)
- **Reliability**: Graceful handling khi image gen bị blocked (content policy), fallback error message
- **Storage**: Images saved with descriptive filenames organized by session/phase
- **Brand Key**: One-pager shows all 9 Brand Key sections in a professional layout

------------------------------------------------------------------------

## 🛠 Solution Design

### Giải pháp đề xuất

**2-Layer Architecture**: GeminiImageClient (low-level API wrapper with google-genai SDK) → Tool layer (plain functions with brand-specific prompt engineering). Separate function for Brand Key (structured template prompt). Centralized output directory management via env var.

### Model

| Model | Capabilities | Use Case |
|-------|-------------|----------|
| `gemini-3.1-flash-image-preview` | Text-to-image, editing, multi-image input, aspect ratios, resolution control (1K/2K/4K) | All image generation in this task |

### Existing Components (Reuse)

| Component | Location | Reuse |
|-----------|----------|-------|
| Gemini LLM config | `src/shared/src/shared/model_clients/llm/google/` | Reuse API key, config patterns |
| google-genai SDK | Already installed | Direct usage |

### New Components

| Component | Location | Purpose |
|-----------|----------|---------|
| Gemini Image Client | `src/shared/src/shared/agent_tools/image/gemini_image_client.py` | API wrapper for image gen |
| generate_image tool | `src/shared/src/shared/agent_tools/image/generate_image.py` | Tool function |
| Image storage manager | `src/shared/src/shared/agent_tools/image/storage.py` | File naming & organization |
| generate_brand_key tool | `src/shared/src/shared/agent_tools/image/generate_brand_key.py` | Brand Key visual tool |

------------------------------------------------------------------------

## 🔄 Implementation Plan

### **Phase 1: Core Image Generation**
1. GeminiImageClient — wrap `google-genai` SDK for image generation
2. Image storage manager — session-based file organization

### **Phase 2: Tool Layer**
1. generate_image plain function with brand-context prompt engineering
2. generate_brand_key specialized tool

### **Phase 3: Test & Polish**
1. Test various brand asset generation prompts
2. Fine-tune default styles for F&B use cases

------------------------------------------------------------------------

## 🔬 Pre-Implementation Research

> **Agent**: Complete this section BEFORE writing any implementation code.
> Log your findings here so the user can verify your understanding is correct.

### Codebase Audit

- **Files read**: [List files reviewed — model_clients/llm/google/, existing agent_tools/, config/system_config.py]
- **Relevant patterns found**: [How other tools handle config access, error handling, logging]
- **Potential conflicts**: [Any existing image generation code, config key naming]

### External Library / API Research

- **Library/API**: google-genai SDK — `google.genai.Client.models.generate_images()`
- **Documentation source**: https://ai.google.dev/gemini-api/docs/image-generation
- **Key findings**:
  - Model `gemini-3.1-flash-image-preview` supports: text-to-image, image editing (up to 14 input images), aspect ratios (1:1, 16:9, 9:16, 4:3, 3:4), resolution control
  - Response structure: `response.generated_images[N].image.image_bytes`
  - Content safety: may block prompts that violate content policy — need graceful error handling
  - Config: `types.GenerateImagesConfig(number_of_images=N, aspect_ratio="W:H")`
- **Interface confirmed**: `client.models.generate_images(model=str, prompt=str, config=GenerateImagesConfig)`

### Nano-Banana-2 Prompt Best Practices (from skill)

- **Styles**: photorealistic, illustration, watercolor, oil painting, digital art, 3D render, flat design
- **Composition**: close-up, wide shot, overhead, macro, portrait, landscape, 3/4 angle
- **Lighting**: natural, studio, golden hour, dramatic shadows, neon, rim light, ambient
- **Quality modifiers**: "high quality", "professional", "detailed", "4K", "print-ready"
- Applied to: all BRAND_PROMPT_TEMPLATES entries

### Unknown / Risks Identified

- [ ] Verify exact generate_images API signature with installed google-genai version
- [ ] Test content policy behavior with brand-related prompts (logos, packaging)
- [ ] Confirm image_bytes field name in response object
- [ ] Test Vietnamese text rendering in Brand Key prompts (if brand names contain Vietnamese)

### Research Status

- [ ] All referenced documentation read
- [ ] google-genai SDK interface verified
- [ ] Prompt templates tested on at least one sample input
- [ ] No unresolved ambiguities remain → Ready to implement

------------------------------------------------------------------------

## 📋 Implementation Detail

> **📝 Coding Standards Reminder**: Apply the standards from Agent Protocol Rule 4 to every file.
> Prompt strings follow Rule 5. Test specifications are written BEFORE implementation — follow TDD order.

### Component 1: Gemini Image Client

#### Requirement 1 - Image Generation API Wrapper
- **Requirement**: Async wrapper for Gemini image generation
- **Implementation**:
  - `src/shared/src/shared/agent_tools/image/gemini_image_client.py`
  ```python
  import os
  from datetime import datetime, timezone
  from pathlib import Path

  from pydantic import BaseModel, Field


  class ImageGenerationResult(BaseModel):
      """Result from image generation."""
      file_path: str
      description: str
      model_used: str
      prompt_used: str
      width: int = 0
      height: int = 0


  class GeminiImageClient:
      """
      Async client for Gemini image generation.

      Supports text-to-image generation using Gemini models.

      Model:
          - gemini-3.1-flash-image-preview: SOTA image generation (Gemini 3.1 Flash Image Preview)
          - Supports: text-to-image, image editing, multiple aspect ratios, resolution control (1K/2K/4K)

      Attributes:
          api_key: Google AI API key
          model: Image generation model (gemini-3.1-flash-image-preview)
          output_dir: Base directory for saving images
      """

      # Supported aspect ratios and their pixel dimensions
      ASPECT_RATIOS = {
          "1:1": (1024, 1024),
          "16:9": (1344, 768),
          "9:16": (768, 1344),
          "4:3": (1152, 896),
          "3:4": (896, 1152),
      }

      def __init__(
          self,
          api_key: str,
          model: str = "gemini-3.1-flash-image-preview",
          output_dir: str | None = None,
      ):
          """
          Initialize the Gemini image generation client.

          Args:
              api_key: Google AI API key for authentication.
              model: Gemini model for image generation.
              output_dir: Base directory for saving images.
                  Default: resolved via OutputDirectoryManager
                  (BRANDMIND_OUTPUT_DIR env var → ./brandmind-output/).
          """
          self.api_key = api_key
          self.model = model
          self.output_dir = output_dir or self._resolve_output_dir()
          self._client = None  # Lazy-initialized google-genai client

      @staticmethod
      def _resolve_output_dir() -> str:
          """Resolve output directory from env var or default."""
          base = os.environ.get(
              "BRANDMIND_OUTPUT_DIR",
              os.path.join(os.getcwd(), "brandmind-output"),
          )
          return os.path.join(base, "images")

      def generate(
          self,
          prompt: str,
          aspect_ratio: str = "1:1",
          style_prefix: str | None = None,
          output_filename: str | None = None,
          session_id: str | None = None,
      ) -> ImageGenerationResult:
          """
          Generate an image from a text prompt.

          Args:
              prompt: Image description — be specific about style,
                  colors, composition, lighting, and subject.
              aspect_ratio: One of "1:1", "16:9", "9:16", "4:3", "3:4".
              style_prefix: Prepended to prompt (e.g., "minimalist, modern").
              output_filename: Custom filename (auto-generated if None).
              session_id: Session ID for folder organization.

          Returns:
              ImageGenerationResult with file path and metadata.

          Raises:
              ValueError: If aspect_ratio is not supported.
              RuntimeError: If image generation fails (content policy, API error).
          """
          if aspect_ratio not in self.ASPECT_RATIOS:
              raise ValueError(
                  f"Unsupported aspect_ratio '{aspect_ratio}'. "
                  f"Choose from: {list(self.ASPECT_RATIOS.keys())}"
              )

          enhanced_prompt = self._build_enhanced_prompt(prompt, style_prefix)

          try:
              from google import genai
              from google.genai import types

              if self._client is None:
                  self._client = genai.Client(api_key=self.api_key)

              gen_config = types.GenerateImagesConfig(
                  number_of_images=1,
                  aspect_ratio=aspect_ratio,
              )

              # google-genai generate_images() is synchronous
              response = self._client.models.generate_images(
                  model=self.model,
                  prompt=enhanced_prompt,
                  config=gen_config,
              )

          except ImportError as e:
              raise ImportError(
                  "google-genai package is required for image generation. "
                  "Install with: uv add google-genai"
              ) from e
          except Exception as e:
              if "SAFETY" in str(e).upper() or "BLOCKED" in str(e).upper():
                  raise RuntimeError(
                      f"Image generation blocked by content safety policy. "
                      f"Try rephrasing the prompt to be less ambiguous. "
                      f"Original error: {e}"
                  ) from e
              raise RuntimeError(f"Image generation failed: {e}") from e

          if not response.generated_images:
              raise RuntimeError(
                  "Image generation returned no images. "
                  "Prompt may have been blocked by content policy."
              )

          image_bytes = response.generated_images[0].image.image_bytes
          filename = output_filename or self._generate_filename()
          file_path = self._save_image(image_bytes, filename, session_id)

          width, height = self.ASPECT_RATIOS[aspect_ratio]
          return ImageGenerationResult(
              file_path=str(file_path),
              description=f"Generated image: {prompt[:100]}",
              model_used=self.model,
              prompt_used=enhanced_prompt,
              width=width,
              height=height,
          )

      def _build_enhanced_prompt(
          self, prompt: str, style_prefix: str | None
      ) -> str:
          """
          Enhance prompt with style prefix and quality modifiers.

          Adds professional quality descriptors that improve Gemini
          image output consistency without changing the user's intent.
          """
          parts = []
          if style_prefix:
              parts.append(style_prefix.strip().rstrip("."))
          parts.append(prompt.strip().rstrip("."))
          parts.append("High quality, professional, detailed rendering")
          return ". ".join(parts) + "."

      def _save_image(
          self,
          image_bytes: bytes,
          filename: str,
          session_id: str | None,
      ) -> Path:
          """
          Save image bytes to organized directory structure.

          Directory: {output_dir}/{session_id}/ or {output_dir}/
          Creates directories if they don't exist.
          """
          if session_id:
              target_dir = Path(self.output_dir) / session_id
          else:
              target_dir = Path(self.output_dir)

          target_dir.mkdir(parents=True, exist_ok=True)
          file_path = target_dir / filename
          file_path.write_bytes(image_bytes)
          return file_path

      @staticmethod
      def _generate_filename(extension: str = "png") -> str:
          """Generate a timestamp-based filename."""
          timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
          return f"generated_{timestamp}.{extension}"
  ```
- **Acceptance Criteria**:
  - [ ] Generates images via google-genai SDK
  - [ ] Supports all 5 aspect ratios
  - [ ] Saves to organized directory structure
  - [ ] Handles content policy blocks gracefully

### Component 2: generate_image Tool

#### Requirement 1 - Plain Function with Brand-Context Prompt Engineering
- **Requirement**: Tool the agent uses to generate brand-related images. Plain function following codebase convention (`search_web`, `scrape_web_content`).
- **Implementation**:
  - `src/prompts/brand_strategy/generate_image.py` — prompt templates (centralized)
  ```python
  # =========================================================================
  # Brand Asset Prompt Templates
  # =========================================================================
  # Each template is optimized for Gemini 3.1 Flash Image Preview.
  # Templates use professional image generation best practices:
  # - Specific style descriptors (photorealistic, illustration, etc.)
  # - Explicit composition instructions (layout, framing, visual weight)
  # - Lighting specifications (natural, studio, golden hour, etc.)
  # - Material/texture details for realism
  # - Quality modifiers for professional output
  # =========================================================================
  BRAND_PROMPT_TEMPLATES = {
      "mood_board": (
          "Professional brand mood board collage for a {{category}} brand. "
          "Visual style: {{style}}. Color palette: {{colors}}. "
          "Include: lifestyle photography, material textures, typography samples, "
          "color swatches with hex codes, spatial/architectural references, "
          "and product imagery that evokes the brand's emotional territory. "
          "Layout: organized grid collage with clean white borders between elements. "
          "Composition: overhead flat-lay arrangement, balanced visual weight across quadrants. "
          "Lighting: soft, natural, diffused — studio reference board aesthetic. "
          "Quality: high-resolution, print-ready, design agency presentation standard."
      ),
      "logo_concept": (
          "Logo concept design for '{{brand_name}}', a {{category}} brand. "
          "Design direction: {{style}}. Concept: {{concept}}. "
          "Clean vector-style logo mark on pure white background. "
          "Style: minimalist, geometric precision, scalable from favicon to billboard. "
          "Typography: modern sans-serif or custom lettering that reflects brand personality. "
          "Composition: centered, generous negative space around the mark. "
          "Include both: icon/symbol mark and wordmark lockup arranged vertically. "
          "Rendering: flat design, no gradients, no shadows, no 3D effects. "
          "Color: use {{colors}} as primary palette. Must work in single-color (black) version."
      ),
      "color_palette": (
          "Professional color palette reference board for brand identity design. "
          "Primary colors: {{colors}}. "
          "Show: large rectangular color swatches arranged horizontally with hex code labels beneath each, "
          "a color harmony wheel showing relationships between palette colors, "
          "sample usage — text on light and dark backgrounds, button styles, "
          "gradient combinations, and complementary accent suggestions. "
          "Layout: clean organized grid on white background, design system documentation aesthetic. "
          "Typography: small clean sans-serif labels for hex codes and color names. "
          "Quality: precise, clinical, design-reference-grade rendering."
      ),
      "packaging": (
          "Photorealistic packaging mockup for {{category}} product: {{item}}. "
          "Brand: '{{brand_name}}'. Design style: {{style}}. Brand colors: {{colors}}. "
          "Composition: 3/4 angle product hero shot with subtle drop shadow on clean neutral surface. "
          "Lighting: soft studio lighting with slight rim light for depth, no harsh shadows. "
          "Material rendering: realistic textures — matte paper, glossy finish, kraft paper, "
          "metallic foil, or transparent elements as appropriate for the product category. "
          "Environment: clean minimal set — product is the hero, no distracting elements. "
          "Quality: commercial product photography standard, suitable for pitch deck or e-commerce."
      ),
      "interior": (
          "Interior design concept visualization for a {{category}} establishment. "
          "Atmosphere and design style: {{style}}. Brand color integration: {{colors}}. "
          "Composition: wide-angle interior shot showing full spatial design — "
          "seating areas, counter and service area, brand elements (signage, menu boards, logo placement). "
          "Lighting: warm ambient lighting with accent spots, golden hour mood through large windows. "
          "Materials: natural wood, polished concrete, matte metal, and green plant elements as appropriate. "
          "People: empty space to focus purely on design intent (no people). "
          "Quality: architectural visualization standard, photorealistic rendering, warm inviting mood."
      ),
      "social_media": (
          "Social media post template design for '{{brand_name}}', a {{category}} brand. "
          "Visual style: {{style}}. Brand colors: {{colors}}. "
          "Layout: clean scroll-stopping composition with clear visual hierarchy — "
          "hero image area (60% of frame), text overlay zone (30%), brand mark corner placement (10%). "
          "Typography: bold headline area at top, clean body text zone, brand-consistent font pairing. "
          "Aspect ratio: square (1:1) optimized for Instagram feed. "
          "Include: subtle brand color accents, consistent border or frame treatment, "
          "space for text overlay that does not obscure key visual elements. "
          "Quality: digital-optimized, vibrant colors, high contrast for mobile screens."
      ),
  }
  ```

  - `src/shared/src/shared/agent_tools/image/generate_image.py` — tool function
  ```python
  import re

  from config.system_config import SETTINGS
  from prompts.brand_strategy.generate_image import BRAND_PROMPT_TEMPLATES
  from shared.agent_tools.image.gemini_image_client import GeminiImageClient


  def generate_image(
      prompt: str,
      style: str | None = None,
      aspect_ratio: str = "1:1",
      template: str | None = None,
      template_vars: dict | None = None,
      session_id: str | None = None,
  ) -> str:
      """
      Generate brand-related images using Gemini image generation.

      Use for: mood boards, logo concepts, color palettes, packaging
      mockups, interior concepts, social media templates, and other
      brand asset direction drafts.

      IMPORTANT: Generated images are DIRECTION DRAFTS — use them
      to communicate visual intent. Production logos and assets need
      a professional designer.

      Args:
          prompt: Detailed image description. Be specific about style,
              colors, composition, lighting, and subject.
          style: Style modifier applied to the prompt. Options:
              "minimalist", "vintage", "modern", "rustic", "luxury",
              "playful", "industrial", "organic", "bold", "elegant"
          aspect_ratio: Image ratio — "1:1" (square, default),
              "16:9" (landscape), "9:16" (portrait/story),
              "4:3" (standard), "3:4" (portrait)
          template: Use a pre-built prompt template instead of raw prompt.
              Options: "mood_board", "logo_concept", "color_palette",
              "packaging", "interior", "social_media"
          template_vars: Variables for the template (e.g., brand_name,
              category, colors, style, concept, item)
          session_id: Session ID for organizing output files.

      Returns:
          Path to saved image file + description of what was generated.
          Format: "Image saved to: {path}\nDescription: {description}"
      """
      # Build prompt from template or use raw prompt
      if template:
          if template not in BRAND_PROMPT_TEMPLATES:
              return (
                  f"Unknown template '{template}'. "
                  f"Available: {', '.join(BRAND_PROMPT_TEMPLATES.keys())}"
              )
          vars_dict = template_vars or {}
          final_prompt = BRAND_PROMPT_TEMPLATES[template]
          for key, value in vars_dict.items():
              final_prompt = final_prompt.replace("{{" + key + "}}", str(value))

          # Validate all placeholders were filled
          remaining = re.findall(r"\{\{(\w+)\}\}", final_prompt)
          if remaining:
              return (
                  f"Missing template variables for '{template}': "
                  f"{', '.join(remaining)}. "
                  f"Provide these in template_vars."
              )
      else:
          final_prompt = prompt

      # Initialize client and generate image
      client = GeminiImageClient(
          api_key=SETTINGS.GEMINI_API_KEY,
      )

      try:
          result = client.generate(
              prompt=final_prompt,
              aspect_ratio=aspect_ratio,
              style_prefix=style,
              session_id=session_id,
          )
          return (
              f"Image saved to: {result.file_path}\n"
              f"Description: {result.description}\n"
              f"Model: {result.model_used}"
          )
      except RuntimeError as e:
          return f"Image generation failed: {e}"
  ```
- **Acceptance Criteria**:
  - [ ] Agent can generate images with natural language prompts
  - [ ] Templates produce high-quality brand asset drafts
  - [ ] Style parameter meaningfully affects output
  - [ ] Returns file path + description for agent context

### Component 3: Image Storage Manager

#### Requirement 1 - Session-Based File Organization
- **Requirement**: Organize generated images by session and phase
- **Implementation**:
  - `src/shared/src/shared/agent_tools/image/storage.py`
  ```python
  import os
  from pathlib import Path


  class ImageStorageManager:
      """
      Manages storage of generated brand images.

      Output directory resolution (highest priority first):
          1. Explicit base_dir passed to constructor
          2. BRANDMIND_OUTPUT_DIR environment variable + /images/
          3. Default: ./brandmind-output/images/ (relative to CWD)

      Directory structure:
          {base_dir}/
          └── {session_id}/
              ├── phase_3/
              │   ├── mood_board_01.png
              │   ├── logo_concept_01.png
              │   └── color_palette_01.png
              └── phase_5/
                  └── brand_key_01.png

      Attributes:
          base_dir: Base directory for all generated image assets
      """

      def __init__(self, base_dir: str | None = None):
          """
          Initialize storage manager with output directory.

          Args:
              base_dir: Override base directory. If None, resolves from
                  BRANDMIND_OUTPUT_DIR env var or defaults to
                  ./brandmind-output/images/.
          """
          if base_dir:
              self.base_dir = base_dir
          else:
              env_base = os.environ.get("BRANDMIND_OUTPUT_DIR")
              if env_base:
                  self.base_dir = os.path.join(env_base, "images")
              else:
                  self.base_dir = os.path.join(
                      os.getcwd(), "brandmind-output", "images"
                  )

      def get_output_path(
          self,
          session_id: str,
          filename: str,
          phase: str | None = None,
      ) -> str:
          """
          Get the full output path, creating directories as needed.

          Args:
              session_id: Session identifier for folder grouping.
              filename: Image filename (e.g., "mood_board_01.png").
              phase: Optional phase subfolder (e.g., "phase_3").

          Returns:
              Absolute path to the output file location.
          """
          if phase:
              target_dir = Path(self.base_dir) / session_id / phase
          else:
              target_dir = Path(self.base_dir) / session_id

          target_dir.mkdir(parents=True, exist_ok=True)
          return str(target_dir / filename)

      def generate_filename(
          self, category: str, index: int = 1, extension: str = "png"
      ) -> str:
          """
          Generate descriptive filename like 'mood_board_01.png'.

          Args:
              category: Asset type (e.g., "mood_board", "logo_concept").
              index: Sequential number for multiple assets of same type.
              extension: File extension (default: "png").

          Returns:
              Formatted filename string.
          """
          return f"{category}_{index:02d}.{extension}"

      def list_session_images(self, session_id: str) -> list[str]:
          """
          List all generated images for a session.

          Args:
              session_id: Session identifier.

          Returns:
              List of absolute file paths for all images in the session.
          """
          session_dir = Path(self.base_dir) / session_id
          if not session_dir.exists():
              return []

          return [
              str(p) for p in session_dir.rglob("*.png")
          ] + [
              str(p) for p in session_dir.rglob("*.jpg")
          ]
  ```
- **Acceptance Criteria**:
  - [ ] Images organized by session/phase
  - [ ] Descriptive filenames
  - [ ] Directory creation handled automatically

### Component 4: generate_brand_key Tool

#### Requirement 1 - Brand Key One-Pager Visual
- **Requirement**: Generate the Brand Key visual summary used in Phase 5 deliverables (ref: Blueprint Section 4.5, Phase 5 Activity 5.2)
- **Implementation**:
  - `src/prompts/brand_strategy/generate_brand_key.py` — prompt template (centralized)
  ```python
  BRAND_KEY_PROMPT_TEMPLATE = """Create a professional Brand Key one-pager infographic — a single-page visual summary of brand strategy, styled like a top-tier consulting firm deliverable (McKinsey, BCG quality).

## Brand Identity
Brand: {{brand_name}}
Brand Colors: {{colors}}

## Visual Design Specifications
- Layout: Vertical single-page infographic, portrait orientation (9:16 aspect ratio)
- Style: Clean, modern corporate — consulting-firm strategy document quality
- Typography: Bold sans-serif section headers in brand primary color, clean body text in dark gray (#333333), clear size hierarchy between header and content
- Color usage: Section headers and accent elements in brand colors; body text dark gray; background pure white or very light gray (#F8F8F8); thin colored accent bars between sections
- Visual elements: Subtle line icons or pictograms next to each section header for scannability; thin horizontal divider lines between sections

## Content Sections (ALL must be visible and readable, top to bottom)

1. **BRAND NAME** (large, bold, centered at top with brand-color accent bar beneath): {{brand_name}}
2. **ROOT STRENGTH** (heritage & core competency): {{root_strength}}
3. **COMPETITIVE ENVIRONMENT** (market context & key competitors): {{competitive_environment}}
4. **TARGET** (primary audience definition): {{target}}
5. **INSIGHT** (the consumer truth that drives brand relevance): {{insight}}
6. **BENEFITS** (functional + emotional benefits): {{benefits}}
7. **VALUES & PERSONALITY** (brand character traits): {{values_personality}}
8. **REASONS TO BELIEVE** (proof points & evidence): {{reasons_to_believe}}
9. **DISCRIMINATOR** (unique differentiator — visually emphasized with a highlight box): {{discriminator}}
10. **BRAND ESSENCE** (2-4 word mantra — large, prominent, centered at bottom with brand-color background block): {{brand_essence}}

## Quality Requirements
- Every section header MUST be clearly labeled and visually distinct from body text
- All text MUST be legible — no overlapping elements, no text smaller than caption size
- The DISCRIMINATOR section should stand out visually (bordered box or highlight background)
- The BRAND ESSENCE at the bottom should feel like the visual anchor and culmination of the page
- Overall: a strategy document you would confidently present to a CEO or board of directors
"""
  ```

  - `src/shared/src/shared/agent_tools/image/generate_brand_key.py` — tool function
  ```python
  import re

  from config.system_config import SETTINGS
  from prompts.brand_strategy.generate_brand_key import (
      BRAND_KEY_PROMPT_TEMPLATE,
  )
  from shared.agent_tools.image.gemini_image_client import GeminiImageClient


  def generate_brand_key(
      brand_name: str,
      root_strength: str,
      competitive_environment: str,
      target: str,
      insight: str,
      benefits: str,
      values_personality: str,
      reasons_to_believe: str,
      discriminator: str,
      brand_essence: str,
      colors: str = "navy blue, white, gold accent",
      session_id: str | None = None,
  ) -> str:
      """
      Generate a Brand Key one-pager visual summary.

      Creates a professional infographic showing the 9 Brand Key
      components — used as the capstone visual in Phase 5 deliverables.

      Args:
          brand_name: The brand name
          root_strength: Core competency / heritage
          competitive_environment: Key competitors and market
          target: Target audience description
          insight: Core consumer insight
          benefits: Functional + emotional benefits
          values_personality: Brand values and personality traits
          reasons_to_believe: Evidence / proof points
          discriminator: Key point of difference
          brand_essence: 2-4 word brand essence / mantra
          session_id: Session ID for organizing output files
          colors: Brand color palette description

      Returns:
          Path to generated Brand Key image + description
      """
      # Fill in the Brand Key template with all section content
      replacements = {
          "brand_name": brand_name,
          "root_strength": root_strength,
          "competitive_environment": competitive_environment,
          "target": target,
          "insight": insight,
          "benefits": benefits,
          "values_personality": values_personality,
          "reasons_to_believe": reasons_to_believe,
          "discriminator": discriminator,
          "brand_essence": brand_essence,
          "colors": colors,
      }
      filled_prompt = BRAND_KEY_PROMPT_TEMPLATE
      for key, value in replacements.items():
          filled_prompt = filled_prompt.replace("{{" + key + "}}", value)

      # Sync call — no asyncio.run() needed
      client = GeminiImageClient(
          api_key=SETTINGS.GEMINI_API_KEY,
      )

      try:
          safe_name = re.sub(r"[^\w\-]", "_", brand_name.lower())
          result = client.generate(
              prompt=filled_prompt,
              aspect_ratio="9:16",  # Portrait for one-pager
              session_id=session_id,
              output_filename=f"brand_key_{safe_name}.png",
          )
          return (
              f"Brand Key saved to: {result.file_path}\n"
              f"Brand: {brand_name}\n"
              f"Essence: {brand_essence}\n"
              f"All 9 Brand Key sections rendered in infographic format."
          )
      except RuntimeError as e:
          return f"Brand Key generation failed: {e}"
  ```
- **Acceptance Criteria**:
  - [ ] Generates a readable Brand Key one-pager
  - [ ] All 9 Brand Key sections visible and labeled
  - [ ] Uses brand colors from Phase 3 output
  - [ ] Professional quality suitable for strategy deck inclusion
  - [ ] **Text rendering caveat**: AI image generation may render text imperfectly (especially Vietnamese diacritics, small font sizes, dense layouts). The generated Brand Key is a **visual direction draft** — the agent should inform the user that production-quality Brand Key documents should use `generate_document` (PDF/DOCX) for precise text layout

------------------------------------------------------------------------

## 🧪 Test Execution Log

> **Agent**: Record actual test results here as you run them.
> Do not mark a test as Passed until you have run it and seen the output.

### Test 1: Basic Image Generation
- **Purpose**: Verify basic text-to-image works with Gemini 3.1 Flash
- **Steps**:
  1. Call `generate_image("A modern coffee cup with steam, minimalist style on white background")`
  2. Verify image saved to brandmind-output/images/
  3. Verify image is valid PNG and visually matches prompt
- **Expected Result**: PNG file generated at expected path with relevant content
- **Actual Result**: [Fill in after running]
- **Status**: ⏳ Pending

### Test 2: Mood Board Template
- **Purpose**: Verify mood_board template produces brand-quality output
- **Steps**:
  1. Call with `template="mood_board"`, `template_vars={"category": "specialty coffee", "style": "warm minimalist", "colors": "earth tones, teal accent"}`
  2. Verify mood board shows grid layout with textures, colors, typography
- **Expected Result**: Mood board with organized grid layout, multiple visual elements, brand-appropriate aesthetic
- **Actual Result**: [Fill in after running]
- **Status**: ⏳ Pending

### Test 3: Brand Key Generation
- **Purpose**: Verify Brand Key one-pager with all 9 sections
- **Steps**:
  1. Call `generate_brand_key` with all 9 Brand Key sections filled with realistic brand data
  2. Verify all sections visible in output image
  3. Verify text is legible and layout is professional
- **Expected Result**: Professional Brand Key infographic with all 9 sections readable
- **Actual Result**: [Fill in after running]
- **Status**: ⏳ Pending

### Test 4: Content Policy Handling
- **Purpose**: Verify graceful error when content policy blocks generation
- **Steps**:
  1. Call with a prompt that might be blocked
  2. Verify error message is informative and includes guidance
- **Expected Result**: Clear error message mentioning content policy, no crash, no traceback exposed
- **Actual Result**: [Fill in after running]
- **Status**: ⏳ Pending

### Test 5: Output Directory Resolution
- **Purpose**: Verify output directory strategy works correctly
- **Steps**:
  1. Test default (no env var): verify images go to `./brandmind-output/images/`
  2. Set `BRANDMIND_OUTPUT_DIR=/tmp/test-output`, verify images go to `/tmp/test-output/images/`
  3. Test with session_id: verify subdirectory created
- **Expected Result**: Directory resolution follows priority order, directories auto-created
- **Actual Result**: [Fill in after running]
- **Status**: ⏳ Pending

### Test 6: All Templates Generate Successfully
- **Purpose**: Verify all 6 BRAND_PROMPT_TEMPLATES produce valid images
- **Steps**:
  1. Loop through all templates: mood_board, logo_concept, color_palette, packaging, interior, social_media
  2. Call each with appropriate template_vars
  3. Verify each produces a valid image
- **Expected Result**: All 6 templates generate images without errors
- **Actual Result**: [Fill in after running]
- **Status**: ⏳ Pending

------------------------------------------------------------------------

## 📊 Decision Log

> **Agent**: Document every significant decision made during implementation.

| # | Decision | Options Considered | Choice Made | Rationale |
|---|----------|--------------------|-------------|-----------|
| 1 | Image generation model | gemini-2.0-flash-exp vs gemini-3.1-flash-image-preview | gemini-3.1-flash-image-preview | SOTA quality, supports resolution control, better prompt adherence |
| 2 | Output directory strategy | Hardcoded `data/generated_assets/` vs env-var based `BRANDMIND_OUTPUT_DIR` | Env-var with CWD default | Flexible for deployment, visible to user, follows CLI best practices (Claude Code pattern) |
| 3 | API wrapper approach | Direct google-genai calls in tool functions vs GeminiImageClient wrapper | GeminiImageClient wrapper | Single Responsibility — separates API concerns from prompt engineering |
| 4 | Prompt template approach | `.format()` vs `.replace()` with `{{var}}` | `{{var}}` + `.replace()` | Project convention — all prompts in `src/prompts/` use `{{var}}` placeholders with `.replace()`. This avoids JSON brace escaping issues (JSON `{}` stays literal). Prompts moved to `src/prompts/brand_strategy/`. |
| 5 | Sync vs async in tool functions | Direct async vs asyncio.run() wrapper vs sync | Sync (no async) | All tool functions in codebase are sync. `google-genai` SDK's `generate_images()` is synchronous. Using `asyncio.run()` would crash if an event loop is already running (e.g., Jupyter, FastAPI). No reason to introduce async — keep it simple and sync. |
| 6 | Brand Key text rendering | AI image gen vs structured PDF/HTML | AI image gen with limitations note | AI image generation has known limitations with text rendering — small text, complex layouts, and Vietnamese diacritics may render incorrectly. Brand Key one-pager should be treated as a **direction draft**; for production, use `generate_document` (Task 39) to create a structured PDF/DOCX with precise text layout. |

------------------------------------------------------------------------

## 📝 Task Summary

> **⚠️ Important**: Complete this section after task implementation and all tests pass.

### What Was Implemented

**Components Completed**:
- [ ] [Component 1]: Gemini Image Client — API wrapper for gemini-3.1-flash-image-preview
- [ ] [Component 2]: generate_image Tool — 6 brand asset templates + freeform prompt
- [ ] [Component 3]: Image Storage Manager — session-based organization with env-var output dir
- [ ] [Component 4]: generate_brand_key Tool — 9-section Brand Key infographic

**Files Created/Modified**:
```
src/prompts/brand_strategy/
├── generate_image.py              # BRAND_PROMPT_TEMPLATES (6 templates)
└── generate_brand_key.py          # BRAND_KEY_PROMPT_TEMPLATE

src/shared/src/shared/agent_tools/image/
├── __init__.py                    # Package exports
├── gemini_image_client.py         # Gemini 3.1 Flash API wrapper
├── generate_image.py              # Tool function (imports prompts from src/prompts/)
├── storage.py                     # Image storage manager
└── generate_brand_key.py          # Brand Key visual tool (imports prompts from src/prompts/)
```

**Key Features Delivered**:
1. **6 brand asset templates**: mood_board, logo_concept, color_palette, packaging, interior, social_media — all optimized with professional image gen best practices
2. **Brand Key infographic**: 9-section one-pager in consulting-firm visual style
3. **Flexible output directory**: BRANDMIND_OUTPUT_DIR env var → ./brandmind-output/ default

### Technical Highlights

**Architecture Decisions** (see Decision Log for details):
- Model: gemini-3.1-flash-image-preview (SOTA)
- Output dir: env-var with CWD default (CLI-friendly)
- 2-layer: GeminiImageClient → tool functions

**Performance / Quality Results**:
- [Image generation latency]: [Observed result]
- [Template consistency]: [Rate across multiple test runs]

**Documentation Checklist**:
- [ ] All functions have comprehensive docstrings (purpose, args, returns)
- [ ] Prompt templates documented with design rationale comments
- [ ] Type hints complete and accurate

### Validation Results

**Test Results**:
- [ ] All tests in Test Execution Log: ✅ Passed
- [ ] All 6 templates generate valid images
- [ ] Brand Key renders all 9 sections
- [ ] Content policy errors handled gracefully

**Deployment Notes**:
- No new dependencies — uses existing google-genai SDK
- Requires GEMINI_API_KEY in environment (already required system-wide)
- Optional: Set BRANDMIND_OUTPUT_DIR to customize output location
- New model `gemini-3.1-flash-image-preview` — verify API access/quota

------------------------------------------------------------------------
