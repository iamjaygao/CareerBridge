"""Fixed vocabulary and limits of the peer mock module (design doc §1, §2, Q4)."""

INTERVIEW_TYPES = ('coding', 'behavioral', 'system_design')

# Directions per interview type. Behavioral has none; an empty direction means "general".
DIRECTIONS = {
    'coding': ('general_swe', 'frontend', 'backend', 'data_ml', 'mobile'),
    'system_design': ('general', 'infra'),
    'behavioral': (),
}

# Bump whenever the privacy notice or the terms change (PR6); users re-accept.
TERMS_VERSION = '2026-10-v1'

MAX_WINDOWS = 20
MIN_WINDOW_MINUTES = 60
MAX_WINDOW_MINUTES = 12 * 60
GRANULARITY_MINUTES = 15
DISPLAY_NAME_MAX = 40
