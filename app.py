from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)
client = MongoClient("mongodb://localhost:27017/")
db = client["webhook_db"]
collection = db["events"]

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    event_type = request.headers.get('X-GitHub-Event')
    timestamp = datetime.utcnow().strftime("%d %B %Y - %I:%M %p UTC")
    record = {}

    if event_type == "push":
        author = data.get('pusher', {}).get('name')
        branch = data.get('ref', '').split('/')[-1]
        record["message"] = f'"{author}" pushed to "{branch}" on {timestamp}'

    elif event_type == "pull_request":
        action = data.get('action')
        author = data['pull_request']['user']['login']
        from_branch = data['pull_request']['head']['ref']
        to_branch = data['pull_request']['base']['ref']

        if action == "opened":
            record["message"] = f'"{author}" submitted a pull request from "{from_branch}" to "{to_branch}" on {timestamp}'
        elif action == "closed" and data['pull_request']['merged']:
            record["message"] = f'"{author}" merged branch "{from_branch}" to "{to_branch}" on {timestamp}'

    if record:
        collection.insert_one(record)
        return jsonify({"status": "recorded"}), 201
    return jsonify({"status": "ignored"}), 200

@app.route('/events')
def events():
    docs = list(collection.find({}, {"_id": 0}))
    return jsonify(docs)

@app.route('/')
def index():
    return render_template('main.html')

if __name__ == '__main__':
    app.run(debug=True)
