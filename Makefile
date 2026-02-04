.PHONY: help install migrate superuser run test coverage lint format clean setup

# Змінні
PYTHON = python
MANAGE = $(PYTHON) manage.py
PIP = pip

# Допомога
help:
	@echo "========================================="
	@echo "  BlogQA - Автоматизовані команди"
	@echo "========================================="
	@echo ""
	@echo "Налаштування:"
	@echo "  make install    - Встановити всі залежності"
	@echo "  make migrate    - Застосувати міграції БД"
	@echo "  make superuser  - Створити суперкористувача"
	@echo "  make setup      - Повне налаштування (install + migrate)"
	@echo ""
	@echo "Розробка:"
	@echo "  make run        - Запустити dev сервер"
	@echo "  make test       - Запустити всі тести"
	@echo "  make coverage   - Генерувати coverage звіт"
	@echo ""
	@echo "Якість коду:"
	@echo "  make lint       - Перевірити код (flake8)"
	@echo "  make format     - Відформатувати код (black)"
	@echo ""
	@echo "Утиліти:"
	@echo "  make clean      - Очистити тимчасові файли"
	@echo ""

# Встановлення залежностей
install:
	@echo "📦 Встановлення залежностей..."
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "✅ Залежності встановлено!"

# Міграції
migrate:
	@echo "🔄 Застосування міграцій..."
	$(MANAGE) makemigrations
	$(MANAGE) migrate
	@echo "✅ Міграції застосовано!"

# Створення суперкористувача
superuser:
	@echo "👤 Створення суперкористувача..."
	$(MANAGE) createsuperuser

# Запуск сервера
run:
	@echo "🚀 Запуск сервера..."
	$(MANAGE) runserver

# Тестування
test:
	@echo "🧪 Запуск тестів..."
	$(MANAGE) test

# Coverage звіт
coverage:
	@echo "📊 Генерація coverage звіту..."
	coverage run --source='.' manage.py test
	coverage report
	coverage html
	@echo "✅ Звіт створено: htmlcov/index.html"

# Linting
lint:
	@echo "🔍 Перевірка коду..."
	flake8 blog/ users/ --max-line-length=120 --exclude=migrations

# Форматування
format:
	@echo "✨ Форматування коду..."
	black blog/ users/
	isort blog/ users/
	@echo "✅ Код відформатовано!"

# Очищення
clean:
	@echo "🧹 Очищення тимчасових файлів..."
	find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .coverage htmlcov/ .pytest_cache/
	@echo "✅ Очищення завершено!"

# Повне налаштування
setup: install migrate
	@echo ""
	@echo "========================================="
	@echo "  ✅ BlogQA налаштовано успішно!"
	@echo "========================================="
	@echo ""
	@echo "Наступні кроки:"
	@echo "  1. make superuser  - Створити адмін-акаунт"
	@echo "  2. make run        - Запустити сервер"
	@echo ""