"""
YouTube Long-Form Video Automation - Bilingual English/Bengali Content Generator
GENERATES 10-MINUTE VIDEOS with improved backgrounds for YouTube
"""

import os
import sys
import json
import random
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY")

# Directories
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
IMAGES_DIR = OUTPUT_DIR / "images"
AUDIO_DIR = OUTPUT_DIR / "audio"
VIDEO_DIR = OUTPUT_DIR / "video"
HISTORY_DIR = OUTPUT_DIR / "history"
LONGFORM_DIR = OUTPUT_DIR / "longform_videos"

for d in [OUTPUT_DIR, IMAGES_DIR, AUDIO_DIR, VIDEO_DIR, HISTORY_DIR, LONGFORM_DIR]:
    d.mkdir(exist_ok=True)

# Video settings (16:9 horizontal for YouTube long-form)
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30
TARGET_DURATION_MINUTES = 5
TARGET_PHRASES = 120

# English category names
CATEGORIES_ENGLISH = [
    "Motivation", "Love", "Success", "Wisdom", "Happiness",
    "Self Improvement", "Gratitude", "Friendship", "Hope", "Creativity",
    "Inner Peace", "Confidence", "Perseverance", "Inspiration", "Positive Life",
    "Courage", "Kindness", "Patience", "Forgiveness", "Strength",
    "Joy", "Balance", "Growth", "Purpose", "Mindfulness",
]

# Bengali translations
CATEGORIES_BENGALI = {
    "Motivation": "অনুপ্রেরণা",
    "Love": "ভালোবাসা",
    "Success": "সাফল্য",
    "Wisdom": "জ্ঞান",
    "Happiness": "সুখ",
    "Self Improvement": "আত্মউন্নয়ন",
    "Gratitude": "কৃতজ্ঞতা",
    "Friendship": "বন্ধুত্ব",
    "Hope": "আশা",
    "Creativity": "সৃজনশীলতা",
    "Inner Peace": "অভ্যন্তরীণ শান্তি",
    "Confidence": "আত্মবিশ্বাস",
    "Perseverance": "অধ্যবসায়",
    "Inspiration": "অনুপ্রেরণা",
    "Positive Life": "ইতিবাচক জীবন",
    "Courage": "সাহস",
    "Kindness": "দয়া",
    "Patience": "ধৈর্য",
    "Forgiveness": "ক্ষমা",
    "Strength": "শক্তি",
    "Joy": "আনন্দ",
    "Balance": "ভারসাম্য",
    "Growth": "বৃদ্ধি",
    "Purpose": "উদ্দেশ্য",
    "Mindfulness": "সচেতনতা",
}

# Edge TTS voices
ENGLISH_VOICE = "en-US-GuyNeural"
LANG_VOICE = "bn-BD-NabanitaNeural"

# Phrase history file
PHRASE_HISTORY_FILE = HISTORY_DIR / "all_generated_phrases.json"

# Viral hook styles for engagement
VIRAL_STYLES = [
    "surprising fact",
    "common mistake correction",
    "quick tip",
    "must-know phrase",
    "local secret",
    "travel hack",
    "flirty phrase",
    "funny expression",
    "cultural insight",
    "word origin story"
]

# AI Model
AI_MODEL = os.getenv("AI_MODEL")

if not AI_MODEL:
    raise ValueError(
        "AI_MODEL not set! Please add 'AI_MODEL=gemini-fast' to your .env file."
    )


# ============== PHRASE HISTORY MANAGEMENT ==============

