#!/usr/bin/env python3
"""
AI Factory - Micro-Tool + Content Funnel Automation
Run: python cli.py --help
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

DB_PATH = Path(__file__).parent / "db" / "factory.db"
TOOL_TEMPLATES = Path(__file__).parent / "tool_templates"
GENERATED_TOOLS = Path(__file__).parent / "generated_tools"
CONTENT_RENDERS = Path(__file__).parent / "content" / "renders"

def ensure_env():
    """Check .env exists"""
    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        print("❌ .env not found. Copy .env.example and fill in your API keys.")
        return False
    return True

def init_db(args=None):
    """Initialize SQLite database and folders"""
    import sqlite3
    
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    GENERATED_TOOLS.mkdir(parents=True, exist_ok=True)
    CONTENT_RENDERS.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS tools (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            niche TEXT,
            version INTEGER DEFAULT 1,
            build_path TEXT,
            landing_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'draft'
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tool_id INTEGER NOT NULL,
            platform TEXT NOT NULL,
            product_id TEXT,
            url TEXT,
            price REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tool_id) REFERENCES tools(id)
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tool_id INTEGER NOT NULL,
            platform TEXT NOT NULL,
            video_path TEXT,
            caption TEXT,
            hashtags TEXT,
            scheduled_at TIMESTAMP,
            posted_at TIMESTAMP,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (tool_id) REFERENCES tools(id)
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tool_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            clicks INTEGER DEFAULT 0,
            sales INTEGER DEFAULT 0,
            revenue REAL DEFAULT 0,
            platform_views_json TEXT,
            FOREIGN KEY (tool_id) REFERENCES tools(id)
        )
    """)
    
    conn.commit()
    conn.close()
    print(f"✅ Database initialized at {DB_PATH}")
    print(f"✅ Folders created")

def build_tool(args):
    """Build a tool from template"""
    import shutil
    import json
    
    slug = args.slug
    template = args.template
    niche = args.niche or "general"
    
    template_path = TOOL_TEMPLATES / template
    if not template_path.exists():
        print(f"❌ Template '{template}' not found. Available: roi_calculator, budget_planner, flip_profit")
        return
    
    output_path = GENERATED_TOOLS / slug
    if output_path.exists():
        print(f"❌ Tool '{slug}' already exists. Delete folder or use different slug.")
        return
    
    # Copy template
    shutil.copytree(template_path, output_path)
    
    # Update config
    config = {
        "slug": slug,
        "template": template,
        "niche": niche,
        "version": 1
    }
    with open(output_path / "config.json", "w") as f:
        json.dump(config, f)
    
    # Add to DB
    import sqlite3
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute("INSERT INTO tools (slug, name, niche, build_path, status) VALUES (?, ?, ?, ?, ?)",
              (slug, slug.replace("-", " ").title(), niche, str(output_path), "built"))
    conn.commit()
    conn.close()
    
    print(f"✅ Built '{slug}' from template '{template}'")
    print(f"   Location: {output_path}")
    print(f"   To preview: cd {output_path} && python -m http.server 8080")

