"""Square Catalog Image management.

Handles downloading images from Jersey Mike's website and uploading to Square.
Designed to be used when:
1. Creating new catalog items (attach image during creation)
2. Updating/fixing missing images on existing items

Image URL mappings stored in: wmc-reconcile/data/square-image-urls.json
"""

import json
import logging
import re
import tempfile
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

# Default path to image URL mappings (relative to this file's typical usage)
DEFAULT_IMAGE_URLS_PATH = (
    Path(__file__).parent.parent.parent / "wmc-reconcile/data/square-image-urls.json"
)


class SquareImageManager:
    """Manages image URL lookups and downloads for Square catalog items."""

    def __init__(self, image_urls_path: Path | None = None) -> None:
        """Initialize with path to image URL mappings JSON.

        Args:
            image_urls_path: Path to square-image-urls.json. If None, uses default.
        """
        self._path = image_urls_path or DEFAULT_IMAGE_URLS_PATH
        self._mappings: dict[str, Any] = {}
        self._base_url_sm = ""
        self._base_url_lg = ""
        self._load_mappings()

    def _load_mappings(self) -> None:
        """Load image URL mappings from JSON file."""
        if not self._path.exists():
            logger.warning("Image URL mappings not found: %s", self._path)
            return

        with open(self._path) as f:
            data = json.load(f)

        self._mappings = data
        meta = data.get("_meta", {})
        self._base_url_sm = meta.get("base_url_sm", "")
        self._base_url_lg = meta.get("base_url_lg", "")

        # Count total mappings
        total = sum(
            len(v) for k, v in data.items() if k != "_meta" and isinstance(v, dict)
        )
        logger.info("Loaded %d image mappings from %s", total, self._path)

    def get_image_url(self, item_name: str, size: str = "sm") -> str | None:
        """Look up image URL for an item by name.

        Searches across all categories (cold_subs, hot_subs, etc.) for a match.
        Uses fuzzy matching to handle slight name variations.

        Args:
            item_name: The item name (e.g., "#1 BLT", "Cookie", "Regular Drink & Chips")
            size: "sm" for small images, "lg" for large images

        Returns:
            Full image URL if found, None otherwise.
        """
        normalized = self._normalize_name(item_name)
        base_url = self._base_url_lg if size == "lg" else self._base_url_sm

        # Search all categories
        for category, items in self._mappings.items():
            if category == "_meta" or not isinstance(items, dict):
                continue

            for name, value in items.items():
                if self._normalize_name(name) == normalized:
                    # Handle both simple string values and dict values with file/size
                    if isinstance(value, dict):
                        file_name = value.get("file", "")
                        item_size = value.get("size", "sm")
                        url_base = (
                            self._base_url_lg
                            if item_size == "lg"
                            else self._base_url_sm
                        )
                        return f"{url_base}{file_name}" if file_name else None
                    else:
                        return f"{base_url}{value}" if value else None

        # Try partial matching for numbered subs (e.g., "#1 BLT" matches "BLT")
        for category, items in self._mappings.items():
            if category == "_meta" or not isinstance(items, dict):
                continue

            for name, value in items.items():
                # Check if the item name contains our search term (minus the number prefix)
                search_without_number = re.sub(r"^#?\d+\s*", "", normalized)
                name_without_number = re.sub(
                    r"^#?\d+\s*", "", self._normalize_name(name)
                )

                if (
                    search_without_number
                    and search_without_number == name_without_number
                ):
                    if isinstance(value, dict):
                        file_name = value.get("file", "")
                        item_size = value.get("size", "sm")
                        url_base = (
                            self._base_url_lg
                            if item_size == "lg"
                            else self._base_url_sm
                        )
                        return f"{url_base}{file_name}" if file_name else None
                    else:
                        return f"{base_url}{value}" if value else None

        logger.debug("No image URL found for item: %s", item_name)
        return None

    def download_image(self, url: str) -> tuple[bytes, str] | None:
        """Download an image from a URL.

        Args:
            url: The image URL to download.

        Returns:
            Tuple of (image_bytes, content_type) if successful, None if failed.
        """
        try:
            # Add a user agent to avoid being blocked
            request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(request, timeout=30) as response:
                content_type = response.headers.get("Content-Type", "image/png")
                image_data = response.read()
                logger.info("Downloaded image from %s (%d bytes)", url, len(image_data))
                return (image_data, content_type)
        except HTTPError as e:
            logger.error("HTTP error downloading %s: %s", url, e)
        except URLError as e:
            logger.error("URL error downloading %s: %s", url, e)
        except Exception as e:
            logger.error("Error downloading %s: %s", url, e)
        return None

    def download_image_to_file(
        self, url: str, dest_path: Path | None = None
    ) -> Path | None:
        """Download an image to a temporary or specified file.

        Args:
            url: The image URL to download.
            dest_path: Optional destination path. If None, creates a temp file.

        Returns:
            Path to the downloaded file, or None if failed.
        """
        result = self.download_image(url)
        if not result:
            return None

        image_data, content_type = result

        # Determine file extension
        ext = ".png"
        if "jpeg" in content_type or "jpg" in content_type:
            ext = ".jpg"
        elif "gif" in content_type:
            ext = ".gif"

        if dest_path:
            path = dest_path
        else:
            # Create temp file
            fd, temp_path = tempfile.mkstemp(suffix=ext)
            path = Path(temp_path)
            import os

            os.close(fd)

        path.write_bytes(image_data)
        logger.info("Saved image to %s", path)
        return path

    def get_image_for_item(
        self, item_name: str, size: str = "sm"
    ) -> tuple[bytes, str] | None:
        """Convenience method: look up URL and download image in one step.

        Args:
            item_name: The item name to look up.
            size: "sm" or "lg" for image size preference.

        Returns:
            Tuple of (image_bytes, content_type) if successful, None if not found or failed.
        """
        url = self.get_image_url(item_name, size)
        if not url:
            return None
        return self.download_image(url)

    @staticmethod
    def _normalize_name(name: str) -> str:
        """Normalize item name for matching."""
        return re.sub(r"\s+", " ", name.lower().strip())

    def list_all_mappings(self) -> dict[str, str]:
        """Return a flat dict of all item name -> URL mappings.

        Useful for debugging or displaying available images.
        """
        result: dict[str, str] = {}
        base_sm = self._base_url_sm
        base_lg = self._base_url_lg

        for category, items in self._mappings.items():
            if category == "_meta" or not isinstance(items, dict):
                continue

            for name, value in items.items():
                if isinstance(value, dict):
                    file_name = value.get("file", "")
                    size = value.get("size", "sm")
                    base = base_lg if size == "lg" else base_sm
                    result[name] = f"{base}{file_name}"
                else:
                    result[name] = f"{base_sm}{value}"

        return result
