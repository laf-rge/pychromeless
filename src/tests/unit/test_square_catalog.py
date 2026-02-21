"""Unit tests for square_catalog module."""

from unittest.mock import MagicMock, patch


class TestSquareCatalogInit:
    """Test that SquareCatalog initializes correctly."""

    @patch("square_catalog.SSMParameterStore")
    @patch("square_catalog.Square")
    def test_init_production(self, mock_square_cls, mock_ssm_cls):
        """Production environment uses PRODUCTION Square environment."""
        mock_ssm_instance = MagicMock()
        mock_ssm_instance.__getitem__ = MagicMock(
            return_value=MagicMock(__getitem__=MagicMock(return_value="fake-token"))
        )
        mock_ssm_cls.return_value = mock_ssm_instance

        from square_catalog import SquareCatalog

        _catalog = SquareCatalog(environment="production")

        mock_square_cls.assert_called_once()
        call_kwargs = mock_square_cls.call_args
        assert call_kwargs.kwargs["token"] == "fake-token"

    @patch("square_catalog.SSMParameterStore")
    @patch("square_catalog.Square")
    def test_init_sandbox(self, mock_square_cls, mock_ssm_cls):
        """Sandbox environment uses SANDBOX Square environment."""
        mock_ssm_instance = MagicMock()
        mock_ssm_instance.__getitem__ = MagicMock(
            return_value=MagicMock(__getitem__=MagicMock(return_value="fake-token"))
        )
        mock_ssm_cls.return_value = mock_ssm_instance

        from square.environment import SquareEnvironment

        from square_catalog import SquareCatalog

        _catalog = SquareCatalog(environment="sandbox")

        call_kwargs = mock_square_cls.call_args
        assert call_kwargs.kwargs["environment"] == SquareEnvironment.SANDBOX


class TestSquareCatalogDryRun:
    """Test that dry_run mode prevents API calls."""

    @patch("square_catalog.SSMParameterStore")
    @patch("square_catalog.Square")
    def test_rename_dry_run_no_api_call(self, mock_square_cls, mock_ssm_cls):
        """Dry run rename should not call upsert."""
        mock_ssm_instance = MagicMock()
        mock_ssm_instance.__getitem__ = MagicMock(
            return_value=MagicMock(__getitem__=MagicMock(return_value="fake-token"))
        )
        mock_ssm_cls.return_value = mock_ssm_instance

        mock_client = MagicMock()
        mock_square_cls.return_value = mock_client

        # Mock get_item to return a current item
        mock_retrieve = MagicMock()
        mock_retrieve.object = MagicMock()
        mock_retrieve.object.to_dict.return_value = {
            "id": "ABC123",
            "version": 1,
            "item_data": {"name": "Old Name"},
        }
        mock_client.catalog.retrieve_catalog_object.return_value = mock_retrieve

        from square_catalog import SquareCatalog

        catalog = SquareCatalog(environment="sandbox")
        result = catalog.rename_item("ABC123", "New Name", dry_run=True)

        assert result is None
        mock_client.catalog.upsert_catalog_object.assert_not_called()

    @patch("square_catalog.SSMParameterStore")
    @patch("square_catalog.Square")
    def test_batch_update_dry_run_no_api_call(self, mock_square_cls, mock_ssm_cls):
        """Dry run batch update should not call batch_upsert."""
        mock_ssm_instance = MagicMock()
        mock_ssm_instance.__getitem__ = MagicMock(
            return_value=MagicMock(__getitem__=MagicMock(return_value="fake-token"))
        )
        mock_ssm_cls.return_value = mock_ssm_instance

        mock_client = MagicMock()
        mock_square_cls.return_value = mock_client

        from square_catalog import SquareCatalog

        catalog = SquareCatalog(environment="sandbox")
        updates = [
            {
                "variation_id": "V1",
                "price_cents": 1275,
                "version": 1,
                "name": "#1 BLT Regular",
            },
            {
                "variation_id": "V2",
                "price_cents": 895,
                "version": 1,
                "name": "#1 BLT Mini",
            },
        ]
        result = catalog.batch_update_prices(updates, dry_run=True)

        assert result == []
        mock_client.catalog.batch_upsert_catalog_objects.assert_not_called()
