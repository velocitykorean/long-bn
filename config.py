"""VELOCITY LONGFORM - 16:9 chapter lesson, brand and motion constants."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

OUTPUT_DIR = BASE_DIR / "output"
LESSONS_DIR = OUTPUT_DIR / "lessons"
HISTORY_DIR = OUTPUT_DIR / "history"
SCENE_DIR = BASE_DIR / "scene"

VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30

TARGET_CHAPTERS = 8
PHRASES_PER_CHAPTER = 7
TARGET_PHRASES = TARGET_CHAPTERS * PHRASES_PER_CHAPTER

# ---------------------------------------------------------------- brand

BRAND = "VELOCITY BENGALI"
BRAND_LOCKUP_TOP = "VELOCITY"
BRAND_LOCKUP_BOTTOM = "BENGALI"
HANDLE = "@velocitybengali"
MASCOT_NAME = "Velo"

# ==== LANGUAGE PACK START ====
LANGUAGE = {'code': 'bn',
 'name': 'Bengali',
 'native_name': 'বাংলা',
 'history_key': 'bengali',
 'english_voice': 'en-US-AvaNeural',
 'english_fallback_voice': 'en-US-GuyNeural',
 'native_voice': 'bn-BD-NabanitaNeural',
 'native_fallback_voice': 'bn-BD-PradeepNeural',
 'native_engine': 'edge',
 'native_lang_code': 'bn',
 'english_rate': '-4%',
 'native_rate': '-10%',
 'english_pitch': '+0Hz',
 'native_pitch': '+0Hz',
 'native_label': 'বাংলা',
 'translit_label': 'SAY IT LIKE',
 'flag': 'bd',
 'greeting': 'নমস্কার!',
 'encouragement': 'অসাধারণ!',
 'rtl': False,
 'char_tiles': False,
 'script_font': 'Script.ttf',
 'glyphs': 'অআইঈউঊএঐওঔকখগঘচছজঝটঠডঢতথদধনপফবভমযরলশষসহড়ঢ়য়'}
# ==== LANGUAGE PACK END ====

# ==== CATEGORIES START ====
CATEGORIES = {'Motivation': 'অনুপ্রেরণা',
 'Love': 'ভালোবাসা',
 'Success': 'সাফল্য',
 'Wisdom': 'জ্ঞান',
 'Happiness': 'সুখ',
 'Self Improvement': 'আত্মউন্নয়ন',
 'Gratitude': 'কৃতজ্ঞতা',
 'Friendship': 'বন্ধুত্ব',
 'Hope': 'আশা',
 'Creativity': 'সৃজনশীলতা',
 'Inner Peace': 'অভ্যন্তরীণ শান্তি',
 'Confidence': 'আত্মবিশ্বাস',
 'Perseverance': 'অধ্যবসায়',
 'Inspiration': 'অনুপ্রেরণা',
 'Positive Life': 'ইতিবাচক জীবন',
 'Courage': 'সাহস',
 'Kindness': 'দয়া',
 'Patience': 'ধৈর্য',
 'Forgiveness': 'ক্ষমা',
 'Strength': 'শক্তি',
 'Joy': 'আনন্দ',
 'Balance': 'ভারসাম্য',
 'Growth': 'বৃদ্ধি',
 'Purpose': 'উদ্দেশ্য',
 'Mindfulness': 'সচেতনতা',
 'Travel & Airport': 'ভ্রমণ ও বিমানবন্দর',
 'Ordering Food & Dining': 'খাবার অর্ডার ও খাওয়া-দাওয়া',
 'Shopping & Prices': 'কেনাকাটা ও দাম',
 'Asking for Directions': 'পথ জিজ্ঞাসা',
 'Hotel & Accommodation': 'হোটেল ও থাকার জায়গা',
 'Daily Routine': 'দৈনন্দিন রুটিন',
 'Meeting People & Greetings': 'মানুষের সাথে দেখা ও সম্ভাষণ',
 'Emergency & Health': 'জরুরী অবস্থা ও স্বাস্থ্য',
 'Public Transportation': 'গণপরিবহন',
 'Work & Office': 'কাজ ও অফিস',
 'Weather & Small Talk': 'আবহাওয়া ও সাধারণ কথাবার্তা',
 'Coffee Shop & Bakery': 'কফি শপ ও বেকারি',
 'Family & Home': 'পরিবার ও বাড়ি',
 'Hobbies & Free Time': 'শখ ও অবসর',
 'Dating & Romance': 'ডেটিং ও রোমান্স',
 'Phone Calls & Messages': 'ফোন কল ও মেসেজ',
 'Banking & Money': 'ব্যাংকিং ও টাকা',
 'Doctor & Pharmacy': 'ডাক্তার ও ফার্মেসি',
 'Sports & Fitness': 'খেলাধুলা ও ফিটনেস',
 'Celebrations & Parties': 'উৎসব ও পার্টি',
 'Feelings & Emotions': 'অনুভূতি ও আবেগ',
 'Agreeing & Disagreeing': 'সম্মত হওয়া ও দ্বিমত পোষণ করা',
 'Making Plans': 'পরিকল্পনা করা',
 'Common Native Slang': 'সাধারণ স্থানীয় স্ল্যাং',
 'Cultural Traditions': 'সাংস্কৃতিক ঐতিহ্য'}
# ==== CATEGORIES END ====

CATEGORY_NAMES = list(CATEGORIES.keys())

AI_MODEL = os.getenv("AI_MODEL", "openai/gpt-5.4-nano")
AI_FALLBACK_MODEL = os.getenv("AI_FALLBACK_MODEL", "gemini-fast")
POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY", "")

# ---------------------------------------------------------------- timing (seconds)

INTRO_DURATION = 7.2
CHAPTER_INTRO_DURATION = 4.4
OUTRO_DURATION = 13.0

EN_CARD_IN = 0.70
GAP_EN_NATIVE = 0.60
NATIVE_CARD_LEAD = 0.40
GAP_BEFORE_REPEAT = 1.00
TAIL_HOLD = 1.30

# ---------------------------------------------------------------- palette

INK = "#30303A"
MUTED = "#8A8A8A"
CREAM = "#FFF8E7"
GREEN = "#58CC02"
GREEN_DARK = "#46A302"
GREEN_DEEP = "#3D8F00"
BLUE = "#1CB0F6"
PURPLE = "#7C5CFF"
ORANGE = "#FF7A00"
RED = "#FF4B4B"
YELLOW = "#F5A700"
TEAL = "#00A889"
PINK = "#E056A0"

# ==== HASHTAGS START ====
HASHTAGS = ['#learnbengali',
 '#bengalilessons',
 '#bengaliforbeginners',
 '#languagelearning',
 '#bengalivocabulary',
 '#velocitybengali',
 '#dailybengali',
 '#bengali',
 '#learnlanguages',
 '#speakbengali']
# ==== HASHTAGS END ====
