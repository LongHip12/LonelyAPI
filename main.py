import aiohttp
import asyncio
from datetime import datetime, timedelta
from colorama import init, Fore, Style
import re
from flask import Flask, request, jsonify, render_template, send_from_directory
import threading
import time
import json
import os
from dotenv import load_dotenv

load_dotenv()
init()

# ==================== CONFIG ====================
SELFBOT_TOKEN = os.getenv("Token")
BASE_URL = "https://discord.com/api/v10"
CLEANUP_INTERVAL = 300
UPDATE_INTERVAL = 5

# ==================== COMPLETE EVENT TYPES ====================
EVENT_TYPES = {
    "fullmoon": {"name": "🌕 Full Moon", "pattern": "Full Moon Spawned", "emoji": "🌕", "category": "island"},
    "nearmoon": {"name": "🌙 Near Moon", "pattern": "Near Moon Spawned", "emoji": "🌙", "category": "island"},
    "kitsune": {"name": "🦊 Kitsune Island", "pattern": "Kitsune Island Spawned", "emoji": "🦊", "category": "island"},
    "mirage": {"name": "🏝️ Mirage Island", "pattern": "Mirage Island Spawned", "emoji": "🏝️", "category": "island"},
    "prehistoric": {"name": "🌋 Prehistoric Island", "pattern": "Prehistoric Island Spawned", "emoji": "🌋", "category": "island"},
    "frozen": {"name": "❄️ Frozen Dimension", "pattern": "Frozen Dimension Spawned", "emoji": "❄️", "category": "island"},
    "berries": {"name": "🍓 Berries", "pattern": "all", "emoji": "🍓", "category": "item"},
    "fruit": {"name": "🍎 Fruit", "pattern": "all", "emoji": "🍎", "category": "item"},
    "legendarysword": {"name": "⚔️ Legendary Sword", "patterns": ["Oroshi", "Shizu", "Saishi", "Wando", "Yama", "Shusui"], "emoji": "⚔️", "category": "weapon"},
    "pirateraid": {"name": "🏴‍☠️ Pirate Raid", "patterns": [
        "Pirates have been spotted approaching the castle!",
        "The pirates are raiding Castle on the Sea!"
    ], "emoji": "🏴‍☠️", "category": "raid"},
    "hakicolor": {"name": "🎨 Haki Color", "pattern": "all", "emoji": "🎨", "category": "haki"},
    "hakilegendary": {"name": "🌈 Legendary Haki", "patterns": ["Snow White", "Pure Red", "Winter Sky"], "emoji": "🌈", "category": "haki"},
    "bossnormal": {"name": "👹 Boss Normal", "pattern": "all", "emoji": "👹", "category": "boss"},
    "eliteboss": {"name": "😈 Elite Boss", "patterns": ["Diablo", "Urban", "Deandre"], "emoji": "😈", "category": "boss"},
    "doughking": {"name": "👑 Dough King", "pattern": "Dough King Spawned", "emoji": "👑", "category": "legendary_boss"},
    "ripindra": {"name": "💀 Rip Indra", "pattern": "Rip Indra True Form Spawned", "emoji": "⚡", "category": "legendary_boss"},
    "tyrant": {"name": "🦅 Tyrant of Skies", "pattern": "Tyrant of the Skies Spawned", "emoji": "🌪️", "category": "legendary_boss"},
    "cakeprince": {"name": "🍰 Cake Prince", "pattern": "Cake Prince Spawned", "emoji": "🍰", "category": "legendary_boss"},
    "soulreaper": {"name": "💀 Soul Reaper", "pattern": "Soul Reaper Spawned", "emoji": "💀", "category": "legendary_boss"},
    "cursedcap": {"name": "👻 Cursed Captain", "pattern": "Cursed Captain Spawned", "emoji": "👻", "category": "legendary_boss"},
    "darkbeard": {"name": "🌑 Darkbeard", "pattern": "Darkbeard Spawned", "emoji": "🌑", "category": "legendary_boss"},
    "greybeard": {"name": "🧓 Greybeard", "pattern": "Grey Beard Spawned", "emoji": "🧓", "category": "legendary_boss"},
    "multiboss": {"name": "🎯 Multi Boss", "emoji": "🎯", "category": "boss"},
    "all": {"name": "📢 All", "emoji": "📢", "category": "special"},
    "island": {"name": "🏝️ All Island", "emoji": "🏝️", "category": "special"},
    "boss": {"name": "👹 All Boss", "emoji": "👹", "category": "special"},
    "legendary": {"name": "⭐ All Special", "emoji": "⭐", "category": "special"},
}

# ==================== COMPLETE MONITOR CHANNELS ====================
MONITOR_CHANNELS = {
    "1453010791489081355": {"name": "FULL MOON", "type": "fullmoon", "pattern": "Full Moon Spawned"},
    "1453010793124593716": {"name": "NEAR MOON", "type": "nearmoon", "pattern": "Near Moon Spawned"},
    "1453010794508845250": {"name": "KITSUNE ISLAND", "type": "kitsune", "pattern": "Kitsune Island Spawned"},
    "1453010796341624939": {"name": "MIRAGE ISLAND", "type": "mirage", "pattern": "Mirage Island Spawned"},
    "1453010798896222441": {"name": "PREHISTORIC ISLAND", "type": "prehistoric", "pattern": "Prehistoric Island Spawned"},
    "1453010801072934976": {"name": "FROZEN DIMENSION", "type": "frozen", "pattern": "Frozen Dimension Spawned"},
    "1453010802528489545": {"name": "BERRIES", "type": "berries", "pattern": "all"},
    "1453010804088504402": {"name": "FRUIT", "type": "fruit", "pattern": "all"},
    "1453010809096765440": {"name": "LEGENDARY SWORD", "type": "legendarysword", "patterns": ["Oroshi", "Shizu", "Saishi", "Wando", "Yama", "Shusui"]},
    "1453010811596312596": {"name": "PIRATE RAID", "type": "pirateraid", "patterns": [
        "Pirates have been spotted approaching the castle!",
        "The pirates are raiding Castle on the Sea!"
    ]},
    "1453010813119103016": {"name": "HAKI NORMAL", "type": "hakicolor", "pattern": "all"},
    "1453010814381330443": {"name": "HAKI LEGENDARY", "type": "hakilegendary", "patterns": ["Snow White", "Pure Red", "Winter Sky"]},
    "1453010816012910673": {"name": "MULTI BOSS", "type": "multiboss"},
    "1453010817497960551": {"name": "BOSS NORMAL", "type": "bossnormal", "pattern": "all"},
    "1453010819473477774": {"name": "ELITE BOSS", "type": "eliteboss", "patterns": ["Diablo", "Urban", "Deandre"]},
    "1453010822099112039": {"name": "DOUGH KING", "type": "doughking", "pattern": "Dough King Spawned"},
    "1453010823386763427": {"name": "RIP INDRA", "type": "ripindra", "pattern": "Rip Indra True Form Spawned"},
    "1453010824716226705": {"name": "TYRANT SKIES", "type": "tyrant", "pattern": "Tyrant of the Skies Spawned"},
    "1453010825940959253": {"name": "CAKE PRINCE", "type": "cakeprince", "pattern": "Cake Prince Spawned"},
    "1453010827937448089": {"name": "SOUL REAPER", "type": "soulreaper", "pattern": "Soul Reaper Spawned"},
    "1453010829531418695": {"name": "CURSED CAPTAIN", "type": "cursedcap", "pattern": "Cursed Captain Spawned"},
    "1453010832068706507": {"name": "DARKBEARD", "type": "darkbeard", "pattern": "Darkbeard Spawned"},
    "1453010834199547904": {"name": "GREYBEARD", "type": "greybeard", "pattern": "Grey Beard Spawned"},
}

