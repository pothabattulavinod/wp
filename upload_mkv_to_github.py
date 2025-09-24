import os
import requests
import ffmpeg
from github import Github

# ---------- CONFIG ----------
MKV_URL = os.getenv("MKV_URL")
if not MKV_URL:
    raise ValueError("Please provide MKV_URL environment variable.")

OUTPUT_DIR = "hls_output"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = os.getenv("GITHUB_REPO")
GITHUB_FOLDER = "hls"
HLS_SEGMENT_FOLDER = "segments"
HLS_SEGMENT_DURATION = 10
# ----------------------------

os.makedirs(OUTPUT_DIR, exist_ok=True)
local_mkv = os.path.join(OUTPUT_DIR, "video.mkv")

# Download MKV
print(f"Downloading {MKV_URL} ...")
with requests.get(MKV_URL, stream=True) as r:
    r.raise_for_status()
    with open(local_mkv, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
print("✅ MKV downloaded")

# Convert to HLS
segment_path = os.path.join(OUTPUT_DIR, HLS_SEGMENT_FOLDER, "segment_%03d.ts")
os.makedirs(os.path.dirname(segment_path), exist_ok=True)
playlist_path = os.path.join(OUTPUT_DIR, "playlist.m3u8")

print("Converting to HLS ...")
ffmpeg.input(local_mkv).output(
    playlist_path,
    format="hls",
    hls_time=HLS_SEGMENT_DURATION,
    hls_list_size=0,
    hls_segment_filename=segment_path
).run(overwrite_output=True)
print("✅ Conversion complete")

# Upload to GitHub
print("Uploading to GitHub...")
if not GITHUB_TOKEN or not REPO_NAME:
    raise ValueError("GITHUB_TOKEN or GITHUB_REPO missing.")

g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

# Upload playlist
with open(playlist_path, "rb") as f:
    content = f.read()
try:
    repo.create_file(os.path.join(GITHUB_FOLDER, "playlist.m3u8"), "Upload playlist.m3u8", content)
    print("Uploaded playlist.m3u8 ✅")
except Exception as e:
    print(f"Skipping playlist.m3u8: {e}")

# Upload segments
segment_dir = os.path.join(OUTPUT_DIR, HLS_SEGMENT_FOLDER)
for file in sorted(os.listdir(segment_dir)):
    file_path = os.path.join(segment_dir, file)
    github_file_path = os.path.join(GITHUB_FOLDER, HLS_SEGMENT_FOLDER, file)
    with open(file_path, "rb") as f:
        content = f.read()
    try:
        repo.create_file(github_file_path, f"Upload {file}", content)
        print(f"Uploaded {file} ✅")
    except Exception as e:
        print(f"Skipping {file}: {e}")

print("🎉 All files uploaded successfully!")
