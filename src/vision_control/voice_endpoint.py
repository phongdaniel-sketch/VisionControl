"""Deterministic one-utterance endpoint policy; no audio or OS side effects."""
class VoiceEndpoint:
    def __init__(self, started, wait=5., silence=1.2, maximum=15.):
        self.started = started
        self.wait, self.silence, self.maximum = wait, silence, maximum
        self.last_speech = None

    def update(self, now, speech):
        if now - self.started >= self.maximum:
            return 'limit'
        if self.last_speech is None and now - self.started >= self.wait:
            return 'empty'
        if speech:
            self.last_speech = now
        if self.last_speech is not None and now - self.last_speech >= self.silence:
            return 'submit'
        return ''
