import io
import json
import logging
import re
from collections import defaultdict
from typing import cast

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload
from ssm_parameter_store import SSMParameterStore
from PyPDF2 import PdfMerger
from googleapiclient.http import MediaIoBaseDownload

logger = logging.getLogger(__name__)


class WMCGdrive:
    def __init__(self):
        self._parameters = cast(
            SSMParameterStore, SSMParameterStore(prefix="/prod")["gcp"]
        )
        gdrive_json = json.loads(cast(str, self._parameters["gdrive"]))

        scopes_list = [
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/drive.file",
        ]

        self._credentials = service_account.Credentials.from_service_account_info(
            gdrive_json, scopes=scopes_list
        )
        self._journal_folder_id = cast(str, self._parameters["journal_folder"])
        self._employees_folder_id = cast(str, self._parameters["employees_folder"])
        self._service = build("drive", "v3", credentials=self._credentials)

    def upload(self, filename, content, mime_type):
        file_metadata = {
            "name": filename,
            "parents": [self._journal_folder_id],
            "mimeType": mime_type,
        }

        media = MediaIoBaseUpload(
            io.BytesIO(content), mimetype=mime_type, resumable=True
        )
        results, existing = self.retrieve_all_files(filename)
        if existing is not None:
            request = (
                self._service.files()
                .update(fileId=existing["id"], media_body=media, supportsAllDrives=True)
                .execute()
            )
        else:
            request = (
                self._service.files()
                .create(
                    body=file_metadata,
                    media_body=media,
                    fields="id",
                    supportsAllDrives=True,
                )
                .execute()
            )

        logger.info("Upload Complete!")
        logger.info(request)

    def retrieve_all_files(self, filename_to_search, folder_id=None):
        results = []
        if folder_id is None:
            folder_id = self._journal_folder_id

        results = self._paginated_file_list(
            {
                "q": "'" + folder_id + "' in parents",
                "supportsAllDrives": True,
                "includeItemsFromAllDrives": True,
                "fields": "nextPageToken, files(id, name)",
            }
        )

        # output the file metadata to console
        file = None
        for file in results:
            if file.get("name") == filename_to_search:
                logger.info(file)
                return results, file

        return results, None

    def get_employee_folder_ids(self):
        employee_folder_ids = {}
        page_token = None

        while True:
            try:
                param = {
                    "q": f"'{self._employees_folder_id}' in parents and mimeType='application/vnd.google-apps.folder'",
                    "supportsAllDrives": True,
                    "includeItemsFromAllDrives": True,
                    "fields": "nextPageToken, files(id, name)",
                }

                if page_token:
                    param["pageToken"] = page_token

                results = self._service.files().list(**param).execute()

                for folder in results.get("files", []):
                    if re.match(r"\d{5} Employee Files", folder["name"]):
                        store_number = folder["name"][:5]
                        employee_folder_ids[store_number] = folder["id"]

                page_token = results.get("nextPageToken")
                if not page_token:
                    break

            except HttpError as error:
                logger.error(f"An error occurred: {error}")
                break

        return employee_folder_ids

    def get_employee_food_handler_cards(self):
        employee_folder_ids = self.get_employee_folder_ids()
        food_handler_cards = defaultdict(list)

        for store_number, folder_id in employee_folder_ids.items():
            employee_folders = self._paginated_file_list(
                {
                    "q": f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and not name starts with '1.' and not name starts with '2.' and not name starts with '3.'",
                    "supportsAllDrives": True,
                    "includeItemsFromAllDrives": True,
                    "fields": "files(id, name, parents)",
                }
            )
            employee_folders = [
                folder for folder in employee_folders if folder_id in folder["parents"]
            ]

            for employee_folder in employee_folders:
                food_handler_folder = self._paginated_file_list(
                    {
                        "q": f"'{employee_folder['id']}' in parents and name='Food Handlers Card' and mimeType='application/vnd.google-apps.folder'",
                        "supportsAllDrives": True,
                        "includeItemsFromAllDrives": True,
                        "fields": "files(id, parents, name)",
                    }
                )

                if not food_handler_folder:
                    logger.info(
                        f"No 'Food Handlers Card' folder found for employee {employee_folder['name']} in store {store_number}"
                    )
                    continue

                food_handler_files = self._paginated_file_list(
                    {
                        "q": f"'{food_handler_folder[0]['id']}' in parents",
                        "supportsAllDrives": True,
                        "includeItemsFromAllDrives": True,
                        "fields": "files(id, name, mimeType)",
                    }
                )

                if not food_handler_files:
                    logger.info(
                        f"Empty 'Food Handlers Card' folder for employee {employee_folder['name']} in store {store_number}"
                    )
                    continue

                for file in food_handler_files:
                    if file["mimeType"] != "application/pdf":
                        logger.info(
                            f"Non-PDF file found: {file['name']} for employee {employee_folder['name']} in store {store_number}"
                        )
                    else:
                        food_handler_cards[store_number].append(
                            {
                                "store_number": store_number,
                                "employee_name": employee_folder["name"],
                                "file_id": file["id"],
                                "file_name": file["name"],
                            }
                        )

        return food_handler_cards

    def _paginated_file_list(self, query_params):
        results = []
        page_token = None

        while True:
            try:
                if page_token:
                    query_params["pageToken"] = page_token

                files = self._service.files().list(**query_params).execute()
                results.extend(files.get("files", []))
                page_token = files.get("nextPageToken")

                if not page_token:
                    break

            except HttpError as error:
                logger.error(f"An error occurred: {error}")
                break

        return results

    def combine_food_handler_cards_by_store(self):
        public_folder_id = "1aYlK99pUJB7EwZraJZth6PXInH8RyJa5"
        food_handler_cards = self.get_employee_food_handler_cards()
        store_pdf_ids = {}

        for store_number, cards in food_handler_cards.items():
            merger = PdfMerger()

            for card in cards:
                request = self._service.files().get_media(fileId=card["file_id"])
                file = io.BytesIO()
                downloader = MediaIoBaseDownload(file, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                file.seek(0)
                merger.append(file)

            output = io.BytesIO()
            merger.write(output)
            merger.close()
            output.seek(0)

            filename = f"Combined_Food_Handler_Cards_Store_{store_number}.pdf"
            file_metadata = {
                "name": filename,
                "parents": [public_folder_id],
                "mimeType": "application/pdf",
            }
            media = MediaIoBaseUpload(
                output, mimetype="application/pdf", resumable=True
            )

            results, existing = self.retrieve_all_files(filename, public_folder_id)
            if existing is not None:
                file = (
                    self._service.files()
                    .update(
                        fileId=existing["id"], media_body=media, supportsAllDrives=True
                    )
                    .execute()
                )
                store_pdf_ids[store_number] = existing["id"]
            else:
                file = (
                    self._service.files()
                    .create(
                        body=file_metadata,
                        media_body=media,
                        fields="id",
                        supportsAllDrives=True,
                    )
                    .execute()
                )
                store_pdf_ids[store_number] = file.get("id")

            logger.info(
                f"Combined PDF for store {store_number} created/updated with ID: {store_pdf_ids[store_number]}"
            )

        return store_pdf_ids

    def get_public_share_links(self, file_ids):
        share_links = {}
        for store_number, file_id in file_ids.items():
            try:
                file = (
                    self._service.files()
                    .get(
                        fileId=file_id, fields="webContentLink", supportsAllDrives=True
                    )
                    .execute()
                )
                download_link = file.get("webContentLink")
                if download_link:
                    # Remove the "export=download" parameter to open in browser
                    share_links[store_number] = download_link.replace(
                        "&export=download", ""
                    )

                logger.info(
                    f"Direct download link created for store {store_number}: {share_links[store_number]}"
                )
            except HttpError as error:
                logger.error(
                    f"An error occurred while creating download link for store {store_number}: {error}"
                )

        return share_links

    def get_food_handler_pdf_links(self):
        food_handler_cards = self.combine_food_handler_cards_by_store()
        share_links = self.get_public_share_links(food_handler_cards)
        return share_links