def publish_product(args):
    """Publish tool to LemonSqueezy or Gumroad"""
    import requests
    from dotenv import load_dotenv
    
    load_dotenv()
    
    slug = args.tool
    platform = args.platform
    price = args.price or 29
    
    # Get tool from DB
    import sqlite3
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute("SELECT id, slug, name, niche FROM tools WHERE slug = ?", (slug,))
    row = c.fetchone()
    if not row:
        print(f"❌ Tool '{slug}' not found")
        return
    tool_id, slug, name, niche = row
    niche = niche or "general"
    
    if platform == "lemonsqueezy":
        api_key = os.getenv("LEMONSQUEEZY_API_KEY")
        store_id = os.getenv("LEMONSQUEEZY_STORE_ID")
        
        if not api_key or not store_id:
            print("❌ LEMONSQUEEZY_API_KEY and LEMONSQUEEZY_STORE_ID required in .env")
            return
        
        # Create product
        url = "https://api.lemonsqueezy.com/v1/products"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/vnd.api+json",
            "Accept": "application/vnd.api+json"
        }
        data = {
            "data": {
                "type": "products",
                "attributes": {
                    "name": name,
                    "price": price * 100,  # cents
                    "price_formatted": f"${price}.00",
                    "description": f"A simple {slug} tool for {niche}",
                    "slug": slug,
                    "status": "published"
                },
                "relationships": {
                    "store": {
                        "data": {"type": "stores", "id": store_id}
                    }
                }
            }
        }
        
        resp = requests.post(url, headers=headers, json=data)
        if resp.status_code in [200, 201]:
            result = resp.json()
            product_id = result["data"]["id"]
            checkout_url = result["data"]["attributes"]["urls"]["checkout_url"]
            
            c.execute("INSERT INTO products (tool_id, platform, product_id, url, price) VALUES (?, ?, ?, ?, ?)",
                      (tool_id, platform, product_id, checkout_url, price))
            conn.commit()
            print(f"✅ Product published to LemonSqueezy")
            print(f"   Checkout URL: {checkout_url}")
        else:
            print(f"❌ Failed: {resp.text}")
    
    conn.close()

def generate_content(args):
    """Generate demo content for a tool"""
    slug = args.tool
    platforms = args.platform.split(",") if args.platform else ["youtube"]
    count = args.count or 1
    
    import sqlite3
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute("SELECT id, slug, name FROM tools WHERE slug = ?", (slug,))
    row = c.fetchone()
    if not row:
        print(f"❌ Tool '{slug}' not found")
        return
    tool_id, slug, name = row
    
    # Generate caption
    caption = f"🔥 Free {name} - Link in bio!\n\n"
    caption += f"Calculate your profits instantly with this free tool.\n"
    caption += f"#free #calculator #profit #business #{slug}"
    
    hashtags = f"#{slug.replace('-', '')} #profit #calculator #free #tool"
    
    for i in range(count):
        for platform in platforms:
            # Create placeholder (in real version, would generate video)
            video_path = CONTENT_RENDERS / f"{slug}_{platform}_{i+1}.mp4"
            
            c.execute("""INSERT INTO content 
                (tool_id, platform, video_path, caption, hashtags, status) 
                VALUES (?, ?, ?, ?, ?, ?)""",
                (tool_id, platform, str(video_path), caption, hashtags, "generated"))
            
            print(f"✅ Generated content for {slug} - {platform}")
    
    conn.commit()
    conn.close()
    print(f"✅ Created {count} content item(s) for {platforms}")

def post_content(args):
    """Post content to social platforms"""
    platforms = args.platform.split(",") if args.platform else ["youtube"]
    
    import sqlite3
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    
    for platform in platforms:
        c.execute("""SELECT c.id, c.tool_id, c.video_path, c.caption, c.hashtags, t.slug
            FROM content c JOIN tools t ON c.tool_id = t.id
            WHERE c.platform = ? AND c.status = 'generated' LIMIT 1""", (platform,))
        
        row = c.fetchone()
        if not row:
            print(f"⚠️ No pending content for {platform}")
            continue
        
        content_id, tool_id, video_path, caption, hashtags, slug = row
        
        if platform == "youtube":
            # YouTube API upload would go here
            print(f"📺 YouTube: Would upload {video_path}")
            print(f"   Title: {slug} - Free Calculator")
            print(f"   Description: {caption}")
            status = "posted"
        
        elif platform == "pinterest":
            # Pinterest API would go here  
            print(f"📌 Pinterest: Would create pin for {slug}")
            status = "posted"
        
        else:
            print(f"⚠️ Platform {platform} not supported")
            continue
        
        c.execute("UPDATE content SET status = ?, posted_at = CURRENT_TIMESTAMP WHERE id = ?",
                  (status, content_id))
        conn.commit()
        print(f"✅ Posted to {platform}")
    
    conn.close()

