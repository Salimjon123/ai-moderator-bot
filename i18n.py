"""
Переводы бота: қазақша (kk), русский (ru), English (en).

Использование:  t("reg_done", lang)   или   t("welcome_back", lang, name="Али")
Чтобы поменять текст — правь его здесь.
"""

from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           KeyboardButton, ReplyKeyboardMarkup)

LANGS = ("kk", "ru", "en")
DEFAULT_LANG = "ru"

T = {
    # ---------- Выбор языка ----------
    "lang_choose": {
        "kk": "🌐 Тілді таңдаңыз / Выберите язык / Choose a language",
        "ru": "🌐 Тілді таңдаңыз / Выберите язык / Choose a language",
        "en": "🌐 Тілді таңдаңыз / Выберите язык / Choose a language",
    },
    "lang_set": {"kk": "✅ Тіл: Қазақша", "ru": "✅ Язык: Русский", "en": "✅ Language: English"},

    # ---------- Приветствие ----------
    "welcome": {
        "kk": ("Сәлеметсіз бе, Таза Контент ботына қош келдіңіз\n\n"
               "@taza_content_bot арқылы мыналарды тексере аласыз:\n\n"
               "•Мәтін - балағат, қорлау, қорқыту;\n"
               "•Дауыстық хабар, аудио - сөйлеу мәтінге айналады;\n"
               "•Видео, фото - 18+, төбелес, қару;\n"
               "•YouTube - video, shorts;\n"
               "•TikTok - video;\n"
               "•Instagram - reels, video;\n"
               "•Сілтемелер - фишинг, казино, алаяқтық\n\n"
               "Тексеруді бастау үшін мәтін, файл немесе сілтеме жіберіңіз"),
        "ru": ("Здравствуйте, добро пожаловать в бот Таза Контент\n\n"
               "Через @taza_content_bot можно проверить:\n\n"
               "•Текст - мат, оскорбления, угрозы;\n"
               "•Голосовые, аудио - речь превращается в текст;\n"
               "•Видео, фото - 18+, драки, оружие;\n"
               "•YouTube - video, shorts;\n"
               "•TikTok - video;\n"
               "•Instagram - reels, video;\n"
               "•Ссылки - фишинг, казино, мошенничество\n\n"
               "Чтобы начать проверку, отправьте текст, файл или ссылку"),
        "en": ("Hello, welcome to the Taza Content bot\n\n"
               "With @taza_content_bot you can check:\n\n"
               "•Text - swearing, insults, threats;\n"
               "•Voice messages, audio - speech is turned into text;\n"
               "•Video, photo - 18+, fights, weapons;\n"
               "•YouTube - video, shorts;\n"
               "•TikTok - video;\n"
               "•Instagram - reels, video;\n"
               "•Links - phishing, casino, scams\n\n"
               "To start, send a text, a file or a link"),
    },
    "short_description": {
        "kk": "Мәтін, аудио, видео мен сілтемелерді қауіпсіздікке тексеретін бот",
        "ru": "Бот проверяет текст, аудио, видео и ссылки на опасный контент",
        "en": "A bot that checks text, audio, video and links for harmful content",
    },
    "welcome_back": {
        "kk": "Қайта келгеніңізге қуаныштымыз, {name}! Тексеру үшін мәтін, файл немесе сілтеме жіберіңіз.",
        "ru": "С возвращением, {name}! Отправь текст, файл или ссылку — я проверю.",
        "en": "Welcome back, {name}! Send a text, a file or a link to check.",
    },

    # ---------- Регистрация ----------
    "reg_step1": {
        "kk": "Алдымен тіркелейік.\n\n<b>1/4-қадам.</b> Атыңыз кім?",
        "ru": "Сначала зарегистрируйся.\n\n<b>Шаг 1 из 4.</b> Как тебя зовут?",
        "en": "First, let's register.\n\n<b>Step 1 of 4.</b> What's your name?",
    },
    "reg_step2": {
        "kk": ("Танысқаныма қуаныштымын, {name}!\n\n"
               "<b>2/4-қадам.</b> Құпиясөз ойлап табыңыз.\n\n"
               "Талаптар:\n"
               "• кемінде {min} таңба\n"
               "• кемінде бір сан\n"
               "• кемінде бір бас және бір кіші ағылшын әрпі\n"
               "• кирилл әріптерісіз және бос орынсыз\n\n"
               "Мысал: <code>Salem2026!</code> (өзіңіздікін ойлап табыңыз)\n"
               "🔒 Құпиясөз жазылған хабарламаны бірден өшіремін."),
        "ru": ("Приятно познакомиться, {name}!\n\n"
               "<b>Шаг 2 из 4.</b> Придумай пароль.\n\n"
               "Требования:\n"
               "• не меньше {min} символов\n"
               "• хотя бы одна цифра\n"
               "• хотя бы одна заглавная и одна строчная английская буква\n"
               "• без русских/казахских букв и пробелов\n\n"
               "Пример: <code>Salem2026!</code> (придумай свой)\n"
               "🔒 Сообщение с паролем я сразу удалю из чата."),
        "en": ("Nice to meet you, {name}!\n\n"
               "<b>Step 2 of 4.</b> Create a password.\n\n"
               "Requirements:\n"
               "• at least {min} characters\n"
               "• at least one digit\n"
               "• at least one uppercase and one lowercase English letter\n"
               "• no Cyrillic letters or spaces\n\n"
               "Example: <code>Salem2026!</code> (make up your own)\n"
               "🔒 I'll delete the message with your password right away."),
    },
    "pw_ok": {
        "kk": "✅ Сенімді құпиясөз!\n\n<b>3/4-қадам.</b> Құпиясөзді қайта енгізіңіз:",
        "ru": "✅ Надёжный пароль!\n\n<b>Шаг 3 из 4.</b> Введи пароль ещё раз:",
        "en": "✅ Strong password!\n\n<b>Step 3 of 4.</b> Enter the password again:",
    },
    "pw_mismatch": {
        "kk": "❌ Құпиясөздер сәйкес келмейді.\n\nҚұпиясөзді қайта ойлап табыңыз (2/4-қадам):",
        "ru": "❌ Пароли не совпадают.\n\nПридумай пароль заново (шаг 2 из 4):",
        "en": "❌ The passwords don't match.\n\nCreate the password again (step 2 of 4):",
    },
    "pw_match": {
        "kk": "✅ Құпиясөздер сәйкес!\n\n<b>4/4-қадам.</b> Телефон нөміріңізді жіберу үшін төмендегі батырманы басыңыз.",
        "ru": "✅ Пароли совпадают!\n\n<b>Шаг 4 из 4.</b> Нажми кнопку ниже, чтобы отправить номер телефона.",
        "en": "✅ The passwords match!\n\n<b>Step 4 of 4.</b> Tap the button below to send your phone number.",
    },
    "btn_phone": {"kk": "📱 Нөмірді жіберу", "ru": "📱 Отправить номер", "en": "📱 Send number"},
    "own_phone": {
        "kk": "Өз нөміріңізді батырма арқылы жіберіңіз.",
        "ru": "Отправь, пожалуйста, свой номер через кнопку.",
        "en": "Please send your own number using the button.",
    },
    "press_phone": {
        "kk": "«📱 Нөмірді жіберу» батырмасын басыңыз.",
        "ru": "Нажми кнопку «📱 Отправить номер».",
        "en": "Tap the «📱 Send number» button.",
    },
    "need_text": {"kk": "Мәтінмен жіберіңіз.", "ru": "Отправь, пожалуйста, текстом.",
                  "en": "Please send it as text."},
    "reg_done": {
        "kk": ("🎉 Тіркелу аяқталды!\n\nЕнді маған жіберіңіз:\n"
               "• мәтін немесе пікірлер (әрқайсысы жаңа жолдан)\n"
               "• видео немесе дөңгелек видео\n"
               "• аудио немесе дауыстық хабар\n"
               "• YouTube, TikTok, Instagram сілтемесі\n\n"
               "Мен оларды буллингке, балағатқа, қорқытуға және заңсыз контентке тексеремін."),
        "ru": ("🎉 Регистрация завершена!\n\nТеперь отправь мне:\n"
               "• текст или комментарии (каждый с новой строки)\n"
               "• видео или кружок\n"
               "• аудио или голосовое\n"
               "• ссылку на YouTube, TikTok, Instagram\n\n"
               "Я проверю их на буллинг, мат, угрозы и нелегал."),
        "en": ("🎉 Registration complete!\n\nNow send me:\n"
               "• a text or comments (each on a new line)\n"
               "• a video or a video message\n"
               "• audio or a voice message\n"
               "• a YouTube, TikTok or Instagram link\n\n"
               "I'll check them for bullying, swearing, threats and illegal content."),
    },

    # ---------- Пароль: правила ----------
    "pw_bad": {"kk": "❌ <b>Құпиясөз жарамайды.</b> Талаптар:\n",
               "ru": "❌ <b>Пароль не подходит.</b> Требования:\n",
               "en": "❌ <b>This password doesn't work.</b> Requirements:\n"},
    "r_len": {"kk": "Кемінде {min} таңба (қазір {n})", "ru": "Не меньше {min} символов (сейчас {n})",
              "en": "At least {min} characters (now {n})"},
    "r_digit": {"kk": "Кемінде бір сан (0-9)", "ru": "Хотя бы одна цифра (0-9)",
                "en": "At least one digit (0-9)"},
    "r_upper": {"kk": "Кемінде бір бас әріп (A-Z)", "ru": "Хотя бы одна заглавная буква (A-Z)",
                "en": "At least one uppercase letter (A-Z)"},
    "r_lower": {"kk": "Кемінде бір кіші әріп (a-z)", "ru": "Хотя бы одна строчная буква (a-z)",
                "en": "At least one lowercase letter (a-z)"},
    "r_chars": {"kk": "Тек ағылшын әріптері, сандар мен таңбалар — кирилл және бос орынсыз",
                "ru": "Только английские буквы, цифры и символы — без русских букв и пробелов",
                "en": "Only English letters, digits and symbols — no Cyrillic or spaces"},
    "r_common": {"kk": "Тым қарапайым емес (12345678, password, qwerty123 емес)",
                 "ru": "Не слишком простой пароль (не 12345678, password, qwerty123)",
                 "en": "Not too simple (not 12345678, password, qwerty123)"},
    "r_name": {"kk": "Атыңыз кірмеуі керек", "ru": "Не содержит твоё имя",
               "en": "Doesn't contain your name"},
    "pw_example": {
        "kk": "\nСенімді құпиясөз мысалы: <code>Salem2026!</code>\nӨзіңіздікін ойлап, қайта енгізіңіз:",
        "ru": "\nПример надёжного пароля: <code>Salem2026!</code>\nПридумай свой и введи ещё раз:",
        "en": "\nExample of a strong password: <code>Salem2026!</code>\nMake up your own and enter it again:",
    },

    # ---------- Проверка: сообщения ----------
    "wait_link": {"kk": "⏳ Видеоны сілтеме бойынша жүктеп, талдап жатырмын...\nБұл 1–3 минутқа созылуы мүмкін.",
                  "ru": "⏳ Скачиваю видео по ссылке и анализирую...\nЭто может занять 1–3 минуты.",
                  "en": "⏳ Downloading the video from the link and analyzing...\nThis can take 1–3 minutes."},
    "wait_text": {"kk": "⏳ Талдап жатырмын...", "ru": "⏳ Анализирую...", "en": "⏳ Analyzing..."},
    "wait_file": {"kk": "⏳ Файлды алдым. Сақтап, талдап жатырмын...\nВидео 30 секундтан 2 минутқа дейін тексеріледі.",
                  "ru": "⏳ Получил файл. Сохраняю и анализирую...\nВидео проверяется 30 секунд – 2 минуты.",
                  "en": "⏳ Got the file. Saving and analyzing...\nA video takes 30 seconds to 2 minutes."},
    "lang_unsupported": {
        "kk": "🌐 Бот тек қазақ, орыс және ағылшын тілдерін қабылдайды.",
        "ru": "🌐 Бот принимает только казахский, русский и английский.",
        "en": "🌐 The bot accepts only Kazakh, Russian and English.",
    },
    "error": {"kk": "❌ Қате: {e}", "ru": "❌ Ошибка: {e}", "en": "❌ Error: {e}"},
    "link_error": {"kk": "❌ Сілтемедегі видеоны тексеру мүмкін болмады: {e}",
                   "ru": "❌ Не удалось проверить видео по ссылке: {e}",
                   "en": "❌ Couldn't check the video from the link: {e}"},
    "dl_ask_danger": {"kk": "⚠️ Видео қауіпті. Бәрібір жүктеп алғыңыз келе ме?",
                      "ru": "⚠️ Видео опасное. Всё равно хочешь скачать его?",
                      "en": "⚠️ The video is harmful. Download it anyway?"},
    "dl_btn_danger": {"kk": "⬇️ Жүктеу (өз жауапкершілігіңізбен)", "ru": "⬇️ Скачать (на свой риск)",
                      "en": "⬇️ Download (at your own risk)"},
    "dl_ask_safe": {"kk": "✅ Видео қауіпсіз. Жүктеп алғыңыз келе ме?",
                    "ru": "✅ Видео безопасное. Хочешь скачать его?",
                    "en": "✅ The video is safe. Do you want to download it?"},
    "dl_btn_safe": {"kk": "⬇️ Видеоны жүктеу", "ru": "⬇️ Скачать видео", "en": "⬇️ Download video"},
    "dl_unavailable": {"kk": "⬇️ Бұл видеоны жүктеу мүмкін емес: бот оны жүктей алмады.",
                       "ru": "⬇️ Скачать это видео нельзя: бот не смог его загрузить.",
                       "en": "⬇️ This video can't be downloaded: the bot couldn't fetch it."},
    "file_too_big": {"kk": "⚠️ Файл 20 МБ-тан үлкен — Telegram боттарға мұндай файлды жүктеуге рұқсат бермейді.\nҚысқарақ видео немесе YouTube/TikTok сілтемесін жіберіңіз.",
                     "ru": "⚠️ Файл больше 20 МБ — Telegram не даёт ботам скачивать такие файлы.\nОтправь видео покороче или ссылку на YouTube/TikTok.",
                     "en": "⚠️ The file is over 20 MB — Telegram doesn't let bots download such files.\nSend a shorter video or a YouTube/TikTok link."},
    "file_saved": {"kk": "✅ Файл базаға сақталды.\nВидео, дөңгелек видео, фото, дауыстық хабар, аудио және жазбалар автоматты түрде тексеріледі.",
                   "ru": "✅ Файл сохранён в базу.\nАвтоматически анализируются видео, кружки, фото, голосовые, аудио и подписи.",
                   "en": "✅ The file is saved.\nVideos, video messages, photos, voice messages, audio and captions are analyzed automatically."},
    "audio_ask_danger": {"kk": "⚠️ Аудио қауіпті. Бәрібір мәтінін көрсету керек пе?",
                         "ru": "⚠️ Аудио опасное. Всё равно показать текст?",
                         "en": "⚠️ The audio is harmful. Show the text anyway?"},
    "audio_ask_susp": {"kk": "🟡 Аудио күдікті. Мәтінін көрсету керек пе?",
                       "ru": "🟡 Аудио подозрительное. Показать текст?",
                       "en": "🟡 The audio is suspicious. Show the text?"},
    "audio_ask_safe": {"kk": "✅ Аудио қауіпсіз. Мәтін нұсқасы керек пе?",
                       "ru": "✅ Аудио безопасное. Нужен текстовый вариант?",
                       "en": "✅ The audio is safe. Do you need the text version?"},
    "btn_show_text": {"kk": "📝 Мәтінді көрсету", "ru": "📝 Показать текст", "en": "📝 Show text"},
    "text_not_found": {"kk": "Мәтін табылмады", "ru": "Текст не найден", "en": "Text not found"},
    "transcript_head": {"kk": "📝 <b>Аудио мәтіні:</b>", "ru": "📝 <b>Текст аудио:</b>",
                        "en": "📝 <b>Audio text:</b>"},
    "video_not_found": {"kk": "Видео серверде табылмады", "ru": "Видео не найдено на сервере",
                        "en": "Video not found on the server"},
    "video_too_big": {"kk": "Видео 50 МБ-тан үлкен — Telegram боттың оны жіберуіне рұқсат бермейді",
                      "ru": "Видео больше 50 МБ — Telegram не даёт боту его отправить",
                      "en": "The video is over 50 MB — Telegram doesn't let the bot send it"},
    "sending_video": {"kk": "⏳ Видеоны жіберіп жатырмын...", "ru": "⏳ Отправляю видео...",
                      "en": "⏳ Sending the video..."},
    "not_registered": {"kk": "Алдымен тіркеліңіз: /start басыңыз",
                       "ru": "Сначала зарегистрируйся: нажми /start",
                       "en": "Please register first: tap /start"},
    "unexpected": {"kk": "Мен басқа жауап күттім, сондықтан әрекетті тоқтаттым.\nФайлды қайта жіберіңіз немесе /start басыңыз.",
                   "ru": "Я ждал другой ответ, поэтому сбросил текущее действие.\nОтправь файл ещё раз или нажми /start.",
                   "en": "I was expecting a different answer, so I reset the current step.\nSend the file again or tap /start."},

    # ---------- Отчёт ----------
    "title_text": {"kk": "📝 Мәтінді талдау", "ru": "📝 Анализ текста", "en": "📝 Text analysis"},
    "title_caption": {"kk": "💬 Жазбаны талдау", "ru": "💬 Анализ подписи", "en": "💬 Caption analysis"},
    "title_voice": {"kk": "🎙 Дауысты талдау", "ru": "🎙 Анализ голоса", "en": "🎙 Voice analysis"},
    "title_speech_video": {"kk": "🗣 Сөйлеу мен жазуды талдау", "ru": "🗣 Анализ речи и надписей",
                           "en": "🗣 Speech and on-screen text analysis"},
    "title_speech_only": {"kk": "🗣 Сөйлеуді талдау (жазусыз)", "ru": "🗣 Анализ речи (без надписей)",
                          "en": "🗣 Speech analysis (no on-screen text)"},
    "title_desc": {"kk": "📄 Атауы мен сипаттамасын талдау", "ru": "📄 Анализ названия и описания",
                   "en": "📄 Title and description analysis"},
    "title_comments": {"kk": "💬 Пікірлерді талдау ({n})", "ru": "💬 Анализ комментариев ({n})",
                       "en": "💬 Comments analysis ({n})"},
    "verdict": {"kk": "Вердикт", "ru": "Вердикт", "en": "Verdict"},
    "toxicity": {"kk": "Уыттылық", "ru": "Токсичность", "en": "Toxicity"},
    "found_words": {"kk": "⚠️ <b>Қауіпті сөздер табылды:</b>", "ru": "⚠️ <b>Найдены опасные слова:</b>",
                    "en": "⚠️ <b>Harmful words found:</b>"},
    "links_head": {"kk": "🔗 <b>Сілтемелерді тексеру:</b>", "ru": "🔗 <b>Проверка ссылок:</b>",
                   "en": "🔗 <b>Link check:</b>"},
    "links_phish": {"kk": "🔴 Фишингке ұқсайды", "ru": "🔴 Похоже на фишинг", "en": "🔴 Looks like phishing"},
    "links_susp": {"kk": "🟡 Күдікті сілтемелер", "ru": "🟡 Подозрительные ссылки", "en": "🟡 Suspicious links"},
    "links_ok": {"kk": "🟢 Сілтемелер қалыпты", "ru": "🟢 Ссылки выглядят нормально", "en": "🟢 Links look fine"},
    "risk": {"kk": "тәуекел", "ru": "риск", "en": "risk"},
    "frames_head": {"kk": "👁 <b>Кадрларды талдау:</b>", "ru": "👁 <b>Анализ кадров:</b>",
                    "en": "👁 <b>Frame analysis:</b>"},
    "frames_head_gemini": {"kk": "👁 <b>Кадрларды талдау (Gemini):</b>", "ru": "👁 <b>Анализ кадров (Gemini):</b>",
                           "en": "👁 <b>Frame analysis (Gemini):</b>"},
    "frames_n": {"kk": "кадр: {n}", "ru": "кадров: {n}", "en": "frames: {n}"},
    "frame_hit": {"kk": "{name}: {n}/{total} кадр (сенімділік {conf}%-ға дейін)",
                  "ru": "{name}: {n} из {total} кадров (уверенность до {conf}%)",
                  "en": "{name}: {n} of {total} frames (confidence up to {conf}%)"},
    "frames_clean": {"kk": "Кадрларда қауіпті ештеңе табылмады", "ru": "Опасного на кадрах не найдено",
                     "en": "Nothing harmful found in the frames"},
    "frames_maybe": {"kk": "1 күмәнді кадр болды ({names}) — модель қатесі болуы мүмкін",
                     "ru": "Был 1 сомнительный кадр ({names}) — скорее всего ошибка модели",
                     "en": "There was 1 doubtful frame ({names}) — most likely a model error"},
    "recognized": {"kk": "Танылғаны", "ru": "Распознано", "en": "Recognized"},
    "speech_lang": {"kk": "🌐 Сөйлеу тілі: {lang}", "ru": "🌐 Язык речи: {lang}", "en": "🌐 Speech language: {lang}"},
    "no_speech_audio": {"kk": "🎙 Аудиода сөйлеу табылмады.", "ru": "🎙 Речь в аудио не найдена.",
                        "en": "🎙 No speech found in the audio."},
    "no_speech_video": {"kk": "🗣 Видеода сөйлеу мен жазу табылмады.", "ru": "🗣 Речи и надписей в видео не найдено.",
                        "en": "🗣 No speech or on-screen text found in the video."},
    "no_speech_video2": {"kk": "🗣 Видеода сөйлеу табылмады.", "ru": "🗣 Речи в видео не найдено.",
                         "en": "🗣 No speech found in the video."},
    "speech_error": {"kk": "🎙 Сөйлеуді тану мүмкін болмады: {e}", "ru": "🎙 Не удалось распознать речь: {e}",
                     "en": "🎙 Couldn't recognize speech: {e}"},
    "speech_missing": {"kk": "🎙 Сөйлеуді тану қосылмаған.", "ru": "🎙 Распознавание речи не подключено.",
                       "en": "🎙 Speech recognition is not connected."},
    "frames_error": {"kk": "👁 Кадрларды тексеру мүмкін болмады: {e}", "ru": "👁 Не удалось проверить кадры: {e}",
                     "en": "👁 Couldn't check the frames: {e}"},
    "channel": {"kk": "Арна", "ru": "Канал", "en": "Channel"},
    "video_word": {"kk": "Видео", "ru": "Видео", "en": "Video"},
    "link_dl_warn": {"kk": "⚠️ Видеоның өзін жүктеу мүмкін болмады, тек атауы, сипаттамасы мен пікірлері тексерілді.",
                     "ru": "⚠️ Само видео скачать не удалось, проверены только название, описание и комментарии.",
                     "en": "⚠️ The video itself couldn't be downloaded; only the title, description and comments were checked."},
    "parser_missing": {"kk": "❌ parser.py модулі қосылмаған — сілтемелер тексерілмейді.",
                       "ru": "❌ Модуль parser.py не подключён — ссылки не проверяются.",
                       "en": "❌ The parser.py module is not connected — links can't be checked."},

    # ---------- Антифлуд ----------
    "flood": {"kk": "⛔ Тым көп хабарлама. {sec} секунд күтіңіз.",
              "ru": "⛔ Слишком много сообщений. Подожди {sec} секунд.",
              "en": "⛔ Too many messages. Please wait {sec} seconds."},
    "busy": {"kk": "⏳ Алдыңғы тексеру әлі жүріп жатыр, күтіңіз.",
             "ru": "⏳ Подожди, предыдущая проверка ещё идёт.",
             "en": "⏳ Please wait, the previous check is still running."},
}

