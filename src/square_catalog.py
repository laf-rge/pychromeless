"""Square Catalog API integration for menu/price synchronization.

Used to sync item names and prices from the primary POS (FlexePOS) to
the Square backup POS. Square is used when FlexePOS is down or at events.

Requires: pip install squareup
SSM Parameters: /prod/square/application_id, /prod/square/access_token

SDK v44 method mapping (v42+ rewrite):
  catalog.list(types=...)           - list catalog objects
  catalog.object.get(object_id)     - fetch single object
  catalog.object.upsert(...)        - create/update single object
  catalog.batch_upsert(...)         - bulk create/update
  catalog.search_items(...)         - search items by name/filter
  catalog.images.create(...)        - upload image and attach to item
"""

import logging
from typing import Any, cast

from square import Square
from square.core.api_error import ApiError
from square.environment import SquareEnvironment

from ssm_parameter_store import SSMParameterStore

logger = logging.getLogger(__name__)


class SquareCatalog:
    """Interface to the Square Catalog API for item and price management."""

    def __init__(self, environment: str = "production") -> None:
        parameters = cast(
            "SSMParameterStore", SSMParameterStore(prefix="/prod")["square"]
        )
        self._application_id = str(parameters["application_id"])
        self._access_token = str(parameters["access_token"])

        env = (
            SquareEnvironment.PRODUCTION
            if environment == "production"
            else SquareEnvironment.SANDBOX
        )
        self._client = Square(token=self._access_token, environment=env)
        logger.info(
            "Square client initialized (app=%s, env=%s)",
            self._application_id,
            environment,
        )

    # ---- Read operations ----

    def list_catalog_items(self) -> list[dict[str, Any]]:
        """Fetch all ITEM type objects from the catalog.

        Returns a flat list of catalog objects. Each ITEM contains
        item_data.variations with pricing info.
        """
        items: list[dict[str, Any]] = []
        try:
            for page in self._client.catalog.list(types="ITEM"):
                items.append(self._serialize(page))
        except ApiError as e:
            logger.error("Failed to list catalog: %s", e)
            raise

        logger.info("Fetched %d catalog items", len(items))
        return items

    def get_item(self, object_id: str) -> dict[str, Any]:
        """Fetch a single catalog object by ID."""
        try:
            response = self._client.catalog.object.get(object_id)
        except ApiError as e:
            logger.error("Failed to get item %s: %s", object_id, e)
            raise

        return self._serialize(response.object)

    def search_items_by_name(self, name: str) -> list[dict[str, Any]]:
        """Search catalog items by name prefix."""
        try:
            response = self._client.catalog.search_items(text_filter=name)
        except ApiError as e:
            logger.error("Failed to search items: %s", e)
            raise

        if not response.items:
            return []
        return [self._serialize(item) for item in response.items]

    # ---- Write operations ----

    def rename_item(
        self, object_id: str, new_name: str, *, dry_run: bool = True
    ) -> dict[str, Any] | None:
        """Rename a catalog item.

        Args:
            object_id: The Square catalog object ID for the ITEM.
            new_name: The new display name.
            dry_run: If True, log what would change but don't call the API.

        Returns:
            Updated catalog object, or None if dry_run.
        """
        try:
            detail = self._client.catalog.object.get(object_id)
        except ApiError as e:
            logger.error("Failed to get item %s: %s", object_id, e)
            raise

        obj = detail.object
        old_name = obj.item_data.name if obj.item_data else ""

        if old_name == new_name:
            logger.info("Item %s already named '%s', skipping", object_id, new_name)
            return self._serialize(obj)

        if dry_run:
            logger.info(
                "[DRY RUN] Would rename '%s' -> '%s' (id=%s)",
                old_name,
                new_name,
                object_id,
            )
            return None

        # Must include full item_data (with variations) or Square rejects the upsert
        item_data = obj.item_data.dict()
        item_data["name"] = new_name

        try:
            response = self._client.catalog.object.upsert(
                idempotency_key=self._idempotency_key(),
                object={
                    "type": "ITEM",
                    "id": object_id,
                    "version": obj.version,
                    "item_data": item_data,
                },
            )
        except ApiError as e:
            logger.error("Failed to rename item %s: %s", object_id, e)
            raise

        logger.info("Renamed '%s' -> '%s' (id=%s)", old_name, new_name, object_id)
        return self._serialize(response.catalog_object)

    def update_variation_price(
        self,
        variation_id: str,
        price_cents: int,
        *,
        version: int,
        dry_run: bool = True,
    ) -> dict[str, Any] | None:
        """Update the price of a single item variation.

        Args:
            variation_id: The Square catalog object ID for the ITEM_VARIATION.
            price_cents: New price in cents (e.g., 1275 for $12.75).
            version: Current version of the object (for optimistic concurrency).
            dry_run: If True, log what would change but don't call the API.

        Returns:
            Updated catalog object, or None if dry_run.
        """
        if dry_run:
            logger.info(
                "[DRY RUN] Would update variation %s to $%.2f",
                variation_id,
                price_cents / 100,
            )
            return None

        try:
            response = self._client.catalog.object.upsert(
                idempotency_key=self._idempotency_key(),
                object={
                    "type": "ITEM_VARIATION",
                    "id": variation_id,
                    "version": version,
                    "item_variation_data": {
                        "pricing_type": "FIXED_PRICING",
                        "price_money": {
                            "amount": price_cents,
                            "currency": "USD",
                        },
                    },
                },
            )
        except ApiError as e:
            logger.error("Failed to update price for %s: %s", variation_id, e)
            raise

        logger.info("Updated variation %s to $%.2f", variation_id, price_cents / 100)
        return self._serialize(response.catalog_object)

    def batch_update_prices(
        self,
        updates: list[dict[str, Any]],
        *,
        dry_run: bool = True,
    ) -> list[dict[str, Any]]:
        """Batch update prices for multiple variations.

        Fetches each variation's full object first, then merges just the price
        change to avoid issues with Item Options and location settings.

        Args:
            updates: List of dicts with keys:
                - variation_id: Square catalog object ID
                - price_cents: New price in cents
                - name: Display name (for logging)
            dry_run: If True, log what would change but don't call the API.

        Returns:
            List of updated catalog objects (empty if dry_run).
        """
        if dry_run:
            for u in updates:
                logger.info(
                    "[DRY RUN] %s -> $%.2f",
                    u.get("name", u["variation_id"]),
                    u["price_cents"] / 100,
                )
            return []

        # Fetch all variations in one batch to get their full data
        variation_ids = [u["variation_id"] for u in updates]
        logger.info("Fetching %d variations for price update...", len(variation_ids))

        # Batch retrieve (up to 1000 at a time)
        RETRIEVE_BATCH_SIZE = 1000
        all_objects: dict[str, Any] = {}

        for i in range(0, len(variation_ids), RETRIEVE_BATCH_SIZE):
            batch_ids = variation_ids[i : i + RETRIEVE_BATCH_SIZE]
            try:
                response = self._client.catalog.batch_get(object_ids=batch_ids)
            except ApiError as e:
                logger.error("Batch retrieve failed at offset %d: %s", i, e)
                raise

            if response.objects:
                for obj in response.objects:
                    all_objects[obj.id] = obj

        # Build update objects with full data, only changing price
        price_map = {u["variation_id"]: u["price_cents"] for u in updates}
        name_map = {
            u["variation_id"]: u.get("name", u["variation_id"]) for u in updates
        }

        UPSERT_BATCH_SIZE = 1000
        results: list[dict[str, Any]] = []

        update_objects = []
        for var_id, new_price_cents in price_map.items():
            obj = all_objects.get(var_id)
            if not obj:
                logger.warning("Variation %s not found, skipping", var_id)
                continue

            # Deep convert to dict using model_dump() for Pydantic v2
            if hasattr(obj, "model_dump"):
                obj_dict = obj.model_dump(mode="json", exclude_none=True)
            elif hasattr(obj, "dict"):
                obj_dict = obj.dict(exclude_none=True)
            else:
                obj_dict = self._serialize(obj)

            # Ensure item_variation_data is a mutable dict
            var_data = dict(obj_dict.get("item_variation_data", {}))
            var_data["price_money"] = {
                "amount": new_price_cents,
                "currency": "USD",
            }
            var_data["pricing_type"] = "FIXED_PRICING"
            obj_dict["item_variation_data"] = var_data

            update_objects.append(obj_dict)

        # Batch upsert
        for i in range(0, len(update_objects), UPSERT_BATCH_SIZE):
            batch = update_objects[i : i + UPSERT_BATCH_SIZE]
            try:
                response = self._client.catalog.batch_upsert(
                    idempotency_key=self._idempotency_key(),
                    batches=[{"objects": batch}],
                )
            except ApiError as e:
                logger.error("Batch upsert failed at offset %d: %s", i, e)
                raise

            if response.objects:
                results.extend([self._serialize(obj) for obj in response.objects])

            logger.info("Batch updated %d variations (offset %d)", len(batch), i)

        return results

    # ---- Create operations ----

    def create_item(
        self,
        name: str,
        variations: list[dict[str, Any]],
        *,
        category_id: str | None = None,
        description: str = "",
        image_data: bytes | None = None,
        image_url: str | None = None,
        dry_run: bool = True,
    ) -> dict[str, Any] | None:
        """Create a new catalog item with variations.

        Args:
            name: Item name (e.g., "Kids Sub").
            variations: List of variation dicts with keys:
                - name: Variation name (e.g., "Regular", "Kids Sub Size")
                - price_cents: Price in cents (e.g., 339 for $3.39)
            category_id: Optional category ID to assign the item to.
            description: Optional item description.
            image_data: Optional raw image bytes to upload and attach.
            image_url: Optional URL to download image from and attach.
                       (Only used if image_data is not provided)
            dry_run: If True, log what would happen but don't call the API.

        Returns:
            The created catalog item object, or None if dry_run.
        """
        if dry_run:
            var_str = ", ".join(
                f"{v['name']}: ${v['price_cents'] / 100:.2f}" for v in variations
            )
            image_msg = ""
            if image_data:
                image_msg = f" with image ({len(image_data)} bytes)"
            elif image_url:
                image_msg = " with image from URL"
            logger.info(
                "[DRY RUN] Would create item '%s' [%s]%s", name, var_str, image_msg
            )
            return None

        # Build the item object
        item_id = f"#temp-item-{self._idempotency_key()[:8]}"

        variation_objects = []
        for i, var in enumerate(variations):
            var_id = f"#temp-var-{i}-{self._idempotency_key()[:8]}"
            variation_objects.append(
                {
                    "type": "ITEM_VARIATION",
                    "id": var_id,
                    "item_variation_data": {
                        "item_id": item_id,
                        "name": var["name"],
                        "pricing_type": "FIXED_PRICING",
                        "price_money": {
                            "amount": var["price_cents"],
                            "currency": "USD",
                        },
                    },
                }
            )

        item_data: dict[str, Any] = {
            "name": name,
            "variations": variation_objects,
        }

        if description:
            item_data["description"] = description

        if category_id:
            item_data["category_id"] = category_id

        try:
            response = self._client.catalog.object.upsert(
                idempotency_key=self._idempotency_key(),
                object={
                    "type": "ITEM",
                    "id": item_id,
                    "item_data": item_data,
                },
            )
        except ApiError as e:
            logger.error("Failed to create item '%s': %s", name, e)
            raise

        created_item = response.catalog_object
        logger.info("Created item '%s' (id=%s)", name, created_item.id)

        # Upload and attach image if provided
        if image_data or image_url:
            try:
                if image_data:
                    self.upload_image(
                        image_data,
                        object_id=created_item.id,
                        image_name=name,
                        dry_run=False,
                    )
                elif image_url:
                    self.upload_image_from_url(
                        image_url,
                        object_id=created_item.id,
                        image_name=name,
                        dry_run=False,
                    )
            except Exception as e:
                # Log but don't fail the item creation
                logger.warning("Failed to attach image to '%s': %s", name, e)

        return self._serialize(created_item)

    # ---- Delete operations ----

    def delete_catalog_object(self, object_id: str, *, dry_run: bool = True) -> bool:
        """Delete a single catalog object.

        Args:
            object_id: The Square catalog object ID to delete.
            dry_run: If True, log what would be deleted but don't call the API.

        Returns:
            True if deleted (or would be deleted in dry_run), False if object not found.
        """
        if dry_run:
            logger.info("[DRY RUN] Would delete object %s", object_id)
            return True

        try:
            self._client.catalog.object.delete(object_id)
        except ApiError as e:
            if e.status_code == 404:
                logger.warning("Object %s not found, skipping delete", object_id)
                return False
            logger.error("Failed to delete object %s: %s", object_id, e)
            raise

        logger.info("Deleted object %s", object_id)
        return True

    def batch_delete_catalog_objects(
        self, object_ids: list[str], *, dry_run: bool = True
    ) -> list[str]:
        """Batch delete multiple catalog objects.

        Args:
            object_ids: List of Square catalog object IDs to delete.
            dry_run: If True, log what would be deleted but don't call the API.

        Returns:
            List of successfully deleted object IDs.
        """
        if not object_ids:
            return []

        if dry_run:
            for oid in object_ids:
                logger.info("[DRY RUN] Would delete object %s", oid)
            return []

        # Square batch delete accepts up to 200 objects per request
        BATCH_SIZE = 200
        deleted: list[str] = []

        for i in range(0, len(object_ids), BATCH_SIZE):
            batch = object_ids[i : i + BATCH_SIZE]
            try:
                response = self._client.catalog.batch_delete(object_ids=batch)
            except ApiError as e:
                logger.error("Batch delete failed at offset %d: %s", i, e)
                raise

            if response.deleted_object_ids:
                deleted.extend(response.deleted_object_ids)

            logger.info("Batch deleted %d objects (offset %d)", len(batch), i)

        return deleted

    # ---- Image operations ----

    def upload_image(
        self,
        image_data: bytes,
        *,
        object_id: str | None = None,
        image_name: str = "item-image",
        content_type: str = "image/png",
        dry_run: bool = True,
    ) -> dict[str, Any] | None:
        """Upload an image to Square and optionally attach it to a catalog object.

        Args:
            image_data: Raw image bytes to upload.
            object_id: Optional catalog object ID to attach image to.
                       If provided, the image will be linked to this item.
            image_name: A name/caption for the image (for Square dashboard).
            content_type: MIME type of the image (image/png, image/jpeg, etc.).
            dry_run: If True, log what would happen but don't call the API.

        Returns:
            The created CatalogImage object, or None if dry_run.
        """
        if dry_run:
            attach_msg = f" and attach to {object_id}" if object_id else ""
            logger.info(
                "[DRY RUN] Would upload image '%s' (%d bytes)%s",
                image_name,
                len(image_data),
                attach_msg,
            )
            return None

        # Determine file extension for the filename
        ext = ".png"
        if "jpeg" in content_type or "jpg" in content_type:
            ext = ".jpg"
        elif "gif" in content_type:
            ext = ".gif"

        try:
            # Build the image request
            image_id = f"#temp-{self._idempotency_key()[:8]}"

            request_data: dict[str, Any] = {
                "idempotency_key": self._idempotency_key(),
                "image": {
                    "type": "IMAGE",
                    "id": image_id,
                    "image_data": {
                        "name": image_name,
                        "caption": image_name,
                    },
                },
            }

            # If attaching to an object, specify it
            if object_id:
                request_data["object_id"] = object_id

            # Use the catalog images create endpoint with file upload
            # Pass as tuple: (filename, content, content_type)
            response = self._client.catalog.images.create(
                request=request_data,
                image_file=(f"{image_name}{ext}", image_data, content_type),
            )

            if response.image:
                logger.info(
                    "Uploaded image '%s' (id=%s)%s",
                    image_name,
                    response.image.id,
                    f" attached to {object_id}" if object_id else "",
                )
                return self._serialize(response.image)

            logger.warning("Image upload returned no image object")
            return None

        except ApiError as e:
            logger.error("Failed to upload image '%s': %s", image_name, e)
            raise

    def upload_image_from_url(
        self,
        url: str,
        *,
        object_id: str | None = None,
        image_name: str = "item-image",
        dry_run: bool = True,
    ) -> dict[str, Any] | None:
        """Download an image from URL and upload it to Square.

        Convenience method that combines download and upload.

        Args:
            url: URL to download image from.
            object_id: Optional catalog object ID to attach image to.
            image_name: A name/caption for the image.
            dry_run: If True, log what would happen but don't call the API.

        Returns:
            The created CatalogImage object, or None if dry_run or download failed.
        """
        if dry_run:
            attach_msg = f" and attach to {object_id}" if object_id else ""
            logger.info(
                "[DRY RUN] Would download from %s and upload as '%s'%s",
                url,
                image_name,
                attach_msg,
            )
            return None

        # Download the image
        from urllib.error import HTTPError, URLError
        from urllib.request import Request, urlopen

        try:
            request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(request, timeout=30) as response:
                content_type = response.headers.get("Content-Type", "image/png")
                image_data = response.read()
                logger.info("Downloaded image from %s (%d bytes)", url, len(image_data))
        except (HTTPError, URLError) as e:
            logger.error("Failed to download image from %s: %s", url, e)
            return None

        return self.upload_image(
            image_data,
            object_id=object_id,
            image_name=image_name,
            content_type=content_type,
            dry_run=False,  # Already checked dry_run above
        )

    def attach_image_to_item(
        self,
        image_id: str,
        item_id: str,
        *,
        dry_run: bool = True,
    ) -> dict[str, Any] | None:
        """Attach an existing image to a catalog item.

        Use this when you have an image already uploaded and want to
        link it to a different or additional item.

        Args:
            image_id: The Square IMAGE object ID.
            item_id: The Square ITEM object ID to attach to.
            dry_run: If True, log what would happen but don't call the API.

        Returns:
            The updated item object, or None if dry_run.
        """
        if dry_run:
            logger.info("[DRY RUN] Would attach image %s to item %s", image_id, item_id)
            return None

        # Fetch the item to get current data
        try:
            detail = self._client.catalog.object.get(item_id)
        except ApiError as e:
            logger.error("Failed to get item %s: %s", item_id, e)
            raise

        obj = detail.object
        item_data = (
            obj.item_data.dict()
            if hasattr(obj.item_data, "dict")
            else dict(obj.item_data)
        )

        # Add the image ID to the item's image_ids list
        current_image_ids = item_data.get("image_ids", []) or []
        if image_id not in current_image_ids:
            current_image_ids.append(image_id)
        item_data["image_ids"] = current_image_ids

        try:
            response = self._client.catalog.object.upsert(
                idempotency_key=self._idempotency_key(),
                object={
                    "type": "ITEM",
                    "id": item_id,
                    "version": obj.version,
                    "item_data": item_data,
                },
            )
        except ApiError as e:
            logger.error("Failed to attach image to item %s: %s", item_id, e)
            raise

        logger.info("Attached image %s to item %s", image_id, item_id)
        return self._serialize(response.catalog_object)

    def get_item_images(self, item_id: str) -> list[str]:
        """Get the image IDs attached to a catalog item.

        Args:
            item_id: The Square ITEM object ID.

        Returns:
            List of image IDs, or empty list if none.
        """
        try:
            detail = self._client.catalog.object.get(item_id)
        except ApiError as e:
            logger.error("Failed to get item %s: %s", item_id, e)
            raise

        item_data = detail.object.item_data
        if not item_data:
            return []

        image_ids = getattr(item_data, "image_ids", None) or []
        return list(image_ids)

    # ---- Helpers ----

    @staticmethod
    def _idempotency_key() -> str:
        import uuid

        return str(uuid.uuid4())

    @staticmethod
    def _serialize(obj: Any) -> dict[str, Any]:
        """Convert a Square SDK object to a plain dict."""
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        return dict(obj)