# ==================== BOSS MAPPING FOR AUTO-DETECT ====================
MULTIBOSS_MAPPING = {
    "Soul Reaper Spawned": {"endpoint": "soulreaper", "name": "Soul Reaper"},
    "Cursed Captain Spawned": {"endpoint": "cursedcap", "name": "Cursed Captain"},
    "Cake Prince Spawned": {"endpoint": "cakeprince", "name": "Cake Prince"},
    "Tyrant of the Skies Spawned": {"endpoint": "tyrant", "name": "Tyrant of the Skies"},
    "Darkbeard Spawned": {"endpoint": "darkbeard", "name": "Darkbeard"},
    "rip_indra True Form Spawned": {"endpoint": "ripindra", "name": "Rip Indra True Form"},
    "Dough King Spawned": {"endpoint": "doughking", "name": "Dough King"},
    "Grey Beard Spawned": {"endpoint": "greybeard", "name": "Grey Beard"},
}

# ==================== FLASK APP ====================
app = Flask(__name__, static_folder='static', template_folder='templates')

# Initialize data store - FIXED VERSION
data_store = {}
print(f"{Fore.CYAN}[INIT]{Style.RESET_ALL} 🗂️ Đang khởi tạo data_store...")

count = 0
for event_type in EVENT_TYPES:
    if event_type and event_type not in data_store:  # CHỈ THÊM NẾU KHÔNG PHẢI NONE VÀ CHƯA CÓ
        data_store[event_type] = {"endpoint": event_type, "jobs": [], "total_jobs": 0}
        count += 1

print(f"{Fore.GREEN}[INIT]{Style.RESET_ALL} ✅ Đã khởi tạo {count}/{len(EVENT_TYPES)} endpoints")

# ==================== SYSTEM STATUS ====================
system_status = {
    "start_time": datetime.now(),
    "selfbot_connected": False,
    "last_message_time": None,
    "total_messages_processed": 0,
    "active_channels": len(MONITOR_CHANNELS),
    "database_status": "healthy",
    "api_status": "online",
    "monitor_status": "active",
    "latest_jobs": [],
    "total_jobs": 0
}

