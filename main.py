import os
import asyncio
import threading
import json
import time
import re
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template
import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiohttp
from colorama import init, Fore, Style
from dotenv import load_dotenv

load_dotenv()
init()

# ==================== CONFIG ====================
BOT_TOKEN = os.getenv("Bot_Token")
SELFBOT_TOKEN = os.getenv("Self_Token")
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000
BASE_URL = "https://discord.com/api/v10"
CLEANUP_INTERVAL = 300
UPDATE_INTERVAL = 5
COUNT_INTERVAL = 300  # 5 phút
COUNT_CHANNEL_ID = "1426831461247488060"
DISPLAY_CHANNEL_ID = "1426798908146843719"

# ==================== CHANNEL MAPPING ====================
CHANNEL_MAPPING = {
    "prehistoric": "1414857810285695047",
    "fullmoon": "1414857913830346792",
    "nearmoon": "1414858005765427330",
    "ripindra": "1414858390244687962",
    "doughking": "1414858646214676510",
    "cakeprince": "1414858744759844915",
    "tyrant": "1414858858756571247",
    "darkbeard": "1414859003661389945",
    "soulreaper": "1414859187367706665",
    "cursedcap": "1414859454993666088",
    "legendarysword": "1414859813946654752",
    "hakilegendary": "1427658880128909454",
    "mirage": "1414857571474473010",
    "kitsune": "1414857691834355722"
}

# ==================== EVENT TYPES ====================
EVENT_TYPES = {
    "fullmoon": {"name": "🌕 Full Moon", "emoji": "🌕", "category": "island"},
    "nearmoon": {"name": "🌙 Near Moon", "emoji": "🌙", "category": "island"},
    "kitsune": {"name": "🦊 Kitsune Island", "emoji": "🦊", "category": "island"},
    "mirage": {"name": "🏝️ Mirage Island", "emoji": "🏝️", "category": "island"},
    "prehistoric": {"name": "🌋 Prehistoric Island", "emoji": "🌋", "category": "island"},
    "legendarysword": {"name": "⚔️ Legendary Sword", "emoji": "⚔️", "category": "weapon"},
    "bossnormal": {"name": "👹 Boss Normal", "emoji": "👹", "category": "boss"},
    "doughking": {"name": "👑 Dough King", "emoji": "👑", "category": "legendary_boss"},
    "ripindra": {"name": "💀 Rip Indra", "emoji": "⚡", "category": "legendary_boss"},
    "soulreaper": {"name": "💀 Soul Reaper", "emoji": "💀", "category": "legendary_boss"},
    "cursedcap": {"name": "👻 Cursed Captain", "emoji": "👻", "category": "legendary_boss"},
    "cakeprince": {"name": "🍰 Cake Prince", "emoji": "🍰", "category": "legendary_boss"},
    "tyrant": {"name": "🦅 Tyrant of Skies", "emoji": "🌪️", "category": "legendary_boss"},
    "darkbeard": {"name": "🌑 Darkbeard", "emoji": "🌑", "category": "legendary_boss"},
    "hakilegendary": {"name": "🌈 Legendary Haki", "emoji": "🌈", "category": "haki"},
    "multiboss": {"name": "🎯 Multi Boss", "emoji": "🎯", "category": "boss"},
}

# ==================== EVENT DISPLAY NAMES (CHO EMBED) ====================
EVENT_DISPLAY_NAMES = {
    "fullmoon": "Full Moon",
    "nearmoon": "Near Full Moon", 
    "kitsune": "Kitsune Island",
    "mirage": "Mirage Island",
    "prehistoric": "Prehistoric Island",
    "legendarysword": "Legendary Sword",
    "legendarysword_saishi": "Saishi",
    "legendarysword_shizu": "Shisui",
    "legendarysword_oroshi": "Oroshi",
    "bossnormal": "Normal Boss",
    "multiboss": "Multi Boss",
    "doughking": "Dough King",
    "ripindra": "Rip Indra",
    "soulreaper": "Soul Reaper",
    "cursedcap": "Cursed Captain",
    "cakeprince": "Cake Prince",
    "tyrant": "Tyrant of Skies",
    "darkbeard": "Darkbeard",
    "hakilegendary": "Legendary Haki",
    "hakilegendary_pure_red": "Pure Red",
    "hakilegendary_winter_sky": "Winter Sky", 
    "hakilegendary_snow_white": "Snow White",
}

# ==================== LEGENDARY SWORD TYPES ====================
LEGENDARY_SWORD_TYPES = {
    "saishi": "Saishi",
    "shizu": "Shisui", 
    "oroshi": "Oroshi"
}

# ==================== LEGENDARY HAKI TYPES ====================
LEGENDARY_HAKI_TYPES = {
    "pure_red": "Pure Red",
    "winter_sky": "Winter Sky", 
    "snow_white": "Snow White"
}

# ==================== MONITOR CHANNELS ====================
MONITOR_CHANNELS = {
    "1085601317717811200": {"name": "CHANNEL 1", "type": "bossnormal"},
    "1333142507801935943": {"name": "CHANNEL 2", "type": "bossnormal"},
    "1085601598555832400": {"name": "CHANNEL 3", "type": "bossnormal"},
    "1088023824555053097": {"name": "CHANNEL 4", "type": "bossnormal"},
    "1144623714663682138": {"name": "CHANNEL 5", "type": "bossnormal"},
    "1197504846459310161": {"name": "BOSS CHANNEL", "type": "multiboss"},
    "1098111694628200518": {"name": "MIRAGE ISLAND", "type": "mirage"},
    "1138764405266456606": {"name": "FULL MOON", "type": "fullmoon"},
    "1146836563251175455": {"name": "LEGENDARY SWORD", "type": "legendarysword"},
    "1297418463010357248": {"name": "KITSUNE ISLAND", "type": "kitsune"},
    "1297418097350803516": {"name": "NEAR FULL MOON", "type": "nearmoon"},
    "1427658880128909454": {"name": "LEGENDARY HAKI", "type": "hakilegendary"},
    "1426831461247488060": {"name": "COUNT CHANNEL", "type": "count"},
}

# ==================== FLASK APP ====================
app = Flask(__name__, static_folder='static', template_folder='templates')

# Initialize data store
data_store = {}
for event_type in EVENT_TYPES:
    if event_type and event_type not in data_store:
        data_store[event_type] = {"endpoint": event_type, "jobs": [], "total_jobs": 0}

# Thêm data store cho các loại kiếm cụ thể
for sword_key in LEGENDARY_SWORD_TYPES:
    endpoint = f"legendarysword_{sword_key}"
    data_store[endpoint] = {"endpoint": endpoint, "jobs": [], "total_jobs": 0}

