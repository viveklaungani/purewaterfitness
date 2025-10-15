import sqlite3
import json
from datetime import datetime
from flask import Flask, request, jsonify, render_template, render_template_string

# ====================================================================
# 1. SECURITY AND SETUP CONFIGURATION
# ====================================================================

# --------------------------------------------------------------------
# !! CRITICAL: YOUR AUTHENTICATION DATA (HARDCODED FOR LOCAL TESTING) !!
# --------------------------------------------------------------------
AUTHORIZED_USER_ID = 6629263251
BOT_TOKEN = "7850840141:AAEgbDSJtGT8i88uFeAzzqsvQIOG8LyZXDg" 
# --------------------------------------------------------------------

# --- FLASK SETUP ---
app = Flask(__name__)
DB_NAME = 'workout_tracker.db'

def get_db_connection():
    """Establishes SQLite connection."""
    # The database file (workout_tracker.db) will be created in the same directory.
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # Allows accessing columns by name
    return conn

def init_db():
    """Initializes the database schema for workout logging."""
    conn = get_db_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS workouts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                entry TEXT NOT NULL,
                type TEXT 
            );
        """)
        conn.commit()
    except Exception as e:
        print(f"Database initialization error: {e}")
    finally:
        conn.close()

# Initialize the database when the app starts
init_db()

# --- ROUTES ---

@app.route('/')
def serve_mini_app():
    """
    Serves the main Mini App HTML file. 
    We use render_template_string for simplicity in this single-file local setup.
    """
    # This renders the index.html content dynamically
    # Note: In a real project, this template should be in a 'templates' folder.
    HTML_CONTENT = """
<!DOCTYPE html>
<html>
<head>
    <title>Workout Tracker Mini App</title>
    <meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: var(--tg-theme-bg-color);
            color: var(--tg-theme-text-color);
            transition: background-color 0.3s, color 0.3s;
        }
        h2 { color: var(--tg-theme-link-color); }
        .log-section {
            background-color: var(--tg-theme-secondary-bg-color);
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        input, textarea, select {
            width: 90%;
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 4px;
            border: 1px solid var(--tg-theme-hint-color);
            background-color: var(--tg-theme-bg-color);
            color: var(--tg-theme-text-color);
        }
        button {
            background-color: var(--tg-theme-button-color);
            color: var(--tg-theme-button-text-color);
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            width: 100%;
        }
        #message {
            margin-top: 10px;
            color: var(--tg-theme-success-color, green);
            font-weight: bold;
        }
    </style>
