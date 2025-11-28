# Aplikacja dyspozycyjności - gotowa pod Render.com

Pliki w paczce:
- app.py
- templates/index.html
- requirements.txt
- Procfile
- runtime.txt
- config.example.json

## Szybkie uruchomienie lokalne
1. python -m venv venv
2. source venv/bin/activate   # lub venv\Scripts\activate na Windows
3. pip install -r requirements.txt
4. python app.py
5. Otwórz http://127.0.0.1:5000

## Deploy na Render.com (krok po kroku)
1. Załóż konto na https://render.com i zaloguj się.
2. Stwórz nowe Repozytorium Git (np. GitHub) i wypchnij wszystkie pliki tego projektu.
   ```
   git init
   git add .
   git commit -m "initial"
   git branch -M main
   git remote add origin <twoje-repo-url>
   git push -u origin main
   ```
3. Na Render: kliknij "New" → "Web Service".
4. Wybierz repo i branch (main).
5. Ustaw:
   - **Environment**: Python
   - **Build Command**: (zostaw puste) lub `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`
6. (Opcjonalnie) Dodaj zmienne środowiskowe w ustawieniach serwisu na Render:
   - SECRET_KEY — losowy klucz
   - SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, FROM_EMAIL — jeśli chcesz wysyłać maile
7. Kliknij Deploy. Po chwili aplikacja będzie dostępna pod adresem render.com.

## Uwaga bezpieczeństwa
- Nie zapisuj haseł w publicznym repozytorium.
- Użyj zmiennych środowiskowych na Render, nie pliku config.json (chyba że repo jest prywatne).
- Dla produkcji ustaw inny SECRET_KEY niż domyślny.