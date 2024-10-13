from flask import Flask, render_template, request, redirect, url_for, session
import json
from datetime import datetime
import csv
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

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
            return render_template('quiz.html', quiz=quiz, image=quiz['images'][current_image_index], image_index=current_image_index)
        else:
            return redirect(url_for('thank_you'))
    else:
        return "Quiz not found", 404

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
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
    with open('results/results.csv', 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, user_id, quiz_id, image_index, answer, response_time])

if __name__ == '__main__':
    app.run(debug=True)