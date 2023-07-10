import os
import datetime
import json
import io
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError
from ssm_parameter_store import SSMParameterStore 

class WMCGdrive:
    def __init__(self):
        self.in_aws = os.environ.get("AWS_EXECUTION_ENV") is not None
        self._parameters = SSMParameterStore(prefix="/prod")["gcp"]  
        gdrive_json = json.loads(self._parameters["gdrive"])   
        
        scopes_list = [
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/drive.file'
        ]

        self._credentials = service_account.Credentials.from_service_account_info(gdrive_json, scopes=scopes_list)
        self._folder_id = "1N2VA2RuHi4UDBeLkRdY7hFDeec_StwDw"
        self._service = build('drive', 'v3', credentials=self._credentials)

    def upload(self, filename, content, mime_type):

        file_metadata = {'name': filename, 'parents': [self._folder_id], 'mimeType': mime_type}
        
        media = MediaIoBaseUpload(io.BytesIO(content), mimetype=mime_type, resumable=True)
        results, existing = self.retrieve_all_files(filename)
        if existing is not None:
            request = self._service.files().update(fileId=existing['id'], media_body=media, supportsAllDrives=True).execute()
        else:
            request = self._service.files().create(body=file_metadata, media_body=media, fields='id', supportsAllDrives=True).execute()
        
        print("Upload Complete!")
        print(request)

    def retrieve_all_files(self, filename_to_search):
        api_service = self._service
        results = []
        page_token = None

        while True:
            try:
                param = {'q' : "'" + self._folder_id + "' in parents",'supportsAllDrives' :True, 'includeItemsFromAllDrives' : True,
                    'fields' : 'nextPageToken, files(id, name)'}

                if page_token:
                    param['pageToken'] = page_token

                files = api_service.files().list(**param).execute()
                # append the files from the current result page to our list
                results.extend(files.get('files'))
                # Google Drive API shows our files in multiple pages when the number of files exceed 100
                page_token = files.get('nextPageToken')

                if not page_token:
                    break

            except HttpError as error:
                print(f'An error has occurred: {error}')
                break
        # output the file metadata to console
        file = None
        for file in results:
            if file.get('name') == filename_to_search:
                print(file)
                return results, file

        return results, None
                
    