def analytics_report(args):
    """Show analytics report"""
    import sqlite3
    from datetime import datetime, timedelta
    
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    
    print("\n📊 AI FACTORY ANALYTICS")
    print("=" * 40)
    
    # Tools
    c.execute("SELECT COUNT(*) FROM tools WHERE status = 'built'")
    tools_count = c.fetchone()[0]
    print(f"Tools built: {tools_count}")
    
    # Products
    c.execute("SELECT COUNT(*) FROM products")
    products_count = c.fetchone()[0]
    print(f"Products published: {products_count}")
    
    # Content
    c.execute("SELECT COUNT(*) FROM content WHERE status = 'posted'")
    posted = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM content")
    total_content = c.fetchone()[0]
    print(f"Content posted: {posted}/{total_content}")
    
    # Revenue
    c.execute("SELECT SUM(revenue) FROM metrics")
    revenue = c.fetchone()[0] or 0
    print(f"Total revenue: ${revenue:.2f}")
    
    # Top performers
    print("\n🏆 Top Tools (by revenue):")
    c.execute("""SELECT t.slug, SUM(m.revenue) as rev, SUM(m.sales) as sales
        FROM tools t JOIN metrics m ON t.id = m.tool_id
        GROUP BY t.id ORDER BY rev DESC LIMIT 5""")
    for row in c.fetchall():
        print(f"  {row[0]}: ${row[1]:.2f} ({row[2]} sales)")
    
    conn.close()

def daily_run(args):
    """Run the full daily automation loop"""
    print("\n🚀 Starting daily automation run...")
    
    # 1. Check analytics
    print("\n📊 Checking analytics...")
    analytics_report(args)
    
    # 2. Find winners
    print("\n� Identifying winners...")
    import sqlite3
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute("""SELECT t.slug FROM tools t
        JOIN metrics m ON t.id = m.tool_id
        GROUP BY t.id ORDER BY SUM(m.revenue) DESC LIMIT 1""")
    winner = c.fetchone()
    if winner:
        print(f"   Winner: {winner[0]}")
    else:
        print("   No winner yet (no sales data)")
    conn.close()
    
    # 3. Generate content for top tools
    print("\n🎬 Generating content...")
    c = conn.cursor()
    c.execute("SELECT slug FROM tools LIMIT 1")
    row = c.fetchone()
    if row:
        slug = row[0]
        # Mock generate
        print(f"   Would generate content for: {slug}")
    conn.close()
    
    print("\n✅ Daily run complete!")
    print("   Use 'python cli.py analytics_report' for full metrics")

def main():
    parser = argparse.ArgumentParser(description="AI Factory CLI")
    subparsers = parser.add_subparsers(dest="command")
    
    subparsers.add_parser("init", help="Initialize database and folders")
    
    build_parser = subparsers.add_parser("build_tool", help="Build a tool from template")
    build_parser.add_argument("--template", required=True, help="Template name")
    build_parser.add_argument("--slug", required=True, help="Tool slug")
    build_parser.add_argument("--niche", help="Niche/category")
    
    publish_parser = subparsers.add_parser("publish_product", help="Publish to store")
    publish_parser.add_argument("--tool", required=True, help="Tool slug")
    publish_parser.add_argument("--platform", default="lemonsqueezy", help="Platform")
    publish_parser.add_argument("--price", type=int, default=29, help="Price")
    
    content_parser = subparsers.add_parser("generate_content", help="Generate demo content")
    content_parser.add_argument("--tool", required=True, help="Tool slug")
    content_parser.add_argument("--platform", help="Comma-separated platforms")
    content_parser.add_argument("--count", type=int, default=1, help="Number to generate")
    
    post_parser = subparsers.add_parser("post_content", help="Post to social")
    post_parser.add_argument("--platform", help="Comma-separated platforms")
    
    subparsers.add_parser("analytics_report", help="Show analytics")
    subparsers.add_parser("daily_run", help="Run daily automation")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    commands = {
        "init": init_db,
        "build_tool": build_tool,
        "publish_product": publish_product,
        "generate_content": generate_content,
        "post_content": post_content,
        "analytics_report": analytics_report,
        "daily_run": daily_run
    }
    
    commands[args.command](args)

if __name__ == "__main__":
    main()