# Thêm data store cho các loại haki cụ thể  
for haki_key in LEGENDARY_HAKI_TYPES:
    endpoint = f"hakilegendary_{haki_key}"
    data_store[endpoint] = {"endpoint": endpoint, "jobs": [], "total_jobs": 0}

# Thêm data store cho total-exec
data_store["total-exec"] = {"endpoint": "total-exec", "jobs": [], "total_jobs": 0}

channel_last_message = {}
for channel_id in MONITOR_CHANNELS:
    channel_last_message[channel_id] = None

print(f"{Fore.GREEN}[INIT]{Style.RESET_ALL} Initialized {len(data_store)} endpoints, {len(MONITOR_CHANNELS)} monitor channels")
print(f"{Fore.CYAN}[CHANNELS]{Style.RESET_ALL} Configured {len(CHANNEL_MAPPING)} notification channels")

# ==================== SYSTEM STATUS ====================
system_status = {
    "start_time": datetime.now(),
    "selfbot_connected": False,
    "discord_bot_connected": False,
    "discord_bot_ready": False,
    "last_message_time": None,
    "total_messages_processed": 0,
    "active_channels": len(MONITOR_CHANNELS),
    "database_status": "healthy",
    "api_status": "online",
    "monitor_status": "active",
    "latest_jobs": [],
    "total_jobs": 0,
    "selfbot_monitoring": False,
    "total_executed": 0,
    "last_count_time": None
}

