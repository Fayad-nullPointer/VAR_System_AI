"""
VAR Events Detection System
AI-powered Video Assistant Referee for detecting soccer events
"""

import cv2
import os
import json
import numpy as np
from datetime import datetime
from roboflow import Roboflow
from var_events_config import VAREventsConfig

class VAREventsSystem:
    def __init__(self, config: VAREventsConfig):
        """Initialize the VAR Events Detection System"""
        self.config = config
        self.rf = None
        self.model = None
        self.results = []
        
        # Initialize Roboflow
        try:
            self.rf = Roboflow(api_key=config.ROBOFLOW_API_KEY)
            project = self.rf.workspace(config.ROBOFLOW_WORKSPACE).project(config.ROBOFLOW_PROJECT)
            self.model = project.version(config.ROBOFLOW_VERSION).model
            print(f"✓ Roboflow model loaded successfully: {config.ROBOFLOW_PROJECT}")
        except Exception as e:
            print(f"✗ Error loading Roboflow model: {e}")
            raise
    
    def extract_frames(self, video_path: str, output_dir: str = None) -> list:
        """Extract frames from video at specified intervals"""
        if output_dir is None:
            output_dir = self.config.FRAMES_OUTPUT_DIR
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0
        
        print(f"Video info: {fps:.2f} FPS, {total_frames} frames, {duration:.2f}s duration")
        
        frame_paths = []
        frame_interval = int(fps * self.config.FRAME_EXTRACTION_INTERVAL)
        frame_count = 0
        saved_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Save frame at specified intervals
            if frame_count % frame_interval == 0:
                timestamp = frame_count / fps if fps > 0 else 0
                frame_filename = f"frame_{saved_count:06d}_t{timestamp:.1f}s.jpg"
                frame_path = os.path.join(output_dir, frame_filename)
                
                # Resize frame if needed
                if self.config.FRAME_RESIZE_WIDTH:
                    height, width = frame.shape[:2]
                    new_width = self.config.FRAME_RESIZE_WIDTH
                    new_height = int(height * new_width / width)
                    frame = cv2.resize(frame, (new_width, new_height))
                
                cv2.imwrite(frame_path, frame)
                frame_paths.append({
                    'path': frame_path,
                    'timestamp': timestamp,
                    'frame_number': frame_count
                })
                saved_count += 1
                print(f"Extracted frame {saved_count}: {frame_filename}")
            
            frame_count += 1
        
        cap.release()
        print(f"✓ Extracted {len(frame_paths)} frames from video")
        return frame_paths
    
    def analyze_frame(self, frame_path: str) -> dict:
        """Analyze a single frame for VAR events"""
        try:
            # Run inference - no confidence threshold, just classify
            prediction = self.model.predict(frame_path)
            
            # Parse results for classification model
            if hasattr(prediction, 'json'):
                result = prediction.json()
                
                # Check if we have predictions
                if 'predictions' in result and result['predictions']:
                    pred = result['predictions'][0]
                    
                    # Method 1: Check 'top' field (most likely class)
                    if 'top' in pred and pred['top']:
                        event_type = pred['top']
                        confidence = pred.get('confidence', 0.0)
                    
                    # Method 2: Check nested predictions array
                    elif 'predictions' in pred and pred['predictions']:
                        best_prediction = max(pred['predictions'], key=lambda x: x.get('confidence', 0))
                        event_type = best_prediction.get('class', 'nothing')
                        confidence = best_prediction.get('confidence', 0.0)
                    
                    else:
                        event_type = 'nothing'
                        confidence = 0.0
                    
                    return {
                        'event': event_type,
                        'confidence': confidence,
                        'raw_predictions': result
                    }
                else:
                    return {
                        'event': 'nothing',
                        'confidence': 0.0,
                        'raw_predictions': result
                    }
            else:
                return {
                    'event': 'nothing',
                    'confidence': 0.0,
                    'raw_predictions': []
                }
                
        except Exception as e:
            print(f"Error analyzing frame {frame_path}: {e}")
            return {
                'event': 'nothing',
                'confidence': 0.0,
                'error': str(e)
            }
    
    def is_significant_event(self, event_type: str, confidence: float) -> bool:
        """Check if an event is significant - all non-nothing events are significant"""
        if event_type == 'nothing':
            return False
        
        # All detected events (non-nothing) are considered significant
        return True
    
    def is_duplicate_event(self, current_event: dict, previous_events: list) -> bool:
        """Check if current event is a duplicate of recent events"""
        if not previous_events:
            return False
        
        # Check if the last event is the same type
        last_event = previous_events[-1]
        return (last_event['event'] == current_event['event'] and 
                current_event['event'] != 'nothing')
    
    def filter_unique_events(self, events: list) -> list:
        """Filter events and handle multiple Yellow Cards properly"""
        unique_events = []
        yellow_card_count = 0
        yellow_card_timestamps = []
        seen_events = set()
        
        for event in events:
            event_type = event['event']
            
            # Skip 'nothing' events entirely
            if event_type == 'nothing':
                continue
            
            # Special handling for Yellow Cards
            if event_type == 'Yellow_Card':
                yellow_card_count += 1
                yellow_card_timestamps.append(event['timestamp'])
            else:
                # For other events, only add if we haven't seen this event type before
                if event_type not in seen_events:
                    unique_events.append(event)
                    seen_events.add(event_type)
        
        # Add Yellow Cards with proper numbering
        for i, timestamp in enumerate(yellow_card_timestamps, 1):
            yellow_event = {
                'event': f'Yellow_Card_{i}',
                'timestamp': timestamp,
                'original_event': 'Yellow_Card'
            }
            
            # Add note for second yellow card
            if i == 2:
                yellow_event['note'] = 'Second yellow = Red card'
            
            unique_events.append(yellow_event)
        
        return unique_events
    
    def process_video(self, video_path: str) -> dict:
        """Process entire video and analyze all frames"""
        print(f"🎬 Processing video: {video_path}")
        start_time = datetime.now()
        
        # Extract frames
        frame_data = self.extract_frames(video_path)
        
        # Analyze each frame
        all_events = []
        for i, frame_info in enumerate(frame_data):
            print(f"Analyzing frame {i+1}/{len(frame_data)}: {os.path.basename(frame_info['path'])}")
            
            # Analyze frame
            analysis = self.analyze_frame(frame_info['path'])
            
            # Create event record
            event = {
                'timestamp': frame_info['timestamp'],
                'frame_number': frame_info['frame_number'],
                'frame_path': os.path.relpath(frame_info['path']),
                'event': analysis['event'],
                'confidence': analysis['confidence'],
                'significant': self.is_significant_event(analysis['event'], analysis['confidence']),
                'duplicate': self.is_duplicate_event(analysis, all_events)
            }
            
            all_events.append(event)
            
            # Print event info
            if event['event'] != 'nothing':
                status = "🚨 SIGNIFICANT" if event['significant'] else "📝 detected"
                duplicate_info = " (DUPLICATE)" if event['duplicate'] else ""
                print(f"  → {status}: {event['event']} (confidence: {event['confidence']:.4f}){duplicate_info}")
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Generate analysis summary
        analysis_summary = self.generate_analysis_summary(
            video_path, all_events, processing_time
        )
        
        # Save results
        self.results = all_events
        
        print(f"✅ Video processing completed in {processing_time:.2f} seconds")
        print(f"📊 Total events detected: {len([e for e in all_events if e['event'] != 'nothing'])}")
        print(f"⚡ Significant events: {len([e for e in all_events if e['significant']])}")
        
        return analysis_summary
    
    def generate_analysis_summary(self, video_path: str, events: list, processing_time: float) -> dict:
        """Generate comprehensive analysis summary"""
        
        # Filter to get unique events only
        unique_events = self.filter_unique_events(events)
        
        # Calculate statistics
        total_events = len([e for e in events if e['event'] != 'nothing'])
        significant_events = [e for e in events if e['significant']]
        
        # Count events by type
        event_counts = {}
        confidence_sums = {}
        confidence_counts = {}
        
        for event in events:
            event_type = event['event']
            confidence = event['confidence']
            
            # Count events
            if event_type in event_counts:
                event_counts[event_type] += 1
            else:
                event_counts[event_type] = 1
            
            # Sum confidences for averaging
            if event_type in confidence_sums:
                confidence_sums[event_type] += confidence
                confidence_counts[event_type] += 1
            else:
                confidence_sums[event_type] = confidence
                confidence_counts[event_type] = 1
        
        # Calculate average confidences
        average_confidences = {
            event_type: confidence_sums[event_type] / confidence_counts[event_type]
            for event_type in confidence_sums
        }
        
        # Create timeline with unique events only - simplified format
        timeline = []
        for event in unique_events:
            event_data = {
                'event': event['event'],
                'timestamp': event['timestamp']
            }
            
            # Add note for special cases (like second yellow card)
            if 'note' in event:
                event_data['note'] = event['note']
                
            timeline.append(event_data)
        
        # Create simplified analysis summary
        summary = {
            'video_info': {
                'filename': os.path.basename(video_path),
                'processed_at': datetime.now().isoformat()
            },
            'events_detected': timeline
        }
        
        return summary
    
    def save_results(self, results: dict, output_path: str = None) -> str:
        """Save analysis results to JSON file"""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"var_analysis_results_{timestamp}.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"📁 Results saved to: {output_path}")
        return output_path

