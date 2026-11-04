"""Gender-consistent person names for the synthetic world.

In many European languages a woman's surname takes a feminine form (Czech Novák → Nováková, Polish Kowalski →
Kowalska, Lithuanian Kazlauskas → Kazlauskienė, Latvian Bērziņš → Bērziņa, Bulgarian Иванов → Иванова, Greek
Παπαδόπουλος → Παπαδοπούλου) and Icelandic patronymics end in -son or -dóttir. A pack's name lists hold the
masculine (dictionary) forms; this module knows which given names are female and maps each surname to its feminine
form, explicitly per country (irregular cases make suffix rules unreliable). Countries without gendered surnames
need no entry.
"""
from __future__ import annotations

import random
from typing import Dict, Set, Tuple

FEMALE: Dict[str, Set[str]] = {
    "PL": {"Anna", "Zofia", "Maja", "Julia", "Natalia", "Katarzyna"},
    "CZ": {"Jana", "Eva", "Lucie", "Kateřina", "Tereza", "Veronika"},
    "SK": {"Jana", "Mária", "Zuzana", "Katarína", "Lucia", "Monika"},
    "LT": {"Ona", "Rūta", "Gabija", "Austėja", "Eglė", "Ieva"},
    "LV": {"Anna", "Līga", "Ilze", "Kristīne", "Laura", "Inese"},
    "IS": {"Guðrún", "Anna", "Kristín", "Sigríður", "Helga", "Katrín"},
    "BG": {"Мария", "Елена", "Виктория", "Десислава", "Цветелина", "Анна"},
    "MK": {"Ана", "Елена", "Марија", "Ивана", "Сара", "Мила"},
    "GR": {"Μαρία", "Ελένη", "Κατερίνα", "Σοφία", "Αγγελική", "Χριστίνα"},
}

FEMININE: Dict[str, Dict[str, str]] = {
    "PL": {"Kowalski": "Kowalska", "Wiśniewski": "Wiśniewska", "Kamiński": "Kamińska", "Lewandowski": "Lewandowska",
           "Zieliński": "Zielińska", "Szymański": "Szymańska", "Dąbrowski": "Dąbrowska", "Kozłowski": "Kozłowska"},
    "CZ": {"Novák": "Nováková", "Svoboda": "Svobodová", "Novotný": "Novotná", "Dvořák": "Dvořáková", "Černý": "Černá",
           "Procházka": "Procházková", "Kučera": "Kučerová", "Veselý": "Veselá", "Horák": "Horáková",
           "Němec": "Němcová", "Marek": "Marková", "Pokorný": "Pokorná"},
    "SK": {"Horváth": "Horváthová", "Kováč": "Kováčová", "Varga": "Vargová", "Tóth": "Tóthová", "Nagy": "Nagyová",
           "Baláž": "Balážová", "Szabó": "Szabóová", "Molnár": "Molnárová", "Lukáč": "Lukáčová",
           "Kollár": "Kollárová", "Novák": "Nováková", "Oravec": "Oravcová"},
    "LT": {"Kazlauskas": "Kazlauskienė", "Jankauskas": "Jankauskienė", "Petrauskas": "Petrauskienė",
           "Stankevičius": "Stankevičienė", "Vasiliauskas": "Vasiliauskienė", "Žukauskas": "Žukauskienė",
           "Butkus": "Butkuvienė", "Paulauskas": "Paulauskienė", "Urbonas": "Urbonienė",
           "Kavaliauskas": "Kavaliauskienė", "Navickas": "Navickienė", "Rimkus": "Rimkuvienė"},
    "LV": {"Bērziņš": "Bērziņa", "Kalniņš": "Kalniņa", "Ozoliņš": "Ozoliņa", "Jansons": "Jansone",
           "Liepiņš": "Liepiņa", "Krūmiņš": "Krūmiņa", "Balodis": "Balode", "Zariņš": "Zariņa",
           "Pētersons": "Pētersone", "Vītols": "Vītola", "Kļaviņš": "Kļaviņa", "Eglītis": "Eglīte"},
    "BG": {"Иванов": "Иванова", "Георгиев": "Георгиева", "Петров": "Петрова", "Николов": "Николова",
           "Христов": "Христова", "Стоянов": "Стоянова", "Тодоров": "Тодорова", "Илиев": "Илиева",
           "Атанасов": "Атанасова", "Петков": "Петкова", "Ангелов": "Ангелова", "Колев": "Колева"},
    "MK": {"Николовски": "Николовска", "Петровски": "Петровска", "Стојановски": "Стојановска",
           "Јовановски": "Јовановска", "Димитровски": "Димитровска", "Илиевски": "Илиевска",
           "Ангеловски": "Ангеловска", "Костовски": "Костовска", "Стефановски": "Стефановска",
           "Митревски": "Митревска", "Наумовски": "Наумовска", "Ристовски": "Ристовска"},
    "GR": {"Παπαδόπουλος": "Παπαδοπούλου", "Παπαδάκης": "Παπαδάκη", "Μαυρίδης": "Μαυρίδου",
           "Καραγιάννης": "Καραγιάννη"},   # genitive surnames (Γεωργίου, Νικολάου, …) do not change
}


def full_name(rng: random.Random, locale) -> Tuple[str, str]:
    """(given name, surname) with the surname in the form that agrees with the given name's gender."""
    first = rng.choice(locale.first_names)
    country = locale.country
    female = first in FEMALE.get(country, set())
    if country == "IS":  # patronymics: -son for men, -dóttir for women
        pool = [s for s in locale.last_names if s.endswith("dóttir") == female]
        return first, rng.choice(pool)
    last = rng.choice([s for s in locale.last_names if not s.endswith(("dóttir",))])
    if female:
        last = FEMININE.get(country, {}).get(last, last)
    return first, last
