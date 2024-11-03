from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import subprocess
import logging
from pathlib import Path
import os
from datetime import datetime
import shutil

class StatsUpdater:
    def __init__(self, update_interval: int = 300):  # 300 seconds = 5 minutes
        """
        Initialize the statistics updater.
        
        Args:
            update_interval: Time between updates in seconds
        """
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Ensure we have a handler
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            self.logger.addHandler(handler)
            
        self.scheduler = BackgroundScheduler()
        self.update_interval = update_interval
        
        # Define paths
        self.base_path = Path('/app')
        self.analysis_script = self.base_path / 'data-analysis.py'
        self.static_path = self.base_path / 'static' / 'images' / 'stats'
        self.data_path = self.base_path / 'data'
        
        # Create stats directory if it doesn't exist
        self.static_path.mkdir(parents=True, exist_ok=True)
        
        # Copy data-analysis.py to the correct location if it's in a different place
        source_script = self.base_path / 'processing' / 'data-analysis.py'
        if source_script.exists():
            shutil.copy2(source_script, self.analysis_script)
            self.logger.info(f"Copied analysis script from {source_script} to {self.analysis_script}")

    def update_statistics(self):
        """Run the analysis script and update the statistics images."""
        try:
            self.logger.info("Starting statistics update...")
            
            # Debug information
            self.logger.info(f"Current working directory: {os.getcwd()}")
            self.logger.info(f"Analysis script path: {self.analysis_script}")
            self.logger.info(f"Static path: {self.static_path}")
            self.logger.info(f"Data path: {self.data_path}")
            
            # Check if the script exists
            if not self.analysis_script.exists():
                self.logger.error(f"Analysis script not found at {self.analysis_script}")
                return
                
            # Check if data files exist
            if not (self.data_path / 'results.csv').exists():
                self.logger.error(f"Data file not found at {self.data_path / 'results.csv'}")
                return
            
            # Print directory contents for debugging
            self.logger.info("Directory contents:")
            self.logger.info(f"/app: {os.listdir('/app')}")
            self.logger.info(f"/app/data: {os.listdir('/app/data')}")
            
            start_time = datetime.now()
            
            # Set up environment variables for the script
            env = os.environ.copy()
            env['DATA_DIR'] = str(self.data_path)
            
            # Run the analysis script
            result = subprocess.run(
                ['python', str(self.analysis_script)],
                capture_output=True,
                text=True,
                check=True,
                cwd=str(self.base_path),
                env=env
            )
            
            # Log the script output
            self.logger.info(f"Script output: {result.stdout}")
            if result.stderr:
                self.logger.warning(f"Script stderr: {result.stderr}")
            
            # Move generated images to static folder
            for image_name in ['accuracy_comparison.png', 'accuracy_trend.png']:
                source = self.base_path / image_name
                if source.exists():
                    destination = self.static_path / image_name
                    os.replace(source, destination)
                    self.logger.info(f"Moved {image_name} to static folder")
                else:
                    self.logger.warning(f"Generated image not found: {source}")
            
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"Statistics update completed in {duration:.2f} seconds")
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error running analysis script: {e}")
            self.logger.error(f"Script output: {e.output}")
            if e.stderr:
                self.logger.error(f"Script stderr: {e.stderr}")
        except Exception as e:
            self.logger.error(f"Unexpected error during statistics update: {e}")
            import traceback
            self.logger.error(traceback.format_exc())

    def start(self):
        """Start the periodic statistics updates."""
        # Run once immediately
        self.update_statistics()
        
        # Schedule periodic updates
        self.scheduler.add_job(
            self.update_statistics,
            trigger=IntervalTrigger(seconds=self.update_interval),
            id='stats_update',
            name='Update Statistics',
            replace_existing=True
        )
        
        self.scheduler.start()
        self.logger.info(f"Started statistics updater (interval: {self.update_interval} seconds)")

    def stop(self):
        """Stop the periodic statistics updates."""
        self.scheduler.shutdown()
        self.logger.info("Stopped statistics updater")