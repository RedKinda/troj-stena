# #### CONSTANTS FILE #### #

GUILD_ID = 598476317758849024
DEBUG_MODE = False
BOT_MSG = "Calculating mean of odd people"
MINIMAL_UPDATE_DELAY = 900
WARNINGS_TO_BAN = 3
TIME_ZONE = 2
UTC_STRING = "UTC+{0}".format(TIME_ZONE)

CONTENT_FILE = "content.dat"
SUBSCRIBER_FILE = "subscribers.dat"
MAIN_DATA_FILE = "information.dat"


# ### STRINGS ### #

# welcome channel msgs
WELCOME_HEADER = "**Vitaj na oficiálnom Discord serveri Trojstenu!**"
DEFAULT_WELCOME_MESSAGE = ("{0}\n\nToto je miesto kde sa stretávajú účastníci a vedúci aby sa zabavili. Ak "
                           "poznáš niekoho, kto by tu tiež mal byť, neváhaj ho pozvať: https://discord.gg/F9HZP9b\n\n"
                           "Pravidlá:\n{1}\n"
                           "Faq:\n{2}\n")

DEFAULT_RULES = [("Správame sa slušne, rešpektujeme ostatných, nespamujeme, "
                  "nepoužívame zbytočne ‘@ everyone’ a všetko čo by rozum napovedal."),
                 "Rešpektujeme pokyny adminov.",
                 "O riešeniach úloh je povolené sa baviť až keď sú zverejnené vzoráky."]

DEFAULT_FAQ_CONTENT = [["Som prvýkrát na discorde o čom to tu je?",
                        ("Skús pohľadať na internete:\n Krátke: <https://www.youtube.com/watch?v=aYSQB0fUzv0>\n"
                         " Dlhšie: <https://www.youtube.com/watch?v=le_CE--Mnvs>")],
                       ["Ako fungujú role a čo to vlastne znamená?",
                        ("Rola ti môže byť pridelená nižšie, kliknutím na niektoré z emoji. "
                         "Role seminárov ti dávajú prístup k jednotlivým kanálom a taktiež budeš dostávať notifikácie, "
                         "keď sa táto rola niekde označí. Farebná rola slúži len na to, aby zmenila farbu tvojho mena. "
                         "Ostatné role vedia priradiť admini. ")],
                       ["Ako je to s prezývkami?",
                        ("Ako prezývku/nickname odporúčame používať to ako ťa v seminárovej komunite volajú, "),
                        ("alebo ako chceš aby ťa volali. V prípade robenia neplechy s duplicitnými nicknames "),
                        ("a predstierania že si niekto iný nebudeme váhať kickovať a banovať.")]]


ZAJO_ID = 185106567916421121
ADDITIONAL_CONTENT = "Ak sa cítiš ako vedúci alebo starec, napíš {0} a bude ti priradená skupina"

# event msgs
TASKS_RELEASE = "**Kolo {0} je tu!** \n Riešenie sa môže začať -> {1}/ulohy"
TASK_ROUND_END = "Kolo {0} skončilo. Gratulujeme úspešným riešitelom!"
SOLUTIONS_RELEASE = "Ahojte, vedúci práve pridali vzoráky k najnovšiemu kolu {0}!\nMôžete ich nájsť tu:  {0}/ulohy"


# warning/ban moderation
WARNING_MSG = ("Máš oficiálne upozornenie od adminov. Tvoj počet upozornení je {0}."
               "Keď toto číslo dosiahne {1}, dostaneš celoserveroový ban."
               "Kontaktuj moderátora/admina pre viac info.\n\n\n-Troj-stena")
BAN_MSG = "Počet upozornení dosiahol {0}. Váš účet bol pridaný na blacklist."
BAN_ERROR_U = ("Máš maximálny možný počet upozornení, ale nebolo možné ťa zabanovať."
               "Admini sú upozornení a vyriešia túto situáciu.")
BAN_ERROR_A = "Nebolo možné vydať ban pre {0}, kým táto chyba nebude vyriešená bude nutné vydávať bany ručne."

# command messages
SUB_RESPONSE = "Super! Teraz budeš dostávať notifikácie o zmenách pre {0}"
SUB_LIST = "Práve sleduješ tieto mená:\n {0}"
SUB_HELP = "``````"

TASK_COMPLETED = "Práve niekto vyriešil úlohu od {0} *({1})*. Gratulujeme!"

RULE_NOT_FOUND = "Pravidlo nebolo nájdené"
FAQ_NOT_FOUND = "FAQ nebolo nájdené"

HELP_HEADER = "Použitie príkazu {0}{1}:"
SEPARATOR = "-"
SEPARATOR_COUNT = 20
COMMANDS_HELP = {
  'rule': [('add "pravidlo"'),
           ('remove číslo_pravidla'),
           ('edit číslo_pravidla "nové pravidlo"')],
  'faq': [('add "otázka" "odpoveď"'),
          ('remove číslo_faq_v_poradí'),
          ('edit číslo_faq_v_poradí "Nová otázka" "Nová odpoveď"'),
          ('*pri použití edit "-" zachová pôvodnú otázku/odpoveď*')]
}

# moderation messages
DELETE_NOTICE = ("{0}. Vedenie sa rozhodlo, že tvoja správa (spomenutá nižšie) porušuje pravidlá."
                 "Správa bola zmazaná, v budúcnosti sa prosím riaď pravidlami serveru.")
DELETE_DETAILS = ("Detaili zmazanej správy:\nZaslaná: {0} *({1})*\nKanál: {2}\n Obsah:\n{3}\n")
SUSPICIOUS_MESSAGES = "Bola označená podozrivá správa v {0}:\n{1}\nLink: {2}"

# channels
TASKS_CHANNEL = 598522778743734342
MODERATING_CHANNEL = 599249382038044703
VOTING_CHANNEL = 600688938562093058
WELCOME_CHANNEL = 600944280650907678
DEV_CHANNEL = 598490170236338176
ADMIN_CHANNEL = 600384787433259010
TESTING_CHANNEL = 601160389736136737

# roles
TIME_OUT_ROLE = 598815157975515147
ADMIN_ROLE = 598478860824346624
VEDUCI_ROLE = 598517418968743957
WHITE_ROLE = 601106902398533632
ORANGE_ROLE = 601098919275135007
GREEN_ROLE = 601099061696659456
BLUE_ROLE = 601098701536231434
KSP_ROLE = 600750067929841736
KMS_ROLE = 600750035801604184
FKS_ROLE = 600750477289848836
PRASK_ROLE = 600750779447509002
UFO_ROLE = 600750981483069458
SEMINAR_ROLES = {"ksp": KSP_ROLE,
                 "kms": KMS_ROLE,
                 "fks": FKS_ROLE,
                 "prask": PRASK_ROLE,
                 "ufo": UFO_ROLE}

# emojis
MISKO_EMOJI = 598820789168373778
SOLVED_EMOJI = 598782166121316363
CHEATALERT_EMOJI = 599242099207962635
QUESTIONABLE_EMOJI = 599248755186728966
KSP_EMOJI = 600745214080188448
KMS_EMOJI = 600745723650113571
FKS_EMOJI = 600745115258060800
PRASK_EMOJI = 600744451861774356
UFO_EMOJI = 600744527631745026
SEMINAR_EMOJIS = {"ksp": KSP_EMOJI,
                  "kms": KMS_EMOJI,
                  "fks": FKS_EMOJI,
                  "prask": PRASK_EMOJI,
                  "ufo": UFO_EMOJI}
