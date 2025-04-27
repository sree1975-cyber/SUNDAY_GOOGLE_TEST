# Web Content Manager

A Streamlit app to save, organize, and manage web links with persistent storage in Google Drive.

## Features
- Save links with titles, descriptions, and tags
- Fetch metadata automatically from URLs
- Search and filter links by text and tags
- Delete multiple links at once
- Export links as Excel files
- Owner, Guest, and Public modes
- Persistent storage in Google Drive for Owner and Guest modes
- Animated balloons and success messages for user actions

## Setup Instructions

### Prerequisites
- Python 3.9+
- Streamlit Cloud account
- Google Cloud account with Google Drive API enabled
- GitHub account

### Google Drive API Setup
1. Create a Google Cloud Project:
   - Go to [Google Cloud Console](https://console.cloud.google.com/).
   - Create a new project (e.g., "WebContentManager").
   - Enable the Google Drive API.

2. Set Up Service Account:
   - Navigate to "IAM & Admin" > "Service Accounts."
   - Create a service account (e.g., "web-content-manager-service").
   - Assign the "Editor" role or a custom role with `drive.files` scope.
   - Download the JSON key (e.g., `service_account_key.json`).

3. Share Google Drive Folder:
   - Create a folder in Google Drive (e.g., "WebContentManagerData").
   - Get the folder ID from the URL (e.g., `https://drive.google.com/drive/folders/<FOLDER_ID>`).
   - Share the folder with the service account email (e.g., `web-content-manager-service@<project>.iam.gserviceaccount.com`) with "Editor" access.

### Streamlit Cloud Setup
1. Fork or clone this repository to your GitHub account.
2. In Streamlit Cloud:
   - Create a new app and link it to your GitHub repository.
   - Set the Python version to 3.9 or higher.
   - Add the following secrets in the app settings:
     - `GOOGLE_DRIVE_CREDENTIALS`: Paste the entire JSON content of the service account key.
     - `GOOGLE_DRIVE_FOLDER_ID`: Paste the folder ID from the shared Google Drive folder.
3. Deploy the app. Streamlit Cloud will automatically install dependencies from `requirements.txt`.

### Local Development
1. Clone the repository:
   ```bash
   git clone https://github.com/<your-username>/web-content-manager.git
   cd web-content-manager
   ```
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Set environment variables or create a `.streamlit/secrets.toml` file with:
   ```toml
   GOOGLE_DRIVE_CREDENTIALS = '''<JSON content of service_account_key.json>'''
   GOOGLE_DRIVE_FOLDER_ID = "<folder_id>"
   ```
4. Run the app:
   ```bash
   streamlit run app.py
   ```

## Usage
- **Owner Mode**: Log in with password `admin123` to manage a shared `web_links.xlsx` file.
- **Guest Mode**: Log in with password `guest456` and a username to manage a personal `guest_<username>.xlsx` file.
- **Public Mode**: Access without logging in; links are stored temporarily in session state and can be downloaded.
- Add links, fetch metadata, search, delete, and export links using the navigation menu.

## Notes
- The service account JSON key must be kept secure and not committed to the repository.
- Streamlit Cloud does not support persistent local storage, so Google Drive is used for Owner and Guest modes.
- Public mode data is temporary and cleared on app restart unless downloaded.

## License
MIT License