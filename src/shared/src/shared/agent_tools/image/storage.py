"""Image storage manager for brand asset organization.

Manages storage of generated brand images with session-based
directory structure and descriptive filenames.
"""

from __future__ import annotations

import os
from pathlib import Path


class ImageStorageManager:
    """Manages storage of generated brand images.

    Output directory resolution (highest priority first):
        1. Explicit base_dir passed to constructor
        2. BRANDMIND_OUTPUT_DIR environment variable + /images/
        3. Default: ./brandmind-output/images/ (relative to CWD)

    Directory structure:
        {base_dir}/
        └── {session_id}/
            ├── phase_3/
            │   ├── mood_board_01.png
            │   └── logo_concept_01.png
            └── phase_5/
                └── brand_key_01.png

    Attributes:
        base_dir: Base directory for all generated image assets.
    """

    def __init__(self, base_dir: str | None = None) -> None:
        """Initialize storage manager with output directory.

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
                self.base_dir = os.path.join(os.getcwd(), "brandmind-output", "images")

    def get_output_path(
        self,
        session_id: str,
        filename: str,
        phase: str | None = None,
    ) -> str:
        """Get the full output path, creating directories as needed.

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
        """Generate descriptive filename like 'mood_board_01.png'.

        Args:
            category: Asset type (e.g., "mood_board", "logo_concept").
            index: Sequential number for multiple assets of same type.
            extension: File extension (default: "png").

        Returns:
            Formatted filename string.
        """
        return f"{category}_{index:02d}.{extension}"

    def list_session_images(self, session_id: str) -> list[str]:
        """List all generated images for a session.

        Args:
            session_id: Session identifier.

        Returns:
            List of absolute file paths for all images in the session.
        """
        session_dir = Path(self.base_dir) / session_id
        if not session_dir.exists():
            return []

        return sorted(
            str(p)
            for p in session_dir.rglob("*")
            if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
        )
