"""Offline audio operations; invoked only from worker threads."""
import asyncio
import io
import math
import sys
import wave
import time
from pathlib import Path

from .paths import resource_root, runtime_data_dir


INITIAL_PROMPT = (
    'Mở máy tính. Mấy giờ rồi? Hôm nay là ngày mấy? Hôm nay là thứ mấy? '
    'Thời tiết hôm nay thế nào? Copy. Paste. Sao chép. Dán. Đóng cửa sổ. '
    'Tắt app. Tắt áp. Khóa máy. Hẹn giờ. Báo thức sau mười phút. '
    'Hủy hẹn giờ. Còn bao nhiêu phút?')


def model_path():
    name = 'faster-whisper-small'
    candidates = [runtime_data_dir() / 'models' / name, resource_root() / 'models' / name]
    return next((p for p in candidates if (p/'model.bin').exists()), candidates[0])


def input_devices():
    import sounddevice as sd
    devices = sd.query_devices()
    return [(d['name'], i) for i,d in enumerate(devices) if d['max_input_channels'] > 0
            and sd.query_hostapis(d['hostapi'])['name'] == 'Windows WASAPI']


def load_model():
    from faster_whisper import WhisperModel
    path = model_path()
    if not path.is_dir():
        raise RuntimeError(f'Không tìm thấy model tiếng Việt: {path}')
    return WhisperModel(str(path), device='cpu', compute_type='int8',
                        cpu_threads=2, num_workers=1, local_files_only=True)


def decode(model, data, rate, diagnostics=None):
    import numpy as np
    if not data or np.sqrt(np.mean(np.frombuffer(data,dtype=np.int16).astype(float)**2)) < 20:
        return '', 0.
    buffer=io.BytesIO()
    with wave.open(buffer,'wb') as audio:
        audio.setnchannels(1);audio.setsampwidth(2);audio.setframerate(rate);audio.writeframes(data)
    buffer.seek(0)
    segments,info=model.transcribe(buffer,language='vi',beam_size=5,temperature=0,
                               initial_prompt=INITIAL_PROMPT,
                               vad_filter=True,condition_on_previous_text=False)
    segments=list(segments)
    if diagnostics is not None:
        diagnostics(dict(
            model='faster-whisper-small',
            duration_after_vad=getattr(info,'duration_after_vad',None),
            rejection=('no_segments' if not segments else
                       'no_speech_probability' if any(s.no_speech_prob>.6 for s in segments) else
                       'low_log_probability' if any(s.avg_logprob < -1 for s in segments) else None),
            segments=[dict(text=s.text[:2000],start=s.start,end=s.end,
                           no_speech_prob=s.no_speech_prob,avg_logprob=s.avg_logprob)
                      for s in segments[:20]]))
    if any(s.no_speech_prob>.6 or s.avg_logprob < -1 for s in segments):return '',0.
    text=' '.join(s.text.strip() for s in segments)
    # Segment scores are a rejection heuristic, not a calibrated accuracy claim.
    return text,min((math.exp(s.avg_logprob) for s in segments),default=0.)


def mono_channel(data, channels):
    import numpy as np
    if channels not in (1, 2) or len(data) % (2 * channels):
        raise ValueError('Invalid interleaved PCM frame size')
    # Keep one channel for the entire utterance; averaging can cancel stereo phase.
    return np.frombuffer(data, dtype='<i2').reshape(-1, channels)[:, 0].tobytes()


