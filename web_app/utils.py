import os
import subprocess
import openai
import json
from youtube_transcript_api import YouTubeTranscriptApi
from django.core.files.base import File
from .models import Reel
import glob
from django.conf import settings
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip


# OpenAI API Key
openai.api_key = 'your_openai_key_here'


def download_youtube_video(url, video):
    """Download YouTube video with merged best audio+video, extract title, and store path in DB."""
    videos_dir = os.path.join(settings.MEDIA_ROOT, "videos")
    os.makedirs(videos_dir, exist_ok=True)
    output_template = os.path.join(videos_dir, f"{video.video_id}.%(ext)s")

    # 🔹 Extract video title using yt-dlp
    title_command = ['yt-dlp', '--get-title', url]
    try:
        video_title = subprocess.check_output(title_command, text=True).strip()
        print(f"Extracted Title: {video_title}")
        video.title = video_title
        video.save()
    except subprocess.CalledProcessError as e:
        print(f"Error extracting title: {e}")
        video.title = f"Video {video.video_id}"
        video.save()

    # 🔹 Use best video + best audio to avoid `-f best` issues
    command = [
        'yt-dlp',
        url,
        '-f', 'bv*+ba/b',
        '--merge-output-format', 'mp4',
        '-o', output_template
    ]

    try:
        print(f"Downloading video: {video_title} from {url}")
        subprocess.run(command, check=True)
        print(f"✅ Download complete for video ID: {video.video_id}")

        matching_files = glob.glob(os.path.join(videos_dir, f"{video.video_id}.*"))
        if matching_files:
            actual_file_path = matching_files[0]
            print(f"Actual downloaded file: {actual_file_path}")
        else:
            print(f"❌ Could not find downloaded file for {video.video_id}")
            return

        with open(actual_file_path, "rb") as file:
            video.file_path.save(os.path.basename(actual_file_path), File(file))
        video.save()

        # 🔹 Extract duration
        try:
            clip = VideoFileClip(actual_file_path)
            video.duration = clip.duration
            video.save()
            print(f"📏 Saved video duration: {video.duration:.2f} seconds")
        except Exception as e:
            print(f"⚠️ Error extracting duration: {e}")

    except subprocess.CalledProcessError as e:
        print(f"❌ Error downloading video: {e}")


def get_youtube_transcript(video_id):
    """Fetch transcript of a YouTube video."""
    try:
        transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
        return [{"start_time": entry["start"], "end_time": entry["start"] + entry["duration"], "text": entry["text"]} for entry in transcript_data]
    except Exception as e:
        print(f"Could not retrieve transcript: {e}")
        return None

def extract_key_moments_with_labels(transcript_segments, num_reels):
    """
    Extract key moments using OpenAI, generate short labels,
    and return structured data including start_time, end_time, text, and label.
    """
    full_text = "\n".join([entry["text"] for entry in transcript_segments])
    
    try:
        # 🔹 Request key moments from OpenAI dynamically based on `num_reels`
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that only responds with JSON format."},
                {"role": "user", "content": (
                    f"Please return the best {num_reels} key moments as 'key_moments' list in JSON format, "
                    "with each moment containing 'start_time', 'end_time', and 'text'. "
                    "Ensure 'start_time' and 'end_time'"
                    "MAKE SURE TO RESPOND ONLY IN JSON FORMAT."
                )},
                {"role": "user", "content": full_text}
            ],
            max_tokens=500,
            temperature=0.5
        )
        print("🔍 Calling OpenAI ---><----")
        print(response)
        
        # Extract response content
        raw_response = response.choices[0].message.content.strip()
        print("Raw OpenAI response:", raw_response)  # Debugging

        # Parse the JSON response
        try:
            response_data = json.loads(raw_response)  
            key_moments_data = response_data["key_moments"]  # Extract key moments list
        except json.JSONDecodeError:
            print("Error: OpenAI response is not valid JSON. Please check the raw response.")
            return None
        except KeyError:
            print("Error: 'key_moments' field not found in OpenAI response.")
            return None

        # Convert time strings to seconds and generate short labels
        for moment in key_moments_data:
            # Convert start_time and end_time from "HH:MM:SS" to seconds
            moment["start_time"] = sum(int(x) * 60 ** i for i, x in enumerate(reversed(moment["start_time"].split(":"))))
            moment["end_time"] = sum(int(x) * 60 ** i for i, x in enumerate(reversed(moment["end_time"].split(":"))))

            # Generate a short label for the moment using OpenAI
            label_request = (
                f"Summarize the following key moment into a short title of 3-5 words:\n"
                "Do not change the start_time and end_time, only summarize the text!!!:\n"
                f"\"{moment['text']}\""
            )
            label_response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that creates concise titles."},
                    {"role": "user", "content": label_request}
                ],
                max_tokens=20,
                temperature=0.5
            )
            moment["label"] = label_response.choices[0].message.content.strip()

        return key_moments_data

    except Exception as e:
        print(f"Error while extracting key moments and generating labels: {e}")
        return None


def create_video_reels(video_file, video, key_moments, num_reels, reel_durations):
    """Generate video reels with subtitles (white text, black background)."""
    video_clip = VideoFileClip(video_file)

    for idx, moment in enumerate(key_moments[:num_reels]):
        start_time = moment["start_time"]
        end_time = moment["end_time"]

        if start_time < 0 or end_time > video_clip.duration:
            print(f"⚠️ Skipping invalid reel {idx+1}: Exceeds video limits.")
            continue

        clip = video_clip.subclip(start_time, end_time)

        # ✅ Create text clip with white text on black background (like subtitles)
        summary_text = moment["text"]

        text_clip = TextClip(
            summary_text,
            fontsize=24,  # Small text
            color='white',
            font='Liberation-Sans',
            size=(clip.w * 0.8, None),
            method='caption'
        ).set_duration(min(7, clip.duration)).set_position(("center", "bottom"))

        # ✅ Add black background behind the text
        text_clip = text_clip.on_color(
            size=(text_clip.w + 20, text_clip.h + 10),
            color=(0, 0, 0),  # Black background
            col_opacity=0.6
        ).set_position(("center", "bottom"))

        final_clip = CompositeVideoClip([clip, text_clip])

        # Save reel
        reel_filename = f"{video.video_id}_reel_{idx+1}.mp4"
        reel_path = os.path.join(settings.MEDIA_ROOT, "reels", reel_filename)

        print(f"▶️ Saving reel {idx+1}/{num_reels}: {reel_filename}")

        final_clip.write_videofile(
            reel_path, 
            codec="libx264", 
            audio_codec="aac",
            threads=4,
            fps=30
        )

        # Save to database
        reel = Reel.objects.create(
            video=video,
            start_time=start_time,
            end_time=end_time,
            label=moment["label"],
            summary=summary_text
        )

        with open(reel_path, "rb") as f:
            reel.file_path.save(reel_filename, File(f), save=True)

        print(f"[✅ Reel Saved] ID: {reel.id}, File: {reel.file_path.url}")

    print("🎬 Reel generation complete with subtitles and background.")
