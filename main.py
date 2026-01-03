import asyncio
import aiohttp
import aiofiles
import os
import time
import cv2
import numpy as np
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm
import config

os.makedirs(config.SAVE_DIR, exist_ok=True)
os.makedirs(config.PROCESSED_DIR, exist_ok=True)

# -- ASYNCIO Task: Download with progress bar ---
async def download_image(session, url, filename, pbar ):
    """Download image from URL, save to folder and updates the shared progress bar"""

    try:
        async with session.get(url) as response:
            if response.status == 200:
                content = await response.read()
                async with aiofiles.open(os.path.join(config.SAVE_DIR, filename), "wb") as f:
                    await f.write(content)
                pbar.update(1)
                return filename
            else:
                print(f"Failed to download {filename}: {response.status}")
    except Exception as e:
        print(f"Error downloading {filename}: {e}")
        pbar.update(1)
        return None



# --- MULTIPROCESSING TASK: OpenCV Object Detection ---
def detect_stars_and_process(filename):
    """Detect stars and process image using OpenCV"""
    input_path = os.path.join(config.SAVE_DIR, filename)
    output_path = os.path.join(config.PROCESSED_DIR, f"detected_{filename}")

    #load image using OpenCV
    img = cv2.imread(input_path)
    if img is None:
        return f"Error loading {filename}"

    # Convert to grayscale for detection
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Setup SimpleBlobDetector parameters for star detection
    params = cv2.SimpleBlobDetector_Params()
    params.filterByColor = True
    params.blobColor = 255  # look for white blobs
    params.filterByArea = True
    params.minArea = 10  # Adjust based on image resolution

    detector = cv2. SimpleBlobDetector_create(params)
    keypoints = detector.detect(gray)

    # Draw detected stars as red circles
    img_with_keys = cv2.drawKeypoints(img, keypoints, None, (0,0,255), cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

    cv2.imwrite(output_path, img_with_keys)
    return f"Found {len(keypoints)} stars in {filename}"


async def main():

    # 1. Fetch Metadata
    async with aiohttp.ClientSession() as session:
        params = {
            "api_key": config.NASA_API_KEY,
            "count": 10,
        }
        async with session.get(config.BASE_URL, params=params) as response:
            data = await response.json()

        valid_items = [item for item in data if item.get("media_type") == "image"]

        # 2. Async  Download Phase (with tqdm progress bar)
        print(f"\n📡 Requesting {len(valid_items)} images from NASA...")
        download_pbar = tqdm(total=len(valid_items), desc="Downloading", unit="img")

        tasks = []
        for i, item in enumerate(valid_items):
            url = item.get("hdurl") or item.get("url")
            tasks.append(download_image(session, url, f"space_{i}.jpg", download_pbar))
        
        download_files = await asyncio.gather(*tasks)
        download_pbar.close()

        # Filter out failed downloads
        downloaded_files = [f for f in download_files if f]


    # 3. Multiprocessing Phase (with tqdm progress bar)
    print(f"\n🔭 Analyzing imagery with OpenCV on all CPU cores...")
    loop = asyncio.get_running_loop()

    results = []

    with ProcessPoolExecutor() as pool:
        # Wrap the list of tasks in tqdm
        pbar = tqdm(total=len(downloaded_files), desc="Analyzing", unit="img")

        # We create tasks and use a callback to update the progress bar
        for fname in downloaded_files:
            fut = loop.run_in_executor(pool, detect_stars_and_process, fname)
            fut.add_done_callback(lambda _: pbar.update(1))
            results.append(fut)

        
        # wait for all processing to finish
        analysis_summaries = await asyncio.gather(*results)
        pbar.close()

    print(f"\n✨ Project Summary! 🚀")
    for summary in analysis_summaries:
        print(f"🔍 {summary}")

if __name__ == "__main__":
    start = time.perf_counter()
    asyncio.run(main())
    end = time.perf_counter()
    print(f"\n🎉 Project completed in {end - start:.2f} seconds!")