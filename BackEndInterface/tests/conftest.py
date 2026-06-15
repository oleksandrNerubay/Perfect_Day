"""
Stub heavy optional packages (whisper, pydub, deepgram) before any test
module is collected so that speech/*.py can be imported without those
libraries being installed.  Pre-importing the submodules means
patch("speech.whisper_handler.*") can resolve the target module.
"""
import sys
from unittest.mock import MagicMock

for _pkg in ("whisper", "pydub", "deepgram"):
    if _pkg not in sys.modules:
        sys.modules[_pkg] = MagicMock(name=_pkg)

# Pre-import so patch() targets are resolvable.
import speech.whisper_handler   # noqa: E402, F401
import speech.deepgram_handler  # noqa: E402, F401
