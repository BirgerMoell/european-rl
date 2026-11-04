"""Synthetic company and VAT identifiers with each country's check-digit rule.

Generated numbers are formally valid but invented; nothing is looked up in a real register. Personal identity
numbers are not generated here (environments that need a person identifier use clearly synthetic test series per
locale pack).
"""
from __future__ import annotations

import random
import string

from eurl.banking import luhn_digit


def _digits(rng: random.Random, n: int, first_nonzero: bool = False) -> str:
    head = str(rng.randint(1, 9)) if first_nonzero else rng.choice(string.digits)
    return head + "".join(rng.choice(string.digits) for _ in range(n - 1))


# --- Sweden: organisationsnummer (Luhn), VAT = SE + org nr + 01 ----------------------------------------------------

def se_org(rng: random.Random) -> str:
    base = "55" + _digits(rng, 7)                 # 55xxxx: aktiebolag series
    return base[:6] + "-" + base[6:] + luhn_digit(base)


def se_vat(org: str) -> str:
    return "SE" + org.replace("-", "") + "01"


def se_vat_valid(vat: str) -> bool:
    s = vat.replace(" ", "")
    from eurl.banking import luhn_valid
    return len(s) == 14 and s.startswith("SE") and s.endswith("01") and luhn_valid(s[2:12])


# --- Germany: USt-IdNr, ISO 7064 MOD 11,10 --------------------------------------------------------------------------

def _mod11_10(digits: str) -> str:
    product = 10
    for ch in digits:
        total = (int(ch) + product) % 10 or 10
        product = (2 * total) % 11
    return str((11 - product) % 10)


def de_vat(rng: random.Random) -> str:
    base = _digits(rng, 8, first_nonzero=True)
    return "DE" + base + _mod11_10(base)


def de_vat_valid(vat: str) -> bool:
    s = vat.replace(" ", "")
    return len(s) == 11 and s.startswith("DE") and s[2:].isdigit() and s[2] != "0" and _mod11_10(s[2:10]) == s[10]


# --- France: SIREN (Luhn), TVA intracom = FR + key + SIREN ----------------------------------------------------------

def fr_siren(rng: random.Random) -> str:
    base = _digits(rng, 8, first_nonzero=True)
    return base + luhn_digit(base)


def fr_vat(siren: str) -> str:
    key = (12 + 3 * (int(siren) % 97)) % 97
    return f"FR{key:02d}{siren}"


def fr_vat_valid(vat: str) -> bool:
    s = vat.replace(" ", "")
    if len(s) != 13 or not s.startswith("FR") or not s[2:].isdigit():
        return False
    siren = s[4:]
    from eurl.banking import luhn_valid
    return luhn_valid(siren) and int(s[2:4]) == (12 + 3 * (int(siren) % 97)) % 97


# --- Poland: NIP, weights 6 5 7 2 3 4 5 6 7, mod 11 (10 is not allowed) -----------------------------------------------

_PL_W = (6, 5, 7, 2, 3, 4, 5, 6, 7)


def pl_nip(rng: random.Random) -> str:
    while True:
        base = _digits(rng, 9, first_nonzero=True)
        check = sum(int(d) * w for d, w in zip(base, _PL_W)) % 11
        if check != 10:
            return base + str(check)


def pl_vat(nip: str) -> str:
    return "PL" + nip


def pl_nip_valid(nip: str) -> bool:
    s = nip.replace("-", "").replace(" ", "")
    if s.startswith("PL"):
        s = s[2:]
    if len(s) != 10 or not s.isdigit():
        return False
    check = sum(int(d) * w for d, w in zip(s[:9], _PL_W)) % 11
    return check != 10 and check == int(s[9])


# --- Finland: Y-tunnus, weights 7 9 10 5 8 4 2, mod 11; VAT = FI + 8 digits --------------------------------------------

_FI_W = (7, 9, 10, 5, 8, 4, 2)


def fi_ytunnus(rng: random.Random) -> str:
    while True:
        base = _digits(rng, 7, first_nonzero=True)
        r = sum(int(d) * w for d, w in zip(base, _FI_W)) % 11
        if r == 1:
            continue
        return f"{base}-{0 if r == 0 else 11 - r}"


def fi_vat(ytunnus: str) -> str:
    return "FI" + ytunnus.replace("-", "")


def fi_ytunnus_valid(value: str) -> bool:
    s = value.replace("-", "").replace(" ", "")
    if s.startswith("FI"):
        s = s[2:]
    if len(s) != 8 or not s.isdigit():
        return False
    r = sum(int(d) * w for d, w in zip(s[:7], _FI_W)) % 11
    return r != 1 and int(s[7]) == (0 if r == 0 else 11 - r)
