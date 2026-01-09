import requests
import numpy as np
import time
import base64
import os
import hashlib
import json
from pathlib import Path
from pypdf import PdfReader
from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    concatenate_videoclips,
    CompositeVideoClip
)
from PIL import Image, ImageDraw, ImageFont
from openai import OpenAI

# Pillow compatibility
if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.Resampling.LANCZOS


# -------------------------------
# CLIENTS
# -------------------------------
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# -------------------------------
# UTILITIES
# -------------------------------
def prompt_hash(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def extract_text_from_file(file_path: Path) -> str:
    if file_path.suffix.lower() == ".pdf":
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text

    elif file_path.suffix.lower() == ".txt":
        return file_path.read_text(encoding="utf-8")

    else:
        raise ValueError("Unsupported file type")


# -------------------------------
# AI ANALYSIS
# -------------------------------
def analyze_chapter_with_ai(chapter_text: str) -> dict:
    prompt = f"""
You are an expert teacher.

Analyze the following book chapter and return JSON with:
- core_ideas
- key_lessons
- important_examples
- actionable_insights

Rewrite everything in simple, beginner-friendly language.

CHAPTER TEXT:
{chapter_text}
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4
    )

    content = response.choices[0].message.content
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {"raw_output": content}


def generate_reel_scripts(chapter_analysis: dict) -> list:
    prompt = f"""
You are an expert educational content creator.

TASK:
Create the OPTIMAL number of educational short-video reels from the content below.

GUIDELINES:
- Decide number of reels based on content depth
- Prefer fewer, deeper reels
- Each reel should explain ONE complete idea
- Spoken narration should be calm, clear, and teacher-like
- Ideal length per reel: 60–120 seconds

FOR EACH REEL, RETURN:
- reel_title
- spoken_narration
- on_screen_captions

OUTPUT FORMAT:
STRICT JSON ARRAY ONLY

SOURCE MATERIAL:
{json.dumps(chapter_analysis, indent=2)}
"""

    for _ in range(2):
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        text = response.choices[0].message.content.strip()

        if text.startswith("```"):
            text = text.split("```")[1].strip()

        if text.lower().startswith("json"):
            text = text[4:].strip()

        try:
            reels = json.loads(text)
            if isinstance(reels, list) and reels:
                return reels
        except json.JSONDecodeError:
            continue

    raise RuntimeError("Failed to generate reel scripts")


# -------------------------------
# IMAGE PROMPTS & GENERATION
# -------------------------------
def generate_image_prompts(reel_title: str, spoken_narration: str) -> dict:
    prompt = f"""
You are a visual director for educational short videos.

VISUAL STYLE:
- Illustrated, semi-realistic explainer style
- Clean digital illustration
- NO photorealism, NO text, NO logos

ASPECT RATIO: 9:16

OUTPUT JSON ONLY:
{{
  "images": [
    {{
      "image_id": 1,
      "description": "...",
      "prompt": "..."
    }}
  ]
}}

REEL TITLE:
{reel_title}

NARRATION:
{spoken_narration}
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4
    )

    text = response.choices[0].message.content.strip()

    if text.startswith("```"):
        text = text.split("```")[1].strip()

    if text.lower().startswith("json"):
        text = text[4:].strip()

    parsed = json.loads(text)
    if "images" not in parsed:
        raise ValueError("Invalid image prompt output")

    return parsed


def generate_image(prompt: str, output_path: Path, max_retries: int = 3):
    hf_token = os.getenv("HUGGINGFACE_TOKEN")
    if not hf_token:
        raise RuntimeError("HUGGINGFACE_TOKEN not set")

    model_id = "stabilityai/stable-diffusion-xl-base-1.0"
    url = f"https://router.huggingface.co/hf-inference/models/{model_id}"

    headers = {
        "Authorization": f"Bearer {hf_token}",
        "Accept": "image/png",
        "Content-Type": "application/json"
    }

    payload = {
        "inputs": prompt,
        "parameters": {
            "height": 1536,
            "width": 1024,
            "guidance_scale": 7.5,
            "num_inference_steps": 30
        }
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)

    for attempt in range(1, max_retries + 1):
        response = requests.post(url, headers=headers, json=payload, timeout=120)

        if response.status_code == 200:
            output_path.write_bytes(response.content)
            return

        if response.status_code in (429, 503):
            time.sleep(5 * attempt)
            continue

        raise RuntimeError(f"SDXL failed: {response.status_code}")

    raise RuntimeError("SDXL unavailable after retries")


# -------------------------------
# VOICEOVER
# -------------------------------
def generate_voiceover(text: str, output_path: Path):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")

    response = requests.post(
        "https://api.openai.com/v1/audio/speech",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "gpt-4o-mini-tts",
            "voice": "alloy",
            "input": text,
            "format": "mp3"
        }
    )

    if response.status_code != 200:
        raise RuntimeError("TTS failed")

    output_path.write_bytes(response.content)


# -------------------------------
# VIDEO ASSEMBLY
# -------------------------------
def assemble_video(
    images_dir: Path,
    audio_path: Path,
    output_path: Path
):
    image_files = sorted(images_dir.glob("image_*.png"))
    if not image_files:
        raise RuntimeError("No images found")

    audio = AudioFileClip(str(audio_path))
    duration = audio.duration
    duration_per_image = duration / len(image_files)

    clips = [
        ImageClip(str(img))
        .set_duration(duration_per_image)
        .resize(height=1536)
        .set_position("center")
        for img in image_files
    ]

    video = concatenate_videoclips(clips, method="compose").set_audio(audio)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    video.write_videofile(
        str(output_path),
        fps=30,
        codec="libx264",
        audio_codec="aac",
        verbose=False,
        logger=None
    )
