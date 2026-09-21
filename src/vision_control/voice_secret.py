"""Windows user-scoped DPAPI storage; no plaintext credential on disk."""
import ctypes
from ctypes import wintypes
import os
import sys


class Blob(ctypes.Structure):
    _fields_ = [('size', wintypes.DWORD), ('data', ctypes.POINTER(ctypes.c_ubyte))]


def _crypt(data, decrypt=False):
    if sys.platform != 'win32':
        raise RuntimeError('Lưu Gemini key an toàn hiện chỉ hỗ trợ Windows.')
    buffer = ctypes.create_string_buffer(data)
    source = Blob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    target = Blob()
    dll = ctypes.WinDLL('crypt32', use_last_error=True)
    fn = dll.CryptUnprotectData if decrypt else dll.CryptProtectData
    fn.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.c_void_p,
                   ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
    fn.restype = wintypes.BOOL
    if not fn(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(target)):
        raise RuntimeError('Windows không thể đọc/ghi Gemini key của tài khoản này.')
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    try:
        return ctypes.string_at(target.data, target.size)
    finally:
        kernel.LocalFree(target.data)


def save_key(path, key):
    if not key or len(key) > 512 or any(c.isspace() or ord(c) < 33 or ord(c) > 126 for c in key):
        raise ValueError('API key không hợp lệ.')
    encrypted = _crypt(key.encode('utf-8'))
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    try:
        temporary.write_bytes(encrypted)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def load_key(path):
    if not path.exists():return ''
    try:
        return _crypt(path.read_bytes(), decrypt=True).decode('utf-8')
    except (OSError, UnicodeError, RuntimeError):
        raise RuntimeError('Không đọc được Gemini key đã lưu. Hãy nhập lại key trên máy này.') from None


def delete_key(path):
    path.unlink(missing_ok=True)
