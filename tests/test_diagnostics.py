import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

import cv2
import numpy as np

from vision_control.diagnostics import DiagnosticInputAdapter, DiagnosticRecorder


class DiagnosticTests(unittest.TestCase):
    def test_adapter_releases_without_os_input(self):
        adapter = DiagnosticInputAdapter()
        adapter.move(12, 34)
        adapter.button_down('left')
        adapter.key_down('w')
        adapter.release_all()
        self.assertEqual(adapter.position(), (12, 34))
        self.assertFalse(adapter.held_buttons | adapter.held_keys)
        self.assertEqual([x['action'] for x in adapter.drain()],
                         ['move', 'button_down', 'key_down', 'button_up', 'key_up'])
        self.assertEqual(adapter.drain(), [])

    def test_duration_and_video_log_correspondence(self):
        now = [100.0]
        with tempfile.TemporaryDirectory() as directory:
            recorder = DiagnosticRecorder(directory, {}, clock=lambda: now[0])
            frame = np.zeros((560, 1280, 3), dtype=np.uint8)
            for elapsed in (0.0, 0.1):
                now[0] = 100 + elapsed
                self.assertTrue(recorder.append(frame, {
                    'elapsed_s': elapsed, 'events': [], 'mouse_found': True,
                    'phase': 'hold', 'timings_ms': {'tracking': 12.0}}))
            now[0] = 130.0
            self.assertFalse(recorder.append(frame, {}))
            recorder.close()
            recorder.close()
            rows = [json.loads(line) for line in (recorder.directory / 'frames.jsonl').read_text().splitlines()]
            self.assertEqual([row['video_frame'] for row in rows], [0, 1])
            self.assertEqual(rows[1]['elapsed_s'], .1)
            summary = json.loads((recorder.directory / 'summary.json').read_text())
            self.assertEqual(summary['processed_fps'], 10)
            video = cv2.VideoCapture(str(recorder.directory / 'session.avi'))
            try:
                for _ in rows:
                    ok, decoded = video.read()
                    self.assertTrue(ok)
                    self.assertEqual(decoded.shape, frame.shape)
                self.assertFalse(video.read()[0])
            finally:
                video.release()

    def test_codec_failure_releases_writer(self):
        writer = Mock()
        writer.isOpened.return_value = False
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(RuntimeError):
                DiagnosticRecorder(directory, {}, writer_factory=lambda *args: writer)
        writer.release.assert_called_once()

    def test_window_stop_pauses_and_flushes_release_events(self):
        from PySide6.QtWidgets import QApplication
        from vision_control.diagnostics_ui import DiagnosticWindow
        app = QApplication.instance() or QApplication([])
        runtime = Mock()
        runtime.adapter = DiagnosticInputAdapter()
        runtime.adapter.button_down('left')
        runtime.adapter.drain()
        runtime.set_paused.side_effect = lambda paused: runtime.adapter.release_all()
        window = DiagnosticWindow(runtime, autostart=False)
        recorder = Mock(count=2, directory=Path('test-session'))
        window.recorder = recorder
        window.stop_recording()
        runtime.set_paused.assert_called_with(True)
        self.assertEqual(recorder.close.call_args.args[1][0]['action'], 'button_up')
        self.assertIsNone(window.recorder)
        window.close()


if __name__ == '__main__':
    unittest.main()
