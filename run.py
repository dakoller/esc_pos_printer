import feedparser
from escpos.printer import Network
import textwrap
import requests
from datetime import datetime
import os
from dotenv import load_dotenv, dotenv_values 
from pprint import pprint
from flask import Flask, redirect, request, session, url_for, jsonify
load_dotenv()
import json
from datetime import date
import random
from ticktick.oauth2 import OAuth2        # OAuth2 Manager
from ticktick.api import TickTickClient   # Main Interface
import datetime

# Step 2: Connect to the ESC/POS printer
printer_ip = '192.168.2.134'

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

def print_rss_feed(printer, caption = 'Heidelberg News', rss_feed_url='https://www.rnz.de/feed/139-RL_Heidelberg_free.xml', _count = 5):
    printer.text(f"{ caption }\n")
    #printer.set(align='left', bold=False, double_height=False)
    printer.set(bold= False,normal_textsize=True)

    feed = feedparser.parse(rss_feed_url)
    # Print each entry from the RSS feed
    for entry in feed.entries[:_count]:  # Limit to the first 5 headlines
        # Wrap text for the small paper width
        #headline = textwrap.fill(entry.title, width=52)
        #description = textwrap.fill(entry.description, width=52)

        headline = entry.title
        description = entry.description

        # Print the headline and description
        printer.set(bold= True,normal_textsize=True)
        printer.text(f"{headline}\n")
        printer.set(bold= False,normal_textsize=True)
        printer.text(f"{description}\n")
        printer.text("\n---\n\n")

# Function to print due tasks
def print_due_tasks(printer):
    try:
        if printer == None:
            printer = Network(printer_ip)
            
        # Get due tasks from the /due_tasks endpoint
        response = requests.get('http://localhost:5001/due_tasks')
        if response.status_code != 200:
            print(f"Failed to get due tasks: {response.status_code}")
            return
            
        data = response.json()
        tasks = data.get('tasks', [])
        
        if not tasks:
            print("No due tasks found")
            return
            
        # Print the header with due/overdue counts
        printer.set(align='center', bold=True, double_height=True)
        printer.text("Upcoming Tasks\n\n")
        printer.set(align='left', bold=False, double_height=False, normal_textsize=True)
        
        # Count due and overdue tasks
        due_today, overdue = count_due_overdue_tasks(tasks)
        
        # Print the counts
        printer.set(bold=True)
        printer.text(f"Overdue: {overdue}  Due Today: {due_today}  Total: {len(tasks)}\n\n")
        printer.set(bold=False)
        
        # Sort tasks by due date (they should already be sorted, but just to be sure)
        tasks.sort(key=lambda x: x['due_date'])
        
        # Print each task
        for task in tasks:
            title = task.get('title', 'No Title')
            description = task.get('description', '')
            due_date = task.get('due_date', '')
            
            # Format the due date
            try:
                # Parse the ISO format date
                dt = datetime.datetime.strptime(due_date, '%Y-%m-%dT%H:%M:%S.%f%z')
                # Format it in a more readable way
                formatted_date = dt.strftime('%a, %b %d, %Y')
            except:
                formatted_date = due_date
                
            # Print the task in the specified format
            printer.text("[ ] ")
            printer.set(bold=True)
            printer.text(f"{title}")
            printer.set(bold=False)
            
            if description:
                printer.text(f": {description}")
                
            printer.text(" (due ")
            # No italic support, use normal text
            printer.text(f"{formatted_date}")
            printer.text(")\n\n")
            
        # Add more space after the task list
        printer.text("\n\n\n")
        
    except Exception as e:
        print(f"Error printing due tasks: {str(e)}")

