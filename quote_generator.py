
import random
import hashlib
from datetime import datetime
from zoneinfo import ZoneInfo


CONTENT = {
    "morning": {
        "title": "GOOD MORNING",
        "opening": [
            "हर सुबह एक नई शुरुआत है।",
            "सूरज की किरणें नई उम्मीद लाती हैं।",
            "आज का दिन आपके लिए खास है।",
            "सुबह की मुस्कान सबसे खूबसूरत है।",
            "नई सुबह नए अवसर लेकर आई है।",
        ],
        "english": [
            "Every morning is a new beginning.",
            "Start your day with a smile.",
            "Today is another opportunity.",
            "Wake up with hope.",
        ],
        "tags": [
            "#GoodMorning",
            "#MorningVibes",
            "#PositiveMorning",
            "#Sunrise",
            "#NewBeginning",
        ],
    },

    "afternoon": {
        "title": "GOOD AFTERNOON",
        "opening": [
            "दिन अभी बाकी है, कोशिश जारी रखो।",
            "हर मेहनत का अपना महत्व है।",
            "आज का समय बहुत कीमती है।",
            "अपने लक्ष्य को याद रखो।",
            "थोड़ा आराम करो, फिर आगे बढ़ो।",
        ],
        "english": [
            "Keep moving towards your dreams.",
            "Make every moment count.",
            "Stay focused and keep growing.",
            "Your efforts matter.",
        ],
        "tags": [
            "#GoodAfternoon",
            "#DailyMotivation",
            "#KeepGoing",
            "#HardWork",
            "#SuccessMindset",
        ],
    },

    "evening": {
        "title": "GOOD EVENING",
        "opening": [
            "शाम का सुकून दिल को खुश करता है।",
            "ढलता सूरज नई उम्मीद देता है।",
            "आज की मेहनत पर गर्व करो।",
            "कुछ पल अपने लिए भी निकालो।",
            "शाम की हवा में सुकून है।",
        ],
        "english": [
            "Enjoy the beauty of the evening.",
            "Take a moment to relax.",
            "Every sunset brings new hope.",
            "Be proud of your progress.",
        ],
        "tags": [
            "#GoodEvening",
            "#EveningVibes",
            "#Sunset",
            "#PeacefulLife",
            "#NatureLovers",
        ],
    },

    "night": {
        "title": "GOOD NIGHT",
        "opening": [
            "रात का सुकून मन को शांत करता है।",
            "आज की चिंता को पीछे छोड़ दो।",
            "चाँद की रोशनी उम्मीद जगाती है।",
            "अपने खूबसूरत सपनों को याद करो।",
            "कल फिर एक नई शुरुआत होगी।",
        ],
        "english": [
            "Rest well and dream big.",
            "Tomorrow is a fresh start.",
            "Let your mind find peace.",
            "Good night and sweet dreams.",
        ],
        "tags": [
            "#GoodNight",
            "#SweetDreams",
            "#NightVibes",
            "#PeacefulNight",
            "#StayPositive",
        ],
    },
}


SECOND_LINES = [
    "अपने दिल में विश्वास बनाए रखो।",
    "छोटी खुशियों को महसूस करो।",
    "हर पल से कुछ नया सीखो।",
    "खुद पर भरोसा करना मत छोड़ो।",
    "जिंदगी को मुस्कुराकर अपनाओ।",
    "अपनी सोच हमेशा सकारात्मक रखो।",
    "अपने सपनों को दिल में सजाए रखो।",
    "हर अनुभव से आगे बढ़ना सीखो।",
]

THIRD_LINES = [
    "मुश्किलें भी हमें मजबूत बनाती हैं।",
    "छोटी कोशिशें बड़ा बदलाव लाती हैं।",
    "धैर्य से हर रास्ता आसान होता है।",
    "अच्छी सोच जीवन को सुंदर बनाती है।",
    "हर दिन कुछ नया सिखाता है।",
    "मेहनत से आत्मविश्वास बढ़ता है।",
    "खुशियाँ छोटी बातों में मिलती हैं।",
    "उम्मीद हमें आगे बढ़ना सिखाती है।",
]

ENDINGS = [
    "हमेशा खुश रहो और मुस्कुराते रहो।",
    "अपने जीवन को खूबसूरत बनाओ।",
    "उम्मीद का साथ कभी मत छोड़ो।",
    "खुद से प्यार करना सीखो।",
    "आपका हर दिन खुशियों से भरा रहे।",
    "अपने सपनों की ओर बढ़ते रहो।",
    "जिंदगी के हर पल का आनंद लो।",
    "सकारात्मक रहो और खुशियाँ बाँटो।",
]


def generate_quote(theme, media_type="photo", used_quotes=None):

    if theme not in CONTENT:
        raise ValueError("Invalid theme")

    if media_type not in ("photo", "reel"):
        raise ValueError("Invalid media type")

    today = datetime.now(
        ZoneInfo("Asia/Kolkata")
    ).date().isoformat()

    seed = hashlib.sha256(
        f"{today}-{theme}-{media_type}".encode()
    ).hexdigest()

    rng = random.Random(seed)

    data = CONTENT[theme]

    used_quotes = set(used_quotes or [])

    for attempt in range(100):

        lines = [
            rng.choice(data["opening"]),
            rng.choice(SECOND_LINES),
            rng.choice(THIRD_LINES),
            rng.choice(ENDINGS),
        ]

        quote_id = hashlib.sha256(
            "\n".join(lines).encode("utf-8")
        ).hexdigest()

        if quote_id not in used_quotes:
            break

    else:
        raise RuntimeError("No unused quote found")

    english = rng.choice(data["english"])

    hashtags = rng.sample(data["tags"], 3)

    hashtags += [
        "#RKGautam",
        "#RKDigitalWorld",
        "#HindiQuotes",
    ]

    if media_type == "reel":
        hashtags.append("#FacebookReels")

    caption = (
        data["title"]
        + "\n\n"
        + "\n".join(lines)
        + "\n\n"
        + english
        + "\n\n"
        + " ".join(hashtags)
    )

    return {
        "id": quote_id,
        "title": data["title"],
        "theme": theme,
        "lines": lines,
        "english": english,
        "caption": caption,
        "hashtags": hashtags,
    }


if __name__ == "__main__":

    used = set()

    for theme in CONTENT:

        for media_type in ("photo", "reel"):

            result = generate_quote(
                theme,
                media_type,
                used
            )

            used.add(result["id"])

            print("=" * 40)
            print(theme, media_type)
            print(result["caption"])

    print("ALL 8 CONTENT QUOTES CREATED")
