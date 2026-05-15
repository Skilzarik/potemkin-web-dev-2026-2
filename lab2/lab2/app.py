import re
from flask import Flask, request, render_template, make_response, redirect, url_for

app = Flask(__name__)

COOKIE_NAME = "my_visit_cookie"
COOKIE_VALUE = "visited"


def validate_phone(phone):
    """
    Проверяет номер телефона.
    Возвращает (True, None) если номер валиден,
    или (False, "сообщение об ошибке") если нет.
    """
    # Проверка на недопустимые символы
    # Допустимы: цифры, пробелы, (), - . +
    if re.search(r'[^\d\s()\-\.\+]', phone):
        return False, "Недопустимый ввод. В номере телефона встречаются недопустимые символы."

    # Считаем только цифры
    digits = re.sub(r'\D', '', phone)
    digit_count = len(digits)

    # Определяем нужное количество цифр
    # Если начинается с +7 или 8 — нужно 11 цифр
    stripped = phone.strip()
    if stripped.startswith('+7') or stripped.startswith('8'):
        required = 11
    else:
        required = 10

    if digit_count != required:
        return False, "Недопустимый ввод. Неверное количество цифр."

    return True, None


def format_phone(phone):
    """
    Форматирует номер телефона в вид 8-***-***-**-**
    """
    digits = re.sub(r'\D', '', phone)
    # Приводим к 11 цифрам (добавляем 8 если 10 цифр)
    if len(digits) == 10:
        digits = '8' + digits
    # Заменяем первую цифру на 8 (7 → 8 для номеров +7...)
    digits = '8' + digits[1:]
    # Формат: 8-***-***-**-**
    return f"{digits[0]}-{digits[1:4]}-{digits[4:7]}-{digits[7:9]}-{digits[9:11]}"


# ── Главная страница ──────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


# ── 1. Параметры URL ──────────────────────────────────────────────────────────

@app.route('/url-params')
def url_params():
    params = request.args.to_dict(flat=False)
    return render_template('url_params.html', params=params)


# ── 2. Заголовки запроса ──────────────────────────────────────────────────────

@app.route('/headers')
def headers():
    hdrs = dict(request.headers)
    return render_template('headers.html', headers=hdrs)


# ── 3. Cookie ────────────────────────────────────────────────────────────────

@app.route('/cookies')
def cookies():
    all_cookies = request.cookies
    cookie_present = COOKIE_NAME in all_cookies

    response = make_response(render_template(
        'cookies.html',
        cookies=all_cookies,
        cookie_name=COOKIE_NAME,
        cookie_present=cookie_present
    ))

    if cookie_present:
        # Удаляем куки
        response.delete_cookie(COOKIE_NAME)
    else:
        # Устанавливаем куки
        response.set_cookie(COOKIE_NAME, COOKIE_VALUE)

    return response


# ── 4. Параметры формы ───────────────────────────────────────────────────────

@app.route('/form-params', methods=['GET', 'POST'])
def form_params():
    form_data = {}
    if request.method == 'POST':
        form_data = request.form.to_dict(flat=False)
    return render_template('form_params.html', form_data=form_data, method=request.method)


# ── 5. Валидация телефона ─────────────────────────────────────────────────────

@app.route('/phone', methods=['GET', 'POST'])
def phone():
    phone_input = ''
    error = None
    formatted = None

    if request.method == 'POST':
        phone_input = request.form.get('phone', '')
        valid, error = validate_phone(phone_input)
        if valid:
            formatted = format_phone(phone_input)

    return render_template('phone.html',
                           phone_input=phone_input,
                           error=error,
                           formatted=formatted)


if __name__ == '__main__':
    app.run(debug=True)