def capture_and_decode(model, device_name, stop, cancel, ready, automatic=False, metrics=None, decoder=None, diagnostics=None, recording=None):
    import sounddevice as sd
    import audioop
    from .voice_endpoint import VoiceEndpoint
    import webrtcvad
    vad = webrtcvad.Vad(2)
    matches = [i for name,i in input_devices() if name == device_name]
    if len(matches) != 1:
        raise RuntimeError('Không tìm thấy đúng micro đã chọn. Hãy kiểm tra kết nối.')
    device = matches[0]
    device_info = sd.query_devices(device)
    rate = int(device_info['default_samplerate'])
    channels = min(2, int(device_info.get('max_input_channels', 1)))
    blocks = []
    raw_blocks = []
    voiced_frames = 0
    total_frames = 0
    converted = b''
    resample_state = None
    started = None
    reason = 'released'
    opening = time.monotonic()
    try:
        with sd.RawInputStream(device=device, samplerate=rate, channels=channels, dtype='int16',
                               blocksize=int(rate*.03)) as stream:
            ready('listening')
            started = time.monotonic()
            endpoint = VoiceEndpoint(started)
            while not stop.is_set() and not cancel.is_set():
                data, overflow = stream.read(int(rate*.03))
                if overflow:
                    raise RuntimeError('Micro bị mất mẫu. Vui lòng nói lại.')
                raw = bytes(data)
                data = mono_channel(raw, channels)
                raw_blocks.append(raw)
                blocks.append(data)
                now = time.monotonic()
                if now-started >= 15:
                    raise RuntimeError('Đã quá 15 giây. Lệnh bị hủy; vui lòng nói ngắn hơn.')
                pcm, resample_state = audioop.ratecv(bytes(data), 2, 1, rate, 16000, resample_state)
                converted += pcm
                speech = False
                while len(converted) >= 960:
                    voiced = vad.is_speech(converted[:960], 16000)
                    voiced_frames += int(voiced)
                    total_frames += 1
                    speech = voiced or speech
                    converted = converted[960:]
                if automatic:
                    outcome = endpoint.update(now, speech)
                    if outcome == 'empty':
                        raise RuntimeError('Không nghe thấy lời nói. Đã tắt micro.')
                    if outcome == 'submit':
                        reason = 'silence'
                        break
        if cancel.is_set() or len(blocks) < 4:
            return '', 0.
        if voiced_frames < 4:
            raise RuntimeError('Micro thu quá ít tiếng nói. Hãy chờ Đang nghe rồi nói lại gần micro hơn.')
        ready('processing')
        if decoder is not None:
            if cancel.is_set():return '', None
            return decoder(b''.join(blocks), rate)
        return decode(model,b''.join(blocks),rate,diagnostics=diagnostics)
    except Exception:
        reason = 'error'
        raise
    finally:
        if recording is not None:
            recording(b''.join(raw_blocks),rate,channels)
        if metrics is not None:
            import numpy as np
            samples = np.frombuffer(b''.join(blocks), dtype=np.int16).astype(float)
            rms = float(np.sqrt(np.mean(samples*samples))) if samples.size else 0.
            peak = float(np.max(np.abs(samples))) if samples.size else 0.
            raw_samples = np.frombuffer(b''.join(raw_blocks), dtype='<i2').reshape(-1, channels).astype(float)
            channel_levels = []
            for index in range(channels):
                values = raw_samples[:, index]
                level = float(np.sqrt(np.mean(values*values))) if values.size else 0.
                maximum = float(np.max(np.abs(values))) if values.size else 0.
                channel_levels.append(dict(channel=index+1,
                    rms_dbfs=round(20*math.log10(max(level,.0001)/32768),1),
                    peak_dbfs=round(20*math.log10(max(maximum,.0001)/32768),1),
                    clipping_ratio=round(float(np.mean(np.abs(values)>=32760)),4) if values.size else 0.))
            metrics(dict(duration_s=round(samples.size/rate, 3), sample_rate=rate,
                         input_channels=channels, mono_policy='channel_1', channel_levels=channel_levels,
                         rms_dbfs=round(20*math.log10(max(rms, .0001)/32768), 1),
                         peak_dbfs=round(20*math.log10(max(peak, .0001)/32768), 1),
                         clipping_ratio=round(float(np.mean(np.abs(samples)>=32760)), 4) if samples.size else 0.,
                         speech_s=round(voiced_frames*.03, 3), vad_frames=total_frames,
                         open_ms=round((started-opening)*1000) if started is not None else None,
                         endpoint='cancelled' if cancel.is_set() else reason))
        blocks.clear()
        raw_blocks.clear()


async def synthesize(text):
    from winrt.windows.media.speechsynthesis import SpeechSynthesizer
    from winrt.windows.storage.streams import DataReader
    voice = next((v for v in SpeechSynthesizer.all_voices if v.language.lower()=='vi-vn'),None)
    if voice is None:
        raise RuntimeError('Cần cài giọng nói tiếng Việt trong Windows Settings.')
    synth = SpeechSynthesizer()
    try:
        synth.voice = voice
        stream = await synth.synthesize_text_to_stream_async(text)
        try:
            reader = DataReader(stream)
            try:
                await reader.load_async(stream.size)
                data = bytearray(stream.size)
                reader.read_bytes(data)
                return bytes(data)
            finally:reader.close()
        finally:stream.close()
    finally:synth.close()


def speak(text, cancel):
    if sys.platform != 'win32':
        raise RuntimeError('Phản hồi giọng nói hiện chỉ hỗ trợ Windows.')
    import sounddevice as sd
    import winrt.runtime
    initialized = False
    try:
        winrt.runtime.init_apartment(winrt.runtime.MTA)
        initialized = True
    except OSError as exc:
        # Some Windows audio bindings already initialize this thread as STA.
        if getattr(exc, 'winerror', None) != -2147417850:
            raise
    try:
        async def render():return await asyncio.wait_for(synthesize(text),30)
        data = asyncio.run(render())
        if cancel.is_set():return
        with wave.open(io.BytesIO(data),'rb') as audio:
            if audio.getsampwidth()!=2:raise RuntimeError('Giọng Windows không trả PCM 16-bit.')
            with sd.RawOutputStream(samplerate=audio.getframerate(), channels=audio.getnchannels(),dtype='int16') as output:
                while not cancel.is_set():
                    block=audio.readframes(max(1,audio.getframerate()//20))
                    if not block:break
                    output.write(block)
    finally:
        if initialized:
            winrt.runtime.uninit_apartment()