# Вердикты (text_check отдаёт их по-русски)
VERDICTS = {
    "Безопасно": {"kk": "Қауіпсіз", "ru": "Безопасно", "en": "Safe"},
    "Подозрительно": {"kk": "Күдікті", "ru": "Подозрительно", "en": "Suspicious"},
    "Опасно": {"kk": "Қауіпті", "ru": "Опасно", "en": "Harmful"},
}

LABELS = {
    "insult": {"kk": "Қорлау", "ru": "Оскорбления", "en": "Insults"},
    "obscenity": {"kk": "Балағат", "ru": "Мат", "en": "Obscenity"},
    "threat": {"kk": "Қорқыту", "ru": "Угрозы", "en": "Threats"},
    "dangerous": {"kk": "Қауіпті контент", "ru": "Опасный контент", "en": "Dangerous content"},
}

# Категории стоп-слов из text_check.STOP_WORDS
CATEGORIES = {
    "наркотики": {"kk": "Есірткі", "ru": "Наркотики", "en": "Drugs"},
    "оружие": {"kk": "Қару", "ru": "Оружие", "en": "Weapons"},
    "казино_и_ставки": {"kk": "Казино және ставкалар", "ru": "Казино и ставки", "en": "Casino and betting"},
    "мошенничество": {"kk": "Алаяқтық", "ru": "Мошенничество", "en": "Fraud"},
    "угрозы_и_буллинг": {"kk": "Қорқыту және буллинг", "ru": "Угрозы и буллинг", "en": "Threats and bullying"},
    "мат": {"kk": "Балағат", "ru": "Мат", "en": "Swearing"},
    "қорлау_және_қорқыту": {"kk": "Қорлау және қорқыту", "ru": "Оскорбления и угрозы (каз.)",
                            "en": "Insults and threats (Kazakh)"},
    "қазақша_балағат": {"kk": "Қазақша балағат", "ru": "Казахский мат", "en": "Kazakh swearing"},
}

