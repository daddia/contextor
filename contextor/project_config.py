"""Advanced configuration management for Contextor"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger()


class ProjectConfig:
    """Represents a project configuration in Context7 format."""

    def __init__(self, config_data: dict[str, Any]):
        """Initialize project configuration from JSON data.

        Args:
            config_data: Dictionary containing the project configuration
        """
        self.settings = config_data.get("settings", {})
        self.tags = config_data.get("tags", {})

    @property
    def title(self) -> str:
        """Get project title."""
        return self.settings.get("title", "Unknown Project")

    @property
    def repo_url(self) -> str:
        """Get repository URL."""
        return self.settings.get("docsRepoUrl", "")

    @property
    def project_path(self) -> str:
        """Get project path (e.g., '/vercel/next.js')."""
        return self.settings.get("project", "")

    @property
    def branch(self) -> str:
        """Get default branch."""
        return self.settings.get("branch", "main")

    @property
    def folders(self) -> list[str]:
        """Get list of folders to include."""
        return self.settings.get("folders", [])

    @property
    def exclude_folders(self) -> list[str]:
        """Get list of folders to exclude."""
        return self.settings.get("excludeFolders", [])

    @property
    def exclude_files(self) -> list[str]:
        """Get list of files to exclude."""
        return self.settings.get("excludeFiles", [])

    @property
    def topics(self) -> list[str]:
        """Get list of topics."""
        return self.settings.get("topics", [])

    @property
    def profile(self) -> str:
        """Get optimization profile."""
        return self.settings.get("profile", "balanced")

    @property
    def transforms(self) -> dict[str, Any]:
        """Get transform configuration."""
        return self.settings.get("transforms", {})

    @property
    def description(self) -> str:
        """Get project description."""
        return self.settings.get("description", "")

    @property
    def is_approved(self) -> bool:
        """Check if project is approved."""
        return self.settings.get("approved", False)

    @property
    def trust_score(self) -> int:
        """Get trust score."""
        return self.settings.get("trustScore", 0)

    @property
    def is_vip(self) -> bool:
        """Check if project is VIP."""
        return self.settings.get("vip", False)

    def to_legacy_format(self) -> dict[str, Any]:
        """Convert to legacy YAML-style configuration format.

        Returns:
            Dictionary in the old YAML configuration format
        """
        # Build include patterns from folders
        include_patterns = []
        if self.folders:
            for folder in self.folders:
                include_patterns.extend(
                    [
                        f"{folder}/*.md",  # Files directly in the folder
                        f"{folder}/**/*.md",  # Files in subfolders
                        f"{folder}/*.mdx",  # MDX files directly in the folder
                        f"{folder}/**/*.mdx",  # MDX files in subfolders
                    ]
                )
        else:
            include_patterns = ["**/*.md", "**/*.mdx"]

        # Build exclude patterns
        exclude_patterns = []

        # Add folder exclusions
        for folder in self.exclude_folders:
            exclude_patterns.append(f"{folder}/**")

        # Add file exclusions
        exclude_patterns.extend(self.exclude_files)

        # Add common exclusions
        exclude_patterns.extend(
            [
                "node_modules/**",
                ".git/**",
                "dist/**",
                "build/**",
                ".next/**",
                ".nuxt/**",
                ".vite/**",
                ".turbo/**",
                "coverage/**",
                "__pycache__/**",
                "*.min.js",
                "*.min.css",
            ]
        )

        return {
            "include": include_patterns,
            "exclude": exclude_patterns,
            "default_topics": self.topics,
            "default_profile": self.profile,
            "transforms": self.transforms,
        }


class ProjectConfigManager:
    """Manages project configurations."""

    def __init__(self, config_dir: Path | None = None):
        """Initialize configuration manager.

        Args:
            config_dir: Directory containing project configurations
        """
        self.config_dir = (
            config_dir or Path(__file__).parent.parent / "config" / "projects"
        )
        self._configs_cache: dict[str, ProjectConfig] = {}

    def load_project_config(self, project_name: str) -> ProjectConfig | None:
        """Load a project configuration by name.

        Args:
            project_name: Name of the project (e.g., 'nextjs', 'react')

        Returns:
            ProjectConfig instance or None if not found
        """
        if project_name in self._configs_cache:
            return self._configs_cache[project_name]

        config_path = self.config_dir / f"{project_name}.json"

        if not config_path.exists():
            logger.warning(
                "Project configuration not found",
                project=project_name,
                path=config_path,
            )
            return None

        try:
            with open(config_path, encoding="utf-8") as f:
                config_data = json.load(f)

            config = ProjectConfig(config_data)
            self._configs_cache[project_name] = config

            logger.info(
                "Loaded project configuration", project=project_name, title=config.title
            )
            return config

        except Exception as e:
            logger.error(
                "Failed to load project configuration",
                project=project_name,
                path=config_path,
                error=str(e),
            )
            return None

    def list_available_projects(self) -> list[str]:
        """List all available project configurations.

        Returns:
            List of project names
        """
        if not self.config_dir.exists():
            return []

        projects = []
        for config_file in self.config_dir.glob("*.json"):
            projects.append(config_file.stem)

        return sorted(projects)

    def get_project_by_repo(self, repo_path: str) -> ProjectConfig | None:
        """Find project configuration by repository path.

        Args:
            repo_path: Repository path like 'vercel/next.js'

        Returns:
            ProjectConfig instance or None if not found
        """
        # Normalize repo path
        if not repo_path.startswith("/"):
            repo_path = f"/{repo_path}"

        for project_name in self.list_available_projects():
            config = self.load_project_config(project_name)
            if config and config.project_path == repo_path:
                return config

        return None

    def create_project_config(
        self, project_name: str, config_data: dict[str, Any]
    ) -> bool:
        """Create a new project configuration.

        Args:
            project_name: Name for the new project
            config_data: Configuration data in Context7 format

        Returns:
            True if created successfully, False otherwise
        """
        config_path = self.config_dir / f"{project_name}.json"

        try:
            # Ensure directory exists
            self.config_dir.mkdir(parents=True, exist_ok=True)

            # Write configuration
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2)

            # Clear cache
            self._configs_cache.pop(project_name, None)

            logger.info(
                "Created project configuration", project=project_name, path=config_path
            )
            return True

        except Exception as e:
            logger.error(
                "Failed to create project configuration",
                project=project_name,
                path=config_path,
                error=str(e),
            )
            return False

    def sync_with_standards_config(
        self, config_path: Path, project_name: str
    ) -> ProjectConfig | None:
        """Synchronize with upstream standards-based config file.

        Args:
            config_path: Path to the standards config file in the source repository
            project_name: Name to use for the project configuration

        Returns:
            ProjectConfig instance if successful, None otherwise
        """
        try:
            # Read the upstream standards config file
            with open(config_path, encoding="utf-8") as f:
                config_data_raw = json.load(f)

            logger.info(
                "Found standards-based config file",
                path=config_path,
                project=project_name,
            )

            # Convert format to our internal format if needed
            # Standards format should already be compatible, but we may need to add our extensions
            if "settings" not in config_data_raw:
                # If it's a raw format, wrap it
                config_data = {"settings": config_data_raw, "tags": {}}
            else:
                config_data = config_data_raw

            # Add sync metadata
            config_data["settings"]["_sync"] = {
                "source_file": str(config_path),
                "synced_at": datetime.utcnow().isoformat() + "Z",
                "auto_detected": True,
            }

            # Determine project name from config data if not provided
            if project_name == "detected":
                # Try to infer from title or repo
                title = config_data["settings"].get("title", "")
                repo = (
                    config_data["settings"]
                    .get("project", "")
                    .lstrip("/")
                    .split("/")[-1]
                )
                project_name = title.lower().replace(" ", "").replace(
                    ".", ""
                ) or repo.lower().replace("-", "").replace("_", "")

            # Save/update our local copy
            local_config_path = self.config_dir / f"{project_name}.json"

            # Check if we need to update (compare timestamps or content)
            should_update = True
            if local_config_path.exists():
                try:
                    with open(local_config_path, encoding="utf-8") as f:
                        existing_data = json.load(f)

                    # Compare core settings (ignoring sync metadata)
                    existing_settings = {
                        k: v
                        for k, v in existing_data.get("settings", {}).items()
                        if not k.startswith("_")
                    }
                    new_settings = {
                        k: v
                        for k, v in config_data["settings"].items()
                        if not k.startswith("_")
                    }

                    if existing_settings == new_settings:
                        logger.info(
                            "Standards configuration unchanged", project=project_name
                        )
                        should_update = False
                    else:
                        logger.info(
                            "Standards configuration updated", project=project_name
                        )

                except Exception as e:
                    logger.warning("Failed to compare existing config", error=str(e))

            if should_update:
                # Ensure directory exists
                self.config_dir.mkdir(parents=True, exist_ok=True)

                # Write updated configuration
                with open(local_config_path, "w", encoding="utf-8") as f:
                    json.dump(config_data, f, indent=2)

                logger.info(
                    "Synchronized standards-based configuration",
                    project=project_name,
                    source=config_path,
                    target=local_config_path,
                )

            # Clear cache and return new config
            self._configs_cache.pop(project_name, None)
            return self.load_project_config(project_name)

        except Exception as e:
            logger.error(
                "Failed to sync with standards config file",
                path=config_path,
                project=project_name,
                error=str(e),
            )
            return None

    def detect_and_sync_standards_config(
        self, source_dir: Path, project_name: str = "detected"
    ) -> ProjectConfig | None:
        """Detect and sync with standards-based config files in a source directory.

        Args:
            source_dir: Directory to search for standards config files
            project_name: Name to use for the project configuration

        Returns:
            ProjectConfig instance if found and synced, None otherwise
        """
        # Define config file names to search for
        config_filenames = ["context7.json"]  # Can be extended for other standards

        # Search locations in order of preference
        search_paths = []
        for filename in config_filenames:
            search_paths.extend(
                [
                    source_dir / filename,  # In the source directory itself
                    source_dir.parent
                    / filename,  # In the parent directory (common for docs subdirs)
                    source_dir / ".context7" / filename,  # In a .context7 subdirectory
                ]
            )

        # Also check if source_dir is a docs directory and look in parent
        if source_dir.name in ["docs", "documentation", "doc"]:
            for filename in config_filenames:
                search_paths.insert(-1, source_dir.parent / filename)

        config_path = None
        for path in search_paths:
            if path.exists():
                config_path = path
                break

        if not config_path:
            logger.debug(
                "No standards config files found",
                source_dir=source_dir,
                searched=search_paths,
            )
            return None

        return self.sync_with_standards_config(config_path, project_name)
