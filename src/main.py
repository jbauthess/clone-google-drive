import argparse
from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from connect import connect
from files.download_item import export_file
from files.list_item import list_items_recursive

# info on the google drive API : https://developers.google.com/drive/api/quickstart/python?hl=fr


def clone(export_folder_path: Path, user_access_info_folder_path: Path | None = None):
    """
    clone the content of a google drive locally replicating the folder tree. For file using specific google
    format as google doc, google spreadsheet and that can not be doanloaded as it, the files are exported to a compatible format (word, excel...)
    """
    creds = connect(user_access_info_folder_path)

    try:
        # Call the Drive v3 API
        service = build("drive", "v3", credentials=creds)

        folder_id = "root"
        items = list_items_recursive(service, folder_id, Path("."))

    except HttpError as error:
        print(f"An error occurred: {error}")

    if not items:
        print("No files found.")
        return

    # download files locally
    for item in items:
        try:
            export_file(service, item, export_folder_path)
        except HttpError as e:
            raise Exception(f"Failed downloading item {item} : {str(e)}") from e


if __name__ == "__main__":
    # --- parse command line
    parser = argparse.ArgumentParser(
        prog="clone-google_drive", description="Clone a google drive locally."
    )
    parser.add_argument(
        "export_folder_path",
        help="path of the local folder the google drive will be cloned into",
        type=Path,
    )

    parser.add_argument(
        "-user_access_info_folder_path",
        help="path of the local folder containing user authentication info",
        type=Path,
        dest="user_access_info_folder_path",
    )

    args = parser.parse_args()
    export_folder_path = args.export_folder_path
    user_access_info_folder_path = args.user_access_info_folder_path

    # --- clone the drive
    clone(export_folder_path, user_access_info_folder_path)
