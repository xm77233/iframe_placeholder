#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A simple Flask server for the itch.io Game Iframe Extractor
Handles extraction requests and allows downloading results
"""

from flask import Flask, request, jsonify, send_from_directory, render_template, send_file
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

# Vercel requires us to create our app at the global scope
app = Flask(__name__, static_url_path='')

# Jobs storage - for Vercel, we need to use a file-based storage since memory won't persist
# between serverless function invocations
JOBS_DATA_DIR = 'jobs'

# Job storage
jobs = {}

# Load jobs from files
def load_jobs():
    global jobs
    if os.path.exists(JOBS_DATA_DIR):
        for filename in os.listdir(JOBS_DATA_DIR):
            if filename.endswith('.json'):
                job_id = filename.split('.')[0]
                try:
                    with open(os.path.join(JOBS_DATA_DIR, filename), 'r', encoding='utf-8') as f:
                        jobs[job_id] = json.load(f)
                except Exception as e:
                    print(f"Error loading job {job_id}: {e}")

# Save job to file
def save_job(job_id):
    if not os.path.exists(JOBS_DATA_DIR):
        os.makedirs(JOBS_DATA_DIR)
    try:
        with open(os.path.join(JOBS_DATA_DIR, f"{job_id}.json"), 'w', encoding='utf-8') as f:
            json.dump(jobs[job_id], f)
    except Exception as e:
        print(f"Error saving job {job_id}: {e}")

def setup_result_directories():
    """Create necessary directories if they don't exist"""
    for directory in ['results', 'logs', 'debug_html', 'jobs']:
        if not os.path.exists(directory):
            os.makedirs(directory)

# Add a job update function
def update_job(job_id, updates):
    if job_id in jobs:
        for key, value in updates.items():
            jobs[job_id][key] = value
        save_job(job_id)

def run_extraction_job(job_id, params):
    """
    Run the iframe extraction job in the background
    
    Args:
        job_id: Unique job identifier
        params: Job parameters
    """
    # Update job status
    update_job(job_id, {'status': 'processing'})
    
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
                        update_job(job_id, {'found': games_found})
                    except:
                        pass
                
                if "成功找到iframe源" in line:
                    update_job(job_id, {'successful': jobs[job_id].get('successful', 0) + 1})
                
                if "已处理 " in line and " 个游戏" in line:
                    try:
                        processed = int(line.split("已处理 ")[1].split(" 个游戏")[0])
                        update_job(job_id, {'processed': processed})
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
            update_job(job_id, {
                'status': 'completed',
                'completed_at': datetime.now().isoformat(),
                'result_count': len(results),
                'result_file': output_file
            })
        else:
            # Something went wrong
            update_job(job_id, {
                'status': 'failed',
                'error': 'No results were generated'
            })
    
    except Exception as e:
        # Handle exceptions
        update_job(job_id, {
            'status': 'failed',
            'error': str(e)
        })

# Add a mock processing mode for Vercel
def mock_process_job(job_id, params):
    """
    A mock job processing function for demonstration purposes
    This is useful for Vercel deployment where background processing isn't available
    
    Args:
        job_id: Job ID
        params: Processing parameters
    """
    # Update job status
    update_job(job_id, {'status': 'processing'})
    
    # Create a results directory if it doesn't exist
    if not os.path.exists('results'):
        os.makedirs('results')
    
    # Create a sample result
    result_file = f"results/job_{job_id}.json"
    sample_results = []
    
    # Create sample data based on the requested number of games
    max_games = min(params.get('max_games', 10), 20)  # Limit to 20 for the mock version
    
    for i in range(max_games):
        sample_results.append({
            "title": f"Sample Game {i+1}",
            "url": f"https://example.itch.io/sample-game-{i+1}",
            "iframe_src": f"https://itch.io/embed-upload/1234567?color=333333&amp;dark=true",
            "extracted_method": "mock_data"
        })
    
    # Save the sample results
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(sample_results, f, indent=2)
    
    # Update the job status
    update_job(job_id, {
        'status': 'completed',
        'completed_at': datetime.now().isoformat(),
        'result_count': len(sample_results),
        'result_file': result_file,
        'processed': max_games,
        'successful': max_games,
        'found': max_games
    })

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    if path == '':
        return send_from_directory('.', 'index.html')
    else:
        return send_from_directory('.', path)

@app.route('/api/extract', methods=['POST'])
def extract():
    """Handle extraction requests"""
    # Get request data
    data = request.json
    
    # Email is now optional
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Create job record
    jobs[job_id] = {
        'id': job_id,
        'email': data.get('email', ''),  # Email is now optional
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
    
    # Save job to file
    save_job(job_id)
    
    # Check if we're running on Vercel or locally
    if 'VERCEL' in os.environ:
        # On Vercel, use mock processing since we can't run background threads
        mock_process_job(job_id, jobs[job_id]['params'])
    else:
        # Start extraction process in a new thread for local development
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

# 添加新的下载API端点
@app.route('/api/download/<job_id>')
def download_results(job_id):
    """Download job results"""
    if job_id not in jobs:
        return jsonify({
            'status': 'error',
            'message': 'Job not found'
        }), 404
    
    if jobs[job_id]['status'] != 'completed':
        return jsonify({
            'status': 'error',
            'message': 'Job is not completed yet'
        }), 400
    
    result_file = jobs[job_id].get('result_file')
    if not result_file or not os.path.exists(result_file):
        return jsonify({
            'status': 'error',
            'message': 'Result file not found'
        }), 404
    
    return send_file(
        result_file,
        mimetype='application/json',
        as_attachment=True,
        download_name=f'iframe_results_{job_id}.json'
    )

# Add a healthcheck endpoint for Vercel
@app.route('/api/healthcheck')
def healthcheck():
    """Health check endpoint for Vercel"""
    return jsonify({
        'status': 'success',
        'message': 'Service is running',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    })

# For local development, we keep the old handlers
if __name__ == '__main__':
    # Load existing jobs
    load_jobs()
    
    # Create necessary directories
    setup_result_directories()
    
    # Start Flask server
    print("Starting itch.io Game Iframe Extractor server on http://127.0.0.1:5000")
    app.run(debug=True, host='127.0.0.1', port=5000) 