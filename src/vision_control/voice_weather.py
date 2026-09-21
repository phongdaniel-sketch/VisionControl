"""On-demand weather lookup with optional Windows location and city fallback."""
import asyncio
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

FORECAST = 'https://api.open-meteo.com/v1/forecast'
GEOCODING = 'https://geocoding-api.open-meteo.com/v1/search'
MAX_RESPONSE = 256 * 1024


def _json(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'VisionControl/0.1'})
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            data = response.read(MAX_RESPONSE + 1)
        if len(data) > MAX_RESPONSE:
            raise ValueError('response too large')
        result = json.loads(data)
        if not isinstance(result, dict) or result.get('error'):
            raise ValueError('invalid response')
        return result
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError):
        raise RuntimeError('Không thể cập nhật thời tiết lúc này.') from None


def windows_coordinates():
    if sys.platform != 'win32':
        raise RuntimeError('Windows Location is unavailable')
    import winrt.runtime
    from winrt.windows.devices.geolocation import Geolocator, PositionAccuracy
    initialized = False
    try:
        try:
            winrt.runtime.init_apartment(winrt.runtime.MTA)
            initialized = True
        except OSError as exc:
            if getattr(exc, 'winerror', None) != -2147417850:
                raise

        async def locate():
            locator = Geolocator()
            locator.desired_accuracy = PositionAccuracy.DEFAULT
            locator.allow_fallback_to_consentless_positions()
            position = await asyncio.wait_for(locator.get_geoposition_async(), 8)
            point = position.coordinate.point.position
            return float(point.latitude), float(point.longitude)

        return asyncio.run(locate())
    finally:
        if initialized:
            winrt.runtime.uninit_apartment()


def geocode(city):
    query = urllib.parse.urlencode({'name': city, 'count': 1, 'language': 'vi', 'format': 'json'})
    result = _json(GEOCODING + '?' + query).get('results') or []
    if not result:
        raise RuntimeError('Không tìm thấy thành phố đã lưu cho thời tiết.')
    place = result[0]
    try:
        return float(place['latitude']), float(place['longitude']), str(place.get('name') or city)
    except (KeyError, TypeError, ValueError):
        raise RuntimeError('Không tìm thấy thành phố đã lưu cho thời tiết.') from None


def _condition(code):
    code = int(code)
    if code == 0:return 'trời quang'
    if code in (1,2):return 'trời có mây'
    if code == 3:return 'trời nhiều mây'
    if code in (45,48):return 'có sương mù'
    if code in (51,53,55,56,57):return 'có mưa phùn'
    if code in (61,63,65,66,67,80,81,82):return 'có mưa'
    if code in (71,73,75,77,85,86):return 'có tuyết'
    if code in (95,96,99):return 'có dông'
    return 'thời tiết thay đổi'


def _period(hour):
    if hour < 5:return ' vào rạng sáng'
    if hour < 12:return ' vào buổi sáng'
    if hour < 18:return ' vào buổi chiều'
    if hour < 22:return ' vào buổi tối'
    return ' vào ban đêm'


def _first(mapping, key):
    value = mapping.get(key)
    if not isinstance(value, list) or not value or value[0] is None:
        raise ValueError(key)
    return value[0]


def weather_report(city='Đà Nẵng', auto_location=True, coordinate_provider=windows_coordinates):
    label = city
    coordinates = None
    if auto_location:
        try:
            coordinates = coordinate_provider()
            label = 'vị trí hiện tại'
        except Exception:
            coordinates = None
    if coordinates is None:
        latitude, longitude, label = geocode(city)
    else:
        latitude, longitude = coordinates
    params = {
        'latitude': round(float(latitude), 5), 'longitude': round(float(longitude), 5),
        'current': 'temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,wind_speed_10m',
        'hourly': 'precipitation_probability',
        'daily': 'weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum,wind_speed_10m_max,uv_index_max',
        'timezone': 'auto', 'forecast_days': 1,
    }
    data = _json(FORECAST + '?' + urllib.parse.urlencode(params))
    try:
        current, daily, hourly = data['current'], data['daily'], data['hourly']
        temperature = round(float(current['temperature_2m']))
        apparent = round(float(current['apparent_temperature']))
        humidity = round(float(current['relative_humidity_2m']))
        wind = round(float(current['wind_speed_10m']))
        low = round(float(_first(daily, 'temperature_2m_min')))
        high = round(float(_first(daily, 'temperature_2m_max')))
        rain = round(float(_first(daily, 'precipitation_probability_max')))
        uv = float(_first(daily, 'uv_index_max'))
        rain_sum = float(_first(daily, 'precipitation_sum'))
        max_wind = float(_first(daily, 'wind_speed_10m_max'))
        condition = _condition(current['weather_code'])
        probabilities = hourly.get('precipitation_probability') or []
        times = hourly.get('time') or []
        likely = ''
        if rain >= 30 and probabilities and len(probabilities) == len(times):
            index = max(range(len(probabilities)), key=lambda i: -1 if probabilities[i] is None else probabilities[i])
            likely = _period(int(str(times[index])[11:13]))
    except (KeyError, TypeError, ValueError, IndexError):
        raise RuntimeError('Không thể cập nhật thời tiết lúc này.') from None
    parts = [
        f'Hôm nay tại {label}, {condition}.',
        f'Hiện tại {temperature} độ, cảm giác như {apparent} độ.',
        f'Nhiệt độ từ {low} đến {high} độ.',
        f'Độ ẩm {humidity} phần trăm.',
        f'Khả năng mưa cao nhất {rain} phần trăm{likely}.',
        f'Gió khoảng {wind} ki-lô-mét một giờ.',
    ]
    notices = []
    if uv >= 6:notices.append('chỉ số tia UV cao')
    if rain_sum >= 20:notices.append('có thể có mưa lớn')
    if max_wind >= 40:notices.append('có thể có gió mạnh')
    if notices:parts.append('Lưu ý: '+', '.join(notices)+'.')
    return ' '.join(parts)


def safe_weather_report(city='Đà Nẵng', auto_location=True):
    try:
        return weather_report(city, auto_location)
    except Exception:
        return 'Không thể cập nhật thời tiết lúc này.'
