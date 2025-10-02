from ir_national_id_validator import is_valid_national_id, validate_or_raise

user_input = "1234567890"
ok, reason, norm = is_valid_national_id(user_input)
if ok:
    print("کد ملی صحیح است:", norm)
else:
    print("کد ملی نامعتبر است. دلیل:", reason)
    
    
try:
    norm = validate_or_raise(user_input)
    # معتبر است، norm را استفاده کن
except ValueError as e:
    # نامعتبر: پیام خطا را به کاربر یا لاگ بده
    print(str(e))
