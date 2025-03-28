"""This module provides useful methods to download resources from google drive"""

import io
from dataclasses import dataclass
from pathlib import Path

from googleapiclient.http import MediaIoBaseDownload

from files.file_item import FileItem, FileItemWithTree


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
    ),  # shortcut are skipped and corresponding content is ignored. TODO: download the target file?
    # !!! We need to expand EXPORT_TABLE to support any google format
    # google specific format : https://developers.google.com/drive/api/guides/mime-types?hl=fr
}


def download_file(service, item: FileItem, folder_path: Path):
    """Download the file from google drive whose ID is 'file_id' inside 'folder_path'"""
    file_path = folder_path.joinpath(item.name)

    # --- Some file are native google file (google doc, google spreadsheet...)
    # -> we need to export them locally using a compatible format

    # get the file type for export
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


def export_file(service, item: FileItemWithTree, root_folder: Path) -> None:
    """Export 'item' content from google drive to root_folder replicating google drive file tree"""
    folder_path = root_folder.joinpath(item.path)

    if not folder_path.exists():
        folder_path.mkdir(parents=True, exist_ok=True)

    download_file(service, item.file_item, folder_path)
