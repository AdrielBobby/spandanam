import os

# Never speak or chant through the OS TTS during tests (it is slow, noisy, and made timing tests flaky).
os.environ.setdefault("THAALAM_MUTE", "1")
