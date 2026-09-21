"""Deterministic, allowlisted Vietnamese commands. No system side effects."""
import math
import re
import unicodedata
from dataclasses import dataclass


def normalize(text):
    text = unicodedata.normalize('NFD', text.lower().replace('đ', 'd'))
    return ' '.join(re.sub(r'[^a-z0-9\s]', ' ', ''.join(
        c for c in text if unicodedata.category(c) != 'Mn')).split())


@dataclass(frozen=True)
class Command:
    name: str
    seconds: int = 0


def number(text):
    if text.isdigit():
        return int(text)
    digits = dict(zip(('mot','hai','ba','bon','nam','sau','bay','tam','chin'), range(1,10)))
    for value in range(1,100):
        tens, unit = divmod(value,10)
        if value < 10:
            forms = [next(k for k,v in digits.items() if v == value)]
        else:
            prefix = 'muoi' if tens == 1 else next(k for k,v in digits.items() if v == tens)+' muoi'
            ending = '' if not unit else ' '+next(k for k,v in digits.items() if v == unit)
            forms = [prefix+ending]
            if unit == 5: forms.append(prefix+' lam')
            if unit == 4: forms.append(prefix+' tu')
        if text in forms:
            return value
    return None


def parse_command(text):
    if re.search(r'\d[.,]\d|[-+]', text):
        return None
    text = normalize(text)
    commands = {
        'mo may tinh':'computer', 'mo this pc':'computer',
        'dong cua so':'close_window',
        'khoa may':'lock_computer', 'khoa may tinh':'lock_computer',
        'khoa man hinh':'lock_computer',
        'may gio roi':'time', 'bay gio la may gio':'time',
        'hom nay la ngay may':'date', 'hom nay ngay may':'date',
        'hom nay la thu may':'weekday', 'hom nay thu may':'weekday',
        'copy':'copy', 'sao chep':'copy', 'paste':'paste', 'dan':'paste', 'da':'paste',
        'dan noi dung':'paste', 'dan van ban':'paste',
        'huy hen gio':'cancel', 'huy bao thuc':'cancel',
        'con bao nhieu phut':'remaining', 'hen gio con bao lau':'remaining',
    }
    if text in commands:
        return Command(commands[text])
    match = re.fullmatch(r'(?:bao thuc sau|hen gio(?: sau)?) (.+) (giay|phut|gio)', text)
    if match:
        value = number(match[1])
        if value is not None:
            seconds = value * {'giay':1,'phut':60,'gio':3600}[match[2]]
            if 1 <= seconds <= 86400:
                return Command('timer', seconds)
    return None


class Countdown:
    def __init__(self):
        self.deadline = None

    def start(self, seconds, now):
        if self.deadline is not None:
            raise ValueError('Đã có hẹn giờ. Hãy hủy trước khi đặt hẹn giờ mới.')
        if not 1 <= seconds <= 86400:
            raise ValueError('Hẹn giờ phải từ 1 giây đến 24 giờ.')
        self.deadline = now + seconds

    def cancel(self):
        self.deadline = None

    def remaining(self, now):
        return None if self.deadline is None else max(0, math.ceil(self.deadline-now))

    def poll(self, now):
        if self.deadline is not None and now >= self.deadline:
            self.cancel()
            return True
        return False