def main():
    """Main function for testing the VAR Events System"""
    # Load configuration
    config = VAREventsConfig()
    
    # Initialize system
    var_system = VAREventsSystem(config)
    
    # Initialize database handler
    try:
        from supabase_handler import SupabaseHandler
        db = SupabaseHandler(config)
        database_available = True
        print("✅ Database connection established")
    except Exception as e:
        print(f"⚠️ Database not available: {e}")
        database_available = False
    
    # Process test video
    test_video = "/home/ahmed-fayad/Projects/VAR_AI/Offside Clip 2(360P).mp4"
    
    if os.path.exists(test_video):
        print("🚀 Starting VAR Events Analysis...")
        
        # Process video
        results = var_system.process_video(test_video)
        
        # Save results to JSON file
        output_file = var_system.save_results(results)
        
        # Save results to database
        if database_available:
            print("\n💾 Saving to database...")
            db_success = db.save_analysis_results(results, test_video)
            if db_success:
                print("✅ Results saved to database successfully!")
            else:
                print("❌ Failed to save to database")
        
        # Print summary
        print("\n" + "="*60)
        print("📊 ANALYSIS SUMMARY")
        print("="*60)
        print(f"Video: {results['video_info']['filename']}")
        
        print("\n🎯 EVENTS DETECTED:")
        if results['events_detected']:
            for event in results['events_detected']:
                event_info = f"  • {event['event']} at {event['timestamp']:.1f}s"
                if 'note' in event:
                    event_info += f" ({event['note']})"
                print(event_info)
        else:
            print("  • No events detected")
        
        print(f"\n📁 JSON results saved to: {output_file}")
        if database_available:
            print("💾 Database results saved to Supabase")
        
    else:
        print(f"❌ Test video not found: {test_video}")

if __name__ == "__main__":
    main()
