import json
import os
import re
from typing import List, Dict
import logging
import argparse
import random

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def load_metadata(file_path: str) -> List[Dict]:
    logging.debug(f"Attempting to load metadata from: {file_path}")
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        logging.debug(f"Successfully loaded metadata with {len(data)} items")
        return data
    except FileNotFoundError:
        logging.error(f"Metadata file not found: {file_path}")
        return []
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON from file: {file_path}")
        return []

def generate_quiz_config(metadata: List[Dict], day: int, display_time: float, speed: str, quiz_id: int, randomize: bool = True) -> Dict:
    logging.debug(f"Generating {speed} quiz config for day {day} with {len(metadata)} illusions")
    quiz = {
        "id": quiz_id,
        "title": f"Müller-Lyer Illusion Quiz - Day {day} ({speed.capitalize()})",
        "speed": speed,
        "images": []
    }

    image_configs = []
    for illusion in metadata:
        image_config = {
            "url": f"/static/images/{illusion['svg_filename']}",
            "display_time": display_time,
            "question": "Which line appears longer?",
            "options": ["Left", "Right", "Same length"],
            "correct_answer": "Same length" if illusion['same_length'] else ("Left" if illusion['actual_difference'] > 0 else "Right"),
            "metadata": {
                "line_length1": illusion['line_length1'],
                "line_length2": illusion['line_length2'],
                "actual_difference": illusion['actual_difference'],
                "arrow_length": illusion['arrow_length'],
                "angle": illusion['angle'],
                "line_thickness": illusion['line_thickness'], 
                "arrow_color": illusion.get('arrow_color', 'black')
            }
        }
        image_configs.append(image_config)
        
    if randomize:
        random.shuffle(image_configs)
    quiz["images"] = image_configs

    logging.debug(f"Generated {speed} quiz for day {day} with {len(quiz['images'])} images")
    return quiz

def extract_day_number(filename: str) -> int:
    """Extract the day number from a metadata filename."""
    match = re.search(r'day(\d+)', filename)
    if match:
        return int(match.group(1))
    return 0

def generate_quizzes(base_folder: str, fast_time: float, slow_time: float, single_set: bool, randomize: bool = True) -> List[Dict]:
    logging.info(f"Generating quizzes from base folder: {base_folder}")
    quizzes = []
    if not os.path.exists(base_folder):
        logging.error(f"Base folder does not exist: {base_folder}")
        return quizzes

    # Get metadata files and sort them by day number
    metadata_files = [f for f in os.listdir(base_folder) if f.endswith('_metadata.json')]
    metadata_files.sort(key=extract_day_number)  # Sort files based on day number

    quiz_id = 0
    for metadata_file in metadata_files:
        day = extract_day_number(metadata_file)
        if day > 0:  # Only process if we successfully extracted a day number
            logging.debug(f"Processing metadata for day {day}")
            metadata_path = os.path.join(base_folder, metadata_file)
            metadata = load_metadata(metadata_path)
            if metadata:
                # Split metadata into control and non-control sets
                control_metadata = [m for m in metadata if m.get('is_control', False)]
                regular_metadata = [m for m in metadata if not m.get('is_control', False)]
                
                if single_set:
                    quiz = generate_quiz_config(regular_metadata, day, slow_time, "single", quiz_id, randomize)
                    quizzes.append(quiz)
                    quiz_id += 1
                    logging.info(f"Added single quiz for day {day}")
                    
                    if control_metadata:
                        control_quiz = generate_quiz_config(control_metadata, day, slow_time, "control-single", quiz_id, randomize)
                        quizzes.append(control_quiz)
                        quiz_id += 1
                        logging.info(f"Added control single quiz for day {day}")
                else:
                    # Regular quizzes
                    fast_quiz = generate_quiz_config(regular_metadata, day, fast_time, "Group 1 - Fast", quiz_id, randomize)
                    quiz_id += 1
                    slow_quiz = generate_quiz_config(regular_metadata, day, slow_time, "Group 1 - Slow", quiz_id, randomize)
                    quiz_id += 1
                    quizzes.extend([fast_quiz, slow_quiz])
                    logging.info(f"Added fast and slow quizzes for day {day}")
                    
                    if control_metadata:
                        control_fast_quiz = generate_quiz_config(control_metadata, day, fast_time, "Group 2 - Fast", quiz_id, randomize)
                        quiz_id += 1
                        control_slow_quiz = generate_quiz_config(control_metadata, day, slow_time, "Group 2 - Slow", quiz_id, randomize)
                        quiz_id += 1
                        quizzes.extend([control_fast_quiz, control_slow_quiz])
                        logging.info(f"Added control fast and slow quizzes for day {day}")
            else:
                logging.warning(f"No metadata found for day {day}")
        else:
            logging.warning(f"Unable to extract day number from metadata file: {metadata_file}")

    logging.info(f"Generated {len(quizzes)} quizzes in total")
    return quizzes

def save_config(quizzes: List[Dict], output_file: str):
    logging.info(f"Saving quiz configuration to: {output_file}")
    with open(output_file, 'w') as f:
        json.dump(quizzes, f, indent=2)
    logging.info(f"Quiz configuration saved successfully")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Müller-Lyer Illusion Quizzes")
    parser.add_argument("--base_folder", default="/home/matt/projects/visual-replication/static/images/", help="Path to the folder containing metadata files")
    parser.add_argument("--output_file", default="/home/matt/projects/visual-replication/config.json", help="Path to save the output config file")
    parser.add_argument("--fast_time", type=float, default=0.5, help="Display time for fast quizzes (in seconds)")
    parser.add_argument("--slow_time", type=float, default=5.0, help="Display time for slow quizzes (in seconds)")
    parser.add_argument("--single_set", action="store_true", help="Generate only a single set of quizzes")
    parser.add_argument("--no-randomize", action="store_false", dest="randomize", 
                      help="Do not randomize the order of images in quizzes")
    parser.set_defaults(randomize=True)
    args = parser.parse_args()

    logging.info("Starting quiz generation process")
    quizzes = generate_quizzes(args.base_folder, args.fast_time, args.slow_time, args.single_set, args.randomize)
    save_config(quizzes, args.output_file)
    logging.info("Quiz generation process completed")