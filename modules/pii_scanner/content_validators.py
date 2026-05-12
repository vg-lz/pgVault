import re
from typing import Callable

_CURP_RE = re.compile(
    r"^[A-Z]{1}[AEIOU]{1}[A-Z]{2}"
    r"\d{6}"
    r"[HM]{1}"
    r"(AS|BC|BS|CC|CS|CH|CL|CM|DF|DG|GT|GR|HG|JC|MC|MN|MS|NT|NL|OC|PL|QT|QR|SP|SL|SR|TC|TS|TL|VZ|YN|ZS|NE)"
    r"[B-DF-HJ-NP-TV-Z]{3}"
    r"[A-Z0-9]{1}"
    r"\d{1}$",
    re.I
)


def validate_curp(value: str) -> bool:
    value = value.strip().upper()
    if len(value) != 18:
        return False
    return bool(_CURP_RE.match(value))


_RFC_FISICA_RE = re.compile(r"^[A-Z]{4}\d{6}[A-Z0-9]{3}$", re.I)
_RFC_MORAL_RE = re.compile(r"^[A-Z]{3}\d{6}[A-Z0-9]{3}$", re.I)


def validate_rfc(value: str) -> bool:
    value = value.strip().upper()
    return bool(_RFC_FISICA_RE.match(value) or _RFC_MORAL_RE.match(value))


_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")


def validate_email(value: str) -> bool:
    value = value.strip()
    if len(value) > 254:
        return False
    return bool(_EMAIL_RE.match(value))


def validate_card_number(value: str) -> bool:
    digits = re.sub(r"[\s\-]", "", value)
    if not digits.isdigit():
        return False
    if not (13 <= len(digits) <= 19):
        return False
    total = 0
    reverse_digits = digits[::-1]
    for i, d in enumerate(reverse_digits):
        n = int(d)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def validate_cvv(value: str) -> bool:
    return bool(re.match(r"^\d{3,4}$", value.strip()))


def validate_clabe(value: str) -> bool:
    value = re.sub(r"\s", "", value)
    if not re.match(r"^\d{18}$", value):
        return False
    weights = [3, 7, 1, 3, 7, 1, 3, 7, 1, 3, 7, 1, 3, 7, 1, 3, 7]
    total = sum(int(value[i]) * weights[i] for i in range(17))
    control = (10 - (total % 10)) % 10
    return control == int(value[17])


def validate_phone_mx(value: str) -> bool:
    value = re.sub(r"[\s\-\(\)]", "", value.strip())
    return bool(re.match(r"^(\+?52)?[1-9]\d{9}$", value))


def validate_token(value: str) -> bool:
    value = value.strip()
    if len(value) < 20:
        return False
    has_upper = any(c.isupper() for c in value)
    has_lower = any(c.islower() for c in value)
    has_digit = any(c.isdigit() for c in value)
    return has_upper and has_lower and has_digit


def validate_ssn(value: str) -> bool:
    value = re.sub(r"\s", "", value)
    return bool(re.match(r"^\d{11}$", value))


VALIDATORS: dict[str, Callable[[str], bool]] = {
    "CVV":          validate_cvv,
    "CARD_NUMBER":  validate_card_number,
    "PASSWORD":     lambda v: len(v.strip()) > 0,
    "CURP":         validate_curp,
    "RFC":          validate_rfc,
    "EMAIL":        validate_email,
    "PHONE":        validate_phone_mx,
    "TOKEN":        validate_token,
    "CLABE":        validate_clabe,
    "SSN":          validate_ssn,
    "DATE_OF_BIRTH": lambda v: bool(re.match(r"\d{4}-\d{2}-\d{2}", v.strip())),
    "FULL_NAME":    lambda v: len(v.strip().split()) >= 2,
}


def validate_content(value: str, data_type: str) -> bool:
    if not value or not isinstance(value, str):
        return False
    validator = VALIDATORS.get(data_type.upper())
    if validator is None:
        return False
    try:
        return validator(value)
    except Exception:
        return False


def match_ratio(sample: list[str], data_type: str) -> float:
    if not sample:
        return 0.0
    valid = sum(1 for v in sample if validate_content(str(v), data_type))
    return valid / len(sample)