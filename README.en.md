# Bad Apple Pixel Replacer

[한국어](README.md) | [English](README.en.md) | [日本語](README.ja.md)

A GUI program that replaces the black/white pixels of a high-contrast video (such as Bad Apple)
with two user-provided images, rendering the result as a mosaic-style video.

## Key Features

- Upload a source video, an image for black pixels, and an image for white pixels
- Optional background: supports still images as well as GIFs/videos, which loop automatically until the source video ends
- If the black/white images have a transparent background (PNG, etc.), the specified background shows through the transparent areas
- Adjustable FPS
- Adjustable resolution (horizontal cell count; vertical count is calculated automatically to match the source aspect ratio)
- Selectable pixel image quality (Low 32px / Medium 64px, recommended / High 96px)
- Supports Korean / English / Japanese (switch from the top-right corner of the app)
- Rendering runs on a separate thread so the GUI never freezes, with a progress bar

## Folder Structure

```
.
├── initial_setting.bat   # Run once: creates venv and installs required libraries
├── run.bat                # Run every time: activates venv and launches the GUI
├── main.py                # GUI + rendering logic
├── LICENSE                # MIT License
├── venv/                  # Auto-created by initial_setting.bat (gitignored)
└── result/                # Rendered output is saved here (auto-created, gitignored)
```

## Usage (Windows)

1. **One-time setup**: Double-click `initial_setting.bat`
   - Creates a `venv` folder
   - Automatically installs PySide6, opencv-python, pillow, imageio, imageio-ffmpeg, numpy
2. **Every time you run it**: Double-click `run.bat`
   - Activates the venv and opens the GUI window
3. In the GUI, configure the following:
   - Select the source video (mp4, avi, mov, mkv)
   - Select the image for black pixels
   - Select the image for white pixels
   - (Optional) Select a background image/video/GIF — only meaningful if your black/white images have a transparent background
   - Adjust FPS, resolution, and pixel image quality
4. Click **Render** → watch the progress bar → click **Open Folder** in the completion dialog to check the result
5. The output video is saved to `result/output.mp4`. Rendering again will overwrite the previous result.

## Requirements

- Python 3.9 or higher (must be added to PATH)
- Windows environment (for the batch files; on macOS/Linux, run `main.py` directly inside the venv for the same behavior)

## Notes

- To increase image quality, set "Pixel Image Quality" to High and/or raise the resolution (horizontal cell count).
  However, both increase the final video resolution, rendering time, and file size together.
  Note that each quality step increases pixel count quadratically, so it's recommended to test with Medium (64px) first.
- Using a video/GIF as the background can render somewhat slower than a static image (since the background must be re-prepared for every frame).
- The rendered video does not include audio (only the frames from the source video are used).

## License

This project is licensed under the [MIT License](LICENSE).
Copyright for the source video (e.g. Bad Apple) and any images you use belongs to their respective original creators; personal, non-commercial use is recommended.
