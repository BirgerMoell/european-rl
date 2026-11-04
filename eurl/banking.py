"""Payment identifiers used across Europe, generated synthetically with valid check digits.

- IBAN (ISO 13616): country length and BBAN structure from the SWIFT IBAN registry, ISO 7064 MOD 97-10 check
  digits. National check digits inside the BBAN are not computed (they do not affect IBAN validity), so a
  generated IBAN is formally valid but belongs to no real account.
- RF creditor reference (ISO 11649), the SEPA-wide structured reference.
- National structured references: Swedish OCR (Luhn), Finnish viitenumero (7-3-1), Norwegian KID (MOD10 / Luhn),
  Belgian structured communication (+++ddd/dddd/ddddd+++, MOD 97).
"""
from __future__ import annotations

import random
import re
import string
from typing import Dict

# BBAN structure in SWIFT notation: n = digits, a = upper-case letters, c = alphanumeric; "0" is a fixed zero.
BBAN: Dict[str, str] = {
    "AL": "8n16c", "AT": "16n", "BA": "16n", "BE": "12n", "BG": "4a6n8c", "CY": "8n16c", "CZ": "20n",
    "DE": "18n", "DK": "14n", "EE": "16n", "ES": "20n", "FI": "14n", "FR": "10n11c2n", "GE": "2a16n",
    "GR": "7n16c", "HR": "17n", "HU": "24n", "IE": "4a14n", "IS": "22n", "IT": "1a10n12c", "LT": "16n",
    "LU": "3n13c", "LV": "4a13c", "MK": "3n10c2n", "MT": "4a5n18c", "NL": "4a10n", "NO": "11n", "PL": "24n",
    "PT": "21n", "RO": "4a16c", "RS": "18n", "SE": "20n", "SI": "15n", "SK": "20n", "TR": "5n1z16c",
    "UA": "6n19c",
}
IBAN_LENGTH: Dict[str, int] = {
    "AL": 28, "AT": 20, "BA": 20, "BE": 16, "BG": 22, "CY": 28, "CZ": 24, "DE": 22, "DK": 18, "EE": 20,
    "ES": 24, "FI": 18, "FR": 27, "GE": 22, "GR": 27, "HR": 21, "HU": 28, "IE": 22, "IS": 26, "IT": 27,
    "LT": 20, "LU": 20, "LV": 21, "MK": 19, "MT": 31, "NL": 18, "NO": 15, "PL": 28, "PT": 25, "RO": 24,
    "RS": 22, "SE": 24, "SI": 19, "SK": 24, "TR": 26, "UA": 29,
}
_CHARSETS = {"n": string.digits, "a": string.ascii_uppercase, "c": string.digits + string.ascii_uppercase, "z": "0"}


def _bban(rng: random.Random, pattern: str) -> str:
    out = []
    for count, kind in re.findall(r"(\d+)([nacz])", pattern):
        out.extend(rng.choice(_CHARSETS[kind]) for _ in range(int(count)))
    return "".join(out)


def _mod97(text: str) -> int:
    """ISO 7064 MOD 97-10 over an alphanumeric string (letters A=10 … Z=35)."""
    digits = "".join(str(int(ch, 36)) for ch in text)
    remainder = 0
    for start in range(0, len(digits), 9):
        remainder = int(str(remainder) + digits[start:start + 9]) % 97
    return remainder


def iban(rng: random.Random, country: str) -> str:
    bban = _bban(rng, BBAN[country])
    check = 98 - _mod97(bban + country + "00")
    return f"{country}{check:02d}{bban}"


def iban_valid(value: str) -> bool:
    s = re.sub(r"\s+", "", value).upper()
    if len(s) < 5 or not s[:2].isalpha() or s[:2] not in IBAN_LENGTH or len(s) != IBAN_LENGTH[s[:2]]:
        return False
    if not s.isalnum():
        return False
    return _mod97(s[4:] + s[:4]) == 1


def iban_print(value: str) -> str:
    """Paper format: groups of four."""
    s = re.sub(r"\s+", "", value)
    return " ".join(s[i:i + 4] for i in range(0, len(s), 4))


# --- ISO 11649 RF creditor reference ---------------------------------------------------------------------------

def rf_reference(rng: random.Random, length: int = 10) -> str:
    body = "".join(rng.choice(string.digits) for _ in range(length))
    check = 98 - _mod97(body + "RF00")
    return f"RF{check:02d}{body}"


def rf_valid(value: str) -> bool:
    s = re.sub(r"\s+", "", value).upper()
    return bool(re.fullmatch(r"RF\d{2}[0-9A-Z]{1,21}", s)) and _mod97(s[4:] + s[:4]) == 1


# --- National references ---------------------------------------------------------------------------------------

def luhn_digit(digits: str) -> str:
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2 == 0:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return str((10 - total % 10) % 10)


def luhn_valid(number: str) -> bool:
    return number.isdigit() and len(number) > 1 and luhn_digit(number[:-1]) == number[-1]


def ocr_se(rng: random.Random, base_length: int = 8) -> str:
    """Swedish OCR with length digit and Luhn check digit (the 'length + check' variant)."""
    base = "".join(rng.choice(string.digits) for _ in range(base_length))
    length_digit = str((base_length + 2) % 10)
    return base + length_digit + luhn_digit(base + length_digit)


def kid_no(rng: random.Random, base_length: int = 9) -> str:
    """Norwegian KID with MOD10 (Luhn) check digit."""
    base = "".join(rng.choice(string.digits) for _ in range(base_length))
    return base + luhn_digit(base)


def viitenumero_fi(rng: random.Random, base_length: int = 9) -> str:
    """Finnish national reference number: weights 7, 3, 1 from the right."""
    base = str(rng.randint(1, 9)) + "".join(rng.choice(string.digits) for _ in range(base_length - 1))
    return base + _fi_check(base)


def _fi_check(base: str) -> str:
    weights = (7, 3, 1)
    total = sum(int(d) * weights[i % 3] for i, d in enumerate(reversed(base)))
    return str((10 - total % 10) % 10)


def viitenumero_valid(value: str) -> bool:
    s = value.replace(" ", "")
    return s.isdigit() and 4 <= len(s) <= 20 and _fi_check(s[:-1]) == s[-1]


def ogm_be(rng: random.Random) -> str:
    """Belgian structured communication: 10 digits + MOD 97 (97 when the remainder is 0), shown +++ddd/dddd/ddddd+++."""
    base = "".join(rng.choice(string.digits) for _ in range(10))
    check = int(base) % 97 or 97
    s = f"{base}{check:02d}"
    return f"+++{s[:3]}/{s[3:7]}/{s[7:]}+++"


def ogm_valid(value: str) -> bool:
    s = re.sub(r"[^0-9]", "", value)
    return len(s) == 12 and (int(s[:10]) % 97 or 97) == int(s[10:])
