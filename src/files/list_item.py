"""This module provides useful functions to list resources present on google drive"""

from pathlib import Path

from files.file_item import FileItem, FileItemWithTree

FOLDER_MIMETYPE = "application/vnd.google-apps.folder"


def list_files_using_drive_API(service, query: str) -> list[dict[str, str]]:
    # https://googleapis.github.io/google-api-python-client/docs/start.html
    results = (
        # Access the collection "files" using the API service and lists them
        service.files()
        .list(
            pageSize=None,
            q=query,
            fields="nextPageToken, files(id, mimeType, name)",
        )
        .execute()
    )
    items = results.get("files", [])
    return items


def list_items(service, folder_id) -> list[FileItem]:
    """List items (files and folders) inside folder whose ID is 'folder_id'"""
    query = f"'{folder_id}' in parents and trashed=false"

    # get file ressource ID, name and type. For more info on possibility:
    # https://developers.google.com/drive/api/reference/rest/v3/files?hl=fr#resource
    items = list_files_using_drive_API(service, query)

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
