import pandas as pd
import json
import argparse
from typing import Dict, Any
import logging

# python data_processor.py --results ../results/results.csv --config ../config.json --metadata ../static/images/muller_lyer_day1_metadata.json --output ../data/processed_data.csv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class MullerLyerDataProcessor:
    def __init__(self, results_path: str, config_path: str, metadata_path: str):
        self.results_path = results_path
        self.config_path = config_path
        self.metadata_path = metadata_path
        
        # Initialize storage for loaded data
        self.results_df = None
        self.config_data = None
        self.metadata = None
        
        # Create mappings
        self.quiz_config_map = {}
        self.image_metadata_map = {}
        
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
            
        # Load metadata
        try:
            with open(self.metadata_path, 'r') as f:
                self.metadata = json.load(f)
            logging.info(f"Loaded metadata for {len(self.metadata)} illusions")
        except Exception as e:
            logging.error(f"Error loading metadata file: {e}")
            raise
    
    def create_mappings(self) -> None:
        """Create lookup mappings from loaded data"""
        logging.info("Creating data mappings...")
        
        # Create quiz configuration mapping
        for quiz in self.config_data:
            quiz_id = quiz['id']
            self.quiz_config_map[quiz_id] = {
                'speed': quiz['speed'],
                'display_time': quiz['images'][0]['display_time'],
                'images': {
                    idx: {
                        'correct_answer': image['correct_answer'],
                        'metadata': image['metadata']
                    }
                    for idx, image in enumerate(quiz['images'])
                }
            }
            
        # Create image metadata mapping using filename as key
        for item in self.metadata:
            filename = item['svg_filename']
            self.image_metadata_map[filename] = item
    
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
                'line_length1': image_config['metadata']['line_length1'],
                'line_length2': image_config['metadata']['line_length2'],
                'actual_difference': image_config['metadata']['actual_difference'],
                'arrow_length': image_config['metadata']['arrow_length'],
                'angle': image_config['metadata']['angle'],
                'arrow_color': image_config['metadata']['arrow_color']
            }
            
            processed_records.append(record)
        
        # Convert to DataFrame
        processed_df = pd.DataFrame(processed_records)
        
        # Add is_correct column
        processed_df['is_correct'] = processed_df['user_answer'] == processed_df['correct_answer']
        
        logging.info(f"Created processed dataset with {len(processed_df)} records")
        return processed_df

def main():
    parser = argparse.ArgumentParser(description='Process Müller-Lyer experiment data')
    parser.add_argument('--results', required=True, help='Path to results CSV file')
    parser.add_argument('--config', required=True, help='Path to quiz configuration JSON file')
    parser.add_argument('--metadata', required=True, help='Path to illusion metadata JSON file')
    parser.add_argument('--output', required=True, help='Path for output CSV file')
    
    args = parser.parse_args()
    
    # Initialize and run processor
    processor = MullerLyerDataProcessor(
        results_path=args.results,
        config_path=args.config,
        metadata_path=args.metadata
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