# Что нашлось на кадрах (local_vision отдаёт по-русски)
FRAME_NAMES = {
    "Контент 18+": {"kk": "18+ контент", "ru": "Контент 18+", "en": "18+ content"},
    "Драка / избиение": {"kk": "Төбелес / ұрып-соғу", "ru": "Драка / избиение", "en": "Fight / beating"},
    "Оружие": {"kk": "Қару", "ru": "Оружие", "en": "Weapon"},
    "Оружие (нож)": {"kk": "Қару (пышақ)", "ru": "Оружие (нож)", "en": "Weapon (knife)"},
    "Кровь / насилие": {"kk": "Қан / зорлық", "ru": "Кровь / насилие", "en": "Blood / violence"},
    "Наркотики": {"kk": "Есірткі", "ru": "Наркотики", "en": "Drugs"},
}

# Названия языков речи
SPEECH_LANGS = {
    "kk": {"kk": "қазақ", "ru": "казахский", "en": "Kazakh"},
    "ru": {"kk": "орыс", "ru": "русский", "en": "Russian"},
    "en": {"kk": "ағылшын", "ru": "английский", "en": "English"},
}


def _pick(table: dict, lang: str) -> str:
    return table.get(lang) or table.get(DEFAULT_LANG) or next(iter(table.values()))


def t(key: str, lang: str, **kw) -> str:
    """Текст по ключу на нужном языке."""
    text = _pick(T[key], lang)
    return text.format(**kw) if kw else text


def tr(table: dict, value: str, lang: str) -> str:
    """Перевод значения из таблицы (вердикт, категория…); если нет — как есть."""
    return _pick(table[value], lang) if value in table else value


def lang_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🇰🇿 Қазақша", callback_data="lang:kk"),
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
        InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en"),
    ]])


def contact_keyboard(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t("btn_phone", lang), request_contact=True)]],
        resize_keyboard=True, one_time_keyboard=True)
