# VAR AI Detection System

A comprehensive AI-powered Video Assistant Referee (VAR) system for soccer match analysis with automated detection, team classification, and card tracking.

## Features

- **Frame-by-Frame Analysis**: Extract frames at customizable intervals (e.g., every 1-2 seconds)
- **AI-Powered Detection**: Uses Roboflow model for object/player detection
- **Team Classification**: Automatically assigns detected players to teams based on colors
- **Smart Card System**: 
  - Tracks yellow and red cards per team
  - Automatic red card when team gets 2 yellow cards
  - 5-minute reset window to avoid duplicate detections
- **Database Integration**: Full Supabase integration for data persistence
- **Organized Output**: Saves frames to organized folders with timestamps

## System Architecture

The system is organized into modular Python files:

- `config.py` - Configuration and settings
- `database_handler.py` - Supabase database operations
- `video_processor.py` - Video processing and frame extraction
- `team_manager.py` - Team classification and card management
- `var_detection_system.py` - Main system orchestrator
- `example_usage.py` - Usage examples and testing

## Installation

1. Install required packages:
```bash
pip install -r requirements.txt
```

2. Database Setup:
   - The system uses direct HTTP requests to Supabase (no additional library needed)
   - Supabase URL and API key are already configured in the code
   - Uses a single table `matchstatistics` for all data storage

3. Update Roboflow credentials in `config.py` if needed

## Quick Start

```python
from var_detection_system import VARDetectionSystem

# Configure teams
team_1_config = {"name": "Real Madrid", "color": "red"}
team_2_config = {"name": "Barcelona", "color": "blue"}

# Initialize system
var_system = VARDetectionSystem()

# Run complete analysis
results = var_system.run_complete_analysis(
    video_path="path/to/your/video.mp4",
    team_1_config=team_1_config,
    team_2_config=team_2_config,
    frame_interval=1.0,  # Extract frame every 1 second
    output_folder="./analysis_output"
)

print(f"Analysis complete! Game ID: {results['game_id']}")
```

## Database Schema

The system uses a single table `matchstatistics` in Supabase with the following structure:

```sql
CREATE TABLE matchstatistics (
    id SERIAL PRIMARY KEY,
    game_id INTEGER,
    timestamp FLOAT,
    classes_detected TEXT,
    frame_path TEXT,
    team_assignments TEXT,
    team TEXT,
    card_type TEXT,
    player_class TEXT,
    event_type TEXT,
    video_path TEXT,
    team_1_name TEXT,
    team_1_color TEXT,
    team_2_name TEXT,
    team_2_color TEXT,
    yellow_cards INTEGER DEFAULT 0,
    red_cards INTEGER DEFAULT 0,
    total_detections INTEGER DEFAULT 0,
    status TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

The `event_type` field distinguishes between different record types:
- `"game"` - Game session information
- `"detection"` - Frame detection results
- `"card"` - Card events (yellow/red cards)
- `"team_stats"` - Team statistics
```

## Configuration

Edit `config.py` to customize:

- **Frame extraction interval**: How often to extract frames (seconds)
- **Team colors and mappings**: Map detected classes to teams
- **Card rules**: Yellow-to-red card ratios, reset times
- **Database settings**: Supabase credentials
- **Output folders**: Where to save extracted frames

## Key Features Explained

### 1. Smart Duplicate Detection
- Prevents counting the same event multiple times
- 5-minute reset window (configurable)
- Per-player tracking to avoid false positives

### 2. Automatic Team Assignment
- Maps detected classes to teams based on colors
- Configurable class-to-team mapping
- Supports referees and neutral objects

### 3. Card Management System
- Tracks yellow/red cards per team
- Automatic red card after 2 yellows
- Database persistence for all events

### 4. Frame Organization
- Saves frames with timestamps in filenames
- Organized folder structure by session
- Optional cleanup of temporary files

## Usage Examples

### Basic Video Analysis
```python
# Run simple analysis
var_system = VARDetectionSystem()
game_id = var_system.setup_game(
    video_path="game.mp4",
    team_1_config={"name": "Team A", "color": "red"},
    team_2_config={"name": "Team B", "color": "blue"}
)

results = var_system.analyze_video("game.mp4", frame_interval=2.0)
```

### Custom Configuration
```python
# Custom frame interval and output
results = var_system.run_complete_analysis(
    video_path="match.mp4",
    team_1_config={"name": "Home", "color": "red"},
    team_2_config={"name": "Away", "color": "blue"},
    frame_interval=0.5,  # Every 0.5 seconds
    output_folder="./custom_output"
)
```

### Get Game Statistics
```python
# Get complete game summary
summary = var_system.get_game_summary(game_id)
print(f"Total detections: {len(summary['detections'])}")
print(f"Total cards: {len(summary['cards'])}")
```

## File Structure

```
VAR_AI/
├── config.py                 # Configuration settings
├── database_handler.py       # Supabase database operations
├── video_processor.py        # Video processing and AI predictions
├── team_manager.py          # Team classification and card tracking
├── var_detection_system.py  # Main system orchestrator
├── example_usage.py         # Usage examples
├── requirements.txt         # Python dependencies
├── README.md               # This file
└── your_videos/            # Place your video files here
```

## Troubleshooting

1. **Database Connection Issues**: Verify Supabase URL and API key in `config.py`
2. **Video Not Found**: Check video file path and permissions
3. **Model Prediction Errors**: Verify Roboflow API key and project settings
4. **Frame Extraction Issues**: Ensure OpenCV can read your video format

## Contributing

Feel free to extend the system by:
- Adding new detection classes
- Implementing advanced card rules
- Creating visualization dashboards
- Adding real-time processing capabilities

## License

This project is for educational and research purposes.