def load_phrase_history():
    if PHRASE_HISTORY_FILE.exists():
        with open(PHRASE_HISTORY_FILE, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    return {"phrases": [], "last_updated": None}


def save_phrase_history(data):
    data["last_updated"] = datetime.now().isoformat()
    with open(PHRASE_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def is_phrase_used(english_phrase):
    history = load_phrase_history()
    english_lower = english_phrase.lower().strip()
    for p in history.get("phrases", []):
        if p.get("english", "").lower().strip() == english_lower:
            return True
    return False


def is_phrase_similar(new_phrase, used_phrases, similarity_threshold=0.6):
    new_words = set(new_phrase.lower().split())
    if len(new_words) < 3:
        for used in used_phrases:
            if new_phrase.lower() in used.lower() or used.lower() in new_phrase.lower():
                return True
        return False
    for used in used_phrases:
        used_words = set(used.lower().split())
        if len(new_words) == 0 or len(used_words) == 0:
            continue
        intersection = len(new_words.intersection(used_words))
        union = len(new_words.union(used_words))
        similarity = intersection / union if union > 0 else 0
        if similarity >= similarity_threshold:
            return True
    return False


def filter_similar_phrases(phrases, history, similarity_threshold=0.6):
    used_phrases = [p.get("english", "") for p in history.get("phrases", [])]
    unique_phrases = []
    for phrase in phrases:
        english_text = phrase.get("english", "")
        if not is_phrase_similar(english_text, used_phrases, similarity_threshold):
            unique_phrases.append(phrase)
        else:
            print(f"[filter] Skipping similar: {english_text[:50]}...")
    return unique_phrases


def add_phrases_to_history(phrases, category):
    history = load_phrase_history()
    for phrase in phrases:
        history["phrases"].append({
            "english": phrase["english"],
            "bengali": phrase["bengali"],
            "category": category,
            "generated_at": datetime.now().isoformat()
        })
    save_phrase_history(history)
    print(f"[history] Added {len(phrases)} phrases to history (total: {len(history['phrases'])})")


# ============== CONTENT GENERATION ==============

def calculate_phrases_needed(target_minutes: int) -> int:
    avg_phrase_duration = 5.0
    total_seconds = target_minutes * 60
    return int(total_seconds / avg_phrase_duration)


def generate_phrases_for_longform(category_english: str, num_phrases: int) -> list:
    category_bengali = CATEGORIES_BENGALI[category_english]
    history = load_phrase_history()
    used_phrases = [p.get("english", "") for p in history.get("phrases", [])]
    viral_style = random.choice(VIRAL_STYLES)
    all_phrases = []
    batch_size = 20
    max_attempts = 5

    for batch_num in range((num_phrases + batch_size - 1) // batch_size):
        remaining = num_phrases - len(all_phrases)
        current_batch_size = min(batch_size, remaining)
        if current_batch_size <= 0:
            break
        for attempt in range(max_attempts):
            try:
                import requests
                url = "https://gen.pollinations.ai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {POLLINATIONS_API_KEY}",
                    "Content-Type": "application/json"
                }
                exclusion_note = ""
                if used_phrases:
                    recent = used_phrases[-30:] if len(used_phrases) > 30 else used_phrases
                    exclusion_note = f"\n\nAVOID these phrases (already used): {recent}"

                prompt = f"""Create {current_batch_size * 2} unique {category_english} phrases for English speakers learning Bengali.

Style: Make each phrase feel like a {viral_style} - something people would want to share!

CRITICAL RULE - ABSOLUTELY ZERO Bengali IN ENGLISH FIELD:
The "english" field must contain ONLY English words. NO Bengali words at all.
The "bengali" field contains the Bengali translation.
The "pronunciation" field is phonetic English spelling approximating Bengali sounds.

These are INSPIRATIONAL PHRASES about the topic, NOT language-learning tips.

WRONG (teaching tip with Bengali words): {{"english": "Don't say 'kemon acho,' it means more than 'hello.'", ...}}
WRONG (Bengali word in english): {{"english": "Use 'dhonnobad' for thank you", ...}}
WRONG (lesson tip): {{"english": "Say 'nomoskar' for greeting", ...}}
CORRECT (pure english phrase): {{"english": "Knowledge is the key to wisdom.", "bengali": "জ্ঞানই শক্তির চাবিকাঠি।", "pronunciation": "gyan-i shok-tir cha-bi-ka-thi"}}
CORRECT: {{"english": "A wise person listens more than they speak.", "bengali": "জ্ঞানী ব্যক্তি কথা বলার চেয়ে বেশি শোনেন।", "pronunciation": "gyani bek-ti ko-tha bo-lar che-ye be-shi sho-nen"}}

The english field MUST be 100% English words only. Absolutely NO Bengali words in the english field.

IMPORTANT RULES FOR NATURAL SPEECH:
1. Keep phrases SHORT (5-12 words max per language)
2. Add NATURAL PAUSES using commas (e.g., "Dream big, start small")
3. Use punctuation for breathing room in TTS
4. Avoid long run-on sentences
5. Each phrase should be speakable in 3-5 seconds
6. Use everyday vocabulary - avoid exotic or rare words
7. Avoid complex grammar - keep it simple and practical
8. Vary sentence structure for natural flow

For each phrase:
1. English phrase (pure English, zero Bengali words) with commas for natural pauses
2. Bengali translation
3. Pronunciation guide (phonetic English spelling)

Return as JSON array:
[{{"english": "...", "bengali": "...", "pronunciation": "..."}}]

IMPORTANT: Create FRESH, UNIQUE phrases that haven't been used before.{exclusion_note}"""

                payload = {
                    "model": AI_MODEL,
                    "messages": [
                        {"role": "system", "content": "You create INSPIRATIONAL PHRASES for YouTube language learning videos. CRITICAL: The 'english' field must be PURE ENGLISH with ZERO Bengali words - no Bengali words at all. These are universal inspirational phrases, NOT language learning tips. Bengali goes ONLY in the 'bengali' field."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 1.0
                }

                response = requests.post(url, headers=headers, json=payload, timeout=90)
                response.raise_for_status()

                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()

                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                phrases = json.loads(content)
                filtered_phrases = filter_similar_phrases(phrases, history)
                unique_phrases = []
                for phrase in filtered_phrases:
                    if len(phrase["english"].split()) > 15:
                        continue
                    if not is_phrase_used(phrase["english"]):
                        unique_phrases.append(phrase)
                for phrase in unique_phrases:
                    if len(all_phrases) < num_phrases:
                        all_phrases.append(phrase)
                if len(all_phrases) >= num_phrases:
                    break
            except Exception as e:
                print(f"[content] Batch {batch_num + 1}, Attempt {attempt + 1} failed: {e}")
        if len(all_phrases) < num_phrases:
            import time
            time.sleep(1)

    final_phrases = all_phrases[:num_phrases]
    if final_phrases:
        add_phrases_to_history(final_phrases, category_english)
    print(f"[content] Generated {len(final_phrases)} phrases for long-form video")
    return final_phrases


def get_fresh_fallback_phrases(category: str, num_phrases: int) -> list:
    all_fallbacks = {
        "Motivation": [
            {"english": "Believe in yourself.", "bengali": "নিজের উপর বিশ্বাস রাখো।", "pronunciation": "ni-jer u-por bi-shash ra-kho"},
            {"english": "You are capable of amazing things.", "bengali": "তুমি অসাধারণ কিছু করতে সক্ষম।", "pronunciation": "tu-mi o-sa-dha-ron ki-chu kor-te sok-khom"},
            {"english": "Dream big, start small.", "bengali": "বড় স্বপ্ন দেখো, ছোট থেকে শুরু করো।", "pronunciation": "bo-ro shop-no de-kho, chho-to the-ke shu-ru ko-ro"},
            {"english": "Your future is created by your actions.", "bengali": "তোমার ভবিষ্যৎ তোমার কাজের দ্বারা তৈরি হয়।", "pronunciation": "to-mar bho-bi-shshot to-mar ka-jer do-ra ta-ri hoy"},
            {"english": "Never give up on your dreams.", "bengali": "তোমার স্বপ্ন কখনো ছেড়ো না।", "pronunciation": "to-mar shop-no ko-kho-no chhe-ro na"},
            {"english": "Small steps lead to big changes.", "bengali": "ছোট পদক্ষেপ বড় পরিবর্তন আনে।", "pronunciation": "chho-to po-dok-khep bo-ro po-ri-bor-ton a-ne"},
            {"english": "You are stronger than you think.", "bengali": "তুমি যতটা ভাবো তার চেয়ে অনেক শক্তিশালী।", "pronunciation": "tu-mi jot-ta bha-bo tar che-ye o-nek shok-ti-sha-li"},
        ],
        "Love": [
            {"english": "Love yourself first.", "bengali": "প্রথমে নিজেকে ভালোবাসো।", "pronunciation": "pro-tho-me ni-je-ke bha-lo-ba-so"},
            {"english": "Love makes everything possible.", "bengali": "ভালোবাসা সবকিছু সম্ভব করে।", "pronunciation": "bha-lo-ba-sho kob-ki-chu shom-bhob ko-re"},
            {"english": "My heart beats for you.", "bengali": "আমার হৃদয় তোমার জন্য স্পন্দিত হয়।", "pronunciation": "a-mar hri-doy to-mar jon-no spon-di-to hoy"},
            {"english": "You are my everything.", "bengali": "তুমিই আমার সবকিছু।", "pronunciation": "tu-mi-i a-mar sob-ki-chu"},
            {"english": "Together forever, hand in hand.", "bengali": "চিরদিন একসাথে, হাতে হাতে।", "pronunciation": "chi-ro-din ek-sa-the, ha-te ha-te"},
        ],
        "Success": [
            {"english": "Success comes from hard work.", "bengali": "সাফল্য কঠোর পরিশ্রম থেকে আসে।", "pronunciation": "sa-phol-lo ko-thor po-ri-shrom the-ke a-she"},
            {"english": "Keep going, you're getting there.", "bengali": "চলতে থাকো, তুমি সেখানে পৌঁছে যাচ্ছো।", "pronunciation": "chol-te tha-ko, tu-mi she-kha-ne pou-chhe ja-chho"},
            {"english": "Winners never quit.", "bengali": "বিজয়ীরা কখনো হাল ছাড়ে না।", "pronunciation": "bi-jo-yi-ra ko-kho-no hal chha-re na"},
            {"english": "Your effort will pay off.", "bengali": "তোমার প্রচেষ্টা ফল দেবে।", "pronunciation": "to-mar pro-chesh-ta phol de-be"},
        ],
        "Wisdom": [
            {"english": "Knowledge is power.", "bengali": "জ্ঞানই শক্তি।", "pronunciation": "gyan-i shok-ti"},
            {"english": "Learn from yesterday, live for today.", "bengali": "গতকাল থেকে শেখো, আজকের জন্য বাঁচো।", "pronunciation": "go-tokal the-ke she-kho, aj-ker jon-no ba-cho"},
            {"english": "Think before you act.", "bengali": "কাজ করার আগে ভাবো।", "pronunciation": "kaj ko-rar a-ge bha-bo"},
            {"english": "Experience is the best teacher.", "bengali": "অভিজ্ঞতা সেরা শিক্ষক।", "pronunciation": "o-bhig-gota she-ra shik-shok"},
        ],
        "Happiness": [
            {"english": "Happiness is a choice.", "bengali": "সুখ একটি পছন্দ।", "pronunciation": "sukh e-ka-ta po-chon-do"},
            {"english": "Find joy in the little things.", "bengali": "ছোট জিনিসে আনন্দ খুঁজে নাও।", "pronunciation": "chho-to ji-ni-she a-non-do khun-je na-o"},
            {"english": "Smile, it makes others happy.", "bengali": "হাসো, এটি অন্যদের খুশি করে।", "pronunciation": "ha-so, e-ti on-no-der khu-shi ko-re"},
            {"english": "Today is a gift.", "bengali": "আজ একটি উপহার।", "pronunciation": "aj e-ka-ta u-pa-har"},
        ],
        "Self Improvement": [
            {"english": "Be better than yesterday.", "bengali": "গতকালের চেয়ে ভালো হও।", "pronunciation": "go-to-ka-ler che-ye bha-lo ho-o"},
            {"english": "Grow through what you go through.", "bengali": "যা কিছু অতিক্রম করো, তা দিয়ে বেড়ে ওঠো।", "pronunciation": "ja ki-chu o-ti-krom ko-ro, ta di-ye be-re o-tho"},
            {"english": "Invest in yourself daily.", "bengali": "প্রতিদিন নিজের মধ্যে বিনিয়োগ করো।", "pronunciation": "pro-ti-din ni-jer mo-dhye bi-ni-yog ko-ro"},
        ],
        "Gratitude": [
            {"english": "Thank you for everything.", "bengali": "সবকিছুর জন্য ধন্যবাদ।", "pronunciation": "sob-ki-chur jon-no dhon-no-bad"},
            {"english": "I appreciate your help.", "bengali": "আমি তোমার সাহায্যের প্রশংসা করি।", "pronunciation": "a-mi to-mar sa-haj-jer pro-shon-sa ko-ri"},
            {"english": "Grateful for this moment.", "bengali": "এই মুহূর্তটির জন্য কৃতজ্ঞ।", "pronunciation": "e-i mu-hur-to-tir jon-no kri-tog-go"},
        ],
        "Friendship": [
            {"english": "Friends forever, no matter what.", "bengali": "চিরকাল বন্ধু, যাই হোক না কেন।", "pronunciation": "chi-ro-kal bon-dhu, ja-i hok na ken"},
            {"english": "You are my best friend.", "bengali": "তুমি আমার সেরা বন্ধু।", "pronunciation": "tu-mi a-mar she-ra bon-dhu"},
            {"english": "True friends stick together.", "bengali": "সত্যিকারের বন্ধুরা একসাথে থাকে।", "pronunciation": "sot-ti-ka-rer bon-dhu-ra ek-sa-the tha-ke"},
        ],
        "Hope": [
            {"english": "There is always hope.", "bengali": "সবসময় আশা থাকে।", "pronunciation": "sob-som-oy a-sha tha-ke"},
            {"english": "Better days are coming.", "bengali": "ভালো দিন আসছে।", "pronunciation": "bha-lo din a-she-chhe"},
            {"english": "Keep faith, keep going.", "bengali": "বিশ্বাস রাখো, চলতে থাকো।", "pronunciation": "bi-shash ra-kho, chol-te tha-ko"},
        ],
        "Creativity": [
            {"english": "Create something beautiful today.", "bengali": "আজ কিছু সুন্দর সৃষ্টি করো।", "pronunciation": "aj ki-chu sun-dor shrish-ti ko-ro"},
            {"english": "Your imagination is unlimited.", "bengali": "তোমার কল্পনার কোনো সীমা নেই।", "pronunciation": "to-mar kol-po-nar ko-no si-ma nei"},
            {"english": "Art comes from the heart.", "bengali": "শিল্প হৃদয় থেকে আসে।", "pronunciation": "shil-po hri-doy the-ke a-she"},
            {"english": "Express yourself freely.", "bengali": "নিজেকে মুক্তভাবে প্রকাশ করো।", "pronunciation": "ni-je-ke muk-to-bha-be pro-kash ko-ro"},
            {"english": "Innovation starts with curiosity.", "bengali": "নবাচার শুরু হয় কৌতূহল দিয়ে।", "pronunciation": "no-ba-bar shu-ru hoy kou-tu-hol di-ye"},
        ],
        "Inner Peace": [
            {"english": "Find peace within yourself.", "bengali": "নিজের ভিতরে শান্তি খুঁজে নাও।", "pronunciation": "ni-jer bhi-to-re shan-ti khun-je na-o"},
            {"english": "Breathe, relax, let go.", "bengali": "শ্বাস নাও, আরাম করো, ছেড়ে দাও।", "pronunciation": "shash na-o, a-ram ko-ro, chhe-re da-o"},
            {"english": "Calm mind, happy heart.", "bengali": "শান্ত মন, সুখী হৃদয়।", "pronunciation": "shan-to mon, su-khi hri-doy"},
        ],
        "Confidence": [
            {"english": "You are enough, just as you are.", "bengali": "তুমি যেমন আছো, তেমনই যথেষ্ট।", "pronunciation": "tu-mi je-mon a-cho, te-mon-i jo-thesh-to"},
            {"english": "Stand tall, speak up.", "bengali": "সোজা হয়ে দাঁড়াও, জোরে কথা বলো।", "pronunciation": "so-ja ho-ye da-ra-o, jo-re ko-tha bo-lo"},
            {"english": "Believe in your abilities.", "bengali": "তোমার দক্ষতায় বিশ্বাস রাখো।", "pronunciation": "to-mar dok-kho-ta-yo bi-shash ra-kho"},
        ],
        "Perseverance": [
            {"english": "Never give up, keep pushing.", "bengali": "কখনো হাল ছেড়ো না, চেষ্টা চালিয়ে যাও।", "pronunciation": "ko-kho-no hal chhe-ro na, cheshta cha-li-ye ja-o"},
            {"english": "Storms make trees take deeper roots.", "bengali": "ঝড় গাছের শিকড়কে গভীর করে।", "pronunciation": "jhor ga-chher shi-kor-ke go-bhir ko-re"},
            {"english": "Patience and persistence win.", "bengali": "ধৈর্য ও অধ্যবসায় জয়ী হয়।", "pronunciation": "dhoir-jo o od-dho-bo-sha-yo jo-yi hoy"},
        ],
        "Inspiration": [
            {"english": "Let your light shine bright.", "bengali": "তোমার আলো উজ্জ্বলভাবে জ্বলুক।", "pronunciation": "to-mar a-lo uj-jol-bha-be jol-uk"},
            {"english": "Inspire others by your actions.", "bengali": "তোমার কাজ দিয়ে অন্যদের অনুপ্রাণিত করো।", "pronunciation": "to-mar kaj di-ye on-no-der o-nu-pra-ni-to ko-ro"},
            {"english": "Be the change you want to see.", "bengali": "তুমিই সেই পরিবর্তন হও যা তুমি দেখতে চাও।", "pronunciation": "tu-mi-i se-i po-ri-bor-ton ho-o ja tu-mi dekh-te cha-o"},
        ],
        "Positive Life": [
            {"english": "Choose positivity every day.", "bengali": "প্রতিদিন ইতিবাচকতা বেছে নাও।", "pronunciation": "pro-ti-din i-ti-bach-ko-ta be-che na-o"},
            {"english": "Good vibes only.", "bengali": "শুধু ইতিবাচক শক্তি।", "pronunciation": "shu-dhu i-ti-bach-ko shok-ti"},
            {"english": "Life is what you make it.", "bengali": "জীবন সেটাই যা তুমি তৈরি করো।", "pronunciation": "ji-bon se-tai ja tu-mi ta-ri ko-ro"},
        ],
        "Courage": [
            {"english": "Be brave, take the first step.", "bengali": "সাহসী হও, প্রথম পদক্ষেপ নাও।", "pronunciation": "sah-ho-si ho-o, pro-thom po-dok-khep na-o"},
            {"english": "Courage is not the absence of fear.", "bengali": "সাহস মানে ভয়ের অনুপস্থিতি নয়।", "pronunciation": "sah-ho-sa ma-ne bho-yer o-nu-po-sthi-ti noy"},
            {"english": "Face your fears head on.", "bengali": "তোমার ভয়ের মুখোমুখি সরাসরি হও।", "pronunciation": "to-mar bho-yer mu-kho-mu-khi so-ra-shi ho-o"},
        ],
        "Kindness": [
            {"english": "Be kind to everyone you meet.", "bengali": "যার সাথে দেখা হয় সবার সাথে দয়ালু হও।", "pronunciation": "jar sa-the de-kha hoy so-bar sa-the do-ya-lu ho-o"},
            {"english": "Kindness costs nothing, means everything.", "bengali": "দয়ার কোনো মূল্য নেই, কিন্তু অর্থ সবকিছু।", "pronunciation": "do-yar ko-no mul-lo nei, ki-n-tu ortho sob-ki-chu"},
            {"english": "Spread kindness wherever you go.", "bengali": "যেখানেই যাও, দয়া ছড়িয়ে দাও।", "pronunciation": "je-kha-ne-i ja-o, do-ya chho-ri-ye da-o"},
        ],
        "Patience": [
            {"english": "Good things take time.", "bengali": "ভালো জিনিস সময় নেয়।", "pronunciation": "bha-lo ji-nis so-moy ne-y"},
            {"english": "Wait patiently, trust the process.", "bengali": "ধৈর্য ধরে অপেক্ষা করো, প্রক্রিয়ার উপর আস্থা রাখো।", "pronunciation": "dhoir-jo dho-re o-pek-kha ko-ro, prok-ki-yar u-por a-stha ra-kho"},
            {"english": "Rome wasn't built in a day.", "bengali": "রোম একদিনে তৈরি হয়নি।", "pronunciation": "Rom ek-di-ne ta-ri hoy-ni"},
        ],
        "Forgiveness": [
            {"english": "Forgive and set yourself free.", "bengali": "ক্ষমা করো এবং নিজেকে মুক্ত করো।", "pronunciation": "kho-ma ko-ro o ebong ni-je-ke muk-to ko-ro"},
            {"english": "Let go of grudges, find peace.", "bengali": "ক্ষোভ ছেড়ে দাও, শান্তি খুঁজে নাও।", "pronunciation": "khobh chhe-re da-o, shan-ti khun-je na-o"},
            {"english": "Forgiveness is a gift to yourself.", "bengali": "ক্ষমা নিজের জন্য একটি উপহার।", "pronunciation": "kho-ma ni-jer jon-no e-ka-ta u-pa-har"},
        ],
        "Strength": [
            {"english": "You are stronger than you know.", "bengali": "তুমি যতটা জানো তার চেয়ে অনেক শক্তিশালী।", "pronunciation": "tu-mi jot-ta ja-no tar che-ye o-nek shok-ti-sha-li"},
            {"english": "Inner strength comes from within.", "bengali": "আভ্যন্তরীণ শক্তি ভেতর থেকে আসে।", "pronunciation": "ab-bon-to-rin shok-ti bhe-tor the-ke a-she"},
            {"english": "Challenges make you stronger.", "bengali": "চ্যালেঞ্জ তোমাকে শক্তিশালী করে।", "pronunciation": "chha-lenj to-ma-ke shok-ti-sha-li ko-re"},
        ],
        "Joy": [
            {"english": "Find joy in every moment.", "bengali": "প্রতিটি মুহূর্তে আনন্দ খুঁজে নাও।", "pronunciation": "pro-ti-ti mu-hur-te a-non-do khun-je na-o"},
            {"english": "Joy is contagious, spread it.", "bengali": "আনন্দ সংক্রামক, এটি ছড়িয়ে দাও।", "pronunciation": "a-non-do shong-kra-mok, e-ti chho-ri-ye da-o"},
            {"english": "Dance like nobody's watching.", "bengali": "এমনভাবে নাচো যেন কেউ দেখছে না।", "pronunciation": "e-mon-bha-be na-cho jen ke-u dekh-chhe na"},
        ],
        "Balance": [
            {"english": "Find balance in your life.", "bengali": "তোমার জীবনে ভারসাম্য খুঁজে নাও।", "pronunciation": "to-mar ji-bo-ne bha-ro-sam-mo khun-je na-o"},
            {"english": "Work hard, rest well.", "bengali": "কঠোর পরিশ্রম করো, ভালোভাবে বিশ্রাম নাও।", "pronunciation": "ko-thor po-ri-shrom ko-ro, bha-lo-bha-be bi-shram na-o"},
            {"english": "Too much of anything is not good.", "bengali": "যেকোনো কিছুর আধিক্য ভালো নয়।", "pronunciation": "je-ko-no ki-chur a-dhik-ko bha-lo noy"},
        ],
        "Growth": [
            {"english": "Growth happens outside your comfort zone.", "bengali": "বৃদ্ধি ঘটে তোমার আরামদায়ক অঞ্চলের বাইরে।", "pronunciation": "bri-dhi gho-te to-mar a-ram-do-yok on-nol-ler ba-i-re"},
            {"english": "Embrace change, grow stronger.", "bengali": "পরিবর্তনকে গ্রহণ করো, শক্তিশালী হও।", "pronunciation": "po-ri-bor-ton-ke gro-ho-non ko-ro, shok-ti-sha-li ho-o"},
            {"english": "Every challenge is a chance to grow.", "bengali": "প্রত্যেকটি চ্যালেঞ্জ বেড়ে ওঠার সুযোগ।", "pronunciation": "pro-t-tyek-ti chha-lenj be-re o-thar su-yog"},
        ],
        "Purpose": [
            {"english": "Find your purpose, follow it.", "bengali": "তোমার উদ্দেশ্য খুঁজে বের করো, তা অনুসরণ করো।", "pronunciation": "to-mar ud-des-sho khun-je be-ro ko-ro, ta o-nu-so-ron ko-ro"},
            {"english": "Your life has meaning.", "bengali": "তোমার জীবনের অর্থ আছে।", "pronunciation": "to-mar ji-bo-ner ortho a-che"},
            {"english": "Live with intention, not accident.", "bengali": "উদ্দেশ্য নিয়ে বাঁচো, দৈবক্রমে নয়।", "pronunciation": "ud-des-sho ni-ye ba-cho, doib-kro-me noy"},
        ],
        "Mindfulness": [
            {"english": "Be present in this moment.", "bengali": "এই মুহূর্তে উপস্থিত থাকো।", "pronunciation": "e-i mu-hur-te u-po-sthi-to tha-ko"},
            {"english": "Breathe deeply, stay grounded.", "bengali": "গভীর শ্বাস নাও, স্থির থাকো।", "pronunciation": "go-bhir shash na-o, sthir tha-ko"},
            {"english": "Notice the little things around you.", "bengali": "তোমার চারপাশের ছোট জিনিসগুলি লক্ষ্য করো।", "pronunciation": "to-mar char-pa-sher chho-to ji-ni-shu-guli lok-kho ko-ro"},
        ],
    }

    fallbacks = all_fallbacks.get(category, all_fallbacks["Motivation"])
    history = load_phrase_history()
    fresh_phrases = []
    for p in fallbacks:
        if not is_phrase_used(p["english"]) and not is_phrase_similar(p["english"], [h.get("english", "") for h in history.get("phrases", [])]):
            fresh_phrases.append(p)

    if len(fresh_phrases) < num_phrases:
        for cat, cat_fallbacks in all_fallbacks.items():
            if cat != category:
                for p in cat_fallbacks:
                    if not is_phrase_used(p["english"]) and not is_phrase_similar(p["english"], [h.get("english", "") for h in history.get("phrases", [])]):
                        fresh_phrases.append(p)
                    if len(fresh_phrases) >= num_phrases:
                        break
            if len(fresh_phrases) >= num_phrases:
                break

    return fresh_phrases[:num_phrases]


# ============== AUDIO GENERATION ==============

async def generate_single_audio(text: str, voice: str, output_path: str):
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
        return True
    except Exception as e:
        print(f"  TTS error: {e}")
        return False


def generate_all_audio(phrases: list, output_dir: str):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_files = []

    for i, phrase in enumerate(phrases):
        english_file = output_dir / f"english_{i}.mp3"
        lang_file = output_dir / f"lang_{i}.mp3"
        combined_file = output_dir / f"combined_{i}.mp3"

        if (i + 1) % 20 == 0:
            print(f"  Generating audio {i+1}/{len(phrases)}...")

        en_success = asyncio.run(generate_single_audio(phrase["english"], ENGLISH_VOICE, str(english_file)))
        if not en_success:
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2", str(english_file)]
            subprocess.run(cmd, capture_output=True)

        lang_success = asyncio.run(generate_single_audio(phrase["bengali"], LANG_VOICE, str(lang_file)))
        if not lang_success:
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2", str(lang_file)]
            subprocess.run(cmd, capture_output=True)

        en_duration = get_audio_duration(str(english_file))
        lang_duration = get_audio_duration(str(lang_file))

        pause_between = 0.5
        total_duration = en_duration + pause_between + lang_duration

        cmd = [
            "ffmpeg", "-y",
            "-i", str(english_file),
            "-i", str(lang_file),
            "-filter_complex", f"[0:a][1:a]concat=n=2:v=0:a=1[out]",
            "-map", "[out]",
            str(combined_file)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            concat_file = output_dir / f"concat_{i}.txt"
            with open(concat_file, "w", encoding="utf-8") as f:
                f.write(f"file '{english_file.as_posix()}'\n")
                f.write(f"file '{lang_file.as_posix()}'\n")
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0",
                "-i", str(concat_file),
                "-c:a", "aac",
                str(combined_file)
            ]
            subprocess.run(cmd, capture_output=True)
            if concat_file.exists():
                concat_file.unlink()

        actual_duration = get_audio_duration(str(combined_file))

        audio_files.append({
            "index": i,
            "english": str(english_file),
            "lang": str(lang_file),
            "combined": str(combined_file),
            "duration": actual_duration,
            "en_duration": en_duration,
            "lang_duration": lang_duration
        })

    print(f"\n[audio] Generated {len(audio_files)} phrase audios")
    return audio_files


def get_audio_duration(audio_file: str) -> float:
    if not Path(audio_file).exists():
        return 2.0
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except:
        return 2.0


def create_final_narration(audio_files: list, output_file: str):
    n = len(audio_files)
    print(f"[audio] Combining {n} audio files...")
    concat_file = Path(output_file).parent / "narration_list.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for audio_info in audio_files:
            combined_path = Path(audio_info["combined"])
            if combined_path.exists():
                path_str = str(combined_path.resolve()).replace("\\", "/").replace("'", "'\\''")
                f.write(f"file '{path_str}'\n")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c:a", "copy", str(output_file)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if concat_file.exists():
        concat_file.unlink()
    if result.returncode == 0 and Path(output_file).exists() and Path(output_file).stat().st_size > 0:
        size = Path(output_file).stat().st_size
        print(f"\n[audio] Final narration: {Path(output_file).name} ({size/1024:.1f} KB)")
        return True
    return False


# ============== BACKGROUND GENERATION ==============

def create_premium_background(category_english: str):
    from PIL import Image, ImageDraw
    img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT))
    draw = ImageDraw.Draw(img)
    for y in range(VIDEO_HEIGHT):
        ratio = y / VIDEO_HEIGHT
        if ratio < 0.5:
            r, g, b = 255, 252, 245
        else:
            r = int(255 + (245 - 255) * ((ratio - 0.5) * 2))
            g = int(252 + (240 - 252) * ((ratio - 0.5) * 2))
            b = int(245 + (230 - 245) * ((ratio - 0.5) * 2))
        draw.rectangle([(0, y), (VIDEO_WIDTH, y + 1)], fill=(r, g, b))
    return img


def generate_complete_image(phrase_data: dict, category_english: str, output_path: str):
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter
    except ImportError:
        print("PIL not available. Install: pip install Pillow")
        return None

    img = create_premium_background(category_english)
    img = img.convert('RGBA')
    draw = ImageDraw.Draw(img)

    # Font paths - check fonts/ directory first
    english_font_paths = [
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]

    lang_font_paths = [
        str(BASE_DIR / "fonts" / "NotoSansBengali-Bold.ttf"),
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]

    def load_font(font_paths, size):
        for font_path in font_paths:
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue
        return ImageFont.load_default()

    font_category = load_font(english_font_paths, 42)
    font_english = load_font(english_font_paths, 68)
    font_lang = load_font(lang_font_paths, 82)
    font_pronunciation = load_font(lang_font_paths, 48)
    font_branding = load_font(english_font_paths, 38)

    english = phrase_data.get("english", "")
    bengali = phrase_data.get("bengali", "")
    pronunciation = phrase_data.get("pronunciation", "")

    def wrap_text(text, font, max_width):
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
            else:
                if current_line: lines.append(' '.join(current_line))
                current_line = [word]
        if current_line: lines.append(' '.join(current_line))
        return lines

    # Header Bar
    cat_text = category_english.upper()
    cat_bbox = draw.textbbox((0, 0), cat_text, font=font_category)
    cat_w = cat_bbox[2] - cat_bbox[0]
    badge_h = 75
    badge_pad_x = 40
    container_w = cat_w + (badge_pad_x * 2)
    container_x = 60
    container_y = 60
    draw.rounded_rectangle(
        [(container_x, container_y), (container_x + container_w, container_y + badge_h)],
        radius=15, fill=(45, 35, 65, 255)
    )
    draw.text(
        (container_x + container_w // 2, container_y + badge_h // 2 + 2),
        cat_text,
        fill=(255, 255, 255, 255),
        font=font_category,
        anchor="mm"
    )

    CONTENT_Y_CENTER = VIDEO_HEIGHT // 2
    GAP = 60

    en_lines = wrap_text(english, font_english, VIDEO_WIDTH - 300)
    en_line_h = 80
    en_total_h = len(en_lines) * en_line_h

    lang_lines = wrap_text(bengali, font_lang, VIDEO_WIDTH - 300)
    lang_line_h = 100
    lang_total_h = len(lang_lines) * lang_line_h

    pron_text = f"[{pronunciation}]"
    pron_lines = wrap_text(pron_text, font_pronunciation, VIDEO_WIDTH - 400)
    pron_line_h = 60
    pron_total_h = len(pron_lines) * pron_line_h

    total_content_h = en_total_h + lang_total_h + pron_total_h + (GAP * 2)
    y_start = CONTENT_Y_CENTER - (total_content_h // 2)

    box_w = VIDEO_WIDTH - 200
    box_x = (VIDEO_WIDTH - box_w) // 2

    # English Box
    en_box_h = en_total_h + 60
    draw.rounded_rectangle(
        [(box_x, y_start), (box_x + box_w, y_start + en_box_h)],
        radius=25, fill=(65, 50, 95, 255)
    )
    for i, line in enumerate(en_lines):
        draw.text((VIDEO_WIDTH // 2, y_start + 30 + (i * en_line_h) + en_line_h // 2),
                  line, fill=(255, 255, 255), font=font_english, anchor="mm")

    y_cursor = y_start + en_box_h + GAP

    # Bengali Section
    lang_box_h = lang_total_h + 60
    draw.rounded_rectangle(
        [(box_x, y_cursor), (box_x + box_w, y_cursor + lang_box_h)],
        radius=25, fill=(95, 80, 125, 255)
    )
    for i, line in enumerate(lang_lines):
        draw.text((VIDEO_WIDTH // 2, y_cursor + 30 + (i * lang_line_h) + lang_line_h // 2),
                  line, fill=(255, 255, 255), font=font_lang, anchor="mm")

    y_cursor += lang_box_h + (GAP // 2)

    # Pronunciation Section
    pron_box_h = pron_total_h + 40
    pron_box_w = box_w - 200
    pron_box_x = (VIDEO_WIDTH - pron_box_w) // 2
    draw.rounded_rectangle(
        [(pron_box_x, y_cursor), (pron_box_x + pron_box_w, y_cursor + pron_box_h)],
        radius=20, fill=(255, 210, 160, 255)
    )
    for i, line in enumerate(pron_lines):
        draw.text((VIDEO_WIDTH // 2, y_cursor + 20 + (i * pron_line_h) + pron_line_h // 2),
                  line, fill=(70, 45, 25), font=font_pronunciation, anchor="mm")

    # Branding
    brand_text = "VELOCITY BENGALI"
    brand_bbox = draw.textbbox((0, 0), brand_text, font=font_branding)
    brand_w = brand_bbox[2] - brand_bbox[0]
    draw.text((VIDEO_WIDTH - brand_w - 60, VIDEO_HEIGHT - 80), brand_text,
              fill=(45, 35, 65, 255), font=font_branding)

    img = img.convert('RGB')
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=95, optimize=True)
    return output_path


# ============== THUMBNAIL GENERATION ==============

def generate_thumbnail(category_english: str, category_bengali: str, output_path: str):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("PIL not available for thumbnail. Install: pip install Pillow")
        return None

    img = create_premium_background(category_english)
    img = img.convert('RGBA')
    draw = ImageDraw.Draw(img)

    english_font_paths = [
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ]
    lang_font_paths = [
        str(BASE_DIR / "fonts" / "NotoSansBengali-Bold.ttf"),
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/arialbd.ttf",
    ]

    def load_font(font_paths, size):
        for font_path in font_paths:
            try: return ImageFont.truetype(font_path, size)
            except: continue
        return ImageFont.load_default()

    font_huge = load_font(english_font_paths, 130)
    font_main = load_font(lang_font_paths, 110)
    font_sub = load_font(english_font_paths, 60)
    font_badge = load_font(english_font_paths, 45)

    draw.text((VIDEO_WIDTH // 2, 220), "MASTER BENGALI", fill=(45, 35, 65), font=font_huge, anchor="mm")

    cat_text = category_english.upper()
    cat_bbox = draw.textbbox((0, 0), cat_text, font=font_sub)
    cat_w = cat_bbox[2] - cat_bbox[0]
    draw.rounded_rectangle(
        [(VIDEO_WIDTH // 2 - cat_w // 2 - 40, 320), (VIDEO_WIDTH // 2 + cat_w // 2 + 40, 410)],
        radius=20, fill=(65, 50, 95, 255)
    )
    draw.text((VIDEO_WIDTH // 2, 365), cat_text, fill=(255, 255, 255), font=font_sub, anchor="mm")

    draw.text((VIDEO_WIDTH // 2, 530), category_bengali, fill=(45, 35, 65), font=font_main, anchor="mm")

    cta_text = "60 BENGALI PHRASES"
    draw.rounded_rectangle(
        [(VIDEO_WIDTH // 2 - 300, 650), (VIDEO_WIDTH // 2 + 300, 730)],
        radius=15, fill=(255, 210, 160, 255)
    )
    draw.text((VIDEO_WIDTH // 2, 690), cta_text, fill=(70, 45, 25), font=font_badge, anchor="mm")

    draw.rectangle([(0, VIDEO_HEIGHT - 100), (VIDEO_WIDTH, VIDEO_HEIGHT)], fill=(45, 35, 65, 255))
    draw.text((VIDEO_WIDTH // 2, VIDEO_HEIGHT - 50), "VELOCITY BENGALI", fill=(255, 255, 255), font=font_badge, anchor="mm")

    img = img.convert('RGB')
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=95, optimize=True)
    return output_path


def extract_video_thumbnail(video_path: str, output_path: str, timestamp_seconds: int = 5):
    try:
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(timestamp_seconds),
            "-i", str(video_path),
            "-vframes", "1",
            "-q:v", "2",
            str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and Path(output_path).exists():
            print(f"  Video thumbnail extracted: {Path(output_path).name}")
            return str(output_path)
        else:
            print(f"  Could not extract video thumbnail")
            return None
    except Exception as e:
        print(f"  Thumbnail extraction error: {e}")
        return None


# ============== TITLE & DESCRIPTION GENERATION ==============

def generate_title_description(category_english: str, category_bengali: str, phrases: list, duration_minutes: float, output_dir: str):
    titles = [
        f"Learn Bengali in 10 Minutes | {category_english} Phrases Every Beginner NEEDS to Know! ({category_bengali})",
        f"60 Bengali Phrases for {category_english} | Speak Bengali Like a Native! ({category_bengali})",
        f"Master Bengali {category_english} | 60 Essential Bengali Phrases with Pronunciation | Velocity Bengali",
        f"Bengali Learning Made Easy | {category_english} Vocabulary | 10 Minute Lesson",
        f"Speak Bengali Fluently | {category_english} Phrases | English + Bengali + Pronunciation",
    ]

    description = f"""\U0001F1E7\U0001F1E9 Learn Bengali with Velocity Bengali! \U0001F1E7\U0001F1E9

In this video, you'll learn 60 essential Bengali phrases about {category_english} ({category_bengali}).
Perfect for beginners and intermediate learners!

\U0001F4DA WHAT YOU'LL LEARN:
\u2022 Practical {category_english} phrases in Bengali
\u2022 Correct pronunciation guide
\u2022 Natural pauses for speaking practice
\u2022 Common expressions used by native speakers

\U0001F551 VIDEO TIMESTAMPS:
"""

    avg_phrase_duration = duration_minutes * 60 / len(phrases)
    for i in range(0, len(phrases), 10):
        timestamp = int(i * avg_phrase_duration / 60)
        minute = timestamp
        second = int((i * avg_phrase_duration) % 60)
        end_phrase = min(i + 10, len(phrases))
        description += f"{minute:02d}:{second:02d} Phrases {i+1}-{end_phrase}\n"

    description += """
\U0001F4DD ALL PHRASES IN THIS VIDEO:
"""

    for i, phrase in enumerate(phrases, 1):
        description += f"""
{i}. {phrase['english']}
   Bengali: {phrase['bengali']}
    Pronunciation: {phrase['pronunciation']}
"""

    description += """
\U0001F3AF PERFECT FOR:
\u2022 Bengali beginners wanting to expand vocabulary
\u2022 Intermediate learners practicing pronunciation
\u2022 Anyone interested in Bengali language and culture
\u2022 Language enthusiasts and polyglots
\u2022 Students preparing for exams

\U0001F4A1 TIPS FOR LEARNING:
1. Repeat each phrase out loud
2. Practice daily for best results
3. Use the pauses to speak along
4. Write down phrases you find difficult
5. Review this video multiple times

\U0001F514 SUBSCRIBE for more Bengali learning content!
\U0001F44D LIKE this video if you found it helpful!
\U0001F4AC COMMENT which phrases you want to learn next!

\U0001F4F1 FOLLOW VELOCITY BENGALI:
[Add your social media links here]

\U0001F3B5 MUSIC:
[Add music credits if applicable]

\U0001F4D6 RELATED VIDEOS:
\u2022 Bengali Motivation Phrases
\u2022 Bengali Love Expressions
\u2022 Basic Bengali Greetings

#LearnBengali #BengaliPhrases #BengaliLanguage #{category_english.replace(' ', '')} #VelocityBengali #BengaliForBeginners #SpeakBengali #BengaliVocabulary #Pronunciation #LanguageLearning #Bengali101 #BengaliLesson

---
\u00A9 Velocity Bengali - Making Bengali learning accessible to everyone!
"""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_dir / "youtube_upload_info.txt", "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("YOUTUBE VIDEO UPLOAD INFORMATION\n")
        f.write("=" * 80 + "\n\n")
        f.write("RECOMMENDED TITLES (Choose one):\n")
        f.write("-" * 80 + "\n")
        for i, title in enumerate(titles, 1):
            f.write(f"\n{i}. {title}\n")
        f.write("\n" + "=" * 80 + "\n")
        f.write("SELECTED TITLE (Recommended):\n")
        f.write("-" * 80 + "\n")
        f.write(f"\n{titles[0]}\n")
        f.write("\n" + "=" * 80 + "\n")
        f.write("VIDEO DESCRIPTION:\n")
        f.write("-" * 80 + "\n\n")
        f.write(description)
        f.write("\n" + "=" * 80 + "\n")
        f.write("VIDEO TAGS (for YouTube):\n")
        f.write("-" * 80 + "\n")
        tags = [
            "Learn Bengali",
            "Bengali Phrases",
            "Bengali Language",
            category_english,
            "Velocity Bengali",
            "Bengali for Beginners",
            "Speak Bengali",
            "Bengali Vocabulary",
            "Pronunciation",
            "Language Learning",
            "Bengali 101",
            "Bengali Lesson"
        ]
        f.write(", ".join(tags) + "\n")

    metadata = {
        "recommended_titles": titles,
        "selected_title": titles[0],
        "description": description,
        "category_english": category_english,
        "category_bengali": category_bengali,
        "phrases_count": len(phrases),
        "duration_minutes": round(duration_minutes, 2),
        "tags": tags
    }

    with open(output_dir / "video_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"\n[metadata] Generated YouTube upload files")
    print(f"  youtube_upload_info.txt (title + description + tags)")
    print(f"  video_metadata.json")

    return metadata


# ============== VIDEO CREATION ==============

def create_video_from_images_audio(image_files: list, audio_files: list, combined_audio: str, output_file: str):
    print(f"\n[video] Creating long-form video from {len(image_files)} images...")

    temp_clips = []

    for i, (img_path, audio_info) in enumerate(zip(image_files, audio_files)):
        duration = audio_info['duration']
        print(f"  Image {i+1}/{len(image_files)}: {duration:.2f}s")

        temp_clip = Path(output_file).parent / f"temp_clip_{i:02d}.mp4"
        temp_clips.append(temp_clip)

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(img_path),
            "-i", audio_info['combined'],
            "-vf", f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2,fps={FPS}",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-b:a", "128k",
            "-pix_fmt", "yuv420p",
            "-preset", "medium",
            "-shortest",
            "-vsync", "cfr",
            str(temp_clip)
        ]

        subprocess.run(cmd, check=True, capture_output=True)

    print("[video] Concatenating clips...")
    concat_file = Path(output_file).parent / "concat_list.txt"

    with open(concat_file, "w", encoding="utf-8") as f:
        for clip in temp_clips:
            f.write(f"file '{clip.resolve().as_posix()}'\n")

    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(output_file)]
    subprocess.run(cmd, check=True, capture_output=True)

    if concat_file.exists():
        concat_file.unlink()

    video_duration = get_audio_duration(str(output_file))
    print(f"[video] Video created: {Path(output_file).name} ({video_duration:.2f}s)")

    for clip in temp_clips:
        if clip.exists():
            clip.unlink()


# ============== MAIN WORKFLOW ==============

def generate_longform_video(category_english: str = None, target_phrases: int = None):
    if not category_english:
        category_english = random.choice(CATEGORIES_ENGLISH)

    phrases_count = target_phrases if target_phrases else TARGET_PHRASES

    print(f"\n{'='*80}")
    print(f"LONG-FORM VIDEO - Category: {category_english} ({CATEGORIES_BENGALI[category_english]})")
    print(f"Target Phrases: {phrases_count}")
    print(f"{'='*80}\n")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_dir = LONGFORM_DIR / f"{category_english}_longform_{timestamp}"
    video_dir.mkdir(exist_ok=True)

    print(f"[1/6] Generating {phrases_count} unique phrases (checking history)...")
    phrases = generate_phrases_for_longform(category_english, phrases_count)

    for i, phrase in enumerate(phrases, 1):
        print(f"  {i}. {phrase['english']} -> {phrase['bengali']}")

    print(f"\n[info] Total phrases: {len(phrases)}")

    print(f"\n[2/6] Generating {len(phrases)} images with premium backgrounds...")
    for i, phrase in enumerate(phrases):
        output_path = video_dir / f"phrase_{i:04d}.jpg"
        generate_complete_image(phrase, category_english, str(output_path))
        if (i + 1) % 10 == 0:
            print(f"  Progress: {i+1}/{len(phrases)} images...")

    print(f"\n[3/6] Generating thumbnail...")
    thumbnail_path = video_dir / "thumbnail.jpg"
    try:
        from generate_thumbnail import generate_scenic_image
        result = generate_scenic_image(category_english, category_english, str(thumbnail_path))
        if result and Path(result).exists():
            print(f"  gpt-image-2 thumbnail saved")
        else:
            print(f"  gpt-image-2 failed, using built-in")
            generate_thumbnail(category_english, CATEGORIES_BENGALI[category_english], str(thumbnail_path))
    except Exception as e:
        print(f"  Thumbnail error: {e}, using built-in")
        generate_thumbnail(category_english, CATEGORIES_BENGALI[category_english], str(thumbnail_path))

    video_thumbnail_path = video_dir / "video_thumbnail_frame.jpg"

    print(f"\n[4/6] Generating audio for {len(phrases)} phrases...")
    audio_files = generate_all_audio(phrases, str(video_dir))

    final_audio = video_dir / "narration.mp3"
    create_final_narration(audio_files, str(final_audio))

    total_duration = sum(a['duration'] for a in audio_files)
    print(f"\n[info] Total audio duration: {total_duration:.2f}s ({total_duration/60:.2f} minutes)")

    print(f"\n[5/6] Creating long-form video with transitions...")
    output_video = video_dir / "final_video.mp4"

    image_files = sorted([str(p) for p in video_dir.glob("phrase_*.jpg")])

    create_video_from_images_audio(
        image_files,
        audio_files,
        str(final_audio),
        str(output_video)
    )

    print(f"\n[5.5/6] Extracting video frame for thumbnail...")
    extract_video_thumbnail(str(output_video), str(video_thumbnail_path), timestamp_seconds=5)

    print(f"\n[6/6] Generating YouTube title, description, and metadata...")
    title_meta = generate_title_description(
        category_english,
        CATEGORIES_BENGALI[category_english],
        phrases,
        total_duration / 60,
        str(video_dir)
    )

    import json as _json
    from pathlib import Path as _Path
    meta_out = {
        "title": title_meta.get("selected_title", f"Learn Bengali: {category_english}"),
        "description": title_meta.get("description", ""),
        "tags": ["Learn Bengali", "Bengali Phrases", "Bengali", category_english, "Velocity Bengali"],
        "category_english": category_english,
        "category_bengali": CATEGORIES_BENGALI[category_english],
        "phrases_count": len(phrases),
        "duration_seconds": total_duration,
        "duration_minutes": total_duration / 60,
        "video_path": str(output_video),
        "thumbnail_path": str(thumbnail_path),
        "phrases": phrases,
        "generated_at": datetime.now().isoformat(),
    }
    _Path("output").mkdir(exist_ok=True)
    with open(_Path("output") / "latest_video.json", "w", encoding="utf-8") as f:
        _json.dump(meta_out, f, indent=2, ensure_ascii=False)
    with open(_Path("output") / "latest_upload_info.json", "w", encoding="utf-8") as f:
        _json.dump({"title": meta_out["title"], "description": meta_out["description"],
                     "category": category_english, "phrases_count": len(phrases)}, f, indent=2)

    print(f"\n{'='*80}")
    print(f"LONG-FORM VIDEO COMPLETE!")
    print(f"  {video_dir}")
    print(f"  {output_video.name}")
    print(f"  thumbnail.jpg (generated)")
    print(f"  {video_thumbnail_path.name} (from video)")
    print(f"  youtube_upload_info.txt (title + description + tags)")
    print(f"  Duration: {total_duration/60:.2f} minutes")
    print(f"  Phrases: {len(phrases)}")
    print(f"  Branding: Velocity Bengali")
    print(f"  Format: 16:9 (1920x1080)")
    print(f"{'='*80}\n")

    return meta_out


def generate_multiple_longform(count: int = 1, target_phrases: int = None):
    print(f"\nGenerating {count} long-form video(s)...")
    print("="*80)
    for i in range(count):
        print(f"\n{'='*80}")
        print(f"VIDEO {i+1}/{count}")
        print("="*80)
        generate_longform_video(target_phrases=target_phrases)
    print("\n" + "="*80)
    print(f"ALL {count} LONG-FORM VIDEOS COMPLETE!")
    print("="*80)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Velocity Bengali YouTube Long-form Video Generator")
    parser.add_argument("--phrases", type=int, default=TARGET_PHRASES, help="Number of phrases to generate")
    parser.add_argument("--category", type=str, default=None, help="Specific category to generate")
    args = parser.parse_args()

    print("\n" + "="*80)
    print("VELOCITY BENGALI - YOUTUBE LONG-FORM AUTOMATION")
    print("="*80)
    print("\nFEATURES:")
    print("  16:9 format (1920x1080) for YouTube long-form")
    print(f"  Target {args.phrases} phrases (~{args.phrases * 5.5 / 60:.1f} minute video)")
    print("  Light Theme (Cream background, dark/light purple + peach containers)")
    print("  Natural pauses with commas (non-robotic TTS)")
    print("  Perfect audio-video synchronization")
    print("  NEVER repeats phrases (permanent history tracking)")
    print(f"\nAVAILABLE CATEGORIES ({len(CATEGORIES_ENGLISH)} total):")
    for i, cat in enumerate(CATEGORIES_ENGLISH, 1):
        print(f"   {i:2d}. {cat} ({CATEGORIES_BENGALI[cat]})")
    print(f"\nVIDEO SPECIFICATIONS:")
    print(f"  Resolution: {VIDEO_WIDTH}x{VIDEO_HEIGHT} (16:9)")
    print(f"  Frame Rate: {FPS} FPS")
    print(f"  Target Phrases: {args.phrases}")
    print(f"  Estimated Duration: ~{args.phrases * 5.5 / 60:.1f} minutes")
    print(f"  Phrase History: PERMANENT (never deletes)")
    print("="*80)

    generate_longform_video(category_english=args.category, target_phrases=args.phrases)