# ==================== HELPER FUNCTIONS ====================
def calculate_uptime():
    """Tính thời gian hệ thống đã chạy"""
    uptime = datetime.now() - system_status["start_time"]
    hours, remainder = divmod(int(uptime.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}h {minutes}m {seconds}s"

def get_total_jobs():
    """Tính tổng số jobs"""
    return sum(data["total_jobs"] for data in data_store.values())

def get_latest_jobs(count=5):
    """Lấy jobs mới nhất - FIXED"""
    all_jobs = []
    
    for endpoint, data in data_store.items():
        # BỎ QUA ENDPOINT NONE
        if endpoint is None:
            continue
            
        # LẤY 3 JOBS ĐẦU TIÊN
        jobs_to_check = data.get("jobs", [])[:3]
        
        for job in jobs_to_check:
            # KIỂM TRA JOB HỢP LỆ
            if job is None or not isinstance(job, dict):
                continue
                
            # TẠO BẢN SAO AN TOÀN
            job_copy = {}
            for key, value in job.items():
                if key is not None:  # CHỈ THÊM KEY KHÔNG PHẢI NONE
                    job_copy[key] = value
            
            job_copy["event_type"] = endpoint
            all_jobs.append(job_copy)
    
    # SORT THEO TIMESTAMP
    try:
        all_jobs.sort(key=lambda x: x.get("timestamp", "2000-01-01"), reverse=True)
        return all_jobs[:count]
    except Exception as e:
        print(f"{Fore.RED}[JOBS]{Style.RESET_ALL} ❌ Lỗi sort jobs: {e}")
        return []

def update_system_status():
    """Cập nhật trạng thái hệ thống"""
    system_status["total_jobs"] = get_total_jobs()
    system_status["latest_jobs"] = get_latest_jobs(3)
    system_status["active_channels"] = len(MONITOR_CHANNELS)

def cleanup_old_jobs():
    """Tự động xóa jobs cũ sau 5 phút - FIXED"""
    current_time = datetime.now()
    cleanup_threshold = current_time - timedelta(seconds=CLEANUP_INTERVAL)
    
    cleaned_count = 0
    
    for endpoint, data in data_store.items():
        # BỎ QUA ENDPOINT NONE
        if endpoint is None:
            continue
            
        original_count = len(data.get("jobs", []))
        
        # LỌC JOBS CŨ
        new_jobs = []
        for job in data.get("jobs", []):
            if job is None or not isinstance(job, dict):
                continue
                
            try:
                job_time = datetime.fromisoformat(job.get("timestamp", "2000-01-01T00:00:00"))
                if job_time > cleanup_threshold:
                    new_jobs.append(job)
            except:
                # NẾU TIMESTAMP LỖI, GIỮ LẠI
                new_jobs.append(job)
        
        data["jobs"] = new_jobs
        data["total_jobs"] = len(new_jobs)
        cleaned_count += (original_count - len(new_jobs))
    
    if cleaned_count > 0:
        print(f"{Fore.YELLOW}[CLEANUP]{Style.RESET_ALL} 🗑️ Đã xóa {cleaned_count} jobs cũ")
    
    return cleaned_count
    
# ==================== FLASK ROUTES ====================
@app.route('/')
def index():
    """Trang chủ - HTML trực tiếp trong Python"""
    update_system_status()
    
    # ==================== TÊN HIỂN THỊ CHO JOBS ====================
    def get_display_name(event_type):
        """Chuyển đổi event_type thành tên hiển thị"""
        name_map = {
            "fullmoon": "🌕 Full Moon",
            "nearmoon": "🌙 Near Moon",
            "kitsune": "🦊 Kitsune Island",
            "mirage": "🏝️ Mirage Island",
            "prehistoric": "🌋 Prehistoric Island",
            "frozen": "❄️ Frozen Dimension",
            "berries": "🍓 Berries",
            "fruit": "🍎 Fruit",
            "legendarysword": "⚔️ Legendary Sword",
            "pirateraid": "🏴‍☠️ Pirate Raid",
            "hakicolor": "🎨 Haki Color",
            "hakilegendary": "✨ Legendary Haki",
            "bossnormal": "👹 Normal Boss",
            "eliteboss": "😈 Elite Boss",
            "multiboss": "🎯 Multi Boss",
            "doughking": "👑 Dough King",
            "ripindra": "☠️Rip Indra",
            "tyrant": "️🦅 Tyrant of The Skies",
            "cakeprince": "🍰 Cake Prince",
            "soulreaper": "💀 Soul Reaper",
            "cursedcap": "👻 Cursed Captain",
            "darkbeard": "🌑 Darkbeard",
            "greybeard": "🧓 Greybeard",
        }
        return name_map.get(event_type, event_type)
    
    # ==================== TẠO JOBS HTML ====================
    latest_jobs_html = ""
    if system_status["latest_jobs"]:
        for job in system_status["latest_jobs"]:
            event_type = job.get('Event-Type', job.get('event_type', 'Unknown'))
            display_name = get_display_name(event_type)
            
            job_id = job.get('Job-Id', 'N/A')
            players = job.get('Players', 'N/A')
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
    
    # ==================== HTML STRING ====================
    html_content = f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="robots" content="noindex, nofollow, noarchive">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <title>System Status</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet">
    
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background-color: #0f0f0f;
            color: #fafafa;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }}

        nav {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 24px;
            background-color: #000000;
            border-bottom: 1px solid rgba(212, 212, 212, 0.25);
        }}

        .logo-section {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .logo-img {{
            width: 32px;
            height: 32px;
            object-fit: cover;
            border-radius: 8px;
        }}

        .logo-text {{
            font-family: 'Space Grotesk', sans-serif;
            font-size: 20px;
            font-weight: 700;
            color: #d0d0d0;
        }}

        .menu-btn {{
            background: none;
            border: none;
            cursor: pointer;
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #fafafa;
            border-radius: 8px;
            transition: background-color 0.2s;
        }}

        .menu-btn:hover {{
            background-color: rgba(255, 255, 255, 0.1);
        }}

        .menu-btn svg {{
            width: 24px;
            height: 24px;
            stroke: currentColor;
            stroke-width: 2;
            stroke-linecap: round;
            stroke-linejoin: round;
        }}

        /* ===== MENU OVERLAY ===== */
        .menu-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: rgba(0, 0, 0, 0.8);
            z-index: 9998;
            opacity: 0;
            visibility: hidden;
            transition: opacity 0.3s, visibility 0.3s;
        }}

        .menu-overlay.active {{
            opacity: 1;
            visibility: visible;
        }}

        /* ===== MENU DROPDOWN ===== */
        .menu-dropdown {{
            position: fixed;
            top: 0;
            right: -320px;
            width: 320px;
            height: 100vh;
            background-color: #000000;
            border-left: 1px solid rgba(212, 212, 212, 0.25);
            z-index: 9999;
            transition: right 0.3s ease;
            display: flex;
            flex-direction: column;
        }}

        .menu-dropdown.active {{
            right: 0;
        }}

        .menu-dropdown-header {{
            padding: 24px;
            border-bottom: 1px solid rgba(212, 212, 212, 0.25);
            display: flex;
            align-items: center;
            gap: 12px;
            position: relative;
        }}

        .close-btn {{
            position: absolute;
            top: 20px;
            right: 20px;
            background: none;
            border: none;
            cursor: pointer;
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #a1a1a1;
            border-radius: 8px;
            transition: background-color 0.2s;
        }}

        .close-btn:hover {{
            background-color: rgba(255, 255, 255, 0.1);
        }}

        .close-btn svg {{
            width: 24px;
            height: 24px;
            stroke: currentColor;
            stroke-width: 2;
            stroke-linecap: round;
            stroke-linejoin: round;
        }}

        .menu-content {{
            padding: 24px;
            flex: 1;
        }}

        .menu-item {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 16px;
            border-radius: 8px;
            text-decoration: none;
            color: #fafafa;
            background-color: rgba(255, 255, 255, 0.05);
            transition: background-color 0.2s;
            margin-bottom: 8px;
        }}

        .menu-item:hover {{
            background-color: rgba(255, 255, 255, 0.1);
        }}

        .menu-item svg {{
            width: 20px;
            height: 20px;
        }}

        .main-content {{
            flex: 1;
            padding: 40px 24px;
        }}

        .hero {{
            text-align: center;
            margin-bottom: 40px;
        }}

        .hero h1 {{
            font-family: 'Space Grotesk', sans-serif;
            font-size: 48px;
            font-weight: 700;
            background: linear-gradient(135deg, #16a34a 0%, #22c55e 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 12px;
        }}

        .hero p {{
            font-size: 18px;
            color: #a1a1a1;
        }}

        .status-card {{
            background-color: #000000;
            border: 1px solid rgba(212, 212, 212, 0.25);
            border-radius: 16px;
            max-width: 800px;
            margin: 0 auto;
        }}

        .status-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 24px;
            border-bottom: 1px solid rgba(212, 212, 212, 0.25);
        }}

        .status-header-left {{
            font-size: 18px;
            font-weight: 600;
        }}

        .status-header-right {{
            font-family: 'Space Grotesk', sans-serif;
            font-size: 18px;
            font-weight: 700;
            color: #16a34a;
        }}

        .status-list {{
            padding: 24px;
        }}

        .status-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 0;
        }}

        .status-row:not(:last-child) {{
            border-bottom: 1px solid rgba(212, 212, 212, 0.1);
        }}

        .status-row-left {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .status-icon {{
            width: 40px;
            height: 40px;
            background-color: rgba(22, 163, 74, 0.1);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .status-icon svg {{
            width: 20px;
            height: 20px;
            stroke: #16a34a;
            stroke-width: 2;
        }}

        .status-name {{
            font-size: 16px;
            font-weight: 500;
        }}

        .status-value {{
            font-family: 'Space Grotesk', sans-serif;
            font-size: 16px;
            font-weight: 700;
            color: #16a34a;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
            padding: 0 24px;
            margin-top: 24px;
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
            color: #16a34a;
            margin-bottom: 4px;
        }}

        .stat-label {{
            font-size: 14px;
            color: #a1a1a1;
        }}

        .jobs-section {{
            padding: 0 24px;
            margin-bottom: 24px;
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
            margin-bottom: 8px;
        }}

        .job-event {{
            font-weight: 600;
            color: #16a34a;
            margin-bottom: 4px;
        }}

        .job-id {{
            font-family: 'Menlo', 'SF Mono', 'Consolas', monospace;
            font-size: 12px;
            color: #a1a1a1;
            margin-bottom: 4px;
        }}

        .job-details {{
            font-size: 14px;
            color: #fafafa;
        }}

        .job-time {{
            font-size: 12px;
            color: #666666;
            margin-top: 4px;
        }}

        .status-footer {{
            padding: 24px;
            border-top: 1px solid rgba(212, 212, 212, 0.25);
        }}

        .status-timestamp {{
            font-size: 14px;
            color: #a1a1a1;
            text-align: center;
        }}

        footer {{
            padding: 20px 24px;
            background-color: #000000;
            border-top: 1px solid rgba(212, 212, 212, 0.25);
        }}

        .copyright {{
            text-align: center;
            font-size: 14px;
            color: #a1a1a1;
        }}

        @media (max-width: 768px) {{
            .stats-grid {{
                grid-template-columns: 1fr;
            }}
            
            .hero h1 {{
                font-size: 36px;
            }}
            
            .menu-dropdown {{
                width: 100%;
                right: -100%;
            }}
            /* CHỐNG BÔI ĐEN VÀ COPY */
            body {{
                -webkit-user-select: none; /* Safari */
                -moz-user-select: none;    /* Firefox */
                -ms-user-select: none;     /* Internet Explorer/Edge */
                user-select: none;         /* Chuẩn */
            }}
            
            /* Cho phép bôi đen trên input/textarea nếu có */
            input, textarea {{
                -webkit-user-select: text;
                -moz-user-select: text;
                -ms-user-select: text;
                user-select: text;
            }}
            
            /* CHỐNG CHUỘT PHẢI */
            body {{
                -webkit-touch-callout: none; /* iOS Safari */
            }}
            
            /* CHỐNG KÉO HÌNH ẢNH */
            img {{
                -webkit-user-drag: none;
                -khtml-user-drag: none;
                -moz-user-drag: none;
                -o-user-drag: none;
                user-drag: none;
                pointer-events: none;
            }}
            
            /* CHỐNG DRAG NỘI DUNG */
            .status-card, .job-item, .stat-card {{
                -webkit-user-drag: none;
                user-drag: none;
            }}
        }}
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav>
        <div class="logo-section">
            <img src="https://i.imgur.com/3CXM7YH.png" alt="Logo" class="logo-img">
            <div class="logo-text">Lonely Hub</div>
        </div>
        <button class="menu-btn" id="menuBtn">
            <svg viewBox="0 0 24 24">
                <line x1="3" y1="6" x2="21" y2="6"></line>
                <line x1="3" y1="12" x2="21" y2="12"></line>
                <line x1="3" y1="18" x2="21" y2="18"></line>
            </svg>
        </button>
    </nav>

    <!-- Menu Overlay & Dropdown -->
    <div class="menu-overlay" id="menuOverlay"></div>
    <div class="menu-dropdown" id="menuDropdown">
        <div class="menu-dropdown-header">
            <img src="https://i.imgur.com/3CXM7YH.png" alt="Logo" class="logo-img">
            <div class="logo-text">Lonely Hub</div>
            <button class="close-btn" id="closeBtn">
                <svg viewBox="0 0 24 24">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
            </button>
        </div>
        <div class="menu-content">
            <a href="https://discord.gg/2anc7nHw6b" target="_blank" class="menu-item">
                <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515a.074.074 0 0 0-.079.037c-.211.375-.444.864-.607 1.25a18.27 18.27 0 0 0-5.487 0c-.163-.386-.395-.875-.607-1.25a.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057a19.9 19.9 0 0 0 5.993 3.03a.078.078 0 0 0 .084-.028a14.975 14.975 0 0 0 1.293-2.1a.07.07 0 0 0-.038-.098a13.11 13.11 0 0 1-1.872-.892a.072.072 0 0 1-.007-.12a10.15 10.15 0 0 0 .372-.294a.074.074 0 0 1 .076-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .076.01c.12.098.246.195.373.294a.072.072 0 0 1-.006.12a12.997 12.997 0 0 1-1.873.892a.07.07 0 0 0-.037.099a14.998 14.998 0 0 0 1.293 2.1a.078.078 0 0 0 .084.028a19.963 19.963 0 0 0 6.002-3.03a.079.079 0 0 0 .033-.057c.5-4.565-.838-8.628-3.546-12.2a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-.965-2.157-2.156c0-1.193.964-2.157 2.157-2.157c1.193 0 2.157.964 2.157 2.157c0 1.191-.964 2.156-2.157 2.156zm7.975 0c-1.183 0-2.157-.965-2.157-2.156c0-1.193.964-2.157 2.157-2.157c1.193 0 2.157.964 2.157 2.157c0 1.191-.964 2.156-2.157 2.156z"/>
                </svg>
                <span>Discord</span>
            </a>
        </div>
    </div>

    <!-- Main Content -->
    <div class="main-content">
        <div class="hero">
            <h1>System Status</h1>
            <p>Real-time health monitoring</p>
        </div>

        <div class="status-card">
            <div class="status-header">
                <div class="status-header-left">Overall Status</div>
                <div class="status-header-right">operational</div>
            </div>

            <div class="status-list">
                <!-- Database -->
                <div class="status-row">
                    <div class="status-row-left">
                        <div class="status-icon">
                            <svg viewBox="0 0 24 24">
                                <rect x="6" y="4" width="12" height="16" rx="2"></rect>
                                <line x1="6" y1="10" x2="18" y2="10"></line>
                                <line x1="6" y1="16" x2="18" y2="16"></line>
                            </svg>
                        </div>
                        <div class="status-name">Database</div>
                    </div>
                    <div class="status-value">100.00%</div>
                </div>

                <!-- Monitor -->
                <div class="status-row">
                    <div class="status-row-left">
                        <div class="status-icon">
                            <svg viewBox="0 0 24 24">
                                <rect x="2" y="3" width="20" height="14" rx="2"></rect>
                                <line x1="8" y1="21" x2="16" y2="21"></line>
                                <line x1="12" y1="17" x2="12" y2="21"></line>
                            </svg>
                        </div>
                        <div class="status-name">Monitor</div>
                    </div>
                    <div class="status-value">{system_status["active_channels"]}/{len(MONITOR_CHANNELS)}</div>
                </div>

                <!-- API Gateway -->
                <div class="status-row">
                    <div class="status-row-left">
                        <div class="status-icon">
                            <svg viewBox="0 0 24 24">
                                <circle cx="12" cy="12" r="1"></circle>
                                <path d="M12 3v6m0 6v6M3 12h6m6 0h6"></path>
                            </svg>
                        </div>
                        <div class="status-name">API Gateway</div>
                    </div>
                    <div class="status-value">99.99%</div>
                </div>
            </div>

            <!-- Stats Grid -->
            <div class="stats-grid" style="padding: 0 24px; margin-top: 0; margin-bottom: 24px;">
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

            <!-- Latest Jobs -->
            <div class="jobs-section" style="padding: 0 24px; margin-bottom: 24px;">
                <div class="jobs-header">Latest Jobs</div>
                {latest_jobs_html}
            </div>

            <div class="status-footer">
                <div class="status-timestamp" id="lastUpdated">Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>
            </div>
        </div>
    </div>

    <!-- Footer -->
    <footer>
        <p class="copyright">© 2025 Lonely Hub. All rights reserved.</p>
    </footer>

    <script>
        // CHỐNG CHUỘT PHẢI
        document.addEventListener('contextmenu', function(e) {{
            e.preventDefault();
            return false;
        }});
        
        // CHỐNG PHÍM TẮT (Ctrl+C, Ctrl+A, Ctrl+U, F12, etc.)
        document.addEventListener('keydown', function(e) {{
            // Ctrl+U (View source)
            if (e.ctrlKey && e.key === 'u') {{
                e.preventDefault();
                return false;
            }}
            
            // Ctrl+S (Save page)
            if (e.ctrlKey && e.key === 's') {{
                e.preventDefault();
                return false;
            }}
            
            // Ctrl+P (Print)
            if (e.ctrlKey && e.key === 'p') {{
                e.preventDefault();
                return false;
            }}
            
            // Ctrl+Shift+I, Ctrl+Shift+J, Ctrl+Shift+C (DevTools)
            if (e.ctrlKey && e.shiftKey && (e.key === 'I' || e.key === 'J' || e.key === 'C')) {{
                e.preventDefault();
                return false;
            }}
            
            // F12 (DevTools)
            if (e.key === 'F12') {{
                e.preventDefault();
                return false;
            }}
        }});
        
        // CHỐNG KÉO VÀ THẢ
        document.addEventListener('dragstart', function(e) {{
            e.preventDefault();
            return false;
        }});
        
        // CHỐNG COPY BẰNG PHÍM TẮT (Ctrl+C, Ctrl+A)
        document.addEventListener('copy', function(e) {{
            e.preventDefault();
            return false;
        }});
        
        document.addEventListener('cut', function(e) {{
            e.preventDefault();
            return false;
        }});
        
        // Update timestamp tự động
        function updateTimestamp() {{
            const now = new Date();
            const formatted = now.toLocaleString('en-GB', {{
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                day: '2-digit',
                month: '2-digit',
                year: 'numeric'
            }});
            document.getElementById('lastUpdated').textContent = 'Last updated: ' + formatted;
        }}

        // Cập nhật mỗi 5 giây
        updateTimestamp();
        setInterval(updateTimestamp, 5000);

        // Auto-refresh trang mỗi 30 giây để cập nhật status
        setInterval(function() {{
            location.reload();
        }}, 30000);

        // Menu toggle - FIX HOÀN TOÀN
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('Page loaded, initializing menu...');
            
            const menuBtn = document.getElementById('menuBtn');
            const closeBtn = document.getElementById('closeBtn');
            const menuOverlay = document.getElementById('menuOverlay');
            const menuDropdown = document.getElementById('menuDropdown');
            
            console.log('Menu elements:', {{
                menuBtn: !!menuBtn,
                closeBtn: !!closeBtn,
                menuOverlay: !!menuOverlay,
                menuDropdown: !!menuDropdown
            }});
            
            // Mở menu
            function openMenu() {{
                console.log('Opening menu');
                menuOverlay.classList.add('active');
                menuDropdown.classList.add('active');
                document.body.style.overflow = 'hidden';
            }}
            
            // Đóng menu
            function closeMenu() {{
                console.log('Closing menu');
                menuOverlay.classList.remove('active');
                menuDropdown.classList.remove('active');
                document.body.style.overflow = '';
            }}
            
            // Gán sự kiện
            if (menuBtn) {{
                menuBtn.addEventListener('click', openMenu);
            }}
            
            if (closeBtn) {{
                closeBtn.addEventListener('click', closeMenu);
            }}
        
            if (menuOverlay) {{
                menuOverlay.addEventListener('click', closeMenu);
            }}
            
            // Đóng bằng phím ESC
            document.addEventListener('keydown', function(e) {{
                if (e.key === 'Escape') {{
                    closeMenu();
                }}
            }});
            
            console.log('Menu initialized successfully');
        }});
    </script>
