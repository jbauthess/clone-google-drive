"""This module defines descriptions of resources present on google drive"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class FileItem:
    # file ID on google drive
    id: str
    # file type
    mimeType: str
    # file name
    name: str


@dataclass
class FileItemWithTree:
    path: Path  # path of the file in the google drive file tree
    file_item: FileItem
