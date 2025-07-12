"""
Configuration file for VAR Events Detection System
Contains all settings and parameters for the AI VAR system
"""

class VAREventsConfig:
    """Configuration class for VAR Events Detection System"""
    
    # Roboflow API Configuration
    ROBOFLOW_API_KEY = "Bv1sz4LNm1SyGeIBwOr4"
    ROBOFLOW_WORKSPACE = "computer-vision-ju8c5"
    ROBOFLOW_PROJECT = "varai-v7upp"
    ROBOFLOW_VERSION = 2
    
    # Video Processing Settings
    FRAME_EXTRACTION_INTERVAL = 1.0  # Extract frame every N seconds
    FRAME_RESIZE_WIDTH = 640  # Resize frames to this width (maintains aspect ratio)
    FRAMES_OUTPUT_DIR = "./var_frames_output"
    
    # Detection Settings - No confidence threshold needed for classification
    # CONFIDENCE_THRESHOLD = 0.4  # Not used anymore
    
    # Event significance - all detected events are significant (no thresholds needed)
    # EVENT_SIGNIFICANCE_THRESHOLDS = {} # Not used anymore for classification
    
    # Event Types Configuration
    EVENT_TYPES = {
        'Yellow_Card': {
            'name': 'Yellow Card',
            'severity': 'high',
            'action': 'review_required',
            'description': 'Player received yellow card'
        },
        'Goal': {
            'name': 'Goal',
            'severity': 'high',
            'action': 'confirm_goal',
            'description': 'Goal scored'
        },
        'offside': {
            'name': 'Offside',
            'severity': 'high',
            'action': 'review_required',
            'description': 'Player in offside position'
        },
        'nothing': {
            'name': 'No Event',
            'severity': 'none',
            'action': 'none',
            'description': 'No significant event detected'
        }
    }
    
    # Output Settings
    OUTPUT_FORMAT = 'json'
    INCLUDE_ALL_FRAMES = True  # Include all frame analysis in output
    INCLUDE_FRAME_PATHS = True  # Include frame file paths in output
    
    # Database Settings (Supabase)
    SUPABASE_URL = "https://fhmqelqgizvxhkexfkul.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZobXFlbHFnaXp2eGhrZXhma3VsIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0ODE1NzAwMSwiZXhwIjoyMDYzNzMzMDAxfQ.lANLnGHnoHSbZppl8MndPmeKb1zhOsiXfpCdAbT2cRU"
    
    def __init__(self):
        """Initialize configuration and validate settings"""
        self.validate_config()
    
    def validate_config(self):
        """Validate configuration parameters"""
        if not self.ROBOFLOW_API_KEY:
            raise ValueError("ROBOFLOW_API_KEY must be set")
        
        if self.FRAME_EXTRACTION_INTERVAL <= 0:
            raise ValueError("FRAME_EXTRACTION_INTERVAL must be positive")
    
    def get_event_info(self, event_type: str) -> dict:
        """Get information about a specific event type"""
        return self.EVENT_TYPES.get(event_type, self.EVENT_TYPES['nothing'])
    
    def is_critical_event(self, event_type: str) -> bool:
        """Check if an event type is considered critical"""
        event_info = self.get_event_info(event_type)
        return event_info.get('severity') in ['critical', 'high']
