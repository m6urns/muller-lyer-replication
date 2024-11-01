import pandas as pd
import json
import argparse
from typing import Dict, Any, List
import logging
import os
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class MullerLyerDataProcessor:
    def __init__(self, results_path: str, config_path: str, metadata_dir: str):
        self.results_path = results_path
        self.config_path = config_path
        self.metadata_dir = metadata_dir
        
        # Initialize storage for loaded data
        self.results_df = None
        self.config_data = None
        self.metadata = []
        
        # Create mappings
        self.quiz_config_map = {}
        self.image_metadata_map = {}
        self.control_status_map = {}
        self.day_map = {}  # New mapping for day information
        
    def load_metadata_files(self) -> None:
        """Load all metadata files from the specified directory"""
        logging.info(f"Loading metadata files from {self.metadata_dir}")
        
        metadata_files = sorted([f for f in os.listdir(self.metadata_dir) 
                               if f.endswith('_metadata.json')])
        
        if not metadata_files:
            raise FileNotFoundError(f"No metadata files found in {self.metadata_dir}")
            
        for metadata_file in metadata_files:
            try:
                file_path = os.path.join(self.metadata_dir, metadata_file)
                with open(file_path, 'r') as f:
                    metadata_content = json.load(f)
                    self.metadata.extend(metadata_content)
                logging.info(f"Loaded metadata from {metadata_file}")
            except Exception as e:
                logging.error(f"Error loading metadata file {metadata_file}: {e}")
                raise
                
        logging.info(f"Loaded metadata for {len(self.metadata)} total illusions")
    
    def load_data(self) -> None:
        """Load all data sources"""
        logging.info("Loading data files...")
        
        # Load results CSV
        try:
            self.results_df = pd.read_csv(self.results_path)
            logging.info(f"Loaded {len(self.results_df)} results records")
        except Exception as e:
            logging.error(f"Error loading results file: {e}")
            raise
            
        # Load quiz config
        try:
            with open(self.config_path, 'r') as f:
                self.config_data = json.load(f)
            logging.info(f"Loaded configuration for {len(self.config_data)} quizzes")
        except Exception as e:
            logging.error(f"Error loading config file: {e}")
            raise
            
        # Load metadata files
        self.load_metadata_files()
    
    def create_mappings(self) -> None:
        """Create lookup mappings from loaded data"""
        logging.info("Creating data mappings...")
        
        # Create quiz configuration mapping
        for quiz in self.config_data:
            quiz_id = quiz['id']
            images = quiz['images']
            
            # Create a mapping for each image in the quiz
            image_configs = {}
            for idx, image in enumerate(images):
                # Extract filename from URL
                url = image['url']
                filename = os.path.basename(url)
                
                # Store the config and filename mapping
                image_configs[idx] = {
                    'correct_answer': image['correct_answer'],
                    'metadata': image['metadata'],
                    'filename': filename
                }
            
            self.quiz_config_map[quiz_id] = {
                'speed': quiz['speed'],
                'display_time': images[0]['display_time'],
                'images': image_configs
            }
            
        # Create metadata mappings
        for item in self.metadata:
            filename = item['svg_filename']
            self.image_metadata_map[filename] = item
            self.control_status_map[filename] = item.get('is_control', False)
            self.day_map[filename] = item['day']  # Add day information to mapping
    
    def process_data(self) -> pd.DataFrame:
        """Combine and process all data into a single DataFrame"""
        logging.info("Processing and combining data...")
        
        # Create a list to store processed records
        processed_records = []
        
        # Process each result
        for _, row in self.results_df.iterrows():
            quiz_id = row['Quiz ID']
            image_idx = row['Image Index']
            
            # Get quiz configuration for this response
            quiz_config = self.quiz_config_map[quiz_id]
            image_config = quiz_config['images'][image_idx]
            
            # Get the filename for this image
            filename = image_config['filename']
            
            # Get control status and day from metadata mapping
            is_control = self.control_status_map.get(filename, False)
            day = self.day_map.get(filename, None)
            
            # Create processed record
            record = {
                # User and response data
                'timestamp': row['Timestamp'],
                'user_id': row['User ID'],
                'quiz_id': quiz_id,
                'image_index': image_idx,
                'user_answer': row['Answer'],
                'response_time': row['Response Time'],
                
                # Quiz configuration data
                'speed_group': quiz_config['speed'],
                'display_time': quiz_config['display_time'],
                'correct_answer': image_config['correct_answer'],
                
                # Image metadata
                'day': day,  # Add day information
                'illusion_filename': filename,  # Add illusion filename
                'line_length1': image_config['metadata']['line_length1'],
                'line_length2': image_config['metadata']['line_length2'],
                'actual_difference': image_config['metadata']['actual_difference'],
                'arrow_length': image_config['metadata']['arrow_length'],
                'angle': image_config['metadata']['angle'],
                'arrow_color': image_config['metadata']['arrow_color'],
                'is_control': is_control
            }
            
            processed_records.append(record)
        
        # Convert to DataFrame
        processed_df = pd.DataFrame(processed_records)
        
        # Add is_correct column
        processed_df['is_correct'] = processed_df['user_answer'] == processed_df['correct_answer']
        
        # Reorder columns to put day and illusion_filename earlier in the DataFrame
        cols = processed_df.columns.tolist()
        reordered_cols = ['timestamp', 'user_id', 'day', 'quiz_id', 'image_index', 
                         'illusion_filename'] + [col for col in cols if col not in 
                         ['timestamp', 'user_id', 'day', 'quiz_id', 'image_index', 'illusion_filename']]
        processed_df = processed_df[reordered_cols]
        
        logging.info(f"Created processed dataset with {len(processed_df)} records")
        return processed_df

def main():
    parser = argparse.ArgumentParser(description='Process Müller-Lyer experiment data')
    parser.add_argument('--results', required=True, help='Path to results CSV file')
    parser.add_argument('--config', required=True, help='Path to quiz configuration JSON file')
    parser.add_argument('--metadata-dir', required=True, help='Directory containing metadata JSON files')
    parser.add_argument('--output', required=True, help='Path for output CSV file')
    
    args = parser.parse_args()
    
    # Initialize and run processor
    processor = MullerLyerDataProcessor(
        results_path=args.results,
        config_path=args.config,
        metadata_dir=args.metadata_dir
    )
    
    # Process data
    try:
        processor.load_data()
        processor.create_mappings()
        processed_df = processor.process_data()
        
        # Save processed data
        processed_df.to_csv(args.output, index=False)
        logging.info(f"Saved processed data to {args.output}")
        
    except Exception as e:
        logging.error(f"Error processing data: {e}")
        raise

if __name__ == "__main__":
    main()