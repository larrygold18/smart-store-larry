from pathlib import Path
from .. import settings

# ensure logs dir exists
Path(settings.LOG_DIR).mkdir(parents=True, exist_ok=True)

# expose get_logger from your helper
from ..utils_logger import init_logger as get_logger  # noqa: E402
