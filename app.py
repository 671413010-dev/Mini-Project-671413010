import os
import io
import time
import asyncio
import edge_tts
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file
from gtts import gTTS

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

# Define available voices
VOICES = {
    'female': {
        'id': 'female',
        'name': 'เสียงผู้หญิง (เปรมวดี)',
        'description': 'เสียงผู้หญิงไทย นุ่มนวล ชัดเจน ไพเราะ เป็นธรรมชาติ',
        'type': 'edge',
        'voice_code': 'th-TH-PremwadeeNeural',
        'icon': 'fa-person-dress',
        'badge': 'ไทยแท้'
    },
    'male': {
        'id': 'male',
        'name': 'เสียงผู้ชาย (นิวัฒน์)',
        'description': 'เสียงผู้ชายไทย อบอุ่น ชัดเจน สุภาพ',
        'type': 'edge',
        'voice_code': 'th-TH-NiwatNeural',
        'icon': 'fa-person',
        'badge': 'ไทยแท้'
    },
    'ava': {
        'id': 'ava',
        'name': 'เสียงหญิงสาว (Ava)',
        'description': 'เสียงหญิงสาวสไตล์สากล สดใส พูดได้หลายภาษา',
        'type': 'edge',
        'voice_code': 'en-US-AvaMultilingualNeural',
        'icon': 'fa-face-smile',
        'badge': 'Multilingual'
    },
    'andrew': {
        'id': 'andrew',
        'name': 'เสียงชายหนุ่ม (Andrew)',
        'description': 'เสียงผู้ชายทุ้มลึก มั่นใจ สไตล์สากลหลายภาษา',
        'type': 'edge',
        'voice_code': 'en-US-AndrewMultilingualNeural',
        'icon': 'fa-user-tie',
        'badge': 'Multilingual'
    },
    'emma': {
        'id': 'emma',
        'name': 'เสียงหญิงนุ่ม (Emma)',
        'description': 'เสียงผู้หญิงโทนสุภาพ เป็นมิตร สไตล์สากลหลายภาษา',
        'type': 'edge',
        'voice_code': 'en-US-EmmaMultilingualNeural',
        'icon': 'fa-headset',
        'badge': 'Multilingual'
    },
    'siri': {
        'id': 'siri',
        'name': 'เสียงสิริ / Google TTS',
        'description': 'เสียงสังเคราะห์อ่านมาตรฐาน (Google Text-to-Speech)',
        'type': 'gtts',
        'voice_code': 'th',
        'icon': 'fa-robot',
        'badge': 'Classic'
    }
}

@app.route('/')
def index():
    return render_template('index.html', voices=VOICES)

@app.route('/api/synthesize', methods=['POST'])
def synthesize():
    target_text = request.form.get('target_text', '').strip()
    voice_key = request.form.get('voice', 'female').strip()
    speed = request.form.get('speed', '1.0').strip()
    pitch = request.form.get('pitch', '0').strip()
    volume = request.form.get('volume', '0').strip()

    if not target_text:
        return jsonify({'success': False, 'error': 'กรุณาระบุข้อความที่ต้องการสังเคราะห์'}), 400

    if voice_key not in VOICES:
        voice_key = 'female'

    voice_info = VOICES[voice_key]
    start_time = time.time()

    try:
        timestamp = int(time.time())
        saved_filename = f"tts_{voice_key}_{timestamp}.mp3"
        output_filepath = OUTPUT_DIR / saved_filename

        if voice_info['type'] == 'edge':
            # Edge-TTS (Neural AI Voices)
            try:
                spd_float = float(speed)
                spd_pct = int((spd_float - 1.0) * 100)
                speed_str = f"{spd_pct:+d}%"
            except Exception:
                speed_str = "+0%"

            # Pitch (+/- Hz)
            try:
                pitch_val = int(pitch)
                pitch_str = f"{pitch_val:+d}Hz"
            except Exception:
                pitch_str = "+0Hz"

            # Volume (+/- %)
            try:
                vol_val = int(volume)
                volume_str = f"{vol_val:+d}%"
            except Exception:
                volume_str = "+0%"

            async def generate_edge():
                communicate = edge_tts.Communicate(
                    target_text, 
                    voice_info['voice_code'], 
                    rate=speed_str,
                    pitch=pitch_str,
                    volume=volume_str
                )
                await communicate.save(str(output_filepath))

            # Run with retry if network glitched
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    asyncio.run(generate_edge())
                    break
                except Exception as ex:
                    if attempt == max_retries - 1:
                        # Fallback to gTTS if edge-tts failed
                        tts = gTTS(text=target_text, lang='th')
                        tts.save(str(output_filepath))
                    else:
                        time.sleep(0.5)

        elif voice_info['type'] == 'gtts':
            # Google TTS
            is_slow = False
            try:
                if float(speed) < 0.8:
                    is_slow = True
            except Exception:
                pass
            tts = gTTS(text=target_text, lang='th', slow=is_slow)
            tts.save(str(output_filepath))

        elapsed = time.time() - start_time

        return jsonify({
            'success': True,
            'message': f'สังเคราะห์สำเร็จด้วย {voice_info["name"]}',
            'audio_url': f"/audio/{saved_filename}",
            'filename': saved_filename,
            'voice_name': voice_info['name'],
            'voice_id': voice_key,
            'processing_time': round(elapsed, 2)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': f'เกิดข้อผิดพลาดในการสังเคราะห์เสียง: {str(e)}'}), 500

@app.route('/audio/<path:filename>')
def serve_audio(filename):
    file_path = OUTPUT_DIR / filename
    if file_path.exists():
        return send_file(file_path, mimetype="audio/mpeg")
    return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    print("Starting Multi-Voice TTS Web App at http://127.0.0.1:5000 ...")
    app.run(host='0.0.0.0', port=5000, debug=True)
