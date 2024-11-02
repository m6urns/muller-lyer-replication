from flask import Flask, render_template, request, redirect, url_for, session
import json
from datetime import datetime
import csv
from dotenv import load_dotenv
import os 
import logging

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
app.config['PREFERRED_URL_SCHEME'] = 'https'

@app.after_request
def add_security_headers(response):
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "img-src 'self' data: https:; "  # Allow HTTPS images
        "connect-src 'self' https:; "
        "font-src 'self' data: https:;"
    )
    return response

# Set data directory
DATA_DIR = os.getenv('DATA_DIR', '/app/data')
os.makedirs(DATA_DIR, exist_ok=True)

logging.basicConfig(level=logging.DEBUG)

def log_debug_info():
    logging.debug(f"Current working directory: {os.getcwd()}")
    logging.debug(f"Contents of current directory: {os.listdir('.')}")
    logging.debug(f"Contents of /app/data: {os.listdir('/app/data')}")
    logging.debug(f"Current user: {os.getuid()}:{os.getgid()}")
    logging.debug(f"DATA_DIR environment variable: {os.getenv('DATA_DIR')}")
    
log_debug_info()

# Load quiz configuration
def load_quiz_config():
    with open('config.json', 'r') as f:
        return json.load(f)

# Routes
@app.route('/')
def index():
    quizzes = load_quiz_config()
    return render_template('index.html', quizzes=quizzes)

@app.route('/start_quiz', methods=['POST'])
def start_quiz():
    quiz_id = int(request.form['quiz_id'])
    user_id = request.form['user_id']
    session['user_id'] = user_id
    session['current_image_index'] = 0
    return redirect(url_for('quiz', quiz_id=quiz_id))

@app.route('/quiz/<int:quiz_id>')
def quiz(quiz_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    quizzes = load_quiz_config()
    if quiz_id < len(quizzes):
        quiz = quizzes[quiz_id]
        current_image_index = session.get('current_image_index', 0)
        
        if current_image_index < len(quiz['images']):
            # Process all image URLs at once
            processed_quiz = quiz.copy()
            processed_quiz['images'] = [
                {
                    **img,
                    'url': url_for('static', filename=img['url'].replace('/static/', ''))
                }
                for img in quiz['images']
            ]
            
            return render_template('quiz.html', 
                                 quiz=processed_quiz,
                                 image_index=current_image_index)
        else:
            return redirect(url_for('thank_you'))
    else:
        return "Quiz not found", 404


@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    if 'user_id' not in session:
        return redirect(url_for('index', _scheme='https', _external=True))
    
    user_id = session['user_id']
    answer = request.form['answer']
    quiz_id = int(request.form['quiz_id'])
    image_index = int(request.form['image_index'])
    response_time = float(request.form['response_time'])
    
    save_answer(user_id, quiz_id, image_index, answer, response_time)
    
    session['current_image_index'] = image_index + 1
    return redirect(url_for('quiz', quiz_id=quiz_id))

@app.route('/complete')
def thank_you():
    return render_template('complete.html')
 
def save_answer(user_id, quiz_id, image_index, answer, response_time):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    results_file = os.path.join(DATA_DIR, 'results.csv')
    file_exists = os.path.isfile(results_file)
    logging.debug(f"Results file: {results_file}")
    
    try:
        with open(results_file, 'a', newline='') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(['Timestamp', 'User ID', 'Quiz ID', 'Image Index', 'Answer', 'Response Time'])
            writer.writerow([timestamp, user_id, quiz_id, image_index, answer, response_time])
            logging.debug(f"Saved answer to {results_file}")
    except Exception as e:
        logging.error(f"Error writing to file: {str(e)}")
        raise
        

if __name__ == '__main__':
    app.run(debug=True)