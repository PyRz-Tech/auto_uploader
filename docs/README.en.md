# Auto Uploader

This is a simple Python script that keeps an eye on a folder on your computer and automatically syncs any changes (like adding, editing, or deleting files) to Google Drive. It’s perfect for folks who can’t be bothered to manually upload stuff, like code backups or documents that keep changing. This project’s mainly for coders who wanna tweak it or keep it running.

## What’s it do?

- Watches a folder in real-time using `watchdog`.
- Uploads new or changed files to Google Drive on the spot.
- Deletes files from Google Drive if you delete them locally.
- Uses OAuth 2.0 to connect to Google Drive.
- Saves your settings in a `config.json` file.
- Checks your internet connection with `socket` before uploading.
- Logs everything with `logging` so you can track down issues.
- Keeps a map of local-to-Google-Drive files in `file_map.json`.
- Handles uploads in a resumable way, so big files don’t crash.
- Comes with full test coverage (100%!)—there’s even a test coverage video in `media/coverage.mp4`.

## What you need

- Python 3.8 or newer.
- A Google account with the Google Drive API enabled:
  - Head to the [Google Cloud Console](https://console.cloud.google.com/), create a new project, enable the Google Drive API, and grab an OAuth 2.0 credential (desktop app type) to get your `credentials.json` file. Check out the [Drive API Quickstart](https://developers.google.com/drive/api/quickstart/python) and [OAuth Credentials Guide](https://developers.google.com/workspace/guides/create-credentials#desktop-app) for step-by-step help.
  - **Heads-up:** Set your project to **Testing** mode so Google doesn’t need to verify your app. In the **OAuth Consent Screen** section of the Google Cloud Console, pick **Testing** and add your email as a tester. This way, only testers you add can log in. For details on setting up the testing mode, see this [OAuth Consent Screen Guide](https://support.google.com/cloud/answer/10311615).
- An internet connection for login and uploads.

## Setup

1. Clone the repo:
   ```
   git clone https://github.com/yourusername/auto_uploader
   cd auto_uploader
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Getting Started

1. Drop the `credentials.json` file in the project root or point to it when the script asks.
   - **Note:** Your Google API needs to be in **Testing** mode to skip Google’s verification. Go to the [Google Cloud Console](https://console.cloud.google.com/), head to the **OAuth Consent Screen**, select **Testing**, and add your email as a tester. Check the [OAuth Consent Screen Guide](https://support.google.com/cloud/answer/10311615) and [OAuth Credentials Guide](https://developers.google.com/workspace/guides/create-credentials#desktop-app) for details. This ensures only tester emails can log in without Google’s app verification. For enabling the API and grabbing `credentials.json`, hit up this [Google Quickstart Guide](https://developers.google.com/drive/api/quickstart/python).
   - The script uses the limited `drive.file` scope, so it only messes with files it creates.
2. Run the script:
   ```
   python3 run.py
   ```
   - If you haven’t set up configs yet, it’ll ask for the `credentials.json` path and the folder you wanna watch.
   - You can also pass the paths directly:
     ```
     python3 run.py --credentials /path/to/credentials.json --watch_folder /path/to/folder
     ```
   - Wanna see the command-line options? Run:
     ```
     python3 run.py --help
     ```
   - Settings get saved in `src/config.json`. On first run, it’ll pop open a browser for login, and your token gets stored in `token.json`.
   - Messed up and files got uploaded wrong? Delete `config.json`, `token.json`, `file_map.json`, and `folder_id.txt`, then rerun to start fresh.

## How to Use It

Just fire it up:
```
python3 run.py
```

- It starts watching your folder and syncs any changes to Google Drive.
- Wanna tweak the settings? Pass the paths like this:
  ```
  python3 run.py --credentials /path/to/credentials.json --watch_folder /path/to/folder
  ```

### Quick Example
Say you create or edit a `note.txt` file in the watched folder—it’ll auto-upload to Google Drive. Delete it locally, and it’s gone from Drive too.

## Modular Design

The project’s built so each part does its own thing without making a mess:
- **Config Layer (`config_loader.py`, `app_runner.py`):** Loads settings from JSON or command line and checks paths to avoid runtime errors.
- **Utility Layer:**
  - `file_utils.py`: Handles file mappings in JSON (saving, reading, deleting).
  - `drive_utils.py`: Deals with Google Drive API stuff (login, folder creation, uploads, deletes). Uploads are resumable for big files.
  - `network_utils.py`: Checks internet with `socket`.
- **Core (`watcher.py`, `main.py`):** The `watcher.py` uses `watchdog` to catch file events (create, modify, delete). `main.py` kicks off the service and starts watching.
- **Entry Point (`run.py`):** Ties it all together.

This setup makes it:
- Easy to write tests (like mocking APIs or files).
- Simple to swap Google Drive for, say, Dropbox later.
- Readable—each file’s under 200 lines and has a clear job.

## Dev Tools

- **Language:** Python 3.8 or newer.
- **Built-in Modules:** `os` (path handling), `json` (mappings and configs), `logging` (error logs), `pickle` (token storage), `time` (watch delays), `socket` (internet checks), `argparse` (command-line args), `sys` (error exits).
- **External Modules:** `google_auth_oauthlib.flow` (for OAuth), `googleapiclient.discovery` and `http` (for Drive API), `watchdog` (for file watching).
- **Tools:**
  - IDE: VS Code or PyCharm.
  - Testing: `pytest` with 100% coverage.
  - Version Control: Git.
  - No GUI—just command line with logs.

## Testing

Tests live in the `tests/` folder, written with `pytest` and `unittest.mock`. They cover 100% of the code, including normal paths, errors (like no internet or bad JSON), and edge cases (like hidden files).

Run them with:
```
pytest tests/
```

Check coverage:
```
coverage run -m pytest
coverage report
```

Get an HTML report:
```
coverage html
```

- **Note:** Tests mock external dependencies (like APIs), so you don’t need `credentials.json` to run them.
- You can run tests in CI/CD (like GitHub Actions) before building configs.
- There’s a test coverage video in `media/coverage.mp4`.

## Lessons and Gotchas

Building this took about 2 weeks (part-time). Some key notes and hiccups:
- **Watchdog Watching:** Super reliable, but it skips hidden files (like `.DS_Store`) to avoid noise.
- **OAuth:** Local server for login works great, but you gotta handle cases where users deny access.
- **Resumable Uploads:** A must for big files to avoid crashes on shaky internet.
- **Errors:**
  - **JSONDecodeError:** If `file_map.json` gets corrupted, `file_utils` rebuilds it.
  - **HttpError (403/404):** Access issues or file not found—logged and skipped.
  - **No Internet:** Checked with `socket`, retries on the next event.
  - **Token Expiry:** Auto-refreshes, but a wrong scope (not `drive.file`) will break things.
  - **Watchdog Quirks:** Behaves differently on Windows vs. Linux; tested on both.
  - **Missing Configs:** Script asks for paths and validates them to avoid crashes.

**Lesson Learned:** Log everything! Modular design made debugging a breeze.

## Project Structure

```
.
├── media
│   └── coverage.mp4  # Test coverage video
├── requirements.txt  # Required packages
├── run.py            # Script entry point
├── src
│   ├── app_runner.py     # Startup and path checks
│   ├── config_loader.py  # Load and save configs
│   ├── drive_utils.py    # Google Drive API stuff
│   ├── file_utils.py     # File mapping management
│   ├── __init__.py
│   ├── main.py           # Core logic
│   ├── network_utils.py  # Internet checks
│   └── watcher.py        # File change watcher
└── tests
    ├── __init__.py
    ├── test_app_runner.py    # Startup tests
    ├── test_config_loader.py # Config tests
    ├── test_drive_utils.py   # Drive utils tests
    ├── test_file_utils.py    # File mapping tests
    ├── test_main.py          # Core tests
    ├── test_network_utils.py # Internet check tests
    └── test_watcher.py       # Watcher tests
```

## Limitations

- Google API needs to be in testing mode.
- If an upload fails, it won’t retry automatically (you gotta restart manually).
- Hidden files (starting with `.`) are ignored completely.
- Renaming or moving folders doesn’t work properly.
- Only tested on Python 3.8 or newer—older versions might choke.
- You need to manually create `credentials.json`.

## Contributing

Wanna chip in? Here’s how:
- Fork the repo.
- Make changes in a separate branch.
- Write tests for new stuff (TDD’s the way to go).
- Before sending a pull request, ensure all tests pass and coverage stays at 100%.

For debugging, logs or `pdb` are your best friends.

## Related Links (placeholders—fill in later)

- dev.to article: [Building an Auto Uploader to Google Drive: Lessons Learned](https://dev.to/yourusername/building-an-auto-uploader-to-google-drive-lessons-learned-1234)
- GitHub: [github.com/yourusername/auto_uploader](https://github.com/yourusername/auto_uploader)
- LinkedIn: [linkedin.com/in/yourusername](https://www.linkedin.com/in/yourusername)
- Twitter (X): [twitter.com/yourusername](https://twitter.com/yourusername)

## License

This project’s under the MIT License. If there’s no [LICENSE](LICENSE) file, assume it’s free for personal use.