# ==================== HELPER FUNCTIONS ====================
def calculate_uptime():
    uptime = datetime.now() - system_status["start_time"]
    hours, remainder = divmod(int(uptime.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}h {minutes}m {seconds}s"

def get_total_jobs():
    return sum(data["total_jobs"] for data in data_store.values())

def get_latest_jobs(count=5):
    all_jobs = []
    for endpoint, data in data_store.items():
        if endpoint is None:
            continue
        for job in data.get("jobs", [])[:3]:
            if job and isinstance(job, dict):
                job_copy = job.copy()
                job_copy["event_type"] = endpoint
                all_jobs.append(job_copy)
    
    try:
        all_jobs.sort(key=lambda x: x.get("timestamp", "2000-01-01"), reverse=True)
        return all_jobs[:count]
    except:
        return []

def update_system_status():
    system_status["total_jobs"] = get_total_jobs()
    system_status["latest_jobs"] = get_latest_jobs(3)

def cleanup_old_jobs():
    current_time = datetime.now()
    cleanup_threshold = current_time - timedelta(seconds=CLEANUP_INTERVAL)
    
    cleaned_count = 0
    for endpoint, data in data_store.items():
        if endpoint is None:
            continue
        original_count = len(data.get("jobs", []))
        new_jobs = []
        for job in data.get("jobs", []):
            if job is None or not isinstance(job, dict):
                continue
            try:
                job_time = datetime.fromisoformat(job.get("timestamp", "2000-01-01T00:00:00"))
                if job_time > cleanup_threshold:
                    new_jobs.append(job)
            except:
                new_jobs.append(job)
        
        data["jobs"] = new_jobs
        data["total_jobs"] = len(new_jobs)
        cleaned_count += (original_count - len(new_jobs))
    
    if cleaned_count > 0:
        print(f"{Fore.CYAN}[CLEAN]{Style.RESET_ALL} Deleted {cleaned_count} old jobs")
    
    return cleaned_count

def format_players(players_str):
    if not players_str:
        return "N/A"

    # strip hết \n, space, `
    players_str = str(players_str).strip().replace("`", "").replace("\n", "").strip()

    # Nếu API gửi N/A
    if players_str.upper() == "N/A":
        return "N/A"

    # Match dạng x/12
    m = re.match(r'^(\d+)\s*/\s*(\d+)$', players_str)
    if m:
        cur = int(m.group(1))
        maxp = int(m.group(2))
        if cur == 0:
            return "N/A"
        return f"{cur}/{maxp}"

    # Nếu chỉ là số: 3 → 3/12
    if players_str.isdigit():
        num = int(players_str)
        if num == 0:
            return "N/A"
        return f"{num}/12"

    return "N/A"

# ==================== CUSTOM ENCODE MAP ====================
ENCODE_MAP = {
    'a': 'Ri1/', 'b': 'nA9', 'c': 'lsv', 'd': 'Zak', 'e': 'Lqd',
    'f': 'h9N', 'g': 'RHj', 'h': 'nVr', 'i': 'Tkw', 'j': 'teo',
    'k': 'e06', 'l': 'n0a', 'm': 'nL2', 'n': 'ahF', 'o': 'mJt',
    'p': 'gT5', 'q': '36', 'r': 'Kro', 's': 'nO2', 't': 'H2o',
    'u': 'Hcl', 'v': 'nLa', 'w': 'nK5', 'x': 'jQz', 'y': 'pF0',
    'z': 'Mfk', 'A': 'ahu', 'B': 'Lma', 'C': 'owU', 'D': 'H48',
    'E': 'bU4', 'F': '6kD', 'G': 'Jrl', 'H': 'Pf4', 'I': 'eod',
    'J': '0eY', 'K': 'Nrb', 'L': 'Bta', 'M': 'kwO', 'N': 'neO',
    'O': 'nw8', 'P': 'I5a', 'Q': 'L3/', 'R': 'Ntv', 'S': 'Htb',
    'T': '4xb', 'U': 'xor', 'V': 'b64', 'W': 'ngu', 'X': 'nig',
    'Y': 'fck', 'Z': 'gay', '-': 'Uf9'
}

def encode_job_id(job_id):
    """Encode Job ID theo custom map"""
    if not job_id or job_id == "N/A":
        return "N/A"
    
    encoded_parts = []
    for char in job_id:
        if char in ENCODE_MAP:
            encoded_parts.append(ENCODE_MAP[char])
        else:
            encoded_parts.append(char)  # Giữ nguyên nếu không có trong map
    
    return ''.join(encoded_parts)

def create_lonelyhub_encoded_job(job_id):
    """Tạo chuỗi job ID đã encode theo format LonelyHub-..."""
    encoded = encode_job_id(job_id)
    # Base64 encode của "DumbAssNigger" + encoded job
    dumb_base64 = "RHVtYkFzc05pZ2dlcl+"  # DumbAssNigger trong base64
    return f"LonelyHub-{dumb_base64}{encoded}=="
    
# ==================== FLASK ROUTES ====================
@app.route('/')
def index():
    update_system_status()
    
    def get_display_name(event_type):
        """CHO FLASK API HIỂN THỊ - VẪN CÓ ICON"""
        event_info = EVENT_TYPES.get(event_type, {"name": event_type})
        return event_info.get("name", event_type)
    
    latest_jobs_html = ""
    if system_status["latest_jobs"]:
        for job in system_status["latest_jobs"]:
            event_type = job.get('Event-Type', job.get('event_type', 'Unknown'))
            display_name = get_display_name(event_type)
            
            job_id = job.get('Job-Id', 'N/A')
            players = format_players(job.get('Players', 'N/A'))
            world = job.get('World', 'N/A')
            timestamp = job.get('timestamp', '').replace('T', ' ')[:19]
            
            latest_jobs_html += f'''
            <div class="job-item">
                <div class="job-event">{display_name}</div>
                <div class="job-id">{job_id[:8]}...</div>
                <div class="job-details">Players: {players} | World: {world}</div>
                <div class="job-time">{timestamp}</div>
            </div>
            '''
    else:
        latest_jobs_html = '''
        <div class="job-item">
            <div class="job-details">No jobs yet...</div>
        </div>
        '''
    
    html_content = f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>System Status</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background-color: #0f0f0f;
            color: #fafafa;
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 800px;
            margin: 0 auto;
        }}

        .header {{
            text-align: center;
            margin-bottom: 40px;
        }}

        .header h1 {{
            font-size: 36px;
            font-weight: 700;
            background: linear-gradient(135deg, #16a34a 0%, #22c55e 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }}

        .header p {{
            font-size: 16px;
            color: #a1a1a1;
        }}

        .status-card {{
            background-color: #000000;
            border: 1px solid rgba(212, 212, 212, 0.25);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 24px;
        }}

        .status-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
        }}

        .status-title {{
            font-size: 20px;
            font-weight: 600;
        }}

        .status-value {{
            font-size: 20px;
            font-weight: 700;
            color: #16a34a;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }}

        .stat-card {{
            background-color: #000000;
            border: 1px solid rgba(212, 212, 212, 0.25);
            border-radius: 12px;
            padding: 16px;
        }}

        .stat-value {{
            font-size: 24px;
            font-weight: 700;
            color: #16a34b;
            margin-bottom: 4px;
        }}

        .stat-label {{
            font-size: 14px;
            color: #a1a1a1;
        }}

        .jobs-section {{
            margin-top: 24px;
        }}

        .jobs-header {{
            font-size: 18px;
            font-weight: 500;
            color: #a1a1a1;
            margin-bottom: 16px;
        }}

        .job-item {{
            background-color: #000000;
            border: 1px solid rgba(212, 212, 212, 0.25);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 12px;
        }}

        .job-event {{
            font-weight: 600;
            color: #16a34a;
            margin-bottom: 8px;
        }}

        .job-details {{
            display: flex;
            gap: 16px;
            font-size: 14px;
            color: #fafafa;
            margin-bottom: 8px;
        }}

        .job-id {{
            font-family: 'Menlo', 'SF Mono', 'Consolas', monospace;
            font-size: 12px;
            color: #a1a1a1;
        }}

        .job-time {{
            font-size: 12px;
            color: #666666;
        }}

        .bot-status {{
            display: flex;
            justify-content: space-between;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid rgba(212, 212, 212, 0.25);
        }}

        .bot-status-item {{
            text-align: center;
        }}

        .bot-label {{
            font-size: 12px;
            color: #a1a1a1;
            margin-bottom: 4px;
        }}

        .bot-value {{
            font-size: 14px;
            font-weight: 600;
        }}

        .bot-online {{
            color: #16a34a;
        }}

        .bot-offline {{
            color: #dc2626;
        }}

        .bot-waiting {{
            color: #f59e0b;
        }}

        .bot-ready {{
            color: #3b82f6;
        }}

        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid rgba(212, 212, 212, 0.25);
            color: #a1a1a1;
            font-size: 14px;
        }}

        @media (max-width: 768px) {{
            .stats-grid {{
                grid-template-columns: 1fr;
            }}
            
            .header h1 {{
                font-size: 28px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>System Status</h1>
            <p>Real-time monitoring • {len(MONITOR_CHANNELS)} channels • {len(CHANNEL_MAPPING)} notification channels</p>
        </div>

        <div class="status-card">
            <div class="status-header">
                <div class="status-title">Overall Status</div>
                <div class="status-value">operational</div>
            </div>

            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{system_status["total_jobs"]}</div>
                    <div class="stat-label">Total Jobs</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{len(MONITOR_CHANNELS)}</div>
                    <div class="stat-label">Monitor Channels</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{len(EVENT_TYPES)}</div>
                    <div class="stat-label">Event Types</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{calculate_uptime()}</div>
                    <div class="stat-label">Uptime</div>
                </div>
            </div>

            <div class="bot-status">
                <div class="bot-status-item">
                    <div class="bot-label">SelfBot</div>
                    <div class="bot-value {'bot-online' if system_status['selfbot_connected'] else 'bot-offline'}">
                        {'✅ Online' if system_status['selfbot_connected'] else '❌ Offline'}
                    </div>
                </div>
                <div class="bot-status-item">
                    <div class="bot-label">Discord Bot</div>
                    <div class="bot-value {'bot-ready' if system_status['discord_bot_ready'] else ('bot-online' if system_status['discord_bot_connected'] else ('bot-waiting' if system_status['discord_bot_connected'] and not system_status['discord_bot_ready'] else 'bot-offline'))}">
                        {'✅ Ready' if system_status['discord_bot_ready'] else ('🌐 Connected' if system_status['discord_bot_connected'] else ('⏳ Waiting' if system_status['discord_bot_connected'] and not system_status['discord_bot_ready'] else '❌ Offline'))}
                    </div>
                </div>
                <div class="bot-status-item">
                    <div class="bot-label">Monitoring</div>
                    <div class="bot-value {'bot-online' if system_status['selfbot_monitoring'] else 'bot-waiting'}">
                        {'✅ Active' if system_status['selfbot_monitoring'] else '⏳ Waiting'}
                    </div>
                </div>
                <div class="bot-status-item">
                    <div class="bot-label">Messages</div>
                    <div class="bot-value">{system_status['total_messages_processed']}</div>
                </div>
            </div>

            <div class="jobs-section">
                <div class="jobs-header">Latest Jobs</div>
                {latest_jobs_html}
            </div>
        </div>

        <div class="footer">
            <p>© 2025 Lonely Hub • Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
    </div>

    <script>
        // Auto-refresh trang mỗi 30 giây
        setInterval(function() {{
            location.reload();
        }}, 30000);
    </script>
</body>
</html>
    '''
    
    return html_content

@app.route('/api/status')
def api_status():
    update_system_status()
    
    status_data = {
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "system": {
            "uptime": calculate_uptime(),
            "start_time": system_status["start_time"].isoformat(),
            "total_jobs": system_status["total_jobs"],
            "total_channels": len(MONITOR_CHANNELS),
            "total_event_types": len(EVENT_TYPES),
            "selfbot_connected": system_status["selfbot_connected"],
            "discord_bot_connected": system_status["discord_bot_connected"],
            "discord_bot_ready": system_status["discord_bot_ready"],
            "selfbot_monitoring": system_status["selfbot_monitoring"],
            "total_messages_processed": system_status["total_messages_processed"],
            "total_executed": system_status["total_executed"]
        },
        "notification_channels": {
            "total": len(CHANNEL_MAPPING),
            "channels": CHANNEL_MAPPING
        }
    }
    
    return jsonify(status_data)

@app.route('/<endpoint>', methods=['GET', 'POST'])
def handle_data(endpoint):
    if endpoint not in data_store:
        return jsonify({"error": "Endpoint Not Found"}), 404
    
    if request.method == 'POST':
        data = request.json or {}
        
        job_data = {
            "Job-Id": data.get("Job-Id", ""),
            "Encoded-Job": data.get("Encoded-Job", ""),
            "Players": format_players(data.get("Players", "")),
            "World": data.get("World", ""),
            "Name": data.get("Name", ""),
            "Script": data.get("Script", ""),
            "Event-Type": data.get("Event-Type", endpoint),
            "timestamp": datetime.now().isoformat()
        }
        
        if job_data["Job-Id"]:
            existing_job_index = -1
            for i, job in enumerate(data_store[endpoint]["jobs"]):
                if job.get("Job-Id") == job_data["Job-Id"]:
                    existing_job_index = i
                    break
            
            if existing_job_index >= 0:
                data_store[endpoint]["jobs"][existing_job_index] = job_data
                print(f"{Fore.GREEN}[FLASK]{Style.RESET_ALL} 🔄 Updated job: {job_data['Job-Id'][:8]}...")
            else:
                data_store[endpoint]["jobs"].append(job_data)
                print(f"{Fore.GREEN}[FLASK]{Style.RESET_ALL} ➕ New job: {job_data['Job-Id'][:8]}...")
            
            data_store[endpoint]["total_jobs"] = len(data_store[endpoint]["jobs"])
            system_status["total_messages_processed"] += 1
            
            # Gửi thông báo đến kênh Discord nếu có mapping VÀ bot đã ready
            target_event_type = endpoint
            # Nếu là kiếm hoặc haki cụ thể, map về channel chung
            if endpoint.startswith("legendarysword_"):
                target_event_type = "legendarysword"
            elif endpoint.startswith("hakilegendary_"):
                target_event_type = "hakilegendary"
            
            if target_event_type in CHANNEL_MAPPING and system_status["discord_bot_ready"]:
                channel_id = CHANNEL_MAPPING[target_event_type]
                print(f"{Fore.CYAN}[NOTIFY]{Style.RESET_ALL} 📤 Sending notification to channel {channel_id}...")
                # Gửi thông báo trong background thread
                threading.Thread(
                    target=lambda: asyncio.run_coroutine_threadsafe(
                        discord_bot.send_lonelyhub_notification(endpoint, job_data),
                        discord_bot.bot.loop
                    ),
                    daemon=True
                ).start()
            elif target_event_type in CHANNEL_MAPPING and not system_status["discord_bot_ready"]:
                print(f"{Fore.YELLOW}[NOTIFY]{Style.RESET_ALL} ⚠️ Discord Bot not ready, skipping notification for {endpoint}")
        
        return jsonify(data_store[endpoint])
    else:
        return jsonify(data_store[endpoint])

# ==================== SELFBOT MONITOR ====================
class SelfBotMonitor:
    def __init__(self, token):
        self.token = token
        self.headers = {"Authorization": token}
        self.processed_messages = set()
        self.monitoring_active = False
        self.last_count_time = datetime.now()
    
    async def start_monitoring(self):
        print(f"{Fore.GREEN}[SELFBOT]{Style.RESET_ALL} 🚀 Starting SelfBot monitor...")
        
        token_valid = await self.check_token_valid()
        if not token_valid:
            print(f"{Fore.RED}[SELFBOT]{Style.RESET_ALL} ❌ Cannot connect SelfBot!")
            system_status["selfbot_connected"] = False
            return
        
        print(f"{Fore.GREEN}[SELFBOT]{Style.RESET_ALL} ✅ Token valid, waiting for Discord Bot to be ready...")
        system_status["monitor_status"] = "waiting"
        
        # Chờ cho đến khi Discord Bot ready
        while not system_status["discord_bot_ready"]:
            print(f"{Fore.YELLOW}[SELFBOT]{Style.RESET_ALL} ⏳ Waiting for Discord Bot to be ready...")
            await asyncio.sleep(5)
        
        print(f"{Fore.GREEN}[SELFBOT]{Style.RESET_ALL} ✅ Discord Bot is ready, starting monitoring...")
        system_status["monitor_status"] = "active"
        system_status["selfbot_monitoring"] = True
        self.monitoring_active = True
        
        # Bắt đầu count embed task
        asyncio.create_task(self.count_embeds_periodically())
        
        tasks = []
        for channel_id, channel_config in MONITOR_CHANNELS.items():
            if channel_id == COUNT_CHANNEL_ID:
                continue  # Bỏ qua channel count
            task = self.monitor_channel_realtime(channel_id, channel_config)
            tasks.append(task)
        
        await asyncio.gather(*tasks)
    
    async def count_embeds_periodically(self):
        """Đếm số embed trong channel COUNT_CHANNEL_ID mỗi 5 phút"""
        while self.monitoring_active:
            try:
                await asyncio.sleep(COUNT_INTERVAL)
                
                print(f"{Fore.CYAN}[COUNT]{Style.RESET_ALL} 🔢 Counting embeds in channel {COUNT_CHANNEL_ID}...")
                
                # Lấy tất cả messages từ channel
                all_messages = []
                last_message_id = None
                
                # Lấy messages theo batch 100
                for _ in range(10):  # Tối đa 1000 messages
                    messages = await self.get_channel_messages_batch(COUNT_CHANNEL_ID, limit=100, before=last_message_id)
                    if not messages:
                        break
                    
                    all_messages.extend(messages)
                    last_message_id = messages[-1]["id"]
                
                # Đếm số embed
                embed_count = 0
                for message in all_messages:
                    if message.get("embeds"):
                        embed_count += len(message["embeds"])
                
                print(f"{Fore.CYAN}[COUNT]{Style.RESET_ALL} 📊 Found {embed_count} embeds")
                
                # Cập nhật system status
                system_status["total_executed"] = embed_count
                system_status["last_count_time"] = datetime.now().isoformat()
                
                # Gửi đến API /total-exec
                try:
                    api_url = f"http://localhost:{FLASK_PORT}/total-exec"
                    data = {"total-execute": embed_count}
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.post(api_url, json=data, timeout=10) as resp:
                            if resp.status == 200:
                                print(f"{Fore.GREEN}[COUNT]{Style.RESET_ALL} ✅ Sent count to /total-exec: {embed_count}")
                            else:
                                print(f"{Fore.RED}[COUNT]{Style.RESET_ALL} ❌ Failed to send count: {resp.status}")
                except Exception as e:
                    print(f"{Fore.RED}[COUNT]{Style.RESET_ALL} ❌ Error sending to API: {e}")
                
                # Cập nhật tên channel DISPLAY_CHANNEL_ID
                await self.update_channel_name(embed_count)
                
            except Exception as e:
                print(f"{Fore.RED}[COUNT]{Style.RESET_ALL} ❌ Error counting embeds: {e}")
                await asyncio.sleep(60)
    
    async def get_channel_messages_batch(self, channel_id, limit=100, before=None):
        """Lấy messages theo batch"""
        url = f"{BASE_URL}/channels/{channel_id}/messages?limit={limit}"
        if before:
            url += f"&before={before}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    print(f"{Fore.RED}[COUNT]{Style.RESET_ALL} ❌ Error getting messages: {resp.status}")
                    return []
    
    async def update_channel_name(self, count):
        """Cập nhật tên channel DISPLAY_CHANNEL_ID"""
        try:
            url = f"{BASE_URL}/channels/{DISPLAY_CHANNEL_ID}"
            data = {"name": f"Total Executed: {count}"}
            
            async with aiohttp.ClientSession() as session:
                async with session.patch(url, json=data, headers=self.headers) as resp:
                    if resp.status == 200:
                        print(f"{Fore.GREEN}[COUNT]{Style.RESET_ALL} ✅ Updated channel name to: Total Executed: {count}")
                        return True
                    else:
                        error_text = await resp.text()
                        print(f"{Fore.RED}[COUNT]{Style.RESET_ALL} ❌ Failed to update channel name: {resp.status} - {error_text}")
                        return False
        except Exception as e:
            print(f"{Fore.RED}[COUNT]{Style.RESET_ALL} ❌ Error updating channel name: {e}")
            return False
    
    async def check_token_valid(self):
        url = f"{BASE_URL}/users/@me"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as resp:
                if resp.status == 200:
                    user_data = await resp.json()
                    print(f"{Fore.GREEN}[SELFBOT]{Style.RESET_ALL} ✅ Token valid: {user_data['username']}")
                    system_status["selfbot_connected"] = True
                    return True
                else:
                    print(f"{Fore.RED}[SELFBOT]{Style.RESET_ALL} ❌ Invalid token (Error {resp.status})")
                    system_status["selfbot_connected"] = False
                    return False
    
    async def monitor_channel_realtime(self, channel_id, channel_config):
        channel_name = channel_config["name"]
        
        print(f"{Fore.CYAN}[SELFBOT]{Style.RESET_ALL} 👀 Monitoring {channel_name} ({channel_id})")
        
        last_check = None
        
        while self.monitoring_active:
            try:
                messages = await self.get_channel_messages(channel_id, limit=5)
                
                if messages:
                    latest_message = messages[0]
                    
                    if last_check is None or latest_message["id"] != last_check:
                        for message in messages:
                            await self.process_discord_message(message)
                        last_check = latest_message["id"]
                
                await asyncio.sleep(6)
                
            except Exception as e:
                print(f"{Fore.RED}[SELFBOT]{Style.RESET_ALL} ❌ Error {channel_name}: {e}")
                await asyncio.sleep(10)
    
    async def get_channel_messages(self, channel_id, limit=5):
        url = f"{BASE_URL}/channels/{channel_id}/messages?limit={limit}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as resp:
                if resp.status == 200:
                    messages = await resp.json()
                    return messages
                else:
                    print(f"{Fore.RED}[SELFBOT]{Style.RESET_ALL} ❌ Error getting messages channel {channel_id}: {resp.status}")
                    return []
    
    def extract_job_id_from_text(self, text):
        if not text:
            return "NOT FOUND"
        
        uuid_pattern = r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}'
        
        matches = re.findall(uuid_pattern, text.lower(), re.IGNORECASE)
        
        if matches:
            job_id = matches[0]
            return job_id
        
        return "NOT FOUND"
    
    async def process_discord_message(self, message):
        channel_id = str(message.get('channel_id'))
        
        if channel_id not in MONITOR_CHANNELS:
            return
        
        message_id = message["id"]
        if message_id in self.processed_messages:
            return
        
        channel_last_message[channel_id] = datetime.now()
        
        config = MONITOR_CHANNELS[channel_id]
        content = message.get('content', '')
        embeds = message.get('embeds', [])
        
        full_text = content
        
        if embeds:
            for embed in embeds:
                if embed.get('title'):
                    full_text += "\n" + embed['title']
                if embed.get('description'):
                    full_text += "\n" + embed['description']
                if embed.get('fields'):
                    for field in embed['fields']:
                        field_name = field.get('name', '')
                        field_value = field.get('value', '')
                        full_text += f"\n{field_name}: {field_value}"
        
        if len(full_text.strip()) == 0:
            return
        
        # DEBUG LOG
        # print(f"{Fore.YELLOW}[DEBUG]{Style.RESET_ALL} Full text: {full_text[:200]}...")
        
        job_id = self.extract_job_id_from_text(full_text)
        
        if job_id == "NOT FOUND":
            # print(f"{Fore.YELLOW}[DEBUG]{Style.RESET_ALL} No Job-ID found")
            return
        
        event_type = self.detect_event_type(channel_id, full_text, config)
        
        # DEBUG: Kiểm tra event type
        # print(f"{Fore.YELLOW}[DEBUG]{Style.RESET_ALL} Detected event type: {event_type}")
        
        # Xác định tên kiếm
        sword_name = ""
        sword_type_key = ""
        if event_type.startswith("legendarysword"):
            for sword_key, sword_display in LEGENDARY_SWORD_TYPES.items():
                if sword_key in full_text.lower():
                    sword_name = sword_display
                    sword_type_key = sword_key
                    break
        
        # Xác định tên haki - FIXED: tìm case-insensitive trong cả text
        haki_name = ""
        haki_type_key = ""
        
        if event_type.startswith("hakilegendary"):
            m = re.search(r'(Snow White|Pure Red|Winter Sky)', full_text, re.IGNORECASE)
            if m:
                haki_name = m.group(1).title()
                haki_type_key = haki_name.lower().replace(" ", "_")
                    
                # Xác định tên haki - FIXED: tìm case-insensitive trong cả text
                haki_name = ""
                haki_type_key = ""
                
                if event_type.startswith("hakilegendary"):
                    # SỬA LỖI: Loại bỏ haki_patterns, dùng regex trực tiếp
                    haki_regex = re.search(r'(Snow White|Pure Red|Winter Sky)', full_text, re.IGNORECASE)
                    if haki_regex:
                        haki_name = haki_regex.group(1).title()
                        haki_type_key = haki_name.lower().replace(" ", "_")
                        
        # Parse players với DEBUG
        players_raw = self.parse_players_from_text(full_text)
        players_formatted = format_players(players_raw)
        
        # DEBUG players
        # print(f"{Fore.YELLow}[DEBUG]{Style.RESET_ALL} Players raw: '{players_raw}' → formatted: '{players_formatted}'")
        
        data = {
            "Job-Id": job_id,
            "Encoded-Job": create_lonelyhub_encoded_job(job_id),
            "Players": players_formatted,
            "World": self.parse_world_from_text(full_text),
            "Script": self.extract_script_from_text(full_text),
            "Event-Type": event_type,
            "Name": sword_name or haki_name or config["name"],
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"{Fore.GREEN}[SELFBOT]{Style.RESET_ALL} {config['name']} | Job: {data['Job-Id'][:8]}... | Type: {event_type}")
        
        if sword_name:
            print(f"{Fore.MAGENTA}[SWORD]{Style.RESET_ALL} Sword Type: {sword_name}")
        elif haki_name:
            print(f"{Fore.MAGENTA}[HAKI]{Style.RESET_ALL} Haki Type: {haki_name}")
        
        if data["Players"] and data["Players"] != "N/A":
            print(f"{Fore.CYAN}[DATA]{Style.RESET_ALL} 👥 Players: {players_raw} → {data['Players']}")
        elif data["Players"] == "N/A":
            print(f"{Fore.YELLOW}[DATA]{Style.RESET_ALL} ⚠️ Players: N/A (0/12)")
        
        if data["World"]:
            print(f"{Fore.CYAN}[DATA]{Style.RESET_ALL} 🌍 World: {data['World']}")
        
        system_status["last_message_time"] = datetime.now()
        system_status["total_messages_processed"] += 1
        
        # Gửi đến API
        api_endpoint = event_type
        if sword_type_key:
            api_endpoint = f"legendarysword_{sword_type_key}"
        elif haki_type_key:
            api_endpoint = f"hakilegendary_{haki_type_key}"
        
        api_success = await self.send_to_api(api_endpoint, data)
        
        if api_success:
            self.processed_messages.add(message_id)
            
            # Gửi thông báo đến kênh Discord nếu có mapping VÀ bot đã ready
            target_event_type = event_type
            if sword_type_key:
                target_event_type = "legendarysword"
            elif haki_type_key:
                target_event_type = "hakilegendary"
            
                if target_event_type in CHANNEL_MAPPING and system_status["discord_bot_ready"]:
                    target_channel = CHANNEL_MAPPING[target_event_type]
                    print(f"{Fore.CYAN}[NOTIFY]{Style.RESET_ALL} 📤 Sending notification to channel {target_channel}...")
                    # Tạo data riêng cho Discord với thông tin cụ thể
                    discord_data = data.copy()
                    if sword_name:
                        discord_data["Event-Type"] = f"legendarysword_{sword_type_key}"
                    elif haki_name:
                        discord_data["Event-Type"] = f"hakilegendary_{haki_type_key}"
                    
                    # SỬA LỖI: Gửi qua Discord Bot thay vì SelfBot
                    await discord_bot.send_lonelyhub_notification(
                        discord_data.get("Event-Type", event_type), 
                        discord_data
                    )
            elif target_event_type in CHANNEL_MAPPING and not system_status["discord_bot_ready"]:
                print(f"{Fore.YELLOW}[NOTIFY]{Style.RESET_ALL} ⚠️ Discord Bot not ready, skipping notification")
    
    def parse_players_from_text(self, text):
        """Parse players từ text với nhiều pattern - FIXED"""
        # Pattern 1: x/12 (phổ biến nhất)
        pattern1 = r'(\d+/\d+)'
        matches = re.findall(pattern1, text)
        if matches:
            # Lấy cái cuối cùng (thường là current/max)
            return matches[-1].strip()
        
        # Pattern 2: Player(s): x hoặc Players: x/12
        pattern2 = r'Player(?:s)?[:\s\-]*(\d+(?:/\d+)?)'
        match = re.search(pattern2, text, re.IGNORECASE)
        if match:
            players = match.group(1).strip()
            if "/" not in players:
                return f"{players}/12"
            return players
        
        # Pattern 3: 👤 x hoặc [👤] x hoặc [👤] x/12
        pattern3 = r'👤\s*(\d+(?:/\d+)?)|\[👤\]\s*(\d+(?:/\d+)?)'
        match = re.search(pattern3, text)
        if match:
            players = match.group(1) or match.group(2)
            if players:
                players = players.strip()
                if "/" not in players:
                    return f"{players}/12"
                return players
        
        # Pattern 4: ``` block chứa players
        # Tìm trong ``` để parse
        code_pattern = r'```[\s\S]*?(\d+/\d+)[\s\S]*?```'
        match = re.search(code_pattern, text)
        if match:
            return match.group(1).strip()
        
        # Pattern 5: Chỉ số đơn từ 0-12
        pattern5 = r'\b([0-9]|1[0-2])\b(?![/\d])'
        match = re.search(pattern5, text)
        if match:
            players = match.group(1).strip()
            return f"{players}/12"
        
        return ""
    
    def parse_world_from_text(self, text):
        """Parse world từ text - BẤT KỲ EVENT NÀO CŨNG PARSE ĐỘNG"""
        
        # Pattern 1: Sea 1, Sea 2, Sea 3 (phổ biến nhất)
        pattern1 = r'Sea\s*[123]'
        match = re.search(pattern1, text, re.IGNORECASE)
        if match:
            world_text = match.group(0)
            num_match = re.search(r'[123]', world_text)
            if num_match:
                return num_match.group(0)
        
        # Pattern 2: World: Sea 1, World: 2, v.v.
        pattern2 = r'World:?\s*(?:Sea\s*)?([123])'
        match = re.search(pattern2, text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # Pattern 3: 🌍 1, 🌍 2, 🌍 3
        pattern3 = r'🌍\s*([123])'
        match = re.search(pattern3, text)
        if match:
            return match.group(1)
        
        # Pattern 4: > World: Sea 3, > World: 2
        pattern4 = r'>\s*World:?\s*(?:Sea\s*)?([123])'
        match = re.search(pattern4, text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # Pattern 5: Số đơn 1,2,3 với các dấu hiệu xung quanh
        pattern5 = r'[\[\(>\s]World[\]\):\s]*([123])'
        match = re.search(pattern5, text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # Pattern 6: Trong code block
        pattern6 = r'```[\s\S]*?(?:Sea|World)[\s\S]*?([123])[\s\S]*?```'
        match = re.search(pattern6, text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # Nếu không tìm thấy, check event type để biết sea mặc định
        # Nhưng sẽ return "?" để biết là không parse được
        return "N/A"
    
    def extract_script_from_text(self, text):
        code_patterns = [
            r'```(?:lua|roblox)?\s*(.*?)```',
            r'```(.*?)```',
            r'`(.*?)`'
        ]
        
        for pattern in code_patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                script = match.group(1).strip()
                if "TeleportToPlaceInstance" in script or "GetService" in script:
                    return script
        
        script_patterns = [
            r'game:GetService\(["\']TeleportService["\']\):TeleportToPlaceInstance\([^)]+\)',
            r':TeleportToPlaceInstance\([^)]+\)',
            r'TeleportToPlaceInstance\([^)]+\)'
        ]
        
        for pattern in script_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                return match.group(0)
        
        return "N/A"
    
    def detect_event_type(self, channel_id, text, config):
        channel_type = config.get("type", "")
        text_lower = text.lower()
        
        if channel_id == "1197504846459310161":
            bosses = {
                "dough king": "doughking",
                "soul reaper": "soulreaper", 
                "cursed captain": "cursedcap",
                "rip_indra": "ripindra",
                "rip indra": "ripindra",
                "cake prince": "cakeprince",
                "cake queen": "kitsune",
                "tyrant of the skies": "tyrant",
                "darkbeard": "darkbeard"
            }
            
            for boss_name, boss_type in bosses.items():
                if boss_name in text_lower:
                    return boss_type
            
            return "multiboss"
        
        elif channel_id == "1146836563251175455":
            for sword_key, sword_name in LEGENDARY_SWORD_TYPES.items():
                if sword_key in text_lower:
                    return f"legendarysword_{sword_key}"
            return "legendarysword"
        
        elif channel_id == "1427658880128909454":
            # Match đúng format: Snow White / Pure Red / Winter Sky
            haki_regex = re.search(r'(Snow White|Pure Red|Winter Sky)', text, re.IGNORECASE)
            if haki_regex:
                haki_name = haki_regex.group(1).lower()
                return "hakilegendary_" + haki_name.replace(" ", "_")
            return "hakilegendary"
                
        return channel_type
    
    async def send_to_api(self, endpoint, data):
        try:
            api_url = f"http://localhost:{FLASK_PORT}/{endpoint}"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, json=data, timeout=10) as resp:
                    if resp.status == 200:
                        print(f"{Fore.GREEN}[API]{Style.RESET_ALL} ✅ Sent to /{endpoint}")
                        return True
                    else:
                        print(f"{Fore.RED}[API]{Style.RESET_ALL} ❌ API Error: {resp.status}")
                        return False
        except Exception as e:
            print(f"{Fore.RED}[API]{Style.RESET_ALL} ❌ Connection error: {e}")
            return False

# ==================== DISCORD BOT ====================
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

class DiscordNotificationBot:
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.ready = False
    
    def get_sea_number(self, event_type):
        """Xác định số Sea dựa trên event type"""
        sea_3_events = [
            "mirage", "prehistoric", "fullmoon", "nearmoon",
            "ripindra", "doughking", "cakeprince", "soulreaper",
            "cursedcap", "tyrant", "darkbeard", "kitsune"
        ]
        
        sea_2_events = [
            "legendarysword"
        ]
        
        # Kiểm tra các biến thể của legendarysword
        if event_type.startswith("legendarysword_"):
            return "2"
        
        # Kiểm tra HAKI LEGENDARY - TỰ ĐỘNG CHECK TỪ EVENT TYPE
        if event_type.startswith("hakilegendary_") or event_type == "hakilegendary":
            # Haki có thể xuất hiện ở Sea 1, 2, hoặc 3
            # Function này chỉ là fallback, nên trả về None để báo hiệu cần lấy từ data
            return None  # Sẽ dùng giá trị từ parse world
        
        if event_type in sea_3_events:
            return "3"
        elif event_type in sea_2_events:
            return "2"
        else:
            return "N/A"  # Default Sea 1
        
    def create_lonelyhub_embed(self, event_type, data):
        """Tạo embed theo format Lonely Hub - VỚI JOB ID ĐÃ ENCODE VÀ PLACEID"""
        # Lấy display name từ EVENT_DISPLAY_NAMES
        display_name = EVENT_DISPLAY_NAMES.get(event_type, event_type)
        
        # ƯU TIÊN: Lấy world từ data đã parse (cho HAKI)
        world = data.get("World", None)
        
        # Nếu không có world trong data, dùng get_sea_number()
        if not world or world == "N/A":
            sea = self.get_sea_number(event_type)
            # Nếu sea là None (Haki), mặc định Sea 2
            world = sea if sea is not None else "2"
        
        players = format_players(data.get("Players", ""))
        job_id = data.get("Job-Id", "Unknown")
        
        # Map PlaceId theo sea
        place_id_map = {
            "1": "85211729168715",
            "2": "79091703265657", 
            "3": "100117331123089"
        }
        place_id = place_id_map.get(world, "85211729168715")  # Default Sea 1
        
        # Tạo job ID đã encode
        encoded_job = create_lonelyhub_encoded_job(job_id)
        
        # Tạo embed theo format mới - BỎ SCRIPT JOIN
        embed = discord.Embed(
            title="<:lonelyhub:1416628422385336361> Lonely Hub Notification <:lonelyhub:1416628422385336361>",
            color=0xFFFFFF,
            timestamp=datetime.now()
        )

        # Field Type: CHỈ ADD NẾU LÀ HAKI HOẶC SWORD
        is_haki = event_type.startswith("hakilegendary_") or event_type == "hakilegendary"
        is_sword = event_type.startswith("legendarysword_") or event_type == "legendarysword"
        
        if is_haki:
            embed.add_field(
                name="**Color Name:**", 
                value=f"```\n{display_name}\n```", 
                inline=False
            )
        elif is_sword:
            embed.add_field(
                name="**Sword Name:**", 
                value=f"```\n{display_name}\n```", 
                inline=False
            )
            
        # Field Status: 🟢
        embed.add_field(
            name="**Status:**", 
            value=f"```\n🟢\n```", 
            inline=False
        )

        # Field Players - CHỈ HIỂN THỊ NẾU KHÔNG PHẢI N/A
        embed.add_field(
            name="**Players:**", 
            value=f"```\n{players}\n```", 
            inline=False
        )
        
        # Field PlaceId
        embed.add_field(
            name="**PlaceId:**", 
            value=f"```\n{place_id}\n```", 
            inline=False
        )
        
        # Field JobId (Desktop) - CODE BLOCK
        embed.add_field(
            name="**JobId:**", 
            value=f"```\n{encoded_job}\n```", 
            inline=False
        )
        
        # Field JobId (Mobile) - KHÔNG CODE BLOCK, chỉ text thường
        embed.add_field(
            name="**JobId (Mobile):**", 
            value=f"{encoded_job}", 
            inline=False
        )
        
        # Thêm footer
        embed.set_footer(
            text=f"Lonely Hub | {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        )
        
        return embed
      
    async def send_lonelyhub_notification(self, event_type, data):
        """Gửi thông báo theo format Lonely Hub"""
        if not self.ready:
            print(f"{Fore.RED}[BOT]{Style.RESET_ALL} ❌ Discord Bot not ready!")
            return False
        
        # Map event_type về channel chung nếu cần
        target_event_type = event_type
        if event_type.startswith("legendarysword_"):
            target_event_type = "legendarysword"
        elif event_type.startswith("hakilegendary_"):
            target_event_type = "hakilegendary"
        
        if target_event_type not in CHANNEL_MAPPING:
            print(f"{Fore.RED}[BOT]{Style.RESET_ALL} ❌ No channel mapping for {target_event_type}")
            return False
        
        channel_id = int(CHANNEL_MAPPING[target_event_type])
        channel = self.bot.get_channel(channel_id)
        
        if not channel:
            print(f"{Fore.RED}[BOT]{Style.RESET_ALL} ❌ Cannot get channel {channel_id}")
            return False
        
        try:
            # KIỂM TRA: Nếu có Encoded-Job thì dùng, không thì tự encode
            if "Encoded-Job" not in data or not data["Encoded-Job"]:
                data["Encoded-Job"] = create_lonelyhub_encoded_job(data.get("Job-Id", "Unknown"))
            
            # Tạo embed
            embed = self.create_lonelyhub_embed(event_type, data)
            
            # Gửi message
            await channel.send(embed=embed)
            
            print(f"{Fore.GREEN}[BOT]{Style.RESET_ALL} ✅ Sent {event_type} to #{channel.name}")
            return True
            
        except discord.Forbidden:
            print(f"{Fore.RED}[BOT]{Style.RESET_ALL} ❌ No permission to send to {channel.name}")
            return False
        except discord.HTTPException as e:
            print(f"{Fore.RED}[BOT]{Style.RESET_ALL} ❌ HTTP Error: {e}")
            return False
        except Exception as e:
            print(f"{Fore.RED}[BOT]{Style.RESET_ALL} ❌ Unknown error: {e}")
            return False
    
    async def initialize(self):
        print(f"{Fore.GREEN}[BOT]{Style.RESET_ALL} ✅ Initialized Discord Bot")

# Khởi tạo Discord Bot
discord_bot = DiscordNotificationBot(bot)

@bot.event
async def on_ready():
    print(f"{Fore.GREEN}[BOT]{Style.RESET_ALL} ✅ Logged in as: {bot.user.name}")
    print(f"{Fore.CYAN}[BOT]{Style.RESET_ALL} 🆔 Bot ID: {bot.user.id}")
    print(f"{Fore.CYAN}[BOT]{Style.RESET_ALL} 📊 Servers: {len(bot.guilds)}")
    
    await discord_bot.initialize()
    
    # Đánh dấu bot đã connected
    system_status["discord_bot_connected"] = True
    
    # Chờ 2 giây để đảm bảo mọi thứ đã sẵn sàng
    await asyncio.sleep(2)
    
    # Đánh dấu bot đã ready
    discord_bot.ready = True
    system_status["discord_bot_ready"] = True
    
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{len(MONITOR_CHANNELS)} channels"
        ),
        status=discord.Status.online
    )
    
    print(f"{Fore.GREEN}[SYSTEM]{Style.RESET_ALL} 🚀 Discord Bot READY! SelfBot can start monitoring now.")

# ==================== MAIN FUNCTIONS ====================
async def auto_cleanup():
    while True:
        await asyncio.sleep(CLEANUP_INTERVAL)
        cleanup_old_jobs()

async def update_status_periodically():
    while True:
        await asyncio.sleep(UPDATE_INTERVAL)
        update_system_status()

def run_flask():
    print(f"{Fore.CYAN}[FLASK]{Style.RESET_ALL} 🚀 Flask API running at http://localhost:{FLASK_PORT}")
    print(f"{Fore.CYAN}[FLASK]{Style.RESET_ALL} 📊 Dashboard: http://localhost:{FLASK_PORT}")
    print(f"{Fore.CYAN}[FLASK]{Style.RESET_ALL} 📋 {len(EVENT_TYPES)} event types")
    print(f"{Fore.CYAN}[SELFBOT]{Style.RESET_ALL} 👁️ Monitoring {len(MONITOR_CHANNELS)} channels")
    print(f"{Fore.CYAN}[BOT]{Style.RESET_ALL} 🤖 {len(CHANNEL_MAPPING)} notification channels configured")
    print(f"{Fore.YELLOW}[NOTES]{Style.RESET_ALL} SelfBot will wait for Discord Bot to be ready before monitoring")
    print(f"{Fore.YELLOW}[COUNT]{Style.RESET_ALL} 🔢 Counting embeds every 5 minutes from channel {COUNT_CHANNEL_ID}")
    
    app.run(host="0.0.0.0", port=FLASK_PORT, debug=False, use_reloader=False)

async def run_selfbot():
    if not SELFBOT_TOKEN:
        print(f"{Fore.YELLOW}[SELFBOT]{Style.RESET_ALL} ⚠️ No SelfBot token provided, skipping SelfBot")
        return
    
    selfbot = SelfBotMonitor(SELFBOT_TOKEN)
    await selfbot.start_monitoring()

async def run_discord_bot():
    if not BOT_TOKEN:
        print(f"{Fore.YELLOW}[BOT]{Style.RESET_ALL} ⚠️ No Discord Bot token provided, skipping Discord Bot")
        return
    
    print(f"{Fore.GREEN}[BOT]{Style.RESET_ALL} 🤖 Starting Discord Bot...")
    await bot.start(BOT_TOKEN)

async def main():
    print(f"{Fore.GREEN}[SYSTEM]{Style.RESET_ALL} 🚀 Starting system...")
    print("=" * 60)
    
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    await asyncio.sleep(3)
    
    tasks = []
    
    if SELFBOT_TOKEN:
        selfbot_task = asyncio.create_task(run_selfbot())
        tasks.append(selfbot_task)
    
    if BOT_TOKEN:
        discord_task = asyncio.create_task(run_discord_bot())
        tasks.append(discord_task)
    
    cleanup_task = asyncio.create_task(auto_cleanup())
    status_task = asyncio.create_task(update_status_periodically())
    
    tasks.extend([cleanup_task, status_task])
    
    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        print(f"{Fore.YELLOW}[SYSTEM]{Style.RESET_ALL} ⏹️ Stopping system...")
    except Exception as e:
        print(f"{Fore.RED}[SYSTEM]{Style.RESET_ALL} ❌ System error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"{Fore.YELLOW}[SYSTEM]{Style.RESET_ALL} ⏹️ Stopped by user")
    except Exception as e:
        print(f"{Fore.RED}[SYSTEM]{Style.RESET_ALL} ❌ Fatal error: {e}")