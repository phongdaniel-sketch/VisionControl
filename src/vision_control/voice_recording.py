"""User-authorized debug WAV and event sidecars, local and bounded."""
from datetime import datetime, timezone
import json
import os
import threading
import uuid
import wave

MAX_BYTES = 256 * 1024 * 1024
MAX_SAMPLES = 500
RESERVE_BYTES = 8 * 1024 * 1024


class VoiceRecording:
    def __init__(self, root, **metadata):
        root.mkdir(parents=True, exist_ok=True)
        files = [p for p in root.iterdir() if p.is_file()]
        if sum(p.stat().st_size for p in files)+RESERVE_BYTES > MAX_BYTES or sum(p.suffix=='.jsonl' for p in files)>=MAX_SAMPLES:
            raise OSError('Thư mục voice debug đạt giới hạn 256 MiB / 500 lượt. Hãy tắt lưu bản thu hoặc dọn mẫu cũ.')
        self.id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_')+uuid.uuid4().hex
        self.path = root/(self.id+'.wav')
        self.log_path = root/(self.id+'.jsonl')
        self.lock = threading.Lock()
        self.event('capture_start', **metadata)

    def event(self, event, **fields):
        row = dict(time=datetime.now(timezone.utc).isoformat(), capture_id=self.id, event=event, **fields)
        line = json.dumps(row, ensure_ascii=False, allow_nan=False)
        with self.lock, self.log_path.open('a', encoding='utf-8') as stream:
            stream.write(line+'\n')

    def save_audio(self, data, rate, channels=1):
        if not data:
            self.event('audio_empty')
            return
        if channels not in (1,2) or not 8000<=rate<=192000 or len(data)>RESERVE_BYTES-65536 or len(data)%(2*channels):
            raise ValueError('Bản thu debug vượt giới hạn hoặc PCM không hợp lệ.')
        temporary = self.path.with_suffix('.wav.tmp')
        try:
            with wave.open(str(temporary),'wb') as audio:
                audio.setnchannels(channels);audio.setsampwidth(2);audio.setframerate(rate)
                audio.writeframes(data)
            os.replace(temporary,self.path)
        finally:
            temporary.unlink(missing_ok=True)
        self.event('audio_saved', filename=self.path.name, sample_rate=rate,
                   channels=channels, duration_s=len(data)/(rate*2*channels))
