"""This module is reponsible of handling the connection with the google authentification service"""

import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


def connect(user_access_info_folder_path: Path = None) -> Credentials:
    """
    generate access credentials to google drive documents for a specific user
    user_access_info_folder_path : path of the folder containing json file "token.json" or "client_secrets.json"
    containing user informations
    """
    if user_access_info_folder_path is None:
        user_access_info_folder_path = Path(".")

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(user_access_info_folder_path.joinpath("token.json")):
        creds = Credentials.from_authorized_user_file(
            user_access_info_folder_path.joinpath("token.json"), SCOPES
        )
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                user_access_info_folder_path.joinpath("client_secrets.json"), SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(user_access_info_folder_path.joinpath("token.json"), "w") as token:
            token.write(creds.to_json())
    return creds
