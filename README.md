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

logs/app.log

---

# Запуск

python main.py

После выполнения результаты появятся в папке output.

---

# Сборка exe

pyinstaller --onefile --name reconciliation_app main.py

Исполняемый файл появится в папке:

dist/

---

# Допущения

1. Формат строк RpaBank_report стабилен.
2. Local DateTime содержит дату в формате YYYYMMDD.
3. В Pindodo_report транзакции представлены вертикальными блоками.
4. Сверка выполняется по дате без учета времени.

