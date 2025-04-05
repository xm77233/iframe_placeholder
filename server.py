#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A simple Flask server for the itch.io Game Iframe Extractor
Handles extraction requests and sends results via email
"""

from flask import Flask, request, jsonify, send_from_directory, render_template
import os
import sys
import json
import smtplib
import threading
import subprocess
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime
import uuid

app = Flask(__name__, static_url_path='')

# Configuration
EMAIL_SENDER = "noreply@iframe-extractor.example.com"  # Replace with your email
SMTP_SERVER = "localhost"  # Replace with your SMTP server
SMTP_PORT = 25  # Replace with your SMTP port
SMTP_USERNAME = None  # Set if required
SMTP_PASSWORD = None  # Set if required

# Job storage
jobs = {}

def setup_result_directories():
    """Create necessary directories if they don't exist"""
    for directory in ['results', 'logs', 'debug_html', 'jobs']:
        if not os.path.exists(directory):
            os.makedirs(directory)

def run_extraction_job(job_id, params):
    """
    Run the iframe extraction job in the background
    
    Args:
        job_id: Unique job identifier
        params: Job parameters
    """
    # Update job status
    jobs[job_id]['status'] = 'processing'
    
    try:
        # Prepare command line arguments
        cmd = [sys.executable, "iframe_scraper.py"]
        
        if params.get('max_games'):
            cmd.extend(["--max_games", str(params['max_games'])])
        
        if params.get('offset'):
            cmd.extend(["--start_offset", str(params['offset'])])
        
        if params.get('delay'):
            cmd.extend(["--delay", str(params['delay'])])
        
        # Set output file specific to this job
        output_file = f"results/job_{job_id}.json"
        cmd.extend(["--output", output_file])
        
        # Run the extraction process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Capture log output
        log_file = f"logs/job_{job_id}.log"
        with open(log_file, 'w', encoding='utf-8') as log:
            for line in iter(process.stdout.readline, ''):
                log.write(line)
                log.flush()
                
                # Update job info with progress data
                if "找到 " in line and " 个游戏" in line:
                    try:
                        games_found = int(line.split("找到 ")[1].split(" 个游戏")[0])
                        jobs[job_id]['found'] = games_found
                    except:
                        pass
                
                if "成功找到iframe源" in line:
                    jobs[job_id]['successful'] = jobs[job_id].get('successful', 0) + 1
                
                if "已处理 " in line and " 个游戏" in line:
                    try:
                        processed = int(line.split("已处理 ")[1].split(" 个游戏")[0])
                        jobs[job_id]['processed'] = processed
                    except:
                        pass
        
        # Wait for process to complete
        process.wait()
        
        # Check if results were generated
        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            # Read results file
            with open(output_file, 'r', encoding='utf-8') as f:
                results = json.load(f)
                
            # Update job info
            jobs[job_id]['status'] = 'completed'
            jobs[job_id]['completed_at'] = datetime.now().isoformat()
            jobs[job_id]['result_count'] = len(results)
            
            # Send results via email
            send_results_email(jobs[job_id]['email'], job_id, output_file, len(results))
        else:
            # Something went wrong
            jobs[job_id]['status'] = 'failed'
            jobs[job_id]['error'] = 'No results were generated'
            
            # Send failure notification
            send_failure_email(jobs[job_id]['email'], job_id)
    
    except Exception as e:
        # Handle exceptions
        jobs[job_id]['status'] = 'failed'
        jobs[job_id]['error'] = str(e)
        
        # Send failure notification
        send_failure_email(jobs[job_id]['email'], job_id)

