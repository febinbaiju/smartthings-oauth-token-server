import datetime
import base64
import time
import json
import sys
import subprocess
import os
import requests
import schedule
import pytz
from dotenv import load_dotenv


def start_http_server(directory="/tmp", port=5165):
    """
    Start a simple HTTP server to serve token files.
    Logs to console. Keeps running independently.
    """
    try:
        subprocess.Popen(
            ['python3', '-m', 'http.server', str(port), '--bind', '0.0.0.0', '--directory', directory],
            start_new_session=True
        )
        print(f"✅ HTTP server started on port {port}, serving {directory}")
    except Exception as e:
        print(f"[ERROR] Failed to start HTTP server: {e}")
        sys.exit(1)


def write_token_file_atomic(filepath, data):
    """
    Atomically write the token file to avoid partial writes.
    """
    tmp_file = filepath + '.tmp'
    with open(tmp_file, 'wt') as f:
        f.write(data)
    os.replace(tmp_file, filepath)


def get_token(token_file_path, client_id, client_secret, seed_refresh_token):
    """
    Get a new access token using a refresh token, retrying indefinitely on failure every 5 seconds.
    """
    try:
        with open(token_file_path, 'rt') as infile:
            refresh_token = json.loads(infile.read()).get('refresh_token')
            if not refresh_token:
                raise ValueError("No refresh_token in token file")
    except (FileNotFoundError, ValueError, json.JSONDecodeError):
        print("⚠️  Using seed refresh token")
        refresh_token = seed_refresh_token

    print(f"[CURRENT] refresh_token: {refresh_token[:10]}...")

    url = "https://api.smartthings.com/oauth/token"
    payload = (
        f'grant_type=refresh_token&client_id={client_id}&client_secret={client_secret}'
        f'&refresh_token={refresh_token}'
    )
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()}',
    }

    while True:
        try:
            response = requests.post(url, headers=headers, data=payload, timeout=30)

            if response.status_code == 200:
                response_dict = response.json()
                response_dict['issued_at'] = datetime.datetime.now(
                    pytz.UTC).isoformat(timespec="seconds").replace('+00:00', 'Z')
                response_json = json.dumps(response_dict, indent=4)
                print(f"[NEW TOKEN] [{datetime.datetime.now()}] Token updated.")

                write_token_file_atomic(token_file_path, response_json)
                break
            else:
                print(f"[ERROR] {response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"[EXCEPTION] Token request failed: {e}")

        print("🔁 Retrying in 5 seconds...")
        time.sleep(5)


if __name__ == "__main__":
    load_dotenv()

    # Read environment variables
    oauth_client_id = os.getenv('SMARTTHINGS_CLIENT_ID')
    oauth_client_secret = os.getenv('SMARTTHINGS_CLIENT_SECRET')
    seed_oauth_refresh_token = os.getenv('REFRESH_TOKEN')

    if not all([oauth_client_id, oauth_client_secret, seed_oauth_refresh_token]):
        sys.exit("❌ Missing SMARTTHINGS_CLIENT_ID, SMARTTHINGS_CLIENT_SECRET, or REFRESH_TOKEN.")

    # Token file path
    oauth_token_file_path = '/tmp/token_info.json'

    # Start HTTP server
    start_http_server(directory='/tmp', port=5165)

    # Schedule token refresh
    schedule.every(960).minutes.do(
        get_token,
        oauth_token_file_path,
        oauth_client_id,
        oauth_client_secret,
        seed_oauth_refresh_token
    )

    # Initial token fetch
    get_token(oauth_token_file_path, oauth_client_id, oauth_client_secret, seed_oauth_refresh_token)

    print("🕒 Scheduler running...")

    # Main loop
    while True:
        schedule.run_pending()
        time.sleep(1)
