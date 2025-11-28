import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import sqlite3, csv, io, smtplib, json
from email.message import EmailMessage

app = Flask(__name__)
# secret key should be set via env var on Render: SECRET_KEY
app.secret_key = os.environ.get('SECRET_KEY', 'replace-this-in-production')

DB = os.environ.get('DB_PATH', 'availability.db')

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS availability (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            note TEXT
        )
    """)
    conn.commit()
    conn.close()

# Call init_db() directly (avoid using @app.before_first_request which may not be available)
init_db()

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM availability ORDER BY date")
    rows = c.fetchall()
    conn.close()
    return render_template('index.html', rows=rows)

@app.route('/add', methods=['POST'])
def add():
    date = request.form.get('date')
    start = request.form.get('start')
    end = request.form.get('end')
    note = request.form.get('note')
    if not date or not start or not end:
        flash('Wypełnij datę, godzinę rozpoczęcia i zakończenia.', 'danger')
        return redirect(url_for('index'))
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO availability (date, start_time, end_time, note) VALUES (?, ?, ?, ?)",
              (date, start, end, note))
    conn.commit()
    conn.close()
    flash('Dyspozycyjność dodana.', 'success')
    return redirect(url_for('index'))

@app.route('/delete/<int:row_id>', methods=['POST'])
def delete(row_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM availability WHERE id = ?", (row_id,))
    conn.commit()
    conn.close()
    flash('Usunięto.', 'info')
    return redirect(url_for('index'))

@app.route('/export')
def export_csv():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM availability ORDER BY date")
    rows = c.fetchall()
    conn.close()
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['date','start_time','end_time','note'])
    for r in rows:
        cw.writerow([r['date'], r['start_time'], r['end_time'], r['note']])
    mem = io.BytesIO(si.getvalue().encode('utf-8'))
    mem.seek(0)
    return send_file(mem, as_attachment=True, download_name='availability.csv', mimetype='text/csv')

@app.route('/send', methods=['POST'])
def send():
    # SMTP configuration can be provided via config.json or environment variables
    cfg = {}
    cfg_path = os.path.join(os.getcwd(), 'config.json')
    if os.path.exists(cfg_path):
        with open(cfg_path, 'r', encoding='utf-8') as f:
            try:
                cfg = json.load(f)
            except:
                cfg = {}
    # environment variables override config.json
    cfg['smtp_host'] = os.environ.get('SMTP_HOST', cfg.get('smtp_host'))
    cfg['smtp_port'] = int(os.environ.get('SMTP_PORT', cfg.get('smtp_port') or 587))
    cfg['use_tls'] = os.environ.get('SMTP_USE_TLS', str(cfg.get('use_tls', True))).lower() in ('1','true','yes')
    cfg['smtp_user'] = os.environ.get('SMTP_USER', cfg.get('smtp_user'))
    cfg['smtp_pass'] = os.environ.get('SMTP_PASS', cfg.get('smtp_pass'))
    cfg['from_email'] = os.environ.get('FROM_EMAIL', cfg.get('from_email'))

    to_email = request.form.get('to_email')
    subject = request.form.get('subject') or 'Moja dyspozycyjność'
    if not to_email:
        flash('Podaj adres e-mail odbiorcy.', 'danger')
        return redirect(url_for('index'))

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM availability ORDER BY date")
    rows = c.fetchall()
    conn.close()

    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['date','start_time','end_time','note'])
    for r in rows:
        cw.writerow([r['date'], r['start_time'], r['end_time'], r['note']])
    csv_bytes = si.getvalue().encode('utf-8')

    msg = EmailMessage()
    msg['From'] = cfg.get('from_email') or cfg.get('smtp_user') or 'no-reply@example.com'
    msg['To'] = to_email
    msg['Subject'] = subject
    body = request.form.get('message') or 'W załączeniu moja dyspozycyjność.'
    msg.set_content(body)
    msg.add_attachment(csv_bytes, maintype='text', subtype='csv', filename='availability.csv')

    try:
        server = smtplib.SMTP(cfg['smtp_host'], cfg['smtp_port'])
        if cfg.get('use_tls'):
            server.starttls()
        if cfg.get('smtp_user'):
            server.login(cfg['smtp_user'], cfg['smtp_pass'])
        server.send_message(msg)
        server.quit()
        flash('Wysłano e-mail z dyspozycyjnością.', 'success')
    except Exception as e:
        flash(f'Błąd wysyłki: {e}', 'danger')
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)