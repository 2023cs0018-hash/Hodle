import os
import random
import ast
import pandas as pd
from flask import Flask, render_template, request, jsonify, session

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_movie_game'

# Load the dataset once when the server starts
df = pd.read_csv('filtered.csv')

def get_random_movie():
    # Sample based on Score column
    movie_row = df.sample(n=1, weights='Score').iloc[0]
    
    title = str(movie_row['Title']).strip()
    year = int(movie_row['Year'])
    
    try:
        genre_list = ast.literal_eval(movie_row['Genre'])
        genre = ", ".join(genre_list)
    except:
        genre = str(movie_row['Genre'])
        
    try:
        hints_list = ast.literal_eval(movie_row['Hints'])
    except:
        hints_list = [str(movie_row['Hints'])]
        
    random.shuffle(hints_list)
    return title, year, genre, hints_list

def generate_display_name(title, revealed_indices):
    display = []
    for i, char in enumerate(title):
        if char.isalnum():
            if i in revealed_indices:
                display.append(char)
            else:
                display.append('_')
        else:
            display.append(char)
    return "".join(display)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/start', methods=['POST'])
def start_game():
    title, year, genre, hints = get_random_movie()
    
    session['target_movie'] = title
    session['year'] = year
    session['genre'] = genre
    session['hints'] = hints
    session['turn'] = 1
    session['revealed_indices'] = []
    
    display_name = generate_display_name(title, session['revealed_indices'])
    
    return jsonify({
        'status': 'started',
        'display_name': display_name,
        'year': year,
        'genre': genre,
        'hint': hints[0] if hints else "No hint available.",
        'turn': 1
    })

@app.route('/api/guess', methods=['POST'])
def guess():
    data = request.json
    user_guess = data.get('guess', '').strip().lower()
    
    if 'target_movie' not in session:
        return jsonify({'error': 'Game not started'}), 400
        
    target_movie = session['target_movie']
    
    # Check if guess is correct
    if user_guess == target_movie.lower():
        return jsonify({
            'status': 'win',
            'movie': target_movie
        })
        
    turn = session['turn']
    
    # 7 turns total
    if turn >= 7:
        return jsonify({
            'status': 'lose',
            'movie': target_movie
        })
        
    # Reveal a random hidden letter if turn >= 2 (so playing for turn 3, 4, 5, 6, 7)
    if turn >= 2:
        revealed = session['revealed_indices']
        unrevealed = [i for i, char in enumerate(target_movie) if char.isalnum() and i not in revealed]
        if unrevealed:
            reveal_idx = random.choice(unrevealed)
            revealed.append(reveal_idx)
            session['revealed_indices'] = revealed
            
    session['turn'] = turn + 1
    
    display_name = generate_display_name(target_movie, session['revealed_indices'])
    hints = session['hints']
    
    # Cycle through hints safely
    next_hint = hints[(session['turn'] - 1) % len(hints)] if hints else "No hints available!"
    
    return jsonify({
        'status': 'continue',
        'display_name': display_name,
        'hint': next_hint,
        'turn': session['turn']
    })

@app.route('/api/giveup', methods=['POST'])
def giveup():
    if 'target_movie' not in session:
        return jsonify({'error': 'Game not started'}), 400
        
    return jsonify({
        'status': 'lose',
        'movie': session['target_movie']
    })

if __name__ == '__main__':
    app.run(debug=True)