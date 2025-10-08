# clone-google-drive
A tool for cloning a google drive repo locally.

This tool parses the full target google drive and replicate the files locally using the same folder tree as on drive. Files using specific google formats (google doc, ...) can not be downloaded as it. Instead they are exported to a compatible format (word, ...).  

## Setup

To clone a google drive repo, you will need first to generate the client_secrets.json file. 
The client_secrets.json file is a JSON-formatted file used to store OAuth 2.0 credentials, including the client_id, client_secret, and other parameters required for authentication with Google APIs. 

**To create this file, follow these steps:**

-  Log in to the [Google Cloud Console](https://console.cloud.google.com/).
- Navigate to APIs & Services > Credentials.
- Click Create Credentials and select OAuth 2.0 Client ID.
- Choose the application type 'Installed' and configure the required fields.

After creation, download the client_secrets.json file at the <CREDENTIAL_FOLDER_LOCATION> of your choice.

## Setup

To clone a google drive, open a cmd, install the dependancies as listed in the pyproject.toml and then run :
> python src/main.py <OUTPUT_FOLDER> -user_access_info_folder_path <CREDENTIAL_FOLDER_LOCATION> 

This will export the google drive repo into: <OUTPUT_FOLDER> 