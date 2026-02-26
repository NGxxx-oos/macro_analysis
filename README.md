# Macro-Economic Data Analysis Tool

Инструмент для анализа макроэкономических данных из CSV файлов.
Считайте несколько файлов, получите средний ВВП по странам в красивой таблице.

# Файлы
macro_analysis.py — основной скрипт

tests/test_macro_analysis.py — тесты

requirements.txt — зависимости

## Инструкции по запуску

```bash
# 1. Сохраните основной скрипт как macro_analysis.py
# 2. Сохраните тесты в tests/test_macro_analysis.py
# 3. Создайте виртуальное окружение и установите зависимости

# Установка
pip install -r requirements.txt

# Запуск с вашими файлами
python macro_analysis.py --files file1.csv file2.csv --report average-gdp

# Запуск тестов
pytest tests/ -v --cov=macro_analysis
