"""Georgia (non-EU)."""
import string

from eurl.calendar import fixed, orthodox_rule
from eurl.locales import Locale
from eurl.money import NBSP, MoneyFormat

HOLIDAYS = (
    fixed(1, 1, {"kat": "ახალი წელი"}),
    fixed(1, 2, {"kat": "ახალი წელი (მეორე დღე)"}),
    fixed(1, 7, {"kat": "შობა ქრისტესი"}),
    fixed(1, 19, {"kat": "ნათლისღება"}),
    fixed(3, 3, {"kat": "დედის დღე"}),
    fixed(3, 8, {"kat": "ქალთა საერთაშორისო დღე"}),
    fixed(4, 9, {"kat": "ეროვნული ერთიანობის დღე"}),
    orthodox_rule(-2, {"kat": "წითელი პარასკევი"}),
    orthodox_rule(-1, {"kat": "დიდი შაბათი"}),
    orthodox_rule(0, {"kat": "აღდგომა"}),
    orthodox_rule(1, {"kat": "აღდგომის ორშაბათი (მიცვალებულთა მოხსენიების დღე)"}),
    fixed(5, 9, {"kat": "ფაშიზმზე გამარჯვების დღე"}),
    fixed(5, 12, {"kat": "წმინდა ანდრია პირველწოდებულის დღე"}),
    fixed(5, 17, {"kat": "ოჯახის სიწმინდისა და მშობლების პატივისცემის დღე"}, since=2025),
    fixed(5, 26, {"kat": "დამოუკიდებლობის დღე"}),
    fixed(8, 28, {"kat": "მარიამობა"}),
    fixed(10, 14, {"kat": "სვეტიცხოვლობა (მცხეთობა)"}),
    fixed(11, 23, {"kat": "გიორგობა"}),
    # One-off days off declared by government decree.
    fixed(5, 17, {"kat": "უქმე დღე"}, since=2024, until=2024),
    fixed(8, 29, {"kat": "უქმე დღე"}, since=2025, until=2025),
)


# --- Identification code of a legal entity (9 digits). No check-digit algorithm is published and python-stdnum
# has no Georgian module; the generator uses the 4xxxxxxxx series of entities registered at the Public Registry
# since 2008 and the validator checks the format. The same code is the VAT number. ----------------------------------

def company_code(rng) -> str:
    return "4" + str(rng.randint(0, 4)) + "".join(rng.choice(string.digits) for _ in range(7))


def vat_id(rng, company: str) -> str:
    return company


def vat_id_valid(value: str) -> bool:
    s = value.replace(" ", "")
    return len(s) == 9 and s.isdigit() and s[0] in "1234"


def invoice_reference(rng) -> str:
    """No national structured reference: the invoice number is quoted as the payment purpose."""
    return f"ინვ-{rng.randint(1, 999999):06d}"


LOCALE = Locale(
    country="GE", name="Georgia", languages=("kat",),
    money=MoneyFormat("GEL", "₾", ",", NBSP),
    timezone="Asia/Tbilisi",
    holidays=HOLIDAYS,
    vat_bp={c: 1800 for c in ("standard", "food", "accommodation", "books", "passenger_transport", "restaurant")},
    vat_as_of="2025",
    vat_source="საქართველოს საგადასახადო კოდექსი, მუხლი 169 (single VAT rate 18 %); Revenue Service of Georgia "
               "(rs.ge)",
    company_id=company_code, vat_id=vat_id, vat_id_valid=vat_id_valid,
    payment_reference=invoice_reference, payment_reference_name={"kat": "ინვოისის ნომერი"},
    company_suffixes=("შპს", "სს"),
    company_stems=("ვაზი", "მთის წყარო", "ლურჯი ტბა", "თეთრი ქვა", "ნაძვი", "ოქროს მარცვალი", "მზიანი ველი",
                   "ბროწეული", "ცისკარი", "ჭადარი"),
    first_names=("ნინო", "გიორგი", "მარიამ", "დავით", "ანა", "ლუკა", "ელენე", "ნიკოლოზ", "თამარ", "ლევან", "სალომე",
                 "ირაკლი"),
    last_names=("ბერიძე", "კაპანაძე", "გელაშვილი", "მაისურაძე", "გიორგაძე", "ლომიძე", "წიკლაური", "ბოლქვაძე",
                "კვარაცხელია", "ნიკოლაიშვილი", "ხუციშვილი", "შენგელია"),
    cities=("თბილისი", "ქუთაისი", "ბათუმი", "რუსთავი", "ზუგდიდი", "ფოთი", "თელავი", "ახალციხე"),
    eu_member=False,
    price_scale=3,
    office_hours=("10:00", "19:00"), lunch=("13:00", "14:00"),
    notes=[
        "Non-EU: one VAT (დღგ) rate of 18 % (no reduced rates; some supplies are exempt); every category uses it.",
        "Holidays: Labour Code of Georgia art. 30 (17 May added from 2025). One-off days off declared by government "
        "decree (2024-05-17, 2025-08-29) are modelled as single-year rules.",
        "Company/VAT number: 9-digit identification code; no published check digit, format-only validation.",
        "Payment reference: no national structured reference; the invoice number is quoted.",
        "Legal form: Georgian usage puts the form first (შპს „ვაზი“); the generator appends it.",
    ],
)
