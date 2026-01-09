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

    try:
        response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4
        )
    except Exception as e:
        raise SystemFailure(f"LLM analysis failed: {e}") from e
    

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

    raise SystemFailure("Failed to generate reel scripts")


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
        raise SystemFailure("Invalid image prompt output")

    return parsed


def generate_image(prompt: str, output_path: Path, max_retries: int = 3):
    hf_token = os.getenv("HUGGINGFACE_TOKEN")
    if not hf_token:
        # 🚨 System misconfiguration → refundable
        raise SystemFailure("HUGGINGFACE_TOKEN not set")

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
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=120
            )
        except Exception as e:
            # 🚨 Network / request failure → refundable
            raise SystemFailure(f"SDXL request failed: {e}") from e

        if response.status_code == 200:
            output_path.write_bytes(response.content)
            return

        # Retry-safe HF failures
        if response.status_code in (429, 503):
            time.sleep(5 * attempt)
            continue

        # 🚨 Hard HF failure → refundable
        raise SystemFailure(
            f"SDXL failed: {response.status_code} {response.text}"
        )

    # 🚨 All retries exhausted → refundable
    raise SystemFailure("SDXL unavailable after retries")



# -------------------------------
# VOICEOVER
# -------------------------------
def generate_voiceover(text: str, output_path: Path):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # 🚨 System misconfiguration → refundable
        raise SystemFailure("OPENAI_API_KEY not set")

    try:
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
            },
            timeout=120
        )
    except Exception as e:
        # 🚨 Network / request failure → refundable
        raise SystemFailure(f"TTS request failed: {e}") from e

    if response.status_code != 200:
        # 🚨 OpenAI TTS failure → refundable
        raise SystemFailure(
            f"TTS failed: {response.status_code} {response.text}"
        )

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


# =========================================================
# INTERNAL PIPELINE STAGES (STEP 3)
# =========================================================

def stage_analyze_input(input_type: str, config: dict, output_dir: Path) -> dict:
    if input_type == "pdf":
        pdf_path = Path(config["pdf_path"])
        source_text = extract_text_from_file(pdf_path)

    elif input_type == "text":
        source_text = config.get("text", "").strip()
        if not source_text:
            raise UserContentError("Empty text input")

    elif input_type == "prompt":
        prompt = config.get("prompt", "").strip()
        if not prompt:
            raise UserContentError("Empty prompt input")

        analysis = analyze_chapter_with_ai(prompt)
        source_text = analysis.get("raw_output", prompt)

    else:
        raise UserContentError("Unsupported input_type")

    analysis = analyze_chapter_with_ai(source_text)
    reels = generate_reel_scripts(analysis)

    (output_dir / "source_text.txt").write_text(source_text, encoding="utf-8")
    (output_dir / "analysis.json").write_text(json.dumps(analysis, indent=2), encoding="utf-8")
    (output_dir / "reels.json").write_text(json.dumps(reels, indent=2), encoding="utf-8")

    return {
        "source_text": source_text,
        "analysis": analysis,
        "reels": reels
    }


# =========================================================
# FAILURE CLASSIFICATION (STEP 5)
# =========================================================

class EngineError(Exception):
    """Base class for engine failures."""


class SystemFailure(EngineError):
    """
    Indicates a system-side failure.
    Eligible for credit refund.
    """
    pass


class UserContentError(EngineError):
    """
    Indicates user input / content issue.
    NOT eligible for refund.
    """
    pass






# =========================================================
# JOB PATH HELPERS (STEP 4)
# =========================================================

def get_reel_dir(output_dir: Path, reel_index: int) -> Path:
    """
    Returns the directory for a specific reel.
    Enforces consistent job-safe structure.
    """
    return output_dir / f"reel_{reel_index:02d}"


def get_images_dir(reel_dir: Path) -> Path:
    """
    Returns the images directory for a reel.
    """
    return reel_dir / "images"




def stage_generate_assets(reels: list, output_dir: Path) -> list:
    assets = []

    for idx, reel in enumerate(reels, start=1):
        
        reel_dir = get_reel_dir(output_dir, idx)
        images_dir = get_images_dir(reel_dir)

        reel_dir.mkdir(parents=True, exist_ok=True)
        images_dir.mkdir(parents=True, exist_ok=True)

        narration = reel.get("spoken_narration", "").strip()
        if not narration:
            continue

        audio_path = reel_dir / "voiceover.mp3"
        generate_voiceover(narration, audio_path)

        image_plan = generate_image_prompts(
            reel_title=reel.get("reel_title", f"Reel {idx}"),
            spoken_narration=narration
        )

        (reel_dir / "image_prompts.json").write_text(
            json.dumps(image_plan, indent=2),
            encoding="utf-8"
        )

        for image in image_plan.get("images", []):
            image_id = image.get("image_id")
            prompt = image.get("prompt")
            if not prompt:
                continue

            image_path = images_dir / f"image_{image_id:02d}.png"
            generate_image(prompt, image_path)

        assets.append({
            "reel_index": idx,
            "reel_dir": reel_dir,
            "images_dir": images_dir,
            "audio_path": audio_path
        })

    return assets


def stage_assemble_videos(assets: list, output_dir: Path) -> list:
    final_videos = []

    for asset in assets:
        reel_dir = asset["reel_dir"]
        images_dir = asset["images_dir"]
        audio_path = asset["audio_path"]

        final_video_path = reel_dir / "final_video.mp4"

        assemble_video(
            images_dir=images_dir,
            audio_path=audio_path,
            output_path=final_video_path
        )

        if final_video_path.exists():
            final_videos.append(str(final_video_path))

    return final_videos



# =========================================================
# ENGINE ENTRY POINT (Perpixa Contract)
# =========================================================

def run_job(
    job_id: str,
    user_id: str,
    config: dict,
    output_dir: str | Path
) -> dict:
    """
    Executes ONE complete video generation job.

    Rules:
    - One job = one output directory
    - No global state
    - All outputs MUST stay inside output_dir
    - Raise exceptions on system failure
    """

    # -------------------------------
    # 0. PREPARE JOB DIRECTORY
    # -------------------------------
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------------
    # 1. INPUT TYPE VALIDATION
    # -------------------------------
    input_type = config.get("input_type")
    if not input_type:
        raise UserContentError("input_type is required in config")

    # -------------------------------
    # 2. PIPELINE EXECUTION (STEP 5)
    # -------------------------------
    try:
        pipeline = stage_analyze_input(
            input_type=input_type,
            config=config,
            output_dir=output_dir
        )

        assets = stage_generate_assets(
            reels=pipeline["reels"],
            output_dir=output_dir
        )

        videos = stage_assemble_videos(
            assets=assets,
            output_dir=output_dir
        )

    except SystemFailure:
        # System failure → bubble up (refund eligible)
        raise

    except UserContentError as e:
        # User/content error → no refund
        return {
            "job_id": job_id,
            "user_id": user_id,
            "status": "failed",
            "reason": "user_content_error",
            "message": str(e),
            "output_dir": str(output_dir)
        }

    except Exception as e:
        # Unknown error → treat as system failure (refund eligible)
        raise SystemFailure(f"Unhandled engine error: {e}") from e

    # -------------------------------
    # 3. RETURN METADATA (SUCCESS)
    # -------------------------------
    return {
        "job_id": job_id,
        "user_id": user_id,
        "status": "completed",
        "reels_created": len(videos),
        "videos": videos,
        "output_dir": str(output_dir)
    }