# Step 3: Format and print the news
@app.route('/print_news')
def print_news():
    try:
        printer= Network(printer_ip)
        # Print the feed title
        print_daily_basics(printer= printer)

        print_daily_quote(printer = printer)
        
        # Print due tasks
        print_due_tasks(printer = printer)

        #printer.set(align='center', bold=True, double_height=True)
        print_rss_feed(printer = printer, caption = 'Heidelberg News', rss_feed_url='https://www.rnz.de/feed/139-RL_Heidelberg_free.xml', _count = 3)

        print_rss_feed(printer = printer, caption= 'Tagesschau', rss_feed_url='https://www.tagesschau.de/inland/index~rss2.xml', _count = 3)

        # Step 4: Cut the paper
        printer.cut()
        return jsonify({"status": "success", "message": "Printed successfully!"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to print: {str(e)}"}), 500

@app.route('/print_text')
def print_text():
    try:
        headline = request.args.get('headline')
    except:
        headline = None

    try:
        text = request.args.get('text')
    except:
        text = None

    try:
        printer = Network(printer_ip)

        if headline:
            printer.set(double_width=True, double_height=True, align='center',bold=True)
            printer.text(f"{ headline }\n\n")
            printer.set(double_width=False, double_height=False, align='center',bold=False, normal_textsize= True)

        if text:    
            printer.text(f"{ text }\n\n")

        printer.cut()
        return jsonify({"status": "success", "message": "Printed successfully!"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to print. ({str(e)})"}), 500
    

def print_daily_basics(printer):

    try:
        if printer == None:
            printer = Network(printer_ip)

        today = date.today()

        printer.set(double_width=True, double_height=True, align='center',bold=True)
        printer.text(f"{ today.strftime('%A %x')}\n\n")
        printer.set(double_width=False, double_height=False, align='center',bold=False, normal_textsize= True)

        sunset = requests.get("https://api.sunrise-sunset.org/json?lat=49.3988&lng=8.6724&date=today&tzid=Europe/Berlin").json()

        printer.text(f"{ sunset['results']['sunrise'] } - { sunset['results']['sunset']}\n")

        printer.set(double_width=True, double_height=True, align='center')
        printer.text(f'# { random.randint(1,53) }\n')
        printer.set(double_width=False, double_height=False, align='center', normal_textsize=True)

        printer.set(align='left')

    except Exception as e:
        pprint(e)


def get_ticktick_accesstoken():
    """
    Get the TickTick access token.
    First tries to read from .tt_token_full, then falls back to .tt_token.
    Returns the token if found, None otherwise.
    """
    try:
        # First try to read from .tt_token_full (contains full OAuth response)
        try:
            with open('.tt_token_full', 'r') as f:
                token_data = json.loads(f.read())
                
            if 'access_token' in token_data:
                print('Using access token from .tt_token_full')
                return token_data['access_token']
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f'Could not read token from .tt_token_full: {str(e)}')
            
        # Fall back to .tt_token (contains only the access token)
        with open('.tt_token', 'r') as f:
            access_token = f.read().replace('\n', '')
        
        if not access_token:
            print('Access token is empty.')
            return None
            
        print('Using access token from .tt_token')
        return access_token
    except FileNotFoundError:
        print('Access token file not found.')
        return None
    except Exception as e:
        print(f'Error reading access token: {str(e)}')
        return None


def is_token_valid(access_token):
    """
    Check if the access token is valid by making a test API call.
    Returns True if valid, False otherwise.
    """
    if not access_token:
        print("No access token provided")
        return False
        
    try:
        headers = {
            'Authorization': f'Bearer {access_token}',
        }
        
        print(f"Checking token validity: {access_token[:5]}...{access_token[-5:]}")
        
        # Make a simple API call to check if the token is valid
        # Try the projects endpoint instead of user profile
        response = requests.get('https://api.ticktick.com/open/v1/project', headers=headers)
        
        print(f"Token validation response: {response.status_code}")
        if response.status_code != 200:
            print(f"Response text: {response.text}")
            
            # If the token is invalid, try to refresh it or get a new one
            # This is a placeholder for future implementation
            # For now, we'll just return False
            return False
        
        # If the response is 200, the token is valid
        print("Token is valid!")
        return True
    except Exception as e:
        print(f"Error checking token validity: {str(e)}")
        return False


def get_ticktick_tasks(use_direct_auth=False):
    """
    Get all tasks from TickTick using the client library.
    Returns a list of tasks if successful, None otherwise.
    
    Args:
        use_direct_auth: If True, bypass token validation and use direct username/password authentication
    """
    try:
        # Use direct username/password authentication
        auth_client = OAuth2(
            client_id=os.getenv("TICKTICK_CLIENT_ID"),
            client_secret=os.getenv("TICKTICK_CLIENT_SECRET"),
            redirect_uri=os.getenv("TICKTICK_REDIRECT_URI")
        )

        client = TickTickClient(
            os.getenv("TICKTICK_USERNAME"), 
            os.getenv("TICKTICK_PASSWORD"), 
            auth_client
        )

        # Return tasks
        return client.state.get('tasks', [])

    except Exception as e:
        print(f"Error getting TickTick tasks: {str(e)}")
        return None


def get_ticktick_api():
    """
    Get a specific task from TickTick using the REST API.
    Returns the task if successful, an error object otherwise.
    """
    access_token = get_ticktick_accesstoken()
    
    if not access_token:
        return {"error": "No access token available"}
    
    try:
        headers = {
            'Authorization': f'Bearer {access_token}',
        }
        
        # Get projects first to find a valid project ID
        projects_response = requests.get('https://api.ticktick.com/open/v1/project', headers=headers)
        
        if projects_response.status_code != 200:
            return {
                "error": projects_response.status_code,
                "text": projects_response.text,
                "message": "Failed to get projects"
            }
            
        projects = projects_response.json()
        
        # If no projects, return empty result
        if not projects:
            return {"message": "No projects found"}
            
        # Get the first project's ID
        project_id = projects[0].get('id')
        
        # Get tasks for this project
        tasks_url = f'https://api.ticktick.com/open/v1/project/{project_id}/task'
        tasks_response = requests.get(tasks_url, headers=headers)
        
        if tasks_response.status_code != 200:
            return {
                "error": tasks_response.status_code,
                "text": tasks_response.text,
                "message": "Failed to get tasks"
            }
            
        return tasks_response.json()
        
    except Exception as e:
        return {"error": "Exception", "message": str(e)}


def get_due_tasks(use_direct_auth=False):
    """
    Get all tasks with due dates from TickTick.
    Returns a list of tasks with title, description, and due date.
    
    Args:
        use_direct_auth: If True, bypass token validation and use direct username/password authentication
    """
    # Get tasks using the client library with direct authentication
    tasks = get_ticktick_tasks(use_direct_auth=use_direct_auth)
    
    if not tasks:
        print("Failed to get tasks using client library, returning empty list")
        return []
    
    # Filter tasks with due dates
    due_tasks = []
    
    for task in tasks:
        if task.get('dueDate'):
            # Format the task
            formatted_task = {
                'title': task.get('title', 'No Title'),
                'description': task.get('content', ''),
                'due_date': task.get('dueDate'),
                'priority': task.get('priority', 0),
                'status': 'Completed' if task.get('status', 0) == 2 else 'Not Completed',
                'id': task.get('id', '')
            }
            due_tasks.append(formatted_task)
    
    # Sort by due date
    due_tasks.sort(key=lambda x: x['due_date'])
    
    return due_tasks


@app.route('/ticktick_callback')
def ticktick_callback():
    """
    Handle the OAuth callback from TickTick.
    Exchanges the authorization code for an access token and stores it.
    """
    try:
        # Get the authorization code from the request
        request_data = request.args
        
        if 'code' not in request_data:
            return jsonify({
                "status": "error", 
                "message": "No authorization code provided"
            }), 400
            
        code = request_data['code']
        
        # Prepare the token request data
        data = {
            'client_id': os.getenv('TICKTICK_CLIENT_ID'),
            'grant_type': 'authorization_code',
            'redirect_uri': os.getenv('TICKTICK_REDIRECT_URI'),
            'client_secret': os.getenv('TICKTICK_CLIENT_SECRET'),
            'code': code,
            'scope': 'tasks:read',
        }
        
        # Exchange the code for an access token
        r = requests.post('https://ticktick.com/oauth/token', data=data)
        
        # Check if the request was successful
        if r.status_code != 200:
            return jsonify({
                "status": "error",
                "message": f"Failed to get access token: {r.text}"
            }), 400
            
        # Parse the response
        response = r.json()
        
        # Store the access token
        if 'access_token' in response:
            with open('.tt_token', 'w') as f:
                f.write(response['access_token'])
                
            # Also store the full response for debugging
            with open('.tt_token_full', 'w') as f:
                f.write(json.dumps(response, indent=2))
                
            return jsonify({
                "status": "success", 
                "message": "Access token received and stored successfully!"
            }), 200
        else:
            return jsonify({
                "status": "error", 
                "message": f"No access token in response: {response}"
            }), 400
            
    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": f"Error in callback: {str(e)}"
        }), 500

def print_daily_quote(printer):
    try:
        if printer == None:
            printer= Network(printer_ip)

        r = requests.get('https://zenquotes.io/api/today').json()[0]

        printer.set(bold= True,double_width=True,align='center')
        printer.text(f"\n\n{ r['q'] }\n")
        printer.set(bold= False,normal_textsize=True, align='center')
        printer.text(f"\n{ r['a'] }\n\n")
        printer.set(bold= False,normal_textsize=True, align='left')
        #pprint(r)

    except Exception as e:
        pprint(e)

# Simple test endpoint that doesn't require authentication
@app.route('/')
def index():
    return jsonify({
        "status": "success",
        "message": "ESC/POS Printer API is running",
        "endpoints": [
            {"path": "/", "method": "GET", "description": "This help page"},
            {"path": "/test_ticktick", "method": "GET", "description": "Test TickTick integration"},
            {"path": "/ticktick_auth", "method": "GET", "description": "Get TickTick OAuth URL"},
            {"path": "/ticktick_callback", "method": "GET", "description": "OAuth callback for TickTick"},
            {"path": "/due_tasks", "method": "GET", "description": "Get tasks with due dates from TickTick"},
            {"path": "/test_due_tasks", "method": "GET", "description": "Test endpoint for due tasks (no auth required)"},
            {"path": "/print_news", "method": "GET", "description": "Print news to the thermal printer"},
            {"path": "/print_text", "method": "GET", "description": "Print custom text to the thermal printer"}
        ]
    })

# Get the OAuth URL for TickTick
@app.route('/ticktick_auth')
def ticktick_auth():
    # Check if we already have a valid token
    access_token = get_ticktick_accesstoken()
    if access_token and is_token_valid(access_token):
        return jsonify({
            "status": "success",
            "message": "You already have a valid access token. No need to re-authenticate.",
            "token_status": "valid"
        })
    
    # If no valid token, provide the auth URL
    auth_url = f"https://ticktick.com/oauth/authorize?client_id={os.getenv('TICKTICK_CLIENT_ID')}&scope=tasks:read&redirect_uri={os.getenv('TICKTICK_REDIRECT_URI')}&response_type=code"
    return jsonify({
        "status": "success",
        "auth_url": auth_url,
        "message": "Open this URL in your browser to authorize the application",
        "token_status": "invalid_or_missing"
    })

# Test endpoint for TickTick functionality without using the printer
@app.route('/test_ticktick')
def test_ticktick():
    try:
        # Check if we have an access token
        access_token = get_ticktick_accesstoken()
        
        # Check if the token is valid
        if not access_token or not is_token_valid(access_token):
            # No valid access token, provide instructions
            auth_url = f"https://ticktick.com/oauth/authorize?client_id={os.getenv('TICKTICK_CLIENT_ID')}&scope=tasks:read&redirect_uri={os.getenv('TICKTICK_REDIRECT_URI')}&response_type=code"
            return jsonify({
                'status': 'error',
                'message': 'No valid access token available. Please authorize the application.',
                'auth_url': auth_url
            }), 401
        
        # Get tasks using the client library
        tasks = get_ticktick_tasks()
        
        # Format tasks for display
        formatted_tasks = []
        if tasks:
            for task in tasks:
                # Extract relevant information from each task
                task_info = {
                    'id': task.get('id', 'No ID'),
                    'title': task.get('title', 'No Title'),
                    'content': task.get('content', 'No Content'),
                    'due_date': task.get('dueDate', 'No Due Date'),
                    'priority': task.get('priority', 0),
                    'status': 'Completed' if task.get('status', 0) == 2 else 'Not Completed',
                    'project': task.get('projectId', 'No Project')
                }
                formatted_tasks.append(task_info)
        
        # Get tasks using the REST API
        api_tasks = get_ticktick_api()
        
        # Prepare the response
        response = {
            'status': 'success',
            'access_token_available': True,
            'client_library': {
                'task_count': len(formatted_tasks) if formatted_tasks else 0,
                'tasks': formatted_tasks
            },
            'rest_api': {
                'result': api_tasks
            }
        }
        
        return jsonify(response), 200
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'traceback': str(e.__traceback__.tb_lineno)
        }), 500


