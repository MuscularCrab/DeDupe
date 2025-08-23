# DeDupe - Video Frame Deduplication Tool

DeDupe is a Windows application with a simple GUI that extracts frames from video files at a specified frame rate and automatically removes duplicate frames based on similarity.

## Features

- **Video Frame Extraction**: Extract frames at customizable FPS (1-60 frames per second)
- **Automatic Duplicate Detection**: Uses perceptual hashing to identify and remove similar frames
- **Adjustable Similarity Threshold**: Slider from 50% to 100% similarity (default: 95%)
- **Selective Area Processing**: Choose specific regions of video frames to process
- **User-Friendly GUI**: Simple and intuitive interface built with tkinter
- **Progress Tracking**: Real-time progress bar and status updates
- **Multiple Video Formats**: Supports MP4, AVI, MOV, MKV, and more

## Installation

### Option 1: Run from Source (Recommended for Development)

#### Prerequisites
- Python 3.7 or higher
- Windows operating system

#### Install Dependencies
1. Open Command Prompt or PowerShell
2. Navigate to the DeDupe directory
3. Install required packages:
```bash
pip install -r requirements.txt
```

### Option 2: Standalone Executable (Recommended for End Users)

#### Download and Run
1. Download `DeDupe.exe` from the releases
2. Double-click to run - no Python installation required
3. Works on any Windows machine

#### Build Your Own Executable
If you want to build the executable yourself:

1. **Install PyInstaller:**
   ```bash
   python -m pip install pyinstaller
   ```

2. **Build the executable:**
   ```bash
   python -m PyInstaller --clean DeDupe.spec
   ```
   
   Or use the provided batch file:
   ```bash
   build_exe.bat
   ```

3. **Find your executable:**
   - The standalone `.exe` file will be in the `dist/` folder
   - Size: approximately 63MB (includes all dependencies)
   - No additional files needed - completely self-contained

## Usage

1. **Run the Application**:
   ```bash
   python DeDupe.py
   ```

2. **Select Video File**:
   - Click "Browse" to select your video file
   - Supported formats: MP4, AVI, MOV, MKV, and more

3. **Configure Settings**:
   - **Frames per second**: Set extraction rate (default: 30 FPS)
   - **Similarity threshold**: Adjust duplicate detection sensitivity (default: 95%)
   - **Selective Area**: Enable to process only specific regions of frames
   - **Output directory**: Choose where to save extracted frames

4. **Start Processing**:
   - Click "Start Processing" to begin frame extraction
   - Monitor progress with the progress bar
   - Use "Stop" button to halt processing if needed

5. **Results**:
   - Extracted frames are saved as JPG images
   - Duplicate frames are automatically filtered out
   - Summary shows total frames saved and duplicates removed

## How It Works

### Frame Extraction
- Calculates frame interval based on video FPS and target extraction FPS
- Extracts frames at regular intervals throughout the video

### Duplicate Detection
- Uses perceptual hashing (dHash) algorithm
- Converts frames to 8x8 grayscale images
- Creates binary hash based on pixel intensity differences
- Compares hashes to identify similar frames

### Similarity Threshold
- Lower threshold (50-70%): More aggressive duplicate removal
- Higher threshold (90-100%): Only removes very similar frames
- Default 95% provides good balance between quality and deduplication

### Selective Area Processing
- **Enable Selective Area**: Check the checkbox to activate region selection
- **Area Selection**: Click "Start Processing" to open the area selection window
- **Visual Selection**: Click and drag on the video frame preview to select a region
- **Coordinate Display**: Shows exact pixel coordinates and dimensions of selected area
- **Region Processing**: Only the selected area will be processed for duplicates
- **Use Cases**: Focus on specific parts of videos (e.g., faces, text, moving objects)

## File Structure

```
DeDupe/
├── DeDupe.py          # Main application file
├── requirements.txt   # Python dependencies
├── DeDupe.spec        # PyInstaller configuration
├── build_exe.bat      # Windows batch file for building executable
├── dist/              # Output folder for executable (after building)
│   └── DeDupe.exe     # Standalone executable (63MB)
├── build/             # Build artifacts (can be deleted)
└── README.md          # This file
```

## Output

- Frames are saved as `frame_000001.jpg`, `frame_000002.jpg`, etc.
- Output directory is automatically created if it doesn't exist
- Default output: `[Video_Directory]/DeDupe_Output/`

## Troubleshooting

### Common Issues
1. **"No video selected"**: Make sure to browse and select a video file first
2. **"Error occurred"**: Check if video file is corrupted or unsupported
3. **Slow processing**: Large videos may take time; use lower FPS for faster processing

### Performance Tips
- Use lower FPS settings for faster processing
- Adjust similarity threshold based on your needs
- Ensure sufficient disk space for output frames

## System Requirements

- **OS**: Windows 7/8/10/11
- **Python**: 3.7 or higher
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: Sufficient space for extracted frames

## License

This project is open source and available under the MIT License.

## Support

For issues or questions, please check the troubleshooting section or create an issue in the project repository.