</body>
</html>
    '''
    
    return html_content
@app.route('/static/images/<filename>')
def serve_image(filename):
    """Serve ảnh từ static/images folder"""
    try:
        return send_from_directory('static/images', filename)
    except:
        # Nếu không có ảnh, trả về ảnh placeholder
        return '''
        <svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
            <rect width="32" height="32" rx="8" fill="#16a34a"/>
            <text x="16" y="22" text-anchor="middle" fill="white" font-family="Arial" font-size="14" font-weight="bold">LH</text>
        </svg>
        ''', 200, {'Content-Type': 'image/svg+xml'}
        
@app.route('/api/status')
def api_status():
    """API trạng thái hệ thống - JSON format"""
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
            "total_messages_processed": system_status["total_messages_processed"]
        },
        "services": {
            "database": {
                "status": system_status["database_status"],
                "uptime": "100.00%"
            },
            "monitor": {
                "status": system_status["monitor_status"],
                "active_channels": system_status["active_channels"],
                "total_channels": len(MONITOR_CHANNELS)
            },
            "api_gateway": {
                "status": system_status["api_status"],
                "uptime": "99.99%"
            }
        },
        "data_store_summary": {
            endpoint: {
                "total_jobs": data["total_jobs"],
                "latest_jobs": len(data["jobs"])
            } for endpoint, data in list(data_store.items())[:10]
        }
    }
    
    return jsonify(status_data)

@app.route('/<endpoint>', methods=['GET', 'POST'])
def handle_data(endpoint):
    """Endpoint chính cho từng loại event"""
    if endpoint not in data_store:
        return jsonify({"error": "Endpoint không tồn tại"}), 404
    
    if request.method == 'POST':
        data = request.json or {}
        
        if 'jobs' in data:
            data_store[endpoint] = data
        else:
            job_data = {
                "Job-Id": data.get("Job-Id", ""),
                "Players": data.get("Players", ""),
                "World": data.get("World", ""),
                "Name": data.get("Name", ""),
                "Script": data.get("Script", ""),
                "Event-Type": data.get("Event-Type", ""),
                "timestamp": datetime.now().isoformat()
            }
            
            # Format thông báo cho notify
            if job_data["Players"] and job_data["World"]:
                print(f"{Fore.GREEN}[NOTIFY]{Style.RESET_ALL} 📢 {job_data['Event-Type']}: Players {job_data['Players']} | World {job_data['World']}")
            
            if job_data["Job-Id"]:
                existing_job_index = -1
                for i, job in enumerate(data_store[endpoint]["jobs"]):
                    if job.get("Job-Id") == job_data["Job-Id"]:
                        existing_job_index = i
                        break
                
                if existing_job_index >= 0:
                    data_store[endpoint]["jobs"][existing_job_index] = job_data
                    print(f"{Fore.GREEN}[FLASK]{Style.RESET_ALL} 🔄 Cập nhật job: {job_data['Job-Id']}")
                else:
                    data_store[endpoint]["jobs"].append(job_data)
                    print(f"{Fore.GREEN}[FLASK]{Style.RESET_ALL} ➕ Thêm job mới: {job_data['Job-Id']}")
                
                data_store[endpoint]["total_jobs"] = len(data_store[endpoint]["jobs"])
                system_status["total_messages_processed"] += 1
        
        return jsonify(data_store[endpoint])
    else:
        return jsonify(data_store[endpoint])

@app.route('/api/notify-add', methods=['POST'])
def api_notify_add():
    """API thêm notification"""
    data = request.json or {}
    
    event_type = data.get("event_type", "")
    channel_id = data.get("channel_id", "")
    
    if event_type and channel_id:
        print(f"{Fore.GREEN}[API]{Style.RESET_ALL} 📝 Thêm notification: {channel_id} -> {event_type}")
        
        return jsonify({
            "status": "success",
            "message": f"Đã thêm notification cho channel {channel_id} với type {event_type}",
            "data": {
                "channel_id": channel_id,
                "event_type": event_type,
                "added_at": datetime.now().isoformat()
            }
        })
    
    return jsonify({"error": "Thiếu channel_id hoặc event_type"}), 400

@app.route('/api/notify-remove', methods=['POST'])
def api_notify_remove():
    """API xóa notification"""
    data = request.json or {}
    
    channel_id = data.get("channel_id", "")
    
    if channel_id:
        print(f"{Fore.YELLOW}[API]{Style.RESET_ALL} 🗑️ Xóa notification: {channel_id}")
        
        return jsonify({
            "status": "success",
            "message": f"Đã xóa notification cho channel {channel_id}"
        })
    
    return jsonify({"error": "Thiếu channel_id"}), 400

@app.route('/api/notify-autosetup', methods=['POST'])
def api_notify_autosetup():
    """API auto setup tất cả channels"""
    print(f"{Fore.CYAN}[API]{Style.RESET_ALL} 🚀 Auto setup channels")
    
    return jsonify({
        "status": "success",
        "message": f"Đã auto setup {len(MONITOR_CHANNELS)} channels",
        "channels": list(MONITOR_CHANNELS.keys())
    })

@app.route('/api/help')
def api_help():
    """API hướng dẫn sử dụng"""
    help_data = {
        "endpoints": {
            "GET /": "Dashboard với trạng thái hệ thống",
            "GET /api/status": "Trạng thái hệ thống (JSON)",
            "GET/POST /<event_type>": "Quản lý jobs cho event type",
            "POST /api/notify-add": "Thêm notification",
            "POST /api/notify-remove": "Xóa notification",
            "POST /api/notify-autosetup": "Auto setup channels",
            "GET /api/help": "Hướng dẫn sử dụng",
            "GET /api/event-types": "Danh sách event types",
            "GET /api/monitor-channels": "Danh sách channels đang monitor"
        },
        "event_types": f"Có sẵn {len(EVENT_TYPES)} loại",
        "monitor_channels": f"Đang monitor {len(MONITOR_CHANNELS)} channels",
        "system_info": {
            "uptime": calculate_uptime(),
            "total_jobs": get_total_jobs(),
            "start_time": system_status["start_time"].isoformat()
        }
    }
    
    return jsonify(help_data)

@app.route('/api/event-types')
def api_event_types():
    """API lấy danh sách event types"""
    simplified_types = {}
    for key, value in EVENT_TYPES.items():
        simplified_types[key] = {
            "name": value["name"],
            "emoji": value.get("emoji", "📌"),
            "category": value.get("category", "unknown")
        }
    return jsonify(simplified_types)

@app.route('/api/monitor-channels')
def api_monitor_channels():
    """API lấy danh sách channels đang monitor"""
    channels_list = []
    for channel_id, config in MONITOR_CHANNELS.items():
        channels_list.append({
            "channel_id": channel_id,
            "name": config["name"],
            "type": config["type"],
            "has_pattern": "pattern" in config,
            "has_patterns": "patterns" in config
        })
    
    return jsonify({
        "total_channels": len(channels_list),
        "channels": channels_list
    })

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

# ==================== SELFBOT MONITOR ====================
class SelfBotMonitor:
    def __init__(self, token):
        self.token = token
        self.headers = {"Authorization": token}
        self.processed_messages = set()
    
    async def start_monitoring(self):
        """Bắt đầu monitor tất cả channels"""
        print(f"{Fore.GREEN}[SELFBOT]{Style.RESET_ALL} 🚀 Đang khởi động monitor...")
        
        # Kiểm tra token
        token_valid = await self.check_token_valid()
        if not token_valid:
            print(f"{Fore.RED}[SELFBOT]{Style.RESET_ALL} ❌ Không thể kết nối SelfBot!")
            return
        
        print(f"{Fore.GREEN}[SELFBOT]{Style.RESET_ALL} ✅ Token hợp lệ, bắt đầu monitor...")
        
        # Bắt đầu monitor các channel
        tasks = []
        for channel_id, channel_config in MONITOR_CHANNELS.items():
            task = self.monitor_channel_realtime(channel_id, channel_config)
            tasks.append(task)
        
        await asyncio.gather(*tasks)
    
    async def check_token_valid(self):
        """Kiểm tra token có hợp lệ không"""
        url = f"{BASE_URL}/users/@me"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as resp:
                if resp.status == 200:
                    user_data = await resp.json()
                    print(f"{Fore.GREEN}[SELFBOT]{Style.RESET_ALL} ✅ Token hợp lệ: {user_data['username']}")
                    system_status["selfbot_connected"] = True
                    return True
                else:
                    print(f"{Fore.RED}[SELFBOT]{Style.RESET_ALL} ❌ Token không hợp lệ (Lỗi {resp.status})")
                    system_status["selfbot_connected"] = False
                    return False
    
    async def monitor_channel_realtime(self, channel_id, channel_config):
        """Monitor channel thời gian thực"""
        channel_name = channel_config["name"]
        
        print(f"{Fore.CYAN}[SELFBOT]{Style.RESET_ALL} 👀 Bắt đầu monitor {channel_name} ({channel_id})")
        
        last_check = None
        
        while True:
            try:
                messages = await self.get_channel_messages(channel_id, limit=5)
                
                if messages:
                    latest_message = messages[0]
                    
                    if last_check is None or latest_message["id"] != last_check:
                        for message in messages:
                            await self.process_discord_message(message)
                        last_check = latest_message["id"]
                
                await asyncio.sleep(5)
                
            except Exception as e:
                print(f"{Fore.RED}[SELFBOT]{Style.RESET_ALL} ❌ Lỗi {channel_name}: {e}")
                await asyncio.sleep(10)
    
    async def get_channel_messages(self, channel_id, limit=5):
        """Lấy tin nhắn mới nhất từ channel"""
        url = f"{BASE_URL}/channels/{channel_id}/messages?limit={limit}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as resp:
                if resp.status == 200:
                    messages = await resp.json()
                    return messages
                else:
                    print(f"{Fore.RED}[SELFBOT]{Style.RESET_ALL} ❌ Lỗi lấy tin nhắn channel {channel_id}: {resp.status}")
                    return []
    
    def extract_script_from_content(self, content):
        """Trích xuất script từ nội dung"""
        # Tìm trong code blocks
        code_patterns = [
            r'```(?:lua|roblox)?\s*(.*?)```',
            r'```(.*?)```',
            r'`(.*?)`'
        ]
        
        for pattern in code_patterns:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                script = match.group(1).strip()
                if "TeleportToPlaceInstance" in script or "GetService" in script:
                    return script
        
        # Tìm trực tiếp
        script_patterns = [
            r'game:GetService\(["\']TeleportService["\']\):TeleportToPlaceInstance\([^)]+\)',
            r':TeleportToPlaceInstance\([^)]+\)',
            r'TeleportToPlaceInstance\([^)]+\)'
        ]
        
        for pattern in script_patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                return match.group(0)
        
        return "N/A"
    
    async def process_discord_message(self, message):
        """Xử lý tin nhắn Discord"""
        channel_id = str(message.get('channel_id'))
        
        if channel_id not in MONITOR_CHANNELS:
            return
        
        message_id = message["id"]
        if message_id in self.processed_messages:
            return
        
        config = MONITOR_CHANNELS[channel_id]
        content = message.get('content', '')
        
        if not content:
            return
        
        # Parse dữ liệu với message object để lấy embed
        data = self.parse_general_data(content, message)
        
        if not data["Job-Id"]:
            print(f"{Fore.YELLOW}[SELFBOT]{Style.RESET_ALL} ⚠️ Không tìm thấy Job-Id, bỏ qua")
            return
        
        # Xác định event type
        event_type, event_name = self.detect_event_type(content, config)
        data["Event-Type"] = event_type
        data["Name"] = event_name
        
        print(f"{Fore.GREEN}[SELFBOT]{Style.RESET_ALL} ✅ {event_name} | Job: {data['Job-Id'][:8]}...")
        
        if data["Players"]:
            print(f"{Fore.CYAN}[DATA]{Style.RESET_ALL} 👥 Players: {data['Players']}")
        
        if data["World"]:
            print(f"{Fore.CYAN}[DATA]{Style.RESET_ALL} 🌍 World: {data['World']}")
        
        # Cập nhật system status
        system_status["last_message_time"] = datetime.now()
        system_status["total_messages_processed"] += 1
        
        # Gửi lên API
        success = await self.send_to_api(event_type, data)
        if success:
            self.processed_messages.add(message_id)
    
    def parse_players_from_embed(self, message):
        """Parse players từ Discord embed"""
        embeds = message.get('embeds', [])
        
        if not embeds:
            return ""
        
        embed = embeds[0]
        
        # TẠO FULL TEXT TỪ EMBED
        full_text = ""
        
        if embed.get('title'):
            full_text += f"{embed['title']}\n"
        
        if embed.get('description'):
            full_text += f"{embed['description']}\n"
        
        if embed.get('fields'):
            for field in embed['fields']:
                field_name = field.get('name', '')
                field_value = field.get('value', '')
                full_text += f"{field_name}: {field_value}\n"
        
        # TÌM PLAYERS BẰNG PATTERN (\d+/\d+)
        players_pattern = r"(\d+/\d+)"
        players_match = re.search(players_pattern, full_text)
        
        if players_match:
            return players_match.group(1).strip()
        
        return ""
    
    def parse_general_data(self, content, message=None):
        """Parse dữ liệu chung từ content và embed"""
        data = {
            "Job-Id": "",
            "Players": "",
            "World": "",
            "PlaceId": "",
            "Name": "",
            "Script": "",
            "Event-Type": "",
            "timestamp": datetime.now().isoformat()
        }
        
        # TÌM JOB-ID
        uuid_pattern = r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})'
        match = re.search(uuid_pattern, content, re.IGNORECASE)
        if match:
            data["Job-Id"] = match.group(1)
        
        # TÌM PLAYERS - CHỈ TỪ EMBED
        if message:
            data["Players"] = self.parse_players_from_embed(message)
        
        # TÌM WORLD
        world_match = re.search(r'>\s*World:\s*(Sea\s*[123])', content, re.IGNORECASE)
        if world_match:
            data["World"] = world_match.group(1)
        
        # TÌM SCRIPT
        script = ""
        code_match = re.search(r'```(?:lua|roblox)?\s*(.*?)```', content, re.DOTALL | re.IGNORECASE)
        if code_match:
            script = code_match.group(1).strip()
        
        if not script:
            teleport_match = re.search(r'TeleportToPlaceInstance\([^)]+\)', content, re.DOTALL)
            if teleport_match:
                script = teleport_match.group(0)
        
        data["Script"] = script if script else "N/A"
        
        # TÌM PLACE ID
        if script:
            place_match = re.search(r'TeleportToPlaceInstance\((\d+)', script)
            if place_match:
                data["PlaceId"] = place_match.group(1)
                
                if not data["World"]:
                    place_mapping = {
                        "7449423635": "Sea 1",
                        "100117331123089": "Sea 2",
                        "537413528": "Sea 3"
                    }
                    if data["PlaceId"] in place_mapping:
                        data["World"] = place_mapping[data["PlaceId"]]
        
        return data
    
    def detect_event_type(self, content, channel_config):
        """Xác định event type từ content và channel config"""
        channel_type = channel_config.get("type", "")
        
        if channel_type == "multiboss":
            for pattern, boss_info in MULTIBOSS_MAPPING.items():
                if pattern in content:
                    return boss_info["endpoint"], boss_info["name"]
        
        if "pattern" in channel_config:
            pattern = channel_config["pattern"]
            if pattern != "all" and pattern in content:
                return channel_type, pattern.replace("Spawned", "").strip()
        
        if "patterns" in channel_config:
            for pattern in channel_config["patterns"]:
                if pattern in content:
                    return channel_type, pattern
        
        code_block_pattern = r'```(.*?)```'
        matches = re.findall(code_block_pattern, content, re.DOTALL)
        if matches:
            for match in matches:
                match_text = match.strip()
                if match_text:
                    for pattern, boss_info in MULTIBOSS_MAPPING.items():
                        if pattern.lower() in match_text.lower():
                            return boss_info["endpoint"], boss_info["name"]
                    
                    for event_type, info in EVENT_TYPES.items():
                        if "pattern" in info and info["pattern"] != "all":
                            if info["pattern"].lower() in match_text.lower():
                                return event_type, info["name"]
                        
                        if "patterns" in info:
                            for pattern in info["patterns"]:
                                if pattern.lower() in match_text.lower():
                                    return event_type, info["name"]
        
        return channel_type, channel_config["name"]
    
    async def send_to_api(self, endpoint, data):
        """Gửi dữ liệu lên API"""
        try:
            api_url = f"http://localhost:5000/{endpoint}"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, json=data, timeout=10) as resp:
                    if resp.status == 200:
                        print(f"{Fore.GREEN}[API]{Style.RESET_ALL} ✅ Đã gửi đến /{endpoint}")
                        return True
                    else:
                        print(f"{Fore.RED}[API]{Style.RESET_ALL} ❌ Lỗi API: {resp.status}")
                        return False
        except Exception as e:
            print(f"{Fore.RED}[API]{Style.RESET_ALL} ❌ Lỗi kết nối: {e}")
            return False
            
    async def monitor_channel_realtime(self, channel_id, channel_config):
        """Monitor channel thời gian thực"""
        channel_name = channel_config["name"]
        
        print(f"{Fore.CYAN}[SELFBOT]{Style.RESET_ALL} 👀 Bắt đầu monitor {channel_name} ({channel_id})")
        
        last_check = None
        
        while True:
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
                print(f"{Fore.RED}[SELFBOT]{Style.RESET_ALL} ❌ Lỗi {channel_name}: {e}")
                await asyncio.sleep(5)
    
    async def start_monitoring(self):
        """Bắt đầu monitor tất cả channels"""
        print(f"{Fore.GREEN}[SELFBOT]{Style.RESET_ALL} 🚀 Đang khởi động monitor...")
        
        # Kiểm tra token
        token_valid = await self.check_token_valid()
        if not token_valid:
            print(f"{Fore.RED}[SELFBOT]{Style.RESET_ALL} ❌ Không thể kết nối SelfBot!")
            return
        
        print(f"{Fore.GREEN}[SELFBOT]{Style.RESET_ALL} ✅ Token hợp lệ, bắt đầu monitor...")
        
        # Bắt đầu monitor các channel
        tasks = []
        for channel_id, channel_config in MONITOR_CHANNELS.items():
            task = self.monitor_channel_realtime(channel_id, channel_config)
            tasks.append(task)
        
        await asyncio.gather(*tasks)

# ==================== MAIN FUNCTIONS ====================
async def auto_cleanup():
    """Tự động cleanup"""
    while True:
        await asyncio.sleep(CLEANUP_INTERVAL)
        cleanup_old_jobs()

async def update_status_periodically():
    """Cập nhật status định kỳ"""
    while True:
        await asyncio.sleep(UPDATE_INTERVAL)
        update_system_status()
        print(f"{Fore.BLUE}[STATUS]{Style.RESET_ALL} 📊 Cập nhật trạng thái hệ thống")

def run_flask():
    """Chạy Flask server"""
    print(f"{Fore.CYAN}[FLASK]{Style.RESET_ALL} 🚀 Flask API chạy tại http://localhost:5000")
    print(f"{Fore.CYAN}[FLASK]{Style.RESET_ALL} 📊 Tổng kênh monitor: {len(MONITOR_CHANNELS)}")
    print(f"{Fore.CYAN}[FLASK]{Style.RESET_ALL} 📋 Tổng loại thông báo: {len(EVENT_TYPES)}")
    print(f"{Fore.CYAN}[FLASK]{Style.RESET_ALL} ⏰ Tự động xóa jobs cũ mỗi 5 phút")
    print(f"{Fore.CYAN}[FLASK]{Style.RESET_ALL} 🔄 Cập nhật status mỗi {UPDATE_INTERVAL} giây")
    
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

async def main():
    """Hàm chính - FIXED VERSION"""
    print(f"{Fore.GREEN}[SYSTEM]{Style.RESET_ALL} 🚀 Đang khởi động hệ thống...")
    
    # FIX 1: XÓA KEY NONE TRONG DATA_STORE TRƯỚC KHI DÙNG
    print(f"{Fore.YELLOW}[FIX]{Style.RESET_ALL} 🔍 Đang kiểm tra data_store...")
    
    # Xóa tất cả key None nếu có
    none_keys = [key for key in list(data_store.keys()) if key is None]
    for key in none_keys:
        del data_store[key]
        print(f"{Fore.YELLOW}[FIX]{Style.RESET_ALL} 🗑️ Đã xóa key None khỏi data_store")
    
    # Khởi tạo lại data_store nếu cần
    if len(data_store) == 0:
        print(f"{Fore.YELLOW}[FIX]{Style.RESET_ALL} 🔄 Đang khởi tạo lại data_store...")
        for event_type in EVENT_TYPES:
            if event_type and event_type not in data_store:  # CHỈ THÊM NẾU KHÔNG PHẢI NONE VÀ CHƯA CÓ
                data_store[event_type] = {"endpoint": event_type, "jobs": [], "total_jobs": 0}
    
    print(f"{Fore.GREEN}[INIT]{Style.RESET_ALL} ✅ data_store có {len(data_store)} endpoints hợp lệ")
    
    # Khởi động Flask API trong thread riêng
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Chờ Flask khởi động
    await asyncio.sleep(3)
    
    # TEST FLASK TRƯỚC
    print(f"{Fore.CYAN}[TEST]{Style.RESET_ALL} 🧪 Đang test Flask API...")
    try:
        import requests
        resp = requests.get("http://localhost:5000/api/status", timeout=5)
        if resp.status_code == 200:
            print(f"{Fore.GREEN}[TEST]{Style.RESET_ALL} ✅ Flask API hoạt động tốt")
        else:
            print(f"{Fore.YELLOW}[TEST]{Style.RESET_ALL} ⚠️ Flask trả về mã {resp.status_code}")
    except Exception as e:
        print(f"{Fore.RED}[TEST]{Style.RESET_ALL} ❌ Không thể kết nối Flask: {e}")
    
    # Khởi tạo SelfBot
    selfbot = SelfBotMonitor(SELFBOT_TOKEN)
    
    # Chạy selfbot, cleanup và status update song song
    print(f"{Fore.GREEN}[SYSTEM]{Style.RESET_ALL} 🚀 Bắt đầu monitor...")
    
    try:
        await asyncio.gather(
            selfbot.start_monitoring(),
            auto_cleanup(),
            update_status_periodically()
        )
    except Exception as e:
        print(f"{Fore.RED}[SYSTEM]{Style.RESET_ALL} ❌ Lỗi khi chạy tasks: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"{Fore.YELLOW}[SYSTEM]{Style.RESET_ALL} ⏹️ Đã dừng hệ thống")
    except Exception as e:
        print(f"{Fore.RED}[SYSTEM]{Style.RESET_ALL} ❌ Lỗi hệ thống: {e}")