# Count due and overdue tasks
def count_due_overdue_tasks(tasks):
    """
    Count how many tasks are due today or overdue.
    
    Args:
        tasks: List of tasks with due_date field
        
    Returns:
        Tuple of (due_today_count, overdue_count)
    """
    today = datetime.datetime.now(datetime.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    due_today = 0
    overdue = 0
    
    for task in tasks:
        due_date_str = task.get('due_date')
        if not due_date_str:
            continue
            
        try:
            # Parse the ISO format date
            due_date = datetime.datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M:%S.%f%z')
            
            # Check if due today
            if due_date.date() == today.date():
                due_today += 1
            # Check if overdue
            elif due_date < today:
                overdue += 1
        except Exception as e:
            print(f"Error parsing date {due_date_str}: {str(e)}")
            
    return (due_today, overdue)

# Endpoint to get tasks with due dates
@app.route('/due_tasks')
def due_tasks():
    try:
        # Get the access token directly from .tt_token_full
        try:
            with open('.tt_token_full', 'r') as f:
                token_data = json.loads(f.read())
                
            if 'access_token' not in token_data:
                print("No access token found in .tt_token_full")
                return jsonify({
                    'status': 'success',
                    'task_count': 0,
                    'tasks': [],
                    'message': 'No access token found'
                }), 200
                
            access_token = token_data['access_token']
            print(f"Using access token from .tt_token_full: {access_token[:5]}...{access_token[-5:]}")
            
            # Use the token to get tasks via the REST API
            headers = {
                'Authorization': f'Bearer {access_token}',
            }
            
            # Get projects first to find a valid project ID
            projects_response = requests.get('https://api.ticktick.com/open/v1/project', headers=headers)
            
            if projects_response.status_code != 200:
                print(f"Failed to get projects: {projects_response.status_code}")
                return jsonify({
                    'status': 'success',
                    'task_count': 0,
                    'tasks': [],
                    'message': 'Failed to get projects'
                }), 200
                
            projects = projects_response.json()
            
            # If no projects, return empty result
            if not projects:
                print("No projects found")
                return jsonify({
                    'status': 'success',
                    'task_count': 0,
                    'tasks': [],
                    'message': 'No projects found'
                }), 200
                
            # Try to get all tasks using the endpoint from the documentation
            all_tasks = []
            all_due_tasks = []  # Store all tasks with due dates directly
            
            # First, check the user project (Inbox)
            print("Checking user project (Inbox)...")
            
            # Try the direct "inbox" project ID first
            inbox_project_id = "inbox"
            inbox_project_name = "Inbox"
            print(f"Trying direct inbox project ID: {inbox_project_id}")
            
            # Get tasks for the inbox project
            inbox_tasks_url = f'https://api.ticktick.com/open/v1/project/{inbox_project_id}/data'
            print(f"Requesting inbox project data from: {inbox_tasks_url}")
            inbox_tasks_response = requests.get(inbox_tasks_url, headers=headers)
            
            if inbox_tasks_response.status_code == 200:
                inbox_project_data = inbox_tasks_response.json()
                if 'tasks' in inbox_project_data:
                    inbox_tasks = inbox_project_data['tasks']
                    print(f"Found {len(inbox_tasks)} tasks in inbox project")
                    
                    # Process tasks from the inbox project
                    for task in inbox_tasks:
                        # Add all tasks to the all_tasks list
                        all_tasks.append(task)
                        
                        # If the task has a due date, format it and add to due_tasks
                        if task.get('dueDate'):
                            formatted_task = {
                                'title': task.get('title', 'No Title'),
                                'description': task.get('content', ''),
                                'due_date': task.get('dueDate'),
                                'priority': task.get('priority', 0),
                                'status': 'Completed' if task.get('status', 0) == 2 else 'Not Completed',
                                'id': task.get('id', ''),
                                'project_id': inbox_project_id,
                                'project_name': inbox_project_name
                            }
                            all_due_tasks.append(formatted_task)
                            print(f"Added task with due date from inbox project: {task.get('title')} (Due: {task.get('dueDate')})")
                else:
                    print(f"No tasks found in inbox project data. Keys: {list(inbox_project_data.keys())}")
            else:
                print(f"Failed to get inbox project data: {inbox_tasks_response.status_code}")
                
                # If direct inbox ID fails, try the user project endpoint
                user_project_url = 'https://api.ticktick.com/open/v1/user/project'
                user_project_response = requests.get(user_project_url, headers=headers)
                
                if user_project_response.status_code == 200:
                    user_project_data = user_project_response.json()
                    if isinstance(user_project_data, dict) and 'id' in user_project_data:
                        user_project_id = user_project_data['id']
                        user_project_name = user_project_data.get('name', 'Inbox')
                        print(f"Found user project: {user_project_name} (ID: {user_project_id})")
                    
                        # Get tasks for the user project
                        user_tasks_url = f'https://api.ticktick.com/open/v1/project/{user_project_id}/data'
                        print(f"Requesting user project data from: {user_tasks_url}")
                        user_tasks_response = requests.get(user_tasks_url, headers=headers)
                        
                        if user_tasks_response.status_code == 200:
                            user_project_data = user_tasks_response.json()
                            if 'tasks' in user_project_data:
                                user_tasks = user_project_data['tasks']
                                print(f"Found {len(user_tasks)} tasks in user project {user_project_name}")
                                
                                # Process tasks from the user project
                                for task in user_tasks:
                                    # Add all tasks to the all_tasks list
                                    all_tasks.append(task)
                                    
                                    # If the task has a due date, format it and add to due_tasks
                                    if task.get('dueDate'):
                                        formatted_task = {
                                            'title': task.get('title', 'No Title'),
                                            'description': task.get('content', ''),
                                            'due_date': task.get('dueDate'),
                                            'priority': task.get('priority', 0),
                                            'status': 'Completed' if task.get('status', 0) == 2 else 'Not Completed',
                                            'id': task.get('id', ''),
                                            'project_id': user_project_id,
                                            'project_name': user_project_name
                                        }
                                        all_due_tasks.append(formatted_task)
                                        print(f"Added task with due date from user project: {task.get('title')} (Due: {task.get('dueDate')})")
                            else:
                                print(f"No tasks found in user project data. Keys: {list(user_project_data.keys())}")
                        else:
                            print(f"Failed to get user project data: {user_tasks_response.status_code}")
                else:
                    print(f"Failed to get user project: {user_project_response.status_code}")
            
            # Now process each regular project to get its tasks
            for i, project in enumerate(projects):
                project_id = project.get('id')
                project_name = project.get('name', 'Unknown')
                print(f"Processing project {i+1}/{len(projects)}: {project_name} (ID: {project_id})")
                
                # Use the endpoint from the documentation: GET /open/v1/project/{projectId}/data
                tasks_url = f'https://api.ticktick.com/open/v1/project/{project_id}/data'
                print(f"Requesting project data from: {tasks_url}")
                tasks_response = requests.get(tasks_url, headers=headers)
                
                print(f"Response status: {tasks_response.status_code}")
                if tasks_response.status_code == 200:
                    project_data = tasks_response.json()
                    
                    # Check if the response contains tasks
                    if 'tasks' in project_data:
                        project_tasks = project_data['tasks']
                        print(f"Found {len(project_tasks)} tasks in project {project_name}")
                        
                        # Process tasks from this project
                        for task in project_tasks:
                            # Add all tasks to the all_tasks list
                            all_tasks.append(task)
                            
                            # If the task has a due date, format it and add to due_tasks
                            if task.get('dueDate'):
                                formatted_task = {
                                    'title': task.get('title', 'No Title'),
                                    'description': task.get('content', ''),
                                    'due_date': task.get('dueDate'),
                                    'priority': task.get('priority', 0),
                                    'status': 'Completed' if task.get('status', 0) == 2 else 'Not Completed',
                                    'id': task.get('id', ''),
                                    'project_id': project_id,
                                    'project_name': project_name
                                }
                                all_due_tasks.append(formatted_task)
                                print(f"Added task with due date: {task.get('title')} (Due: {task.get('dueDate')})")
                    else:
                        print(f"No tasks found in project data. Keys: {list(project_data.keys())}")
                else:
                    print(f"Failed to get project data: {tasks_response.text}")
            
            print(f"Total tasks found across all projects: {len(all_tasks)}")
            print(f"Tasks with due dates across all projects: {len(all_due_tasks)}")
            
            # Sort by due date
            all_due_tasks.sort(key=lambda x: x['due_date'])
            
            # Count due and overdue tasks
            due_today, overdue = count_due_overdue_tasks(all_due_tasks)
            
        except Exception as e:
            print(f"Error getting tasks: {str(e)}")
            return jsonify({
                'status': 'success',
                'task_count': 0,
                'tasks': [],
                'message': f'Error getting tasks: {str(e)}'
            }), 200
        
        # Prepare the response
        response = {
            'status': 'success',
            'task_count': len(all_due_tasks),
            'due_today': due_today,
            'overdue': overdue,
            'tasks': all_due_tasks
        }
        
        return jsonify(response), 200
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'traceback': str(e.__traceback__.tb_lineno)
        }), 500


