"""Amount due on an invoice, under the issuing subsidiary's national VAT rules.

Levels (meta.level):
  1  one VAT category; the rate is printed on each line
  2  mixed categories; rates printed on each line
  3  + line discounts and an earlier part payment; lines show only a product category, and the rates come from the
     company handbook excerpt for the issuing country (the model has to look them up)
  4  + a credit note (standard rate) and rounding of the amount due to whole currency units
  5  + intra-EU business customers: with the customer's VAT number on the invoice no VAT is charged (reverse
     charge); without it, the issuing country's rates apply
About 12 % of tasks are unanswerable (a price is missing, or a category is missing from the handbook); then the
only correct answer is `ANSWER: UNKNOWN`.

Languages: eng (group finance office, any subsidiary), swe (SE, FI), deu (DE), fra (FR), pol (PL), fin (FI).
"""
from __future__ import annotations

from eurl.contract import TypedEnvironment, TypedTask
from eurl.locales import load as load_locale
from eurl.money import format_money, round_half_up

LOCALES_FOR = {"eng": ("SE", "DE", "FR", "PL", "FI"), "swe": ("SE", "FI"), "deu": ("DE",), "fra": ("FR",),
               "pol": ("PL",), "fin": ("FI",)}
EU = ("SE", "DE", "FR", "PL", "FI")
# Base prices in euro cents; other currencies scale by a rough, fixed factor (the world is synthetic).
SCALE = {"EUR": 1, "SEK": 11, "PLN": 4}

ITEMS = [  # (category, base price range in cents, names per language)
    ("standard", (6000, 18000), {"eng": "Consulting hour", "swe": "Konsulttimme", "deu": "Beratungsstunde",
                                  "fra": "Heure de conseil", "pol": "Godzina konsultacji", "fin": "Konsulttituntti"}),
    ("standard", (500, 4000), {"eng": "Office supplies", "swe": "Kontorsmaterial", "deu": "Büromaterial",
                               "fra": "Fournitures de bureau", "pol": "Materiały biurowe", "fin": "Toimistotarvikkeet"}),
    ("standard", (2000, 9000), {"eng": "Software licence (month)", "swe": "Programlicens (månad)",
                                "deu": "Softwarelizenz (Monat)", "fra": "Licence logicielle (mois)",
                                "pol": "Licencja na oprogramowanie (miesiąc)", "fin": "Ohjelmistolisenssi (kk)"}),
    ("food", (1200, 3500), {"eng": "Coffee beans (kg)", "swe": "Kaffebönor (kg)", "deu": "Kaffeebohnen (kg)",
                            "fra": "Café en grains (kg)", "pol": "Kawa ziarnista (kg)", "fin": "Kahvipavut (kg)"}),
    ("accommodation", (7000, 16000), {"eng": "Hotel night", "swe": "Hotellnatt", "deu": "Hotelübernachtung",
                                      "fra": "Nuitée d'hôtel", "pol": "Nocleg w hotelu", "fin": "Hotelliyö"}),
    ("books", (1500, 6000), {"eng": "Printed book", "swe": "Tryckt bok", "deu": "Gedrucktes Buch",
                             "fra": "Livre imprimé", "pol": "Książka drukowana", "fin": "Painettu kirja"}),
    ("passenger_transport", (3000, 12000), {"eng": "Train ticket", "swe": "Tågbiljett", "deu": "Bahnfahrkarte",
                                            "fra": "Billet de train", "pol": "Bilet kolejowy", "fin": "Junalippu"}),
]
CATEGORY = {
    "standard": {"eng": "standard", "swe": "normal", "deu": "Regelsatz", "fra": "taux normal", "pol": "stawka podstawowa", "fin": "yleinen"},
    "food": {"eng": "food", "swe": "livsmedel", "deu": "Lebensmittel", "fra": "denrées alimentaires", "pol": "żywność", "fin": "elintarvikkeet"},
    "accommodation": {"eng": "accommodation", "swe": "hotell och logi", "deu": "Beherbergung", "fra": "hébergement", "pol": "zakwaterowanie", "fin": "majoitus"},
    "books": {"eng": "books", "swe": "böcker", "deu": "Bücher", "fra": "livres", "pol": "książki", "fin": "kirjat"},
    "passenger_transport": {"eng": "passenger transport", "swe": "persontransport", "deu": "Personenbeförderung", "fra": "transport de voyageurs", "pol": "przewóz osób", "fin": "henkilökuljetus"},
}