</head>
<body>

    <h2>🏋️ PureWater Tracker</h2>

    <div class="log-section">
        <label for="workout-type">Workout Type:</label>
        <select id="workout-type">
            <option value="Running">Running/Cardio</option>
            <option value="Lifting">Weight Lifting</option>
            <option value="Yoga">Yoga/Stretch</option>
            <option value="Nutrition">Nutrition Log</option>
            <option value="Other">Other</option>
        </select>
        
        <label for="workout-entry">Details:</label>
        <textarea id="workout-entry" placeholder="e.g., 30 min run, 5x5 squats @ 100kg" rows="3"></textarea>
        
        <button onclick="logEntry()">Log Entry</button>
        <button onclick="showHistory()" style="margin-top: 10px; background-color: var(--tg-theme-hint-color);">Show Last 5</button>
        <div id="message"></div>
        <div id="history-output" style="margin-top: 20px; white-space: pre-wrap;"></div>
    </div>

    <script>
        const tg = window.Telegram.WebApp;
        tg.ready();
        tg.expand();
        
        const authorizedUserId = AUTHORIZED_USER_ID; // Injected from Python

        // Get the user ID from the Mini App's secure initialization data
        const userData = tg.initDataUnsafe.user;
        const userId = userData ? userData.id : null;
        
        if (userId && userId !== authorizedUserId) {
             document.body.innerHTML = '<h1>ACCESS DENIED</h1><p>This Mini App is private.</p>';
        }

        async function logEntry() {
            const entryType = document.getElementById('workout-type').value;
            const entryText = document.getElementById('workout-entry').value;
            const messageDiv = document.getElementById('message');
            messageDiv.innerText = "Logging...";
            messageDiv.style.color = "orange";
            
            if (!entryText.trim()) {
                messageDiv.innerText = "Please enter some details!";
                messageDiv.style.color = "red";
                return;
            }

            if (!userId) {
                messageDiv.innerText = "Error: Could not retrieve Telegram User ID.";
                messageDiv.style.color = "red";
                return;
            }

            try {
                const response = await fetch('/api/log', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        user_id: userId,
                        entry: entryText,
                        type: entryType
                    })
                });

                const result = await response.json();
                
                if (response.ok) {
                    messageDiv.innerText = `✅ Logged as ${entryType} at ${new Date().toLocaleTimeString()}!`;
                    messageDiv.style.color = "green";
                    document.getElementById('workout-entry').value = ''; 
                } else {
                    messageDiv.innerText = `❌ Error: ${result.message || response.statusText}`;
                    messageDiv.style.color = "red";
                }
            } catch (error) {
                messageDiv.innerText = '❌ Failed to connect to server. Is your Python server and ngrok running?';
                messageDiv.style.color = "red";
                console.error('Fetch error:', error);
            }
        }
        
        async function showHistory() {
            const historyOutput = document.getElementById('history-output');
            historyOutput.innerText = "Fetching history...";
            
            try {
                const response = await fetch('/api/history', {
                    method: 'POST', // Use POST to send user_id securely
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: userId })
                });

                const result = await response.json();
                
                if (response.ok) {
                    if (result.history && result.history.length > 0) {
                        let output = "🗓 Your Last 5 Logs:\n\n";
                        result.history.forEach(log => {
                            output += `[${log.timestamp.substring(0, 16)}] - ${log.type}: ${log.entry}\n`;
                        });
                        historyOutput.innerText = output;
                    } else {
                        historyOutput.innerText = "⏳ No history found. Log a workout first!";
                    }
                } else {
                    historyOutput.innerText = `❌ Error fetching history: ${result.message || response.statusText}`;
                }
            } catch (error) {
                historyOutput.innerText = '❌ Failed to connect to server.';
                console.error('Fetch error:', error);
            }
        }
    </script>
</body>
</html>
    """
    # Use f-string to inject the authorized user ID into the JavaScript
    rendered_html = render_template_string(HTML_CONTENT, AUTHORIZED_USER_ID=AUTHORIZED_USER_ID)
    return rendered_html

@app.route('/api/log', methods=['POST'])
def log_workout():
    """API endpoint to receive workout data from the JavaScript frontend and save it."""
    data = request.json
    
    # SECURITY CHECK
    if data.get('user_id') != AUTHORIZED_USER_ID:
        return jsonify({"status": "error", "message": "Unauthorized user."}), 403

    # Log the data to SQLite
    try:
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO workouts (user_id, timestamp, entry, type) VALUES (?, ?, ?, ?)",
            (AUTHORIZED_USER_ID, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), data.get('entry'), data.get('type'))
        )
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Workout logged!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/history', methods=['POST'])
def get_history():
    """API endpoint to retrieve the last 5 workout logs."""
    data = request.json
    
    # SECURITY CHECK
    if data.get('user_id') != AUTHORIZED_USER_ID:
        return jsonify({"status": "error", "message": "Unauthorized user."}), 403
        
    try:
        conn = get_db_connection()
        # Query the last 5 entries for the authorized user
        history_rows = conn.execute(
            "SELECT timestamp, entry, type FROM workouts WHERE user_id = ? ORDER BY id DESC LIMIT 5", 
            (AUTHORIZED_USER_ID,)
        ).fetchall()
        conn.close()

        # Convert rows to a list of dictionaries
        history = [dict(row) for row in history_rows]
        
        return jsonify({"status": "success", "history": history})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Database error: {str(e)}"}), 500


# --- RUNNER ---
if __name__ == '__main__':
    print("Initializing SQLite Database...")
    print(f"Authorized User ID: {AUTHORIZED_USER_ID}")
    print("Starting Flask server on http://127.0.0.1:5000...")
    # Start the local server
    app.run(debug=True, port=5000)
