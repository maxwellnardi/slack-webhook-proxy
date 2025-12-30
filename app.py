from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Your Tasklet webhook URL (set as environment variable)
TASKLET_WEBHOOK_URL = os.environ.get('TASKLET_WEBHOOK_URL')

@app.route('/slack/events', methods=['POST'])
def slack_events():
    data = request.json
    
    # Handle Slack URL verification challenge
    if data.get('type') == 'url_verification':
        return jsonify({'challenge': data.get('challenge')})
    
    # Handle actual events
    if data.get('type') == 'event_callback':
        event = data.get('event', {})
        event_type = event.get('type')
        
        # Handle DM messages
        if event_type == 'message' and event.get('channel_type') == 'im':
            # Skip bot messages and edits/deletes
            subtype = event.get('subtype')
            skip_subtypes = ['message_changed', 'message_deleted', 'bot_message']
            if 'bot_id' not in event and subtype not in skip_subtypes:
                forward_to_tasklet('slack_dm', event)
        
        # Handle @mentions in channels
        elif event_type == 'app_mention':
            # Skip bot messages
            if 'bot_id' not in event:
                forward_to_tasklet('slack_mention', event)
    
    return jsonify({'ok': True})

def forward_to_tasklet(event_type, event):
    """Forward event to Tasklet webhook"""
    try:
        requests.post(TASKLET_WEBHOOK_URL, json={
            'event_type': event_type,
            'user': event.get('user'),
            'text': event.get('text', ''),
            'channel': event.get('channel'),
            'ts': event.get('ts'),
            'thread_ts': event.get('thread_ts'),
            'files': event.get('files', [])
        }, timeout=5)
    except Exception as e:
        print(f'Error forwarding to Tasklet: {e}')

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