# Test endpoint for due tasks (no authentication required)
@app.route('/test_due_tasks')
def test_due_tasks():
    try:
        # Create some sample tasks with due dates for testing
        sample_tasks = [
            {
                'id': 'task1',
                'title': 'Complete project proposal',
                'description': 'Finish the proposal document for the new client project',
                'due_date': '2025-09-20T10:00:00.000+0000',
                'priority': 5,
                'status': 'Not Completed'
            },
            {
                'id': 'task2',
                'title': 'Weekly team meeting',
                'description': 'Regular team sync-up to discuss progress and blockers',
                'due_date': '2025-09-21T14:00:00.000+0000',
                'priority': 3,
                'status': 'Not Completed'
            },
            {
                'id': 'task3',
                'title': 'Review pull request',
                'description': 'Review and approve the pending code changes',
                'due_date': '2025-09-19T16:00:00.000+0000',
                'priority': 3,
                'status': 'Not Completed'
            },
            {
                'id': 'task4',
                'title': 'Submit expense report',
                'description': 'Submit monthly expense report to accounting',
                'due_date': '2025-09-30T23:59:59.000+0000',
                'priority': 1,
                'status': 'Not Completed'
            }
        ]
        
        # Sort by due date
        sample_tasks.sort(key=lambda x: x['due_date'])
        
        # Prepare the response
        response = {
            'status': 'success',
            'message': 'This is a test endpoint with sample data (no authentication required)',
            'task_count': len(sample_tasks),
            'tasks': sample_tasks
        }
        
        return jsonify(response), 200
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'traceback': str(e.__traceback__.tb_lineno)
        }), 500

