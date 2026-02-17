#!/usr/bin/env python3
"""
YouTube Uploader - Upload shorts to YouTube via Data API v3
Requires: google-api-python-client, google-auth-oauthlib
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
import pickle
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

CONTENT_RENDERS = Path(__file__).parent.parent / "content" / "renders"

def get_credentials(creds_path):
    """Get OAuth credentials"""
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    
    token_path = Path(creds_path).parent / "token.pickle"
    
    # If we have a saved token, use it
    if token_path.exists():
        with open(token_path, 'rb') as f:
            return pickle.load(f)
    
    # Otherwise, run OAuth flow
    flow = InstalledAppFlow.from_client_secrets_file(
        creds_path,
        scopes=['https://www.googleapis.com/auth/youtube.upload']
    )
    
    credentials = flow.run_local_server(port=8080)
    
    # Save for next time
    with open(token_path, 'wb') as f:
        pickle.dump(credentials, f)
    
    return credentials

def upload_to_youtube(video_path, title, description, tags, category_id="22"):
    """Upload video to YouTube"""
    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        from google.oauth2.credentials import Credentials
        import pickle
        
        # Load credentials
        creds_path = os.getenv("YOUTUBE_CLIENT_SECRET_JSON_PATH")
        if not creds_path:
            print("❌ YOUTUBE_CLIENT_SECRET_JSON_PATH not set")
            return None
        
        token_path = Path(creds_path).parent / "youtube_token.pickle"
        
        if token_path.exists():
            with open(token_path, 'rb') as f:
                credentials = pickle.load(f)
        else:
            print("❌ No YouTube credentials. Run OAuth setup first.")
            return None
        
        # Build YouTube service
        youtube = build('youtube', 'v3', credentials=credentials)
        
        # Upload
        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": tags,
                    "categoryId": category_id,
                    "privacyStatus": "public"
                },
                "status": {
                    "selfDeclaredMadeForKids": False
                }
            },
            media_body=MediaFileUpload(video_path)
        )
        
        response = request.execute()
        
        video_id = response['id']
        print(f"✅ Uploaded to YouTube: https://youtube.com/watch?v={video_id}")
        
        return f"https://youtube.com/watch?v={video_id}"
    
    except ImportError:
        print("❌ Install: pip install google-api-python-client google-auth-oauthlib")
        return None
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return None

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="YouTube Uploader")
    parser.add_argument("--video", required=True, help="Path to video file")
    parser.add_argument("--title", required=True, help="Video title")
    parser.add_argument("--description", help="Video description")
    parser.add_argument("--tags", help="Comma-separated tags")
    
    args = parser.parse_args()
    
    description = args.description or "Check out this free tool!"
    tags = args.tags.split(",") if args.tags else ["free", "tool", "calculator"]
    
    result = upload_to_youtube(args.video, args.title, description, tags)
    
    if result:
        print(f"🎉 Success: {result}")
    else:
        print("❌ Failed to upload")

if __name__ == "__main__":
    main()
