# backend/app/services/template_manager.py
import json
import logging
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
from pptx import Presentation

logger = logging.getLogger(__name__)


class TemplateManager:
    """Manage PPTX template library"""

    def __init__(self, templates_dir: Optional[Path] = None):
        if templates_dir:
            self.templates_dir = Path(templates_dir)
        else:
            # Try multiple possible locations
            # Updated 2025-11-14: Use ppt_templates directory (9 custom templates)
            possible_paths = [
                Path(__file__).parent.parent.parent.parent / "ppt_templates",  # From project root
                Path("/app") / ".." / "ppt_templates",  # Docker container
                Path.cwd() / "ppt_templates"  # Current directory
            ]
            self.templates_dir = None
            for path in possible_paths:
                if path.exists():
                    self.templates_dir = path
                    break
            if not self.templates_dir:
                # Default to first path even if not exists
                self.templates_dir = possible_paths[0]

        self.metadata_cache: Optional[Dict[str, Any]] = None
        self.logger = logger

    def list_templates(self) -> List[Dict[str, Any]]:
        """
        List all available templates with metadata

        Returns:
            List of template metadata dicts
        """
        if not self.templates_dir.exists():
            self.logger.warning(f"Templates directory not found: {self.templates_dir}")
            return []

        templates = []
        for template_file in self.templates_dir.glob("*.pptx"):
            metadata = self._get_template_metadata(template_file)
            templates.append(metadata)

        return templates

    def get_template_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get template metadata by filename

        Args:
            name: Template filename

        Returns:
            Template metadata or None
        """
        templates = self.list_templates()
        for template in templates:
            if template["filename"] == name:
                return template
        return None

    def get_recommended_template(self, presentation_type: str = "general") -> Optional[str]:
        """
        Get recommended template based on presentation type

        Args:
            presentation_type: Type of presentation (general, modern, standard, swift)
            Note: This method is deprecated for enhancement pipeline.
            Use Presenton built-in templates via API instead.

        Returns:
            Template filename or None
        """
        # Presenton API uses built-in template IDs: general, modern, standard, swift
        # This method is kept for backward compatibility but should not be used
        # for new implementations

        available = self.list_templates()
        if available:
            self.logger.info(f"Found {len(available)} templates in {self.templates_dir}")
            return available[0]["filename"]

        self.logger.warning(f"No templates found in {self.templates_dir}")
        return None

    def _get_template_metadata(self, template_path: Path) -> Dict[str, Any]:
        """
        Extract metadata from template file

        Args:
            template_path: Path to template file

        Returns:
            Template metadata dict
        """
        metadata = {
            "filename": template_path.name,
            "path": str(template_path),
            "valid": False,
            "layout_count": 0,
            "size_bytes": template_path.stat().st_size if template_path.exists() else 0,
            "layouts": []
        }

        try:
            prs = Presentation(str(template_path))
            metadata["valid"] = True
            metadata["layout_count"] = len(prs.slide_layouts)

            for idx, layout in enumerate(prs.slide_layouts):
                layout_info = {
                    "index": idx,
                    "name": layout.name
                }
                metadata["layouts"].append(layout_info)

        except Exception as e:
            self.logger.error(f"Failed to load template {template_path.name}: {e}")
            metadata["error"] = str(e)

        return metadata

    def validate_template(self, template_name_or_path: str) -> Dict[str, Any]:
        """
        Validate template compatibility

        Args:
            template_name_or_path: Template filename or full path

        Returns:
            Validation result dict
        """
        if os.path.isabs(template_name_or_path):
            template_path = Path(template_name_or_path)
        else:
            if "uploaded" in template_name_or_path:
                template_path = self.templates_dir / "uploaded" / template_name_or_path
            else:
                template_path = self.templates_dir / template_name_or_path

        if not template_path.exists():
            return {
                "valid": False,
                "error": "Template file not found"
            }

        try:
            prs = Presentation(str(template_path))

            has_title_layout = False
            has_content_layout = False

            for layout in prs.slide_layouts:
                layout_name_lower = layout.name.lower()
                if "title" in layout_name_lower:
                    has_title_layout = True
                if "content" in layout_name_lower or "body" in layout_name_lower:
                    has_content_layout = True

            return {
                "valid": True,
                "layout_count": len(prs.slide_layouts),
                "has_title_layout": has_title_layout,
                "has_content_layout": has_content_layout,
                "compatible": has_title_layout and has_content_layout
            }

        except Exception as e:
            return {
                "valid": False,
                "error": str(e)
            }

    def save_metadata_cache(self, output_path: Optional[Path] = None):
        """
        Save template metadata to JSON file

        Args:
            output_path: Output file path
        """
        if output_path is None:
            output_path = Path(__file__).parent.parent / "claudedocs" / "template_metadata.json"

        templates = self.list_templates()

        metadata = {
            "templates_dir": str(self.templates_dir),
            "template_count": len(templates),
            "templates": templates
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")

        self.logger.info(f"Saved template metadata to {output_path}")
        return output_path
