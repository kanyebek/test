
# Сверка данных банковских отчетов

## Описание проекта
Данный проект реализует скрипт на Python для автоматической обработки и сверки транзакционных отчетов из двух источников:

- RpaBank_report
- Pindodo_report

Скрипт выполняет:
1. Парсинг текстовых отчетов
2. Преобразование данных в таблицы
3. Экспорт данных в Excel
4. Сверку транзакций между отчетами
5. Формирование итогового файла сверки

---

# Структура проекта

project/
│
├── RPA/
│   └── RpaBank_report.txt
│
├── PINDODO/
│   └── Pindodo_report.txt
│
├── output/
│
├── main.py
├── requirements.txt
└── README.md

---

# Используемые библиотеки

| Библиотека | Назначение |
|---|---|
| pandas | обработка таблиц |
| openpyxl | запись Excel |
| loguru | логирование |

Установка зависимостей:

pip install -r requirements.txt

---

# Формат входных данных

## RpaBank_report

Строки отчета имеют структуру:

Number  Index  LocalDateTime+TransactionID  Amount+Currency+CardNumber  TerminalID

Пример:

10 2 20250625id5291047836204958173620 10000.00KGS249400 42344552

Разделение полей:

LocalDateTime = 20250625  
TransactionID = id5291047836204958173620  

Amount = 10000.00  
Currency = KGS  
CardNumber = 249400

---

## Pindodo_report

Каждая транзакция записана вертикальным блоком:

Transaction Date                     2025-06-25
Retrieval Reference Number           063534
Transaction Amount                   22.34
Card Acceptor Terminal ID            32445551
Transaction Currency                 EUR

Блоки разделены строкой из дефисов.

---

# Правила сверки

| RpaBank | Pindodo |
|---|---|
| Local DateTime | Transaction Date |
| Transaction Amount | Transaction Amount |
| Currency | Transaction Currency |
| Card Number | Retrieval Reference Number |
| Terminal ID | Card Acceptor Terminal ID |

Перед сверкой выполняется нормализация данных:
- даты приводятся к формату YYYY-MM-DD
- суммы приводятся к числовому виду
- удаляются лишние пробелы

---

# Результаты работы

После запуска создаются файлы:

output/
│
├── RpaBank_report.xlsx
├── Pindodo_report.xlsx
└── reconciliation_result.xlsx

Файл reconciliation_result.xlsx содержит листы:

| Лист | Описание |
|---|---|
| Успешные | транзакции, найденные в обоих отчетах |
| RpaBank_неуспешные | записи только из RpaBank |
| Pindodo_неуспешные | записи только из Pindodo |

---

# Логирование

Используется библиотека loguru.

Логи сохраняются в файл:

output/app.log

---

# Запуск

python main.py

После выполнения результаты появятся в папке output.

---

# Сборка exe

Установить PyInstaller:

pip install pyinstaller

Собрать:

pyinstaller --onefile --name reconciliation_app main.py

Исполняемый файл появится в папке:

dist/

---

# Допущения

1. Формат строк RpaBank_report стабилен.
2. Local DateTime содержит дату в формате YYYYMMDD.
3. В Pindodo_report транзакции представлены вертикальными блоками.
4. Сверка выполняется по дате без учета времени.

---

# Возможные улучшения

- unit‑тесты
- обработка дубликатов
- конфигурационный файл
- более гибкий парсер
