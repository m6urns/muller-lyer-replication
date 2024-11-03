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
        self.data_processor = self.base_path / 'data-processor.py'
        self.analysis_script = self.base_path / 'data-analysis.py'
        self.static_path = self.base_path / 'static' / 'images' / 'stats'
        self.data_path = self.base_path / 'data'
        
        # Create necessary directories
        self.static_path.mkdir(parents=True, exist_ok=True)
        self.data_path.mkdir(parents=True, exist_ok=True)

    def run_data_processor(self):
        """Run the data processor script to prepare data for analysis."""
        try:
            self.logger.info("Running data processor...")
            
            # Prepare paths for data processor arguments
            results_path = self.data_path / 'results.csv'  # Updated path
            config_path = self.base_path / 'config.json'
            metadata_dir = self.base_path / 'static' / 'images'
            output_path = self.data_path / 'processed_data.csv'
            
            # Debug info
            self.logger.info(f"Results path: {results_path}")
            self.logger.info(f"Results file exists: {results_path.exists()}")
            
            if not results_path.exists():
                self.logger.error("Results file not found")
                return False
            
            # Build command
            cmd = [
                'python', str(self.data_processor),
                '--results', str(results_path),
                '--config', str(config_path),
                '--metadata-dir', str(metadata_dir),
                '--output', str(output_path)
            ]
            
            # Run data processor
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            self.logger.info("Data processor completed successfully")
            if result.stdout:
                self.logger.info(f"Data processor output: {result.stdout}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error running data processor: {e}")
            self.logger.error(f"Data processor stderr: {e.stderr}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error in data processor: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False

    def update_statistics(self):
        """Run the data processor and analysis scripts to update statistics."""
        try:
            self.logger.info("Starting statistics update...")
            start_time = datetime.now()
            
            # First run the data processor
            if not self.run_data_processor():
                self.logger.error("Data processing failed, skipping analysis")
                return
            
            # Then run the analysis script
            result = subprocess.run(
                ['python', str(self.analysis_script)],
                capture_output=True,
                text=True,
                check=True,
                cwd=str(self.base_path),
                env=os.environ.copy()
            )
            
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