# Function to format TickTick tasks for printing (not currently used)
def format_ticktick_tasks_for_display(tasks):
    """
    Format TickTick tasks for display or printing.
    This function doesn't send anything to the printer.
    """
    formatted_output = []
    
    if not tasks or len(tasks) == 0:
        return ["No tasks found"]
    
    for task in tasks:
        task_info = []
        task_info.append(f"Title: {task.get('title', 'No Title')}")
        
        if task.get('content'):
            task_info.append(f"Description: {task.get('content')}")
        
        if task.get('dueDate'):
            # Format the date if needed
            task_info.append(f"Due: {task.get('dueDate')}")
        
        priority_map = {0: "None", 1: "Low", 3: "Medium", 5: "High"}
        priority = priority_map.get(task.get('priority', 0), "Unknown")
        task_info.append(f"Priority: {priority}")
        
        status = "Completed" if task.get('status', 0) == 2 else "Not Completed"
        task_info.append(f"Status: {status}")
        
        # Add a separator between tasks
        task_info.append("---")
        
        formatted_output.append("\n".join(task_info))
    
    return formatted_output

# Execute the print job
if __name__ == '__main__':
    print("Starting ESC/POS Printer API...")
    print(f"TickTick client ID: {os.getenv('TICKTICK_CLIENT_ID')}")
    print(f"TickTick redirect URI: {os.getenv('TICKTICK_REDIRECT_URI')}")
    
    # Check if we have a valid access token
    access_token = get_ticktick_accesstoken()
    if access_token:
        if is_token_valid(access_token):
            print("TickTick access token is available and valid.")
        else:
            print("TickTick access token is available but invalid.")
            print("To authorize, visit:")
            print(f"https://ticktick.com/oauth/authorize?client_id={os.getenv('TICKTICK_CLIENT_ID')}&scope=tasks:read&redirect_uri={os.getenv('TICKTICK_REDIRECT_URI')}&response_type=code")
    else:
        print("TickTick access token is not available.")
        print("To authorize, visit:")
        print(f"https://ticktick.com/oauth/authorize?client_id={os.getenv('TICKTICK_CLIENT_ID')}&scope=tasks:read&redirect_uri={os.getenv('TICKTICK_REDIRECT_URI')}&response_type=code")
    
    # Run the Flask application
    print(f"Server running at http://localhost:5001")
    app.run(debug=True, host='0.0.0.0', port=5001)
