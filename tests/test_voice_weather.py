import unittest
from unittest.mock import Mock, patch

import test_voice
from vision_control.voice_commands import Command, parse_command
from vision_control.voice_weather import weather_report, safe_weather_report


FORECAST = {
    'current': {'temperature_2m': 29.4, 'apparent_temperature': 33.2,
                'relative_humidity_2m': 78, 'weather_code': 2, 'wind_speed_10m': 12.4},
    'daily': {'temperature_2m_min': [25.1], 'temperature_2m_max': [32.2],
              'precipitation_probability_max': [70], 'precipitation_sum': [23],
              'wind_speed_10m_max': [45], 'uv_index_max': [8.1], 'weather_code': [80]},
    'hourly': {'time': ['2026-09-21T08:00', '2026-09-21T16:00'],
               'precipitation_probability': [20, 70]},
}


class WeatherTests(unittest.TestCase):
    def test_exact_weather_phrases(self):
        self.assertEqual(parse_command('Thời tiết hôm nay thế nào?'), Command('weather'))
        self.assertEqual(parse_command('Hôm nay thời tiết thế nào'), Command('weather'))
        self.assertIsNone(parse_command('Thời tiết ngày mai thế nào'))

    def test_auto_coordinates_and_vietnamese_summary(self):
        with patch('vision_control.voice_weather._json', return_value=FORECAST) as request:
            text = weather_report('Đà Nẵng', True, lambda: (16.05, 108.2))
        self.assertIn('tại vị trí hiện tại', text)
        self.assertIn('cảm giác như 33 độ', text)
        self.assertIn('70 phần trăm vào buổi chiều', text)
        self.assertIn('tia UV cao', text)
        self.assertIn('mưa lớn', text)
        self.assertIn('gió mạnh', text)
        self.assertIn('latitude=16.05', request.call_args.args[0])

    def test_location_failure_falls_back_to_saved_city(self):
        with patch('vision_control.voice_weather.geocode', return_value=(16.05,108.2,'Đà Nẵng')) as geocode, \
             patch('vision_control.voice_weather._json', return_value=FORECAST):
            text = weather_report('Đà Nẵng', True, Mock(side_effect=OSError('disabled')))
        geocode.assert_called_once_with('Đà Nẵng')
        self.assertIn('tại Đà Nẵng', text)

    def test_safe_report_never_exposes_network_error(self):
        with patch('vision_control.voice_weather.weather_report', side_effect=RuntimeError('private detail')):
            self.assertEqual(safe_weather_report(), 'Không thể cập nhật thời tiết lúc này.')


class WeatherServiceTests(test_voice.VoiceServiceTests):
    def test_weather_runs_in_worker_and_replies_when_complete(self):
        self.service.config.update(weather_location='Đà Nẵng', weather_auto_location=True)
        with patch('vision_control.voice_weather.safe_weather_report', return_value='Dự báo'), \
             patch.object(self.service, 'run') as run:
            self.service.execute(Command('weather'))
            self.assertEqual(self.service.state, 'processing')
            self.assertEqual(run.call_args.args[0], 'weather')
            operation = run.call_args.args[1]
            self.assertEqual(operation(), 'Dự báo')
        with patch.object(self.service, 'reply') as reply:
            self.service.finish(0, 'weather', 'Dự báo')
        reply.assert_called_once_with('Dự báo')
        self.assertEqual(self.service.state, 'ready')


if __name__ == '__main__':
    unittest.main()