def send_results_email(recipient, job_id, results_file, result_count):
    """
    Send extraction results via email
    
    Args:
        recipient: Email recipient
        job_id: Job identifier
        results_file: Path to results file
        result_count: Number of results
    """
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = recipient
        msg['Subject'] = f"Your itch.io Iframe Extraction Results (Job {job_id})"
        
        # Email body
        body = f"""
        Hello,
        
        Your itch.io iframe extraction job has been completed successfully.
        
        Job Summary:
        - Job ID: {job_id}
        - Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        - Results: {result_count} game iframe sources extracted
        
        The results are attached as a JSON file. You can use these iframe sources to embed games in your website or application.
        
        For help with using these results, please refer to our documentation.
        
        Thank you for using our service!
        
        Best regards,
        itch.io Game Iframe Extractor Team
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach results file
        with open(results_file, 'rb') as f:
            attachment = MIMEApplication(f.read(), _subtype='json')
            attachment.add_header('Content-Disposition', 'attachment', filename=f'iframe_results_{job_id}.json')
            msg.attach(attachment)
        
        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            if SMTP_USERNAME and SMTP_PASSWORD:
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
            
    except Exception as e:
        print(f"Error sending results email: {e}")
        # Update job status
        jobs[job_id]['email_status'] = 'failed'
        jobs[job_id]['email_error'] = str(e)

def send_failure_email(recipient, job_id):
    """
    Send failure notification via email
    
    Args:
        recipient: Email recipient
        job_id: Job identifier
    """
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = recipient
        msg['Subject'] = f"itch.io Iframe Extraction Failed (Job {job_id})"
        
        # Email body
        body = f"""
        Hello,
        
        We're sorry, but your itch.io iframe extraction job has failed.
        
        Job Summary:
        - Job ID: {job_id}
        - Error: {jobs.get(job_id, {}).get('error', 'Unknown error')}
        
        You can try submitting a new job with different parameters. If the problem persists, please contact our support.
        
        Thank you for using our service!
        
        Best regards,
        itch.io Game Iframe Extractor Team
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            if SMTP_USERNAME and SMTP_PASSWORD:
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
            
    except Exception as e:
        print(f"Error sending failure email: {e}")
        # Update job status
        if job_id in jobs:
            jobs[job_id]['email_status'] = 'failed'
            jobs[job_id]['email_error'] = str(e)

@app.route('/')
def index():
    """Serve the main page"""
    return send_from_directory('.', 'index.html')

@app.route('/api/extract', methods=['POST'])
def extract():
    """Handle extraction requests"""
    # Get request data
    data = request.json
    
    # Validate request
    if not data or not data.get('email'):
        return jsonify({
            'status': 'error',
            'message': 'Email address is required'
        }), 400
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Create job record
    jobs[job_id] = {
        'id': job_id,
        'email': data.get('email'),
        'params': {
            'max_games': data.get('max_games', 10),
            'offset': data.get('offset', 0),
            'delay': data.get('delay', 2),
            'categories': data.get('categories', []),
            'include_info': data.get('include_info', [])
        },
        'status': 'queued',
        'created_at': datetime.now().isoformat(),
        'processed': 0,
        'successful': 0,
        'found': 0
    }
    
    # Start extraction process in a new thread
    thread = threading.Thread(
        target=run_extraction_job,
        args=(job_id, jobs[job_id]['params'])
    )
    thread.daemon = True
    thread.start()
    
    # Return job ID to client
    return jsonify({
        'status': 'success',
        'message': 'Extraction job submitted successfully',
        'job_id': job_id
    })

@app.route('/api/status/<job_id>')
def job_status(job_id):
    """Get job status"""
    if job_id not in jobs:
        return jsonify({
            'status': 'error',
            'message': 'Job not found'
        }), 404
    
    # Return job info
    return jsonify({
        'status': 'success',
        'job': {
            'id': jobs[job_id]['id'],
            'status': jobs[job_id]['status'],
            'created_at': jobs[job_id]['created_at'],
            'processed': jobs[job_id].get('processed', 0),
            'successful': jobs[job_id].get('successful', 0),
            'found': jobs[job_id].get('found', 0),
            'completed_at': jobs[job_id].get('completed_at'),
            'result_count': jobs[job_id].get('result_count')
        }
    })

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('.', path)

if __name__ == '__main__':
    # Create necessary directories
    setup_result_directories()
    
    # Start Flask server
    print("Starting itch.io Game Iframe Extractor server on http://127.0.0.1:5000")
    app.run(debug=True, host='127.0.0.1', port=5000) 