#!/usr/bin/env python3
"""First-time YouTube OAuth authorization"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load env
load_dotenv('.env')

creds_path = os.getenv('YOUTUBE_CLIENT_SECRET_JSON_PATH')
print(f'Using credentials: {creds_path}')

if not creds_path:
    print('❌ YOUTUBE_CLIENT_SECRET_JSON_PATH not set')
    sys.exit(1)

from google_auth_oauthlib.flow import InstalledAppFlow
import pickle

flow = InstalledAppFlow.from_client_secrets_file(
    creds_path,
    scopes=['https://www.googleapis.com/auth/youtube.upload']
)

print('Opening browser for OAuth authorization...')
credentials = flow.run_local_server(port=8080, prompt='consent', open_browser=True)

# Save token
token_path = Path(creds_path).parent / 'youtube_token.pickle'
with open(token_path, 'wb') as f:
    pickle.dump(credentials, f)

print(f'✅ OAuth complete! Token saved to {token_path}')
