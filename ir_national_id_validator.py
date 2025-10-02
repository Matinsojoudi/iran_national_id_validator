# ir_national_id_validator.py
"""
ماژول تک‌فایلی برای بررسی صحت کد ملی ایرانی (Iranian National ID).

توابع اصلی:
- normalize_national_id(s: str) -> str
    ورودی را نرمالایز می‌کند (حذف فاصله، تبدیل ارقام فارسی/عربی به لاتین، حذف کاراکترهای غیررقمی)
    و رشتهٔ حاصل را برمی‌گرداند.

- is_valid_national_id(s: str) -> (bool, Optional[str], Optional[str])
    بررسی کامل انجام می‌دهد و سه‌تایی برمی‌گرداند:
    (valid_flag, reason_if_invalid_or_None, normalized_code_or_None)

    دلایل ممکن (مثال):
      - 'empty'                -> ورودی خالی بود
      - 'length_or_not_digits' -> پس از نرمال‌سازی طول != 10 یا شامل غیررقم است
      - 'all_same_digits'      -> تمام ارقام یکسان (مثل "1111111111")
      - 'checksum'             -> مهره کنترل (کنترل‌دیجیت) نادرست است

- validate_or_raise(s: str) -> str
    مانند is_valid ولی اگر نامعتبر بود، خطا (ValueError) می‌اندازد و در صورت معتبر بودن کد نرمال‌شده را بازمی‌گرداند.

همچنین این فایل شامل CLI ساده است:
    python ir_national_id_validator.py <national_id>
"""
from typing import Tuple, Optional
import re
import sys

# نگاشت ارقام فارسی و عربی به انگلیسی
_DIGIT_MAP = {
    '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
    '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9',
    '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
    '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9',
}

# مجموعه‌ی رشته‌هایی که تمام ارقام یکسان هستند (نا معتبر)
_INVALID_SAME_DIGITS = {str(i) * 10 for i in range(10)}

# الگوی 10 رقم لاتین
_RE_10_DIGITS = re.compile(r'^\d{10}$')


def normalize_national_id(s: Optional[str]) -> str:
    """
    ورودی s را نرمالایز می‌کند:
      - None -> ''
      - تبدیل ارقام فارسی/عربی به لاتین
      - حذف هر کاراکتر غیررقمی
      - حذف فضاهای اضافی

    خروجی: رشته‌ای متشکل از فقط ارقام (ممکن است طول آن 10 یا غیر 10 باشد).
    """
    if s is None:
        return ''
    s = str(s).strip()
    if not s:
        return ''

    # تبدیل کاراکتر به کاراکتر برای نگه‌داشتن ترتیب و جایگزینی ارقام فارسی
    out_chars = []
    for ch in s:
        if ch in _DIGIT_MAP:
            out_chars.append(_DIGIT_MAP[ch])
        else:
            out_chars.append(ch)
    joined = ''.join(out_chars)

    # حذف همه چیز به جز ارقام لاتین
    normalized = re.sub(r'[^0-9]', '', joined)
    return normalized


def _checksum_ok(code10: str) -> bool:
    """
    محاسبهٔ مهرهٔ کنترلی:
    - code10 باید 10 رقم باشد
    - محاسبه به صورت استاندارد:
        s = sum(d[i] * (10 - i) for i in range(9))
        r = s % 11
        اگر r < 2: check_digit == r
        در غیراینصورت: check_digit == 11 - r
    """
    # دقت حساب به‌صورت رقم‌به‌رقم
    digits = [int(ch) for ch in code10]
    s = 0
    # i از 0 تا 8
    for i in range(9):
        weight = 10 - i
        s += digits[i] * weight
    r = s % 11
    check_digit = digits[9]
    if r < 2:
        return check_digit == r
    else:
        return check_digit == (11 - r)


def is_valid_national_id(s: Optional[str]) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    بررسی کامل کد ملی.

    باز می‌گرداند:
        (is_valid, reason_if_invalid_or_None, normalized_code_or_None)

    مثال:
        >>> is_valid_national_id('۰۱۲۳۴۵۶۷۸۹')
        (False, 'checksum' or other reason, '0123456789' )
    """
    if s is None:
        return False, 'empty', None

    norm = normalize_national_id(s)
    if not norm:
        return False, 'empty', None

    # باید دقیقاً 10 رقم باشد
    if not _RE_10_DIGITS.match(norm):
        # برگردانده می‌شود برای دیباگ: norm را هم بازمی‌گردانیم
        return False, 'length_or_not_digits', norm

    # الگوهای نامعتبر مانند همه ارقام یکسان
    if norm in _INVALID_SAME_DIGITS:
        return False, 'all_same_digits', norm

    # بررسی checksum با احتیاط
    try:
        if not _checksum_ok(norm):
            return False, 'checksum', norm
    except Exception:
        # اگر برای هر دلیلی محاسبه شکست خورد
        return False, 'checksum_error', norm

    # معتبر است
    return True, None, norm


def validate_or_raise(s: Optional[str]) -> str:
    """
    اگر s معتبر بود، کد نرمال‌شده را بازمی‌گرداند.
    در غیر این صورت ValueError با پیام مناسب تویپ می‌کند.
    """
    ok, reason, norm = is_valid_national_id(s)
    if ok:
        # guarantee returning the normalized 10-digit string
        return norm  # type: ignore[return-value]
    else:
        raise ValueError(f"Invalid national id: reason={reason}, normalized={norm}")


# اختیاری: تابع کمکی که فقط bool برمی‌گرداند (ساده برای استفاده در شرط‌ها)
def is_valid(s: Optional[str]) -> bool:
    ok, _, _ = is_valid_national_id(s)
    return ok


# CLI ساده
def _cli_main(argv):
    if len(argv) < 2:
        print("Usage: python ir_national_id_validator.py <national_id> [<national_id> ...]")
        return 2
    exit_code = 0
    for code in argv[1:]:
        ok, reason, norm = is_valid_national_id(code)
        if ok:
            print(f"VALID  -> {code}  normalized: {norm}")
        else:
            print(f"INVALID -> {code}  reason: {reason}  normalized: {norm}")
            exit_code = 1
    return exit_code


if __name__ == "__main__":
    sys.exit(_cli_main(sys.argv))

# برای این ماژول: توابع قابل export
__all__ = [
    "normalize_national_id",
    "is_valid_national_id",
    "validate_or_raise",
    "is_valid",
]
