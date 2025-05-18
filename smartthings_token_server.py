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

def get_token(token_file_path, client_id, client_secret, seed_refresh_token):
    """
    Get a new access token using a refresh token.
    """
    try:
        with open(token_file_path, 'rt') as infile:
            refresh_token = json.loads(infile.read()).get('refresh_token')
            if not refresh_token:
                raise FileNotFoundError
    except FileNotFoundError:
        refresh_token = seed_refresh_token

    print(f"[CURRENT] refresh_token: {refresh_token}")

    url = "https://api.smartthings.com/oauth/token"
    payload = (
        f'grant_type=refresh_token&client_id={client_id}&client_secret='
        f'&refresh_token={refresh_token}'
    )
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()}',
    }

    response = requests.post(url, headers=headers, data=payload, timeout=30)

    if response.status_code == 200:
        response_dict = response.json()
        response_dict['issued_at'] = datetime.datetime.now(
            pytz.UTC).isoformat(timespec="seconds").replace('+00:00', 'Z')
        response_json = json.dumps(response_dict, indent=4)
        print(f" [NEW] [{datetime.datetime.now()}] {response_json}")

        with open(token_file_path, 'wt') as outfile:
            outfile.write(response_json)
    else:
        sys.exit(f"[ERROR] {response.status_code} {response.text}")


if __name__ == "__main__":
    load_dotenv()
    # Read environment variables
    oauth_client_id = os.getenv('SMARTTHINGS_CLIENT_ID')
    oauth_client_secret = os.getenv('SMARTTHINGS_CLIENT_SECRET')
    seed_oauth_refresh_token = os.getenv('REFRESH_TOKEN')

    if not all([oauth_client_id, oauth_client_secret, seed_oauth_refresh_token]):
        sys.exit("Missing SMARTTHINGS_CLIENT_ID, SMARTTHINGS_CLIENT_SECRET, or REFRESH_TOKEN.")

    # Token file location (in container)
    oauth_token_file_path = '/tmp/token_info.json'

    # Start HTTP server to serve the token file
    subprocess.Popen(
        ['python3', '-m', 'http.server', '--bind', '0.0.0.0', '--directory', '/tmp', '5165'],
        start_new_session=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    print("STARTING HTTP SERVER ON PORT 5165")

    # Refresh every 960 minutes
    schedule.every(960).minutes.do(
        get_token,
        oauth_token_file_path,
        oauth_client_id,
        oauth_client_secret,
        seed_oauth_refresh_token
    )

    # Initial fetch
    get_token(oauth_token_file_path, oauth_client_id, oauth_client_secret, seed_oauth_refresh_token)

    print("STARTING TOKEN REFRESH SCHEDULER...")

    while True:
        schedule.run_pending()
        time.sleep(1)
