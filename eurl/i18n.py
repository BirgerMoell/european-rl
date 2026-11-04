"""Interface strings per language: answer-format hints and tool-episode messages.

The answer keyword `ANSWER:` and the abstention token `UNKNOWN` are the same in every language (one convention for
the model to learn, shared with our eu_qa suite); the explanation around them is localised. `REVIEW` records who
checked each language's strings: "llm" (written or translated by an LLM, not yet reviewed by a native speaker) or
"native:<initials>". Languages without a table fall back to English and are flagged by the contract check.
"""
from __future__ import annotations

from typing import Dict

ANSWER_KEY = "ANSWER"
ABSTAIN = "UNKNOWN"

STRINGS: Dict[str, Dict[str, str]] = {
    "eng": {
        "money": "End with a line of the form `ANSWER: <amount>`, for example `ANSWER: {example}`.",
        "date": "End with a line of the form `ANSWER: YYYY-MM-DD`.",
        "datetime": "End with a line of the form `ANSWER: YYYY-MM-DD HH:MM`.",
        "integer": "End with a line of the form `ANSWER: <whole number>`.",
        "text": "End with a line of the form `ANSWER: <answer>`.",
        "mapping": "End with `ANSWER:` followed by a JSON object.",
        "strings": "End with `ANSWER:` followed by a JSON list of strings, exactly as written in the text and in "
                   "the order they appear.",
        "abstain": "If the task cannot be solved with the information given, answer `ANSWER: UNKNOWN`.",
        "done": "Done.",
        "err_action": "invalid action: call a tool or write a final answer",
        "err_tool": "unknown tool: {name}",
        "err_args_object": "the arguments must be a JSON object",
        "err_missing": "missing argument: {key}",
        "err_unknown_arg": "unknown argument: {key}",
        "err_type": "wrong type for {key}: {expected} expected",
        "err_enum": "invalid value for {key}",
    },
    "swe": {
        "money": "Avsluta med en rad i formen `ANSWER: <belopp>`, till exempel `ANSWER: {example}`.",
        "date": "Avsluta med en rad i formen `ANSWER: ÅÅÅÅ-MM-DD`.",
        "datetime": "Avsluta med en rad i formen `ANSWER: ÅÅÅÅ-MM-DD TT:MM`.",
        "integer": "Avsluta med en rad i formen `ANSWER: <heltal>`.",
        "text": "Avsluta med en rad i formen `ANSWER: <svar>`.",
        "mapping": "Avsluta med `ANSWER:` följt av ett JSON-objekt.",
        "strings": "Avsluta med `ANSWER:` följt av en JSON-lista med strängar, exakt som de står i texten och i "
                   "den ordning de förekommer.",
        "abstain": "Om uppgiften inte går att lösa med den information som finns, svara `ANSWER: UNKNOWN`.",
        "done": "Klart.",
        "err_action": "ogiltig handling: anropa ett verktyg eller skriv ett slutsvar",
        "err_tool": "okänt verktyg: {name}",
        "err_args_object": "argumenten måste vara ett JSON-objekt",
        "err_missing": "argument saknas: {key}",
        "err_unknown_arg": "okänt argument: {key}",
        "err_type": "fel typ för {key}: {expected} förväntas",
        "err_enum": "ogiltigt värde för {key}",
    },
    "deu": {
        "money": "Schließe mit einer Zeile der Form `ANSWER: <Betrag>` ab, zum Beispiel `ANSWER: {example}`.",
        "date": "Schließe mit einer Zeile der Form `ANSWER: JJJJ-MM-TT` ab.",
        "datetime": "Schließe mit einer Zeile der Form `ANSWER: JJJJ-MM-TT HH:MM` ab.",
        "integer": "Schließe mit einer Zeile der Form `ANSWER: <ganze Zahl>` ab.",
        "text": "Schließe mit einer Zeile der Form `ANSWER: <Antwort>` ab.",
        "mapping": "Schließe mit `ANSWER:` gefolgt von einem JSON-Objekt ab.",
        "strings": "Schließe mit `ANSWER:` gefolgt von einer JSON-Liste von Zeichenketten ab, genau wie im Text "
                   "und in der Reihenfolge ihres Vorkommens.",
        "abstain": "Wenn sich die Aufgabe mit den vorliegenden Angaben nicht lösen lässt, antworte "
                   "`ANSWER: UNKNOWN`.",
        "done": "Erledigt.",
        "err_action": "ungültige Aktion: rufe ein Werkzeug auf oder schreibe eine abschließende Antwort",
        "err_tool": "unbekanntes Werkzeug: {name}",
        "err_args_object": "die Argumente müssen ein JSON-Objekt sein",
        "err_missing": "Argument fehlt: {key}",
        "err_unknown_arg": "unbekanntes Argument: {key}",
        "err_type": "falscher Typ für {key}: {expected} erwartet",
        "err_enum": "ungültiger Wert für {key}",
    },
    "fra": {
        "money": "Termine par une ligne de la forme `ANSWER: <montant>`, par exemple `ANSWER: {example}`.",
        "date": "Termine par une ligne de la forme `ANSWER: AAAA-MM-JJ`.",
        "datetime": "Termine par une ligne de la forme `ANSWER: AAAA-MM-JJ HH:MM`.",
        "integer": "Termine par une ligne de la forme `ANSWER: <nombre entier>`.",
        "text": "Termine par une ligne de la forme `ANSWER: <réponse>`.",
        "mapping": "Termine par `ANSWER:` suivi d'un objet JSON.",
        "strings": "Termine par `ANSWER:` suivi d'une liste JSON de chaînes, exactement telles qu'elles figurent "
                   "dans le texte et dans leur ordre d'apparition.",
        "abstain": "Si la tâche ne peut pas être résolue avec les informations disponibles, réponds "
                   "`ANSWER: UNKNOWN`.",
        "done": "Terminé.",
        "err_action": "action invalide : appelle un outil ou écris une réponse finale",
        "err_tool": "outil inconnu : {name}",
        "err_args_object": "les arguments doivent être un objet JSON",
        "err_missing": "argument manquant : {key}",
        "err_unknown_arg": "argument inconnu : {key}",
        "err_type": "type incorrect pour {key} : {expected} attendu",
        "err_enum": "valeur invalide pour {key}",
    },
    "pol": {
        "money": "Zakończ wierszem w formie `ANSWER: <kwota>`, na przykład `ANSWER: {example}`.",
        "date": "Zakończ wierszem w formie `ANSWER: RRRR-MM-DD`.",
        "datetime": "Zakończ wierszem w formie `ANSWER: RRRR-MM-DD GG:MM`.",
        "integer": "Zakończ wierszem w formie `ANSWER: <liczba całkowita>`.",
        "text": "Zakończ wierszem w formie `ANSWER: <odpowiedź>`.",
        "mapping": "Zakończ `ANSWER:`, a po nim obiektem JSON.",
        "strings": "Zakończ `ANSWER:`, a po nim listą JSON napisów, dokładnie w brzmieniu z tekstu i w kolejności "
                   "występowania.",
        "abstain": "Jeśli zadania nie da się rozwiązać na podstawie podanych informacji, odpowiedz "
                   "`ANSWER: UNKNOWN`.",
        "done": "Gotowe.",
        "err_action": "nieprawidłowa akcja: wywołaj narzędzie albo napisz odpowiedź końcową",
        "err_tool": "nieznane narzędzie: {name}",
        "err_args_object": "argumenty muszą być obiektem JSON",
        "err_missing": "brak argumentu: {key}",
        "err_unknown_arg": "nieznany argument: {key}",
        "err_type": "zły typ dla {key}: oczekiwano {expected}",
        "err_enum": "nieprawidłowa wartość dla {key}",
    },
    "fin": {
        "money": "Päätä rivillä muodossa `ANSWER: <summa>`, esimerkiksi `ANSWER: {example}`.",
        "date": "Päätä rivillä muodossa `ANSWER: VVVV-KK-PP`.",
        "datetime": "Päätä rivillä muodossa `ANSWER: VVVV-KK-PP TT:MM`.",
        "integer": "Päätä rivillä muodossa `ANSWER: <kokonaisluku>`.",
        "text": "Päätä rivillä muodossa `ANSWER: <vastaus>`.",
        "mapping": "Päätä merkinnällä `ANSWER:` ja sen perään JSON-objektilla.",
        "strings": "Päätä merkinnällä `ANSWER:` ja sen perään JSON-listalla merkkijonoja täsmälleen tekstin "
                   "kirjoitusasussa ja esiintymisjärjestyksessä.",
        "abstain": "Jos tehtävää ei voi ratkaista annettujen tietojen perusteella, vastaa `ANSWER: UNKNOWN`.",
        "done": "Valmis.",
        "err_action": "virheellinen toiminto: kutsu työkalua tai kirjoita lopullinen vastaus",
        "err_tool": "tuntematon työkalu: {name}",
        "err_args_object": "argumenttien on oltava JSON-objekti",
        "err_missing": "argumentti puuttuu: {key}",
        "err_unknown_arg": "tuntematon argumentti: {key}",
        "err_type": "väärä tyyppi kentälle {key}: odotettiin {expected}",
        "err_enum": "virheellinen arvo kentälle {key}",
    },
}

REVIEW: Dict[str, str] = {"eng": "author", "swe": "llm", "deu": "llm", "fra": "llm", "pol": "llm", "fin": "llm"}


def text(lang: str, key: str, **slots) -> str:
    table = STRINGS.get(lang, STRINGS["eng"])
    return table.get(key, STRINGS["eng"][key]).format(**slots)