T = {
    "eng": {
        "intro": ["You work in the group finance office. Work out how much the customer {customer} has to pay on "
                  "invoice {number} from our subsidiary {seller} ({country}), dated {date}.",
                  "Group finance needs the outstanding amount on invoice {number}, issued by {seller} in {country} "
                  "to {customer} on {date}.",
                  "A colleague at {seller} ({country}) asks you to check invoice {number} of {date} to {customer}."],
        "head_rate": "| Line | Description | Qty | Unit price excl. VAT | VAT{disc} |",
        "head_cat": "| Line | Description | Qty | Unit price excl. VAT | VAT category{disc} |",
        "disc": ", discount", "discount": "discount {p} %",
        "rules": "Rules: line amount = quantity × unit price. Discounts are deducted from the line amount before VAT. "
                 "VAT is calculated per line on the amount after discount. Discount and VAT are rounded per line to "
                 "whole cents (minor units); exactly half rounds up.",
        "handbook": "Excerpt from the group finance handbook, {country}: VAT rates by category — {rates}. Each line "
                    "is priced at quantity × unit price; a line discount is taken off before VAT is computed on the "
                    "remainder. Round discounts and VAT on each line to the minor unit, halves upward.",
        "missing_price": "per separate quote",
        "credit": "A credit note of {amount} excluding VAT (standard rate) is to be deducted.",
        "paid": "The customer has already paid {amount} on this invoice.",
        "round": "The amount due is rounded to whole {unit}; a half rounds up.",
        "rc_rule": "Group policy: if the customer is a business in another EU member state and its VAT number is "
                   "shown on the invoice, no VAT is charged (reverse charge); otherwise the issuing country's rates "
                   "apply.",
        "buyer_vat": "Customer: {customer}, {city}, {buyer_country}; VAT number {vat}.",
        "buyer_novat": "Customer: {customer}, {city}, {buyer_country}; no VAT number on file.",
        "question": ["How much, including VAT, remains to be paid?", "What is the remaining amount due, VAT included?"],
        "unit": {"EUR": "euros", "SEK": "kronor", "PLN": "złoty"},
    },
    "swe": {
        "intro": ["Du arbetar på ekonomiavdelningen hos {seller} ({country}). Beräkna hur mycket kunden {customer} "
                  "ska betala på faktura {number} (fakturadatum {date}).",
                  "Ekonomichefen på {seller} ({country}) vill veta vad som återstår att betala på faktura {number} "
                  "till {customer}, daterad {date}.",
                  "Gå igenom faktura {number} från {seller} ({country}) till {customer}, daterad {date}."],
        "head_rate": "| Rad | Beskrivning | Antal | À-pris exkl. moms | Moms{disc} |",
        "head_cat": "| Rad | Beskrivning | Antal | À-pris exkl. moms | Momskategori{disc} |",
        "disc": ", rabatt", "discount": "rabatt {p} %",
        "rules": "Regler: radbelopp = antal × à-pris. Rabatt dras från radbeloppet före moms. Moms beräknas per rad "
                 "på beloppet efter rabatt. Rabatt och moms avrundas per rad till hela ören (minsta enhet), och exakt "
                 "en halv avrundas uppåt.",
        "handbook": "Utdrag ur koncernens ekonomihandbok, {country}: momssatser per kategori — {rates}. Varje rad "
                    "prissätts som antal × à-pris; en radrabatt dras av innan momsen beräknas på resten. Rabatt och "
                    "moms avrundas per rad till minsta enhet, halvor uppåt.",
        "missing_price": "enligt separat offert",
        "credit": "En kreditnota på {amount} exklusive moms (normalsats) ska dras av.",
        "paid": "Kunden har redan betalat {amount} på fakturan.",
        "round": "Beloppet att betala avrundas till hela {unit}; en halv avrundas uppåt.",
        "rc_rule": "Koncernens policy: om kunden är ett företag i ett annat EU-land och dess momsregistreringsnummer "
                   "står på fakturan tas ingen moms ut (omvänd skattskyldighet); annars gäller det fakturerande "
                   "landets momssatser.",
        "buyer_vat": "Kund: {customer}, {city}, {buyer_country}; momsregistreringsnummer {vat}.",
        "buyer_novat": "Kund: {customer}, {city}, {buyer_country}; inget momsregistreringsnummer registrerat.",
        "question": ["Vilket belopp, inklusive moms, återstår att betala?", "Hur mycket återstår att betala inklusive moms?"],
        "unit": {"EUR": "euro", "SEK": "kronor", "PLN": "złoty"},
    },
    "deu": {
        "intro": ["Du arbeitest in der Buchhaltung der {seller} ({country}). Berechne, wie viel der Kunde {customer} "
                  "auf die Rechnung {number} vom {date} zu zahlen hat.",
                  "Die Finanzleitung der {seller} ({country}) möchte wissen, welcher Betrag auf Rechnung {number} an "
                  "{customer} vom {date} noch offen ist.",
                  "Prüfe die Rechnung {number} der {seller} ({country}) an {customer} vom {date}."],
        "head_rate": "| Pos. | Beschreibung | Menge | Einzelpreis netto | USt.{disc} |",
        "head_cat": "| Pos. | Beschreibung | Menge | Einzelpreis netto | USt.-Kategorie{disc} |",
        "disc": ", Rabatt", "discount": "Rabatt {p} %",
        "rules": "Regeln: Positionsbetrag = Menge × Einzelpreis. Rabatte werden vor der Umsatzsteuer vom "
                 "Positionsbetrag abgezogen. Die Umsatzsteuer wird je Position auf den rabattierten Betrag berechnet. "
                 "Rabatt und Umsatzsteuer werden je Position auf volle Cent gerundet; genau ein halber Cent wird "
                 "aufgerundet.",
        "handbook": "Auszug aus dem Finanzhandbuch des Konzerns, {country}: Umsatzsteuersätze nach Kategorie — "
                    "{rates}. Jede Position kostet Menge × Einzelpreis; ein Positionsrabatt wird abgezogen, bevor die "
                    "Umsatzsteuer auf den Rest berechnet wird. Rabatt und Steuer je Position auf die kleinste "
                    "Einheit runden, Hälften aufrunden.",
        "missing_price": "laut gesondertem Angebot",
        "credit": "Eine Gutschrift über {amount} netto (Regelsatz) ist abzuziehen.",
        "paid": "Der Kunde hat auf diese Rechnung bereits {amount} gezahlt.",
        "round": "Der offene Betrag wird auf volle {unit} gerundet; die Hälfte wird aufgerundet.",
        "rc_rule": "Konzernrichtlinie: Ist der Kunde ein Unternehmen in einem anderen EU-Mitgliedstaat und steht "
                   "seine USt-IdNr. auf der Rechnung, wird keine Umsatzsteuer berechnet (Reverse-Charge); sonst "
                   "gelten die Sätze des Rechnungslandes.",
        "buyer_vat": "Kunde: {customer}, {city}, {buyer_country}; USt-IdNr. {vat}.",
        "buyer_novat": "Kunde: {customer}, {city}, {buyer_country}; keine USt-IdNr. hinterlegt.",
        "question": ["Welcher Betrag einschließlich Umsatzsteuer ist noch zu zahlen?",
                     "Wie hoch ist der noch offene Betrag inklusive Umsatzsteuer?"],
        "unit": {"EUR": "Euro", "SEK": "Kronen", "PLN": "Złoty"},
    },
    "fra": {
        "intro": ["Tu travailles au service comptable de {seller} ({country}). Calcule le montant que le client "
                  "{customer} doit payer sur la facture {number} du {date}.",
                  "La direction financière de {seller} ({country}) veut connaître le reste à payer de la facture "
                  "{number} adressée à {customer} le {date}.",
                  "Vérifie la facture {number} émise par {seller} ({country}) à {customer} le {date}."],
        "head_rate": "| Ligne | Désignation | Qté | Prix unitaire HT | TVA{disc} |",
        "head_cat": "| Ligne | Désignation | Qté | Prix unitaire HT | Catégorie de TVA{disc} |",
        "disc": ", remise", "discount": "remise {p} %",
        "rules": "Règles : montant de la ligne = quantité × prix unitaire. La remise est déduite du montant de la "
                 "ligne avant TVA. La TVA est calculée par ligne sur le montant après remise. Remise et TVA sont "
                 "arrondies par ligne au centime ; un demi-centime est arrondi au supérieur.",
        "handbook": "Extrait du manuel financier du groupe, {country} : taux de TVA par catégorie — {rates}. Chaque "
                    "ligne vaut quantité × prix unitaire ; la remise de ligne est déduite avant le calcul de la TVA "
                    "sur le reste. Arrondir remise et TVA par ligne à l'unité minimale, les moitiés vers le haut.",
        "missing_price": "selon devis séparé",
        "credit": "Un avoir de {amount} HT (taux normal) doit être déduit.",
        "paid": "Le client a déjà payé {amount} sur cette facture.",
        "round": "Le montant dû est arrondi à l'unité entière ({unit}) ; une moitié est arrondie au supérieur.",
        "rc_rule": "Politique du groupe : si le client est une entreprise d'un autre État membre de l'UE et que son "
                   "numéro de TVA figure sur la facture, aucune TVA n'est facturée (autoliquidation) ; sinon, les "
                   "taux du pays émetteur s'appliquent.",
        "buyer_vat": "Client : {customer}, {city}, {buyer_country} ; numéro de TVA {vat}.",
        "buyer_novat": "Client : {customer}, {city}, {buyer_country} ; aucun numéro de TVA enregistré.",
        "question": ["Quel montant, TVA comprise, reste à payer ?", "Combien reste-t-il à payer, TVA incluse ?"],
        "unit": {"EUR": "euro", "SEK": "couronne", "PLN": "złoty"},
    },
    "pol": {
        "intro": ["Pracujesz w dziale księgowości firmy {seller} ({country}). Oblicz, ile klient {customer} ma "
                  "zapłacić za fakturę {number} z dnia {date}.",
                  "Dyrektor finansowy {seller} ({country}) chce wiedzieć, ile pozostało do zapłaty na fakturze "
                  "{number} wystawionej dla {customer} w dniu {date}.",
                  "Sprawdź fakturę {number} wystawioną przez {seller} ({country}) dla {customer} w dniu {date}."],
        "head_rate": "| Lp. | Opis | Ilość | Cena jedn. netto | VAT{disc} |",
        "head_cat": "| Lp. | Opis | Ilość | Cena jedn. netto | Kategoria VAT{disc} |",
        "disc": ", rabat", "discount": "rabat {p} %",
        "rules": "Zasady: wartość pozycji = ilość × cena jednostkowa. Rabat odejmuje się od wartości pozycji przed "
                 "VAT. VAT liczy się dla każdej pozycji od kwoty po rabacie. Rabat i VAT zaokrągla się w każdej "
                 "pozycji do pełnych groszy; dokładnie pół grosza zaokrągla się w górę.",
        "handbook": "Fragment podręcznika finansowego grupy, {country}: stawki VAT według kategorii — {rates}. "
                    "Każda pozycja to ilość × cena jednostkowa; rabat pozycji odejmuje się przed obliczeniem VAT od "
                    "reszty. Rabat i VAT zaokrągla się w każdej pozycji do najmniejszej jednostki, połówki w górę.",
        "missing_price": "według osobnej oferty",
        "credit": "Należy odjąć fakturę korygującą na {amount} netto (stawka podstawowa).",
        "paid": "Klient zapłacił już {amount} za tę fakturę.",
        "round": "Kwotę do zapłaty zaokrągla się do pełnych {unit}; połowę zaokrągla się w górę.",
        "rc_rule": "Zasada grupy: jeśli klient jest firmą z innego państwa członkowskiego UE i jego numer VAT "
                   "widnieje na fakturze, nie nalicza się VAT (odwrotne obciążenie); w przeciwnym razie obowiązują "
                   "stawki kraju wystawienia.",
        "buyer_vat": "Klient: {customer}, {city}, {buyer_country}; numer VAT {vat}.",
        "buyer_novat": "Klient: {customer}, {city}, {buyer_country}; brak numeru VAT w kartotece.",
        "question": ["Jaka kwota, łącznie z VAT, pozostaje do zapłaty?", "Ile pozostało do zapłaty z VAT?"],
        "unit": {"EUR": "euro", "SEK": "koron", "PLN": "złotych"},
    },
    "fin": {
        "intro": ["Työskentelet yrityksen {seller} ({country}) taloushallinnossa. Laske, paljonko asiakas {customer} "
                  "maksaa laskusta {number} (päiväys {date}).",
                  "Yrityksen {seller} ({country}) talousjohtaja haluaa tietää, paljonko laskusta {number} asiakkaalle "
                  "{customer} ({date}) on vielä maksamatta.",
                  "Tarkista yrityksen {seller} ({country}) lasku {number} asiakkaalle {customer}, päiväys {date}."],
        "head_rate": "| Rivi | Kuvaus | Määrä | Yksikköhinta (veroton) | ALV{disc} |",
        "head_cat": "| Rivi | Kuvaus | Määrä | Yksikköhinta (veroton) | ALV-luokka{disc} |",
        "disc": ", alennus", "discount": "alennus {p} %",
        "rules": "Säännöt: rivin summa = määrä × yksikköhinta. Alennus vähennetään rivin summasta ennen arvonlisäveroa. "
                 "Arvonlisävero lasketaan riveittäin alennuksen jälkeisestä summasta. Alennus ja vero pyöristetään "
                 "riveittäin senttiin; tasan puolikas pyöristetään ylöspäin.",
        "handbook": "Ote konsernin taloushallinnon käsikirjasta, {country}: arvonlisäverokannat luokittain — {rates}. "
                    "Rivin hinta on määrä × yksikköhinta; rivialennus vähennetään ennen kuin vero lasketaan "
                    "jäljelle jäävästä. Alennus ja vero pyöristetään riveittäin pienimpään yksikköön, puolikkaat ylöspäin.",
        "missing_price": "erillisen tarjouksen mukaan",
        "credit": "Hyvityslasku {amount} (veroton, yleinen verokanta) vähennetään.",
        "paid": "Asiakas on jo maksanut laskusta {amount}.",
        "round": "Maksettava summa pyöristetään täysiin {unit}; puolikas pyöristetään ylöspäin.",
        "rc_rule": "Konsernin ohje: jos asiakas on yritys toisessa EU-jäsenvaltiossa ja sen ALV-tunniste on "
                   "laskussa, arvonlisäveroa ei veloiteta (käännetty verovelvollisuus); muuten sovelletaan "
                   "laskuttavan maan verokantoja.",
        "buyer_vat": "Asiakas: {customer}, {city}, {buyer_country}; ALV-tunniste {vat}.",
        "buyer_novat": "Asiakas: {customer}, {city}, {buyer_country}; ALV-tunnistetta ei ole rekisterissä.",
        "question": ["Paljonko arvonlisäveroineen on vielä maksettava?", "Mikä on jäljellä oleva maksettava summa veroineen?"],
        "unit": {"EUR": "euroihin", "SEK": "kruunuihin", "PLN": "zlotyihin"},
    },
}
COUNTRY = {
    "SE": {"eng": "Sweden", "swe": "Sverige", "deu": "Schweden", "fra": "Suède", "pol": "Szwecja", "fin": "Ruotsi"},
    "DE": {"eng": "Germany", "swe": "Tyskland", "deu": "Deutschland", "fra": "Allemagne", "pol": "Niemcy", "fin": "Saksa"},
    "FR": {"eng": "France", "swe": "Frankrike", "deu": "Frankreich", "fra": "France", "pol": "Francja", "fin": "Ranska"},
    "PL": {"eng": "Poland", "swe": "Polen", "deu": "Polen", "fra": "Pologne", "pol": "Polska", "fin": "Puola"},
    "FI": {"eng": "Finland", "swe": "Finland", "deu": "Finnland", "fra": "Finlande", "pol": "Finlandia", "fin": "Suomi"},
}


