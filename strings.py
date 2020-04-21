# ### STRINGS ### #

# welcome channel msgs
WELCOME_HEADER = "**Vitaj na oficiálnom Discord serveri Online Školy Programovania Trojstenu!**"
DEFAULT_WELCOME_MESSAGE = ("{0}\n\nToto je uvítací kanál pre nových účastníkov. \n\nCíť sa tu ako doma, a ak poznáš "
                           "niekoho, kto by tu tiež mal byť, neváhaj ho pozvať: https://discord.gg/9vwtHhP\n\n"
                           "Pravidlá:\n{1}\n"
                           "Faq:\n{2}\n")

DEFAULT_RULES = {"0": ("Správame sa slušne, rešpektujeme ostatných, nespamujeme, "
                       "nepoužívame zbytočne ‘@ everyone’ a všetko čo by rozum napovedal."),
                 "1": "Rešpektujeme pokyny adminov.",
                 "2": "O riešeniach úloh je povolené sa baviť až keď sú zverejnené vzoráky."}

DEFAULT_FAQ_CONTENT = {"0": {"Som prvýkrát na discorde o čom to tu je?":
                             ("Skús pohľadať na internete:\n Krátke: <https://www.youtube.com/watch?v=aYSQB0fUzv0>\n"
                              " Dlhšie: <https://www.youtube.com/watch?v=le_CE--Mnvs>")},
                       "1": {"Ako fungujú role a čo to vlastne znamená?":
                             ("Rola ti môže byť pridelená nižšie, kliknutím na niektoré z emoji. "
                              "Role seminárov ti dávajú prístup k jednotlivým kanálom a taktiež budeš dostávať "
                              "notifikácie, keď sa táto rola niekde označí. Farebná rola slúži len na to, aby zmenila"
                              " farbu tvojho mena. Ostatné role vedia priradiť admini.")},
                       "2": {"Ako je to s prezývkami?":
                             ("Ako prezývku/nickname odporúčame používať to ako ťa v seminárovej komunite volajú, "
                              "alebo ako chceš aby ťa volali. V prípade robenia neplechy s duplicitnými nicknames "
                              "a predstierania že si niekto iný nebudeme váhať kickovať a banovať.")}}

ADDITIONAL_CONTENT = "\nAk sa cítiš ako vedúci alebo starec, napíš {0} a bude ti priradená skupina"

ROLE_MESSAGE = "Nižšie si môžeš vybrať zo seminárov, ktoré riešiš alebo ťa zaujímajú:"
COLOR_MESSAGE = "A farbu tvojho mena:"
# event/system msgs
TASKS_ANNOUNCEMENT = "**Kolo {} je tu!** Môžete začať riešiť:"
TASKS_RELEASE = ["Vyšlo nové kolo {}", "Práve beží kolo {}.", "Úlohy nájdete [tu]({}/ulohy/)"]
TASK_END_ANNOUNCEMENT = "**Kolo {} skončilo.** Gratulujeme úspešným riešitelom!"
TASKS_ROUND_END = "**Toto kolo {} už skončilo.** \nVýsledky ({})"
SOLUTIONS_RELEASE = ("Ahojte, vedúci práve pridali vzoráky k najnovšiemu kolu {0}!\n"
                     "Môžete ich nájsť tu:  {0}/ulohy")
VOTE_MESSAGE = "Tu môžeš označiť aktuálne úlohy, ktoré sa ti páčili:"
ROUND_END = "Kolo už skončilo."
# warning/ban moderation
WARNING_MSG = ("Máš oficiálne upozornenie od adminov. Tvoj počet upozornení je {0}."
               "Keď toto číslo dosiahne {1}, dostaneš celoserveroový ban."
               "Kontaktuj moderátora/admina pre viac info."
               "\n\n\n-Troj-stena")
BAN_MSG = "Počet upozornení dosiahol {0}. Váš účet bol pridaný na blacklist."
BAN_ERROR_U = ("Máš maximálny možný počet upozornení, ale nebolo možné ťa zabanovať."
               "Admini sú upozornení a vyriešia túto situáciu.")
BAN_ERROR_A = "Nebolo možné vydať ban pre {0}, kým táto chyba nebude vyriešená bude nutné vydávať bany ručne."
# command messages
SUB_RESPONSE = "Super! Teraz budeš dostávať notifikácie o zmenách pre {0}"
SUB_LIST = "Práve sleduješ tieto mená:\n {0}"
SUB_ERROR_EXISTING = "Toto meno už sleduješ"
SUB_HELP = "``````"
TASK_SUBMITED = "{0} práve pridal úlohu na vyriešenie, označí sa {1}, keď bude vyriešená."
TASK_COMPLETED = "Práve niekto vyriešil úlohu od {0} *({1})*. Gratulujeme!"
PURGE_EMPTY_CHANNEL = "Kanál je prázdny"
RULE_NOT_FOUND = "Pravidlo nebolo nájdené"
FAQ_NOT_FOUND = "FAQ nebolo nájdené"
HELP_HEADER = "Použitie príkazu {0}{1}:"
COMMANDS_HELP = {
    'rule': ['add "pravidlo"',
             'remove číslo_pravidla',
             'edit číslo_pravidla "nové pravidlo"'],
    'faq': ['add "otázka" "odpoveď"',
            'remove číslo_faq_v_poradí',
            'edit číslo_faq_v_poradí "Nová otázka" "Nová odpoveď"',
            '*pri použití edit "-" zachová pôvodnú otázku/odpoveď*'],
    'lead': ['seminar',
             '*seminar sa automaticky doplní ak použieš príkaz v kanáli semináru']
}
CMD_NONEXISTENT = "Príkaz nenájdený"
DISABLED_ERROR = "Príkaz ešte nieje použiteľný."
ONLY_GUILD_ERROR = "Tento príkaz sa nedá použiť v DM."
ONLY_DM_ERROR = "Tento príkaz sa dá použiť len v DM."
PERMISSION_ERROR = "Nemáš práva na použitie tohoto príkazu."
CHANNEL_ERROR = "{0}{1} sa dá použiť len v administrátorských chatoch."
SUB_CHANGE = "Pozícia, alebo body pre {0} sa zmenili/a! Pozrieť sa môžeš tu -> {1}/vysledky"
# moderation messages
DELETE_NOTICE = ("{0}. Vedenie sa rozhodlo, že tvoja správa (spomenutá nižšie) porušuje pravidlá."
                 "Správa bola zmazaná, v budúcnosti sa prosím riaď pravidlami serveru.")
DELETE_DETAILS = ("Detaili zmazanej správy:\n"
                  "Zaslaná: {0} *({1})*\n"
                  "Kanál: {2}\n"
                  "Obsah:\n{3}\n")
SUSPICIOUS_MESSAGES = ("Bola označená podozrivá správa v {0}:\n"
                       "{1}\n"
                       "Link: {2}")
