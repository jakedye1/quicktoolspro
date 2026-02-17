#!/usr/bin/env python3
"""
Content Generator - Create demo videos from tool screenshots
Uses FFmpeg to create slideshow-style demo videos
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

TOOL_TEMPLATES = Path(__file__).parent / "tool_templates"
GENERATED_TOOLS = Path(__file__).parent.parent / "generated_tools"
CONTENT_RENDERS = Path(__file__).parent.parent / "content" / "renders"
THUMBNAILS = Path(__file__).parent.parent / "content" / "thumbnails"

def ensure_folders():
    """Create necessary folders"""
    CONTENT_RENDERS.mkdir(parents=True, exist_ok=True)
    THUMBNAILS.mkdir(parents=True, exist_ok=True)

def capture_tool_screenshot(tool_path, output_path):
    """Use Playwright or wkhtmltoimage to capture tool screenshot"""
    # For now, we'll assume the tool has a preview image or we'll use a placeholder
    # In production, you'd use Playwright to load the page and screenshot it
    
    index_file = Path(tool_path) / "index.html"
    if not index_file.exists():
        print(f"❌ No index.html found in {tool_path}")
        return None
    
    # Create a simple placeholder image with tool name
    tool_name = Path(tool_path).name.replace("-", " ").title()
    
    # Try to use screencapture via AppleScript for preview
    # For now, return None and we'll use text-based video
    return None

def generate_script(tool_name, tool_niche):
    """Generate a video script using the template"""
    
    templates = [
        f"🔥 FREE {tool_name} - Link in bio!\n\n"
        f"Stop guessing your profits. This free tool does the math for you.\n\n"
        f"✅ Fast\n✅ Free\n✅ Accurate\n\n"
        f"Check the link in my bio to try it now!",
        
        f"💰 {tool_name} - Free Tool\n\n"
        f"Ever wondered how much you're actually making?\n"
        f"Now you can calculate it in seconds.\n\n"
        f"Free tool - link in bio 👆",
        
        f"📊 {tool_name} is LIVE\n\n"
        f"I've been using this to track my profits and it's game-changing.\n"
        f"Completely free - no signup required.\n\n"
        f"👇 Link in bio to try it"
    ]
    
    return templates[0]  # Return first template for now

def generate_video_from_images(image_paths, output_path, duration_per_image=3):
    """Create video from a list of images using FFmpeg"""
    if not image_paths:
        print("❌ No images to create video from")
        return False
    
    # Create concat file
    concat_file = output_path.parent / "concat.txt"
    with open(concat_file, "w") as f:
        for img in image_paths:
            f.write(f"file '{img}'\n")
            f.write(f"duration {duration_per_image}\n")
    
    # FFmpeg command to create video
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-shortest",
        str(output_path)
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✅ Video created: {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}")
        return False

def generate_slideshow_video(tool_slug, tool_name, output_path):
    """Generate a simple text-based slideshow video"""
    
    # Create simple colored slides as images using sips (macOS) or Python
    # For simplicity, we'll create a video directly with FFmpeg using color slides
    
    # Generate title slide, feature slides, CTA slide
    slides = []
    
    # Colors for slides
    colors = ["#667eea", "#764ba2", "#11998e", "#38ef7d"]
    
    for i, (text, color) in enumerate([
        (f"📊 {tool_name}", colors[0]),
        ("Calculate Your Profits", colors[1]),
        ("Fast • Free • Accurate", colors[2]),
        ("Link in Bio!", colors[3])
    ]):
        slide_file = CONTENT_RENDERS / f"slide_{i}.png"
        slides.append(slide_file)
        
        # Create simple PNG with text using Python + PIL if available
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            img = Image.new('RGB', (1080, 1920), color=color)
            draw = ImageDraw.Draw(img)
            
            # Draw text centered
            # Use default font
            draw.text((540, 960), text, fill="white", anchor="mm")
            
            img.save(slide_file)
        except ImportError:
            # PIL not available, skip slide creation
            pass
    
    # Create video from slides
    if slides and all(s.exists() for s in slides):
        return generate_video_from_images([str(s) for s in slides], output_path)
    else:
        # Create a simple solid color video as fallback
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c=#667eea:s=1080x1920:d=5",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            str(output_path)
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"✅ Video created (fallback): {output_path}")
            return True
        except:
            return False

def generate_thumbnail(tool_name, output_path):
    """Create a thumbnail image for the video"""
    try:
        from PIL import Image, ImageDraw
        
        img = Image.new('RGB', (1280, 720), color="#667eea")
        draw = ImageDraw.Draw(img)
        
        # Draw tool name
        draw.text((640, 360), f"📊 {tool_name}", fill="white", anchor="mm")
        
        img.save(output_path)
        print(f"✅ Thumbnail created: {output_path}")
        return True
    except:
        print("⚠️ PIL not available, skipping thumbnail")
        return False

def generate_content_for_tool(tool_slug, platforms, count=1):
    """Generate content for a specific tool"""
    
    ensure_folders()
    
    # Find tool
    tool_path = GENERATED_TOOLS / tool_slug
    if not tool_path.exists():
        print(f"❌ Tool '{tool_slug}' not found")
        return
    
    # Load tool config
    config_file = tool_path / "config.json"
    if config_file.exists():
        with open(config_file) as f:
            config = json.load(f)
            tool_name = config.get("name", tool_slug)
            niche = config.get("niche", "general")
    else:
        tool_name = tool_slug.replace("-", " ").title()
        niche = "general"
    
    # Generate script
    script = generate_script(tool_name, niche)
    
    # Generate content for each platform
    for i in range(count):
        for platform in platforms:
            output_video = CONTENT_RENDERS / f"{tool_slug}_{platform}_{i+1}.mp4"
            thumbnail = THUMBNAILS / f"{tool_slug}_{platform}_{i+1}.jpg"
            
            # Generate video
            success = generate_slideshow_video(tool_slug, tool_name, output_video)
            
            if success:
                # Generate thumbnail
                generate_thumbnail(tool_name, thumbnail)
                
                # Generate hashtags
                hashtags = f"#{tool_slug.replace('-', '')} #{niche} #free #calculator #tool #sidehustle"
                
                print(f"✅ Generated {platform} content: {output_video}")
                print(f"   Caption: {script[:100]}...")
                print(f"   Hashtags: {hashtags}")
                
                # Save caption to file
                caption_file = CONTENT_RENDERS / f"{tool_slug}_{platform}_{i+1}_caption.txt"
                with open(caption_file, "w") as f:
                    f.write(f"{script}\n\n{hashtags}")
            else:
                print(f"❌ Failed to generate video for {platform}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Content Generator")
    parser.add_argument("--tool", required=True, help="Tool slug")
    parser.add_argument("--platform", default="youtube", help="Platform (youtube,pinterest)")
    parser.add_argument("--count", type=int, default=1, help="Number to generate")
    
    args = parser.parse_args()
    
    platforms = args.platform.split(",") if "," in args.platform else [args.platform]
    
    generate_content_for_tool(args.tool, platforms, args.count)

if __name__ == "__main__":
    main()