def _company(rng, locale) -> str:
    return f"{rng.choice(locale.company_stems)} {rng.choice(locale.company_suffixes)}"


def _pct(bp: int, decimal: str) -> str:
    return (f"{bp // 100}" if bp % 100 == 0 else f"{bp / 100:g}".replace(".", decimal)) + " %"


def compute_due(lines, vat_bp, credit_net=0, credit_bp=0, paid=0, round_to=0, reverse_charge=False):
    """Ground truth. lines: [(qty, unit_price, discount_pct, category)] in minor units."""
    total = 0
    for qty, price, discount, category in lines:
        gross = qty * price
        net = gross - round_half_up(gross * discount, 100)
        vat = 0 if reverse_charge else round_half_up(net * vat_bp[category], 10000)
        total += net + vat
    credit_vat = 0 if reverse_charge else round_half_up(credit_net * credit_bp, 10000)
    due = total - credit_net - credit_vat - paid
    if round_to:
        due = round_half_up(due, round_to) * round_to
    return due


class FinanceAmountDue(TypedEnvironment):
    id = "finance_amount_due"
    abstention = True
    languages = tuple(T)

    def generate(self, rng, language=None) -> TypedTask:
        lang = language or rng.choice(self.languages)
        country = rng.choice(LOCALES_FOR[lang])
        loc = load_locale(country)
        t, f = T[lang], loc.money
        scale = SCALE[f.currency]
        level = rng.choice([1, 2, 3, 4, 5])
        pool = [it for it in ITEMS if it[0] == "standard"] if level == 1 else ITEMS
        n_lines = rng.randint(2, len(pool) if level == 1 else 3 + min(level, 3))
        lines = []
        for category, (lo, hi), names in rng.sample(pool, n_lines):
            price = rng.randint(lo, hi) * scale + rng.choice([0, 0, 0, 50, 7, 33, 99]) * (scale if scale > 1 else 1)
            discount = rng.choice([0, 0, 5, 10, 15, 20, 25]) if level >= 3 else 0
            lines.append((rng.randint(1, 12), price, discount, category, names[lang]))
        seller, customer = _company(rng, loc), None
        reverse_charge, buyer_line = False, ""
        if level == 5:
            buyer_country = rng.choice([c for c in EU if c != country])
            bloc = load_locale(buyer_country)
            customer = _company(rng, bloc)
            if rng.random() < 0.6:
                reverse_charge = True
                vat_number = bloc.vat_id(rng, bloc.company_id(rng))
                buyer_line = t["buyer_vat"].format(customer=customer, city=rng.choice(bloc.cities),
                                                   buyer_country=COUNTRY[buyer_country][lang], vat=vat_number)
            else:
                buyer_line = t["buyer_novat"].format(customer=customer, city=rng.choice(bloc.cities),
                                                     buyer_country=COUNTRY[buyer_country][lang])
        else:
            customer = _company(rng, loc)
            while customer == seller:
                customer = _company(rng, loc)
        round_to = 10 ** f.minor_digits if level >= 4 else 0
        vat_bp = loc.vat_bp
        credit_net = 0
        if level >= 4:  # a credit note of at most 40 % of the invoice's net amount, in whole currency units
            net_total = sum(q * p - round_half_up(q * p * d, 100) for q, p, d, _, _ in lines)
            credit_net = max(1, rng.randint(1, max(1, net_total * 4 // 10 // 100))) * 100
        due_before_paid = compute_due([l[:4] for l in lines], vat_bp, credit_net, vat_bp["standard"], 0, 0,
                                      reverse_charge)
        paid = round_half_up(due_before_paid * rng.choice([20, 25, 30, 40, 50]), 100) \
            if level >= 3 and rng.random() < .6 and due_before_paid > 0 else 0
        due = compute_due([l[:4] for l in lines], vat_bp, credit_net, vat_bp["standard"], paid, round_to,
                          reverse_charge)

        # unanswerable variants: a hidden price, or (handbook levels) a category missing from the excerpt
        missing = rng.random() < .12
        hidden_line, dropped_category = None, None
        if missing:
            if level >= 3 and rng.random() < .5:
                dropped_category = rng.choice(sorted({l[3] for l in lines}))
            else:
                hidden_line = rng.randrange(len(lines))
        number = f"2025-{rng.randint(1000, 9999)}"
        date = f"2025-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}"
        rows = []
        for i, (qty, price, discount, category, name) in enumerate(lines):
            shown_price = t["missing_price"] if i == hidden_line else format_money(price, f)
            disc = f", {t['discount'].format(p=discount)}" if discount else ""
            vat_cell = _pct(vat_bp[category], f.decimal) if level <= 2 else CATEGORY[category][lang]
            rows.append(f"| {i + 1} | {name} | {qty} | {shown_price} | {vat_cell}{disc} |")
        head = (t["head_rate"] if level <= 2 else t["head_cat"]).format(disc=t["disc"] if level >= 3 else "")
        text = [rng.choice(t["intro"]).format(customer=customer, number=number, seller=seller,
                                              country=COUNTRY[country][lang], date=date)]
        if buyer_line:
            text.append(buyer_line)
        text += ["", head, "|---|---|---|---|---|", *rows, ""]
        if level <= 2:
            text.append(t["rules"])
        else:
            shown = [c for c in CATEGORY if c != dropped_category]
            rng.shuffle(shown)
            rates = "; ".join(f"{CATEGORY[c][lang]} {_pct(vat_bp[c], f.decimal)}" for c in shown)
            text.append(t["handbook"].format(country=COUNTRY[country][lang], rates=rates))
        if level == 5:
            text.append(t["rc_rule"])
        if credit_net:
            text.append(t["credit"].format(amount=format_money(credit_net, f)))
        if paid:
            text.append(t["paid"].format(amount=format_money(paid, f)))
        if round_to:
            text.append(t["round"].format(unit=t["unit"][f.currency]))
        text.append(rng.choice(t["question"]))
        spec = {"type": "abstain"} if missing else {"type": "money", "value": due, "minor_digits": f.minor_digits}
        meta = {"level": level, "unanswerable": missing, "lines": len(lines), "locale": country,
                "reverse_charge": reverse_charge, "currency": f.currency,
                # for probes: the same invoice under the wrong treatment
                "due_other_treatment": None if missing else compute_due(
                    [l[:4] for l in lines], vat_bp, credit_net, vat_bp["standard"], paid, round_to,
                    not reverse_charge) if level == 5 else None,
                "due_without_discounts": None if missing or level < 3 else compute_due(
                    [(q, p, 0, c) for q, p, _, c, _ in lines], vat_bp, credit_net, vat_bp["standard"], paid,
                    round_to, reverse_charge),
                # the same invoice under another country's VAT rates (the model applied the wrong locale)
                "due_other_country": None if missing or reverse_charge else compute_due(
                    [l[:4] for l in lines], load_locale(next(c for c in EU if c != country)).vat_bp, credit_net,
                    load_locale(next(c for c in EU if c != country)).vat_bp["standard"], paid, round_to, False)}
        return TypedTask("\n".join(text), spec, "money", lang, country, meta)

    def extra_probes(self, prompt: str) -> dict:
        m, f = self._task.meta, load_locale(self._task.locale).money
        probes = {}
        if m.get("due_other_treatment") is not None:
            probes["wrong_vat_treatment"] = f"ANSWER: {format_money(m['due_other_treatment'], f)}"
        if m.get("due_without_discounts") is not None:
            probes["ignore_discounts"] = f"ANSWER: {format_money(m['due_without_discounts'], f)}"
        if m.get("due_other_country") is not None and m["due_other_country"] != self._task.spec.get("value"):
            probes["wrong_country_vat"] = f"ANSWER: {format_money(m['due_other_country'], f)}"
        if not m["unanswerable"] and self._task.spec["type"] == "money":
            probes["off_by_one_unit"] = f"ANSWER: {format_money(self._task.spec['value'] - 100, f)}"
        return probes


def create():
    return FinanceAmountDue()
