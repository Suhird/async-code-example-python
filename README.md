# Python Concurrent Example

A demonstration project showcasing how to combine **asyncio** (for I/O-bound operations) and **multiprocessing** (for CPU-bound operations) in Python to achieve efficient concurrent execution.

## What This Project Does

This project demonstrates a real-world use case of concurrent programming in Python:

1. **Downloads images from NASA's Astronomy Picture of the Day (APOD) API** using asyncio
   - Concurrently downloads multiple images simultaneously
   - Uses async/await for non-blocking I/O operations

2. **Processes images using OpenCV** for star detection using multiprocessing
   - Analyzes each downloaded image across multiple CPU cores
   - Detects stars using OpenCV's blob detection
   - Draws detected stars on the images

3. **Shows progress** with visual progress bars using `tqdm`

### Key Concepts Demonstrated

- **Asyncio**: For I/O-bound operations (downloading images from the internet)
- **Multiprocessing**: For CPU-bound operations (image processing with OpenCV)
- **ProcessPoolExecutor**: Runs CPU-intensive tasks in separate processes
- **asyncio.gather()**: Runs multiple coroutines concurrently
- **loop.run_in_executor()**: Bridges async code with blocking functions

For detailed explanations of these concepts, see [EXPLANATION.md](EXPLANATION.md).

## Requirements

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (Python package installer and resolver)
- NASA API key (free from [NASA API](https://api.nasa.gov/))

## Setup

1. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Clone this repository** (or navigate to the project directory)

3. **Create virtual environment and install dependencies**:
   ```bash
   uv sync
   ```
   This command will:
   - Create a `.venv` folder
   - Install all dependencies from `pyproject.toml`

4. **Configure NASA API Key**:
   - Get your free API key from [NASA API](https://api.nasa.gov/)
   - Edit `config.py` and replace `YOUR_NASA_API_KEY_HERE` with your API key
   - Or use the demo key (has rate limits)

## Running the Project

**Option 1: Using uv (Recommended)**
```bash
uv run python main.py
```

**Option 2: Activate virtual environment first**
```bash
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate     # On Windows

python main.py
```

## What to Expect

The script will:

1. **Fetch metadata** from NASA APOD API
2. **Download images** concurrently (you'll see a progress bar)
   - Images are saved to `space_images/` directory
3. **Process images** using all CPU cores (you'll see another progress bar)
   - Processed images with detected stars are saved to `processed_images/` directory
4. **Display results** showing how many stars were detected in each image
5. **Show total execution time**

### Example Output

```
📡 Requesting 10 images from NASA...
Downloading: 100%|████████████████| 10/10 [00:02<00:00,  4.2img/s]

🔭 Analyzing imagery with OpenCV on all CPU cores...
Analyzing: 100%|████████████████| 10/10 [00:02<00:00,  4.5img/s]

✨ Project Summary! 🚀
🔍 Found 15 stars in space_0.jpg
🔍 Found 23 stars in space_1.jpg
...
🎉 Project completed in 4.52 seconds!
```

## Project Structure

```
.
├── main.py              # Main application code
├── config.py            # Configuration (API key, directories)
├── pyproject.toml       # Project dependencies
├── EXPLANATION.md       # Detailed explanation of concurrency concepts
├── space_images/        # Downloaded images (gitignored)
└── processed_images/    # Processed images with detected stars (gitignored)
```

## Dependencies

- `aiohttp` - Async HTTP client for downloading images
- `aiofiles` - Async file I/O
- `opencv-python` - Computer vision library for image processing
- `tqdm` - Progress bars
- `pillow` - Image processing library

## Performance Benefits

This concurrent approach provides significant performance improvements:

- **Sequential approach**: ~30 seconds (downloads one-by-one, processes one-by-one)
- **Concurrent approach**: ~4-5 seconds (downloads concurrently, processes in parallel)
- **~7x faster!** 🚀

## Learn More

For detailed explanations of the concurrency concepts used in this project, see [EXPLANATION.md](EXPLANATION.md).

## License

This is an educational example project.

