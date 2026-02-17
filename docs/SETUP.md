# AI Factory - Setup Guide

## Prerequisites

1. **Python 3.11+** - Install via Homebrew:
   ```bash
   brew install python3.11
   ```

2. **FFmpeg** (optional, for video generation):
   ```bash
   brew install ffmpeg
   ```

## Installation

1. Navigate to the project:
   ```bash
   cd ai-factory
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy environment file:
   ```bash
   cp .env.example .env
   ```

4. Initialize database:
   ```bash
   python cli.py init
   ```

## API Setup

### LemonSqueezy (Storefront)
1. Sign up at [lemonsqueezy.com](https://lemonsqueezy.com)
2. Go to Settings → API
3. Copy your API key to `.env`
4. Get your Store ID from Settings → Stores

### YouTube (Shorts Upload)
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a project and enable YouTube Data API v3
3. Create OAuth credentials (Desktop Application)
4. Download the JSON file and set path in `.env`:
   ```
   YOUTUBE_CLIENT_SECRET_JSON_PATH=/path/to/client_secret.json
   ```
5. Get your Channel ID from YouTube → Settings → Advanced

### Pinterest (Pin Creation)
1. Sign up at [developers.pinterest.com](https://developers.pinterest.com)
2. Create an app and get Access Token
3. Add token to `.env`

## First Run

Build a tool:
```bash
python cli.py build_tool --template roi_calculator --slug my-profit-calc --niche "small business"
```

Publish to store:
```bash
python cli.py publish_product --tool my-profit-calc --price 29
```

Generate content:
```bash
python cli.py generate_content --tool my-profit-calc --platform youtube,pinterest --count 3
```

Daily automation:
```bash
python cli.py daily_run
```

## Commands

| Command | Description |
|---------|-------------|
| `python cli.py init` | Initialize DB and folders |
| `python cli.py build_tool` | Build from template |
| `python cli.py publish_product` | Publish to storefront |
| `python cli.py generate_content` | Create demo content |
| `python cli.py post_content` | Post to social platforms |
| `python cli.py analytics_report` | View metrics |
| `python cli.py daily_run` | Full automation loop |

## Adding New Templates

1. Create folder in `tool_templates/`
2. Add `config.json` with inputs/formula
3. Add `index.html` with the tool UI
4. Use: `python cli.py build_tool --template your_new_template --slug name`
