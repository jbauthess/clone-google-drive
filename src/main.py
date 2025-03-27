import io
import os.path
from dataclasses import dataclass
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

# info on the google drive API : https://developers.google.com/drive/api/quickstart/python?hl=fr


FOLDER_MIMETYPE = "application/vnd.google-apps.folder"

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


@dataclass
class ExportInfo:
    mime_type: str
    extension: str


EXPORT_TABLE = {
    "application/vnd.google-apps.document": ExportInfo(
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".docx",
    ),
    "application/vnd.google-apps.spreadsheet": ExportInfo(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xlsx",
    ),
    "application/vnd.google-apps.shortcut": ExportInfo(
        "", ""
    ),  # shortcut are skipped and corresponding content is ignored. TODO: download the target file
}


@dataclass
class FileItem:
    id: str
    mimeType: str
    name: str


@dataclass
class FileItemWithTree:
    path: Path  # path of the file in the google drive file tree
    file_item: FileItem


def connect() -> Credentials:
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "client_secrets.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds


def list_items(service, folder_id) -> list[FileItem]:
    """List items (files and folders) inside folder whose ID is 'folder_id'"""
    query = f"'{folder_id}' in parents and trashed=false"

    # get file ressource ID, name and type. For more info on possibility:
    # https://developers.google.com/drive/api/reference/rest/v3/files?hl=fr#resource
    results = (
        service.files()
        .list(
            pageSize=None,
            q=query,
            fields="nextPageToken, files(id, mimeType, name)",
        )
        .execute()
    )
    items = results.get("files", [])

    return [FileItem(**item) for item in items]


def list_items_recursive(
    service, folder_id, folder_path: Path
) -> list[FileItemWithTree]:
    """List items (files and folders) inside folder whose ID is 'folder_id' recursively."""
    items = list_items(service, folder_id)

    items_final: list[FileItemWithTree] = []
    for item in items:
        if item.mimeType == FOLDER_MIMETYPE:
            items_final.extend(
                list_items_recursive(
                    service, item.id, folder_path=folder_path.joinpath(item.name)
                )
            )
        else:
            items_final.append(FileItemWithTree(folder_path, item))

    return items_final


def download_file(service, item: FileItem, folder_path: Path):
    """Download the file from google drive whose ID is 'file_id'."""
    file_path = folder_path.joinpath(item.name)

    # --- Some file are native google file (google doc, google spreadsheet...)
    # -> we need to export them using a compatible format
    # !!! We need to expand EXPORT_TABLE to support any google format
    # get the file type for export
    # google specific format : https://developers.google.com/drive/api/guides/mime-types?hl=fr
    mime_type_export = item.mimeType
    mime_type_export_info = EXPORT_TABLE.get(item.mimeType)
    if mime_type_export_info:
        if mime_type_export_info.mime_type != "":
            mime_type_export = mime_type_export_info.mime_type
            file_path = str(file_path) + mime_type_export_info.extension
            request = service.files().export(fileId=item.id, mimeType=mime_type_export)
        else:
            # those type are skipped
            print("SKIPPED")
            return
    else:
        request = service.files().get_media(fileId=item.id)
        # request = service.files().download(fileId=item.id, mimeType=mime_type_export)

    print(f"download {file_path}")
    # Request to get the file
    fh = io.BytesIO()  # Create a BytesIO buffer to hold the file content

    # Create a MediaIoBaseDownload object
    downloader = MediaIoBaseDownload(fh, request)

    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print(f"Download {int(status.progress() * 100)}%.")

    # Write the content to a file
    with open(file_path, "wb") as f:
        f.write(fh.getvalue())
    print(f"File downloaded as {file_path}")


def export_item(service, item: FileItemWithTree, root_folder: Path) -> None:
    """Export 'item' content from google drive to root_folder replicating google drive file tree"""
    folder_path = root_folder.joinpath(item.path)

    if not folder_path.exists():
        folder_path.mkdir(parents=True, exist_ok=True)

    download_file(service, item.file_item, folder_path)


def main():
    """
    clone the content of a google drive locally replicating the folder tree. For file using specific google
    format as google doc, google spreadsheet and that can not be doanloaded as it, the files are exported to a compatible format (word, excel...)
    """
    creds = connect()

    try:
        service = build("drive", "v3", credentials=creds)

        ###  the following should work onece download_file is fixed
        # Call the Drive v3 API
        folder_id = "root"
        items = list_items_recursive(service, folder_id, Path("."))

    except HttpError as error:
        print(f"An error occurred: {error}")

    if not items:
        print("No files found.")
        return

    for item in items:
        try:
            export_item(service, item, Path("."))
        except HttpError as e:
            raise Exception(f"Failed downloading item {item} : {str(e)}") from e


if __name__ == "__main__":
    main()
