# MyFin
A simple open source expenses tracking app using Google Drive, Apps Script and Flutter.

## Setup
1. Create a new empty Google Sheet
2. Open a corresponding Apps Script project with _Tools > Script editor_
3. Copy the files from `./apps_script`
4. Set your own value for the constant `API_KEY`
4. Run the `setup` function and grant the app access to your Google Sheets
5. Create a new deployment and copy the Deployment ID
6. Create `./flutter_app/lib/config.dart` based on `./flutter_app/lib/config.dart.template` using your API key and Deployment ID
