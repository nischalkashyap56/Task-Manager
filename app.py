from flask import Flask, render_template, request, redirect, url_for, jsonify, session, abort
from pymongo import MongoClient
from bson import ObjectId
import os
import pathlib
import requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests

app = Flask(__name__)

client = MongoClient('mongodb://localhost:27017/')
db = client['task_manager']  
tasks_collection = db['tasks']  

app.config['SECRET KEY'] = '4aa57280e394f94555e5e1880ac92e94'

app.secret_key = "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" # Make sure this matches with that's in client_secret.json

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1" # To allow http traffic for local dev

GOOGLE_CLIENT_ID = "266864823063-c5g0prc2gd3voh7tfgj8vf88f8uce09m.apps.googleusercontent.com"
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri="http://127.0.0.1:5000/callback"
)

@app.route('/')
def home():
    return render_template("home.html")

def login_is_required(function):
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            return abort(401)  # Authorization required
        else:
            return function()
    return wrapper

@app.route("/login")
def login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)

status_mapping = {
    0: 'To-Do',
    1: 'In-Progress',
    2: 'Completed',
}

@login_is_required
@app.route('/index')
def index():
    tasks = tasks_collection.find()
    return render_template('index.html', tasks=tasks, status_mapping=status_mapping)

@app.route('/leader', methods = ['GET', 'POST'])
def leader():
    tasks = tasks_collection.find()
    assignees = tasks_collection.distinct('assignee')
    return render_template('leader.html', tasks=tasks, status_mapping=status_mapping,assignees=assignees)

@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)
    if not session["state"] == request.args["state"]:
        abort(500)  # State does not match!

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )
    session["google_id"] = id_info.get("sub")
    session["name"] = id_info.get("name")
    return redirect(url_for('home'))

@login_is_required
@app.route('/add_task', methods=['GET', 'POST'])
def add_task():

    new_task = {
        'name': request.form.get('name'),
        'description' : request.form.get('description'),
        'deadline': request.form.get('deadline'),
        'status': int(request.form.get('status')),
        'assignee': request.form.get('assignee')
        }

    # Insert the new task into MongoDB
    tasks_collection.insert_one(new_task)
    return redirect(url_for('home'))

@login_is_required
@app.route('/delete_task/<string:task_id>', methods=['DELETE'])
def delete_task(task_id):
    try:

        task_id = ObjectId(task_id)

        result = tasks_collection.delete_one({'_id': task_id})
        if result.deleted_count == 1:
            return jsonify({'message': 'Task deleted successfully'})
        else:
            return jsonify({'error': 'Task not found'})
    except Exception as e:
        print('Error:', e)
        return jsonify({'error': 'An error occurred while deleting the task.'})

@login_is_required
@app.route('/update_status/<string:task_id>', methods=['PUT'])
def update_status(task_id):
    try:
        # Convert the string to ObjectId
        task_id = ObjectId(task_id)

        # Get the new status from the request data
        new_status = int(request.json.get('status'))

        # Update the task status in MongoDB
        result = tasks_collection.update_one({'_id': task_id}, {'$set': {'status': new_status}})
        if result.modified_count == 1:
            return jsonify({'message': 'Task status updated successfully'})
        else:
            return jsonify({'error': 'Task not found'})
    except Exception as e:
        print('Error:', e)
        return jsonify({'error': 'An error occurred while updating the task status.'})

@login_is_required
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=True)