# MyFin
A simple open source expenses tracking app using Google Drive, Apps Script, Flutter and Python.

## Setup
1. Create a new empty Google Sheet
2. Open a corresponding Apps Script project with _Tools > Script editor_
3. Copy the files from `./apps_script`
4. Set your own value for the constant `API_KEY`
5. Run the `setup` function and grant the app access to your Google Sheets
6. Create a new deployment and copy the Deployment ID
7. Create `./flutter_app/lib/config.dart` based on `./flutter_app/lib/config.dart.template` using your API key and Deployment ID
8. Create `./reporting/config.py` based on `./reporting/config.py.template` using your API key and Deployment ID
9. Install python dependencies using `pip3 install -r requirements.txt`
