import os
import io
import logging
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from flask import session

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def create_flow():
    client_config = {
        "web": {
            "client_id": os.environ.get("GOOGLE_CLIENT_ID"),
            "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost:5000/oauth2callback"]
        }
    }
    return Flow.from_client_config(client_config, SCOPES)

def get_drive_service():
    if 'credentials' not in session:
        return None
        
    credentials = Credentials(**session['credentials'])
    return build('drive', 'v3', credentials=credentials)

def list_folders():
    service = get_drive_service()
    if not service:
        return None
        
    try:
        results = service.files().list(
            q="mimeType='application/vnd.google-apps.folder'",
            fields="files(id, name)"
        ).execute()
        return results.get('files', [])
    except Exception as e:
        logging.error(f"Error listing folders: {str(e)}")
        return None

def download_folder_contents(folder_id, upload_folder):
    service = get_drive_service()
    if not service:
        return False, "Not authenticated"
        
    try:
        # Query for all files in the folder
        results = service.files().list(
            q=f"'{folder_id}' in parents and (mimeType='image/jpeg' or mimeType='image/png' or mimeType='image/gif')",
            fields="files(id, name, mimeType)"
        ).execute()
        
        files = results.get('files', [])
        downloaded_files = []
        
        for file in files:
            try:
                request = service.files().get_media(fileId=file['id'])
                file_handle = io.BytesIO()
                downloader = MediaIoBaseDownload(file_handle, request)
                done = False
                
                while not done:
                    _, done = downloader.next_chunk()
                
                file_handle.seek(0)
                filename = os.path.join(upload_folder, 'unsorted', file['name'])
                with open(filename, 'wb') as f:
                    f.write(file_handle.read())
                downloaded_files.append(file['name'])
                
            except Exception as e:
                logging.error(f"Error downloading file {file['name']}: {str(e)}")
                continue
                
        return True, downloaded_files
        
    except Exception as e:
        logging.error(f"Error processing folder: {str(e)}")
        return False, str(e)
