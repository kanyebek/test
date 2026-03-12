import re
import sys
from pathlib import Path

import pandas as pd
from loguru import logger


def setup_logger():
    Path("logs").mkdir(exist_ok=True)

    logger.remove()
    logger.add(sys.stderr, level="INFO")
    logger.add(
        "logs/app.log",
        level="DEBUG",
        rotation="1 MB",
        encoding="utf-8",
        enqueue=True
    )

def parse_rpabank_report(file_path: str) -> pd.DataFrame:
    logger.info(f"Читаю RpaBank отчет: {file_path}")

    rows = []

    pattern = re.compile(
        r"^\s*(\d+)\s+"                                   # Number
        r"(\d+)\s+"                                       # Index
        r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})"        # Local DateTime
        r"([A-Za-z0-9\-_\/]+)\s+"                         # Transaction ID
        r"([\d.,]+)"                                      # Transaction Amount
        r"([A-Z]{3})"                                     # Currency
        r"([\d*]+)\s+"                                    # Card Number
        r"(.+?)\s*$"                                      # Terminal ID
    )

    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()

            if not line:
                continue

            match = pattern.match(line)

            if match:
                rows.append(match.groups())
            else:
                logger.warning(f"Не удалось распарсить строку {line_num}: {line}")

    columns = [
        "Number",
        "Index",
        "Local DateTime",
        "Transaction ID",
        "Transaction Amount",
        "Currency",
        "Card Number",
        "Terminal ID"
    ]

    df = pd.DataFrame(rows, columns=columns)

    if not df.empty:
        df["Transaction Amount"] = (
            df["Transaction Amount"]
            .astype(str)
            .str.replace(",", ".", regex=False)
            .astype(float)
        )

    logger.info(f"RpaBank: распознано {len(df)} строк")
    return df


def parse_pindodo_report(file_path: str) -> pd.DataFrame:
    logger.info(f"Читаю Pindodo отчет: {file_path}")

    needed_keys = [
        "Transaction Date",
        "Transaction Amount",
        "Transaction Currency",
        "Retrieval Reference Number",
        "Card Acceptor Terminal ID"
    ]

    records = []
    current_record = {}

    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()

            if not line:
                if current_record:
                    records.append(current_record)
                    current_record = {}
                continue

            found = False

            for key in needed_keys:
                if line.startswith(key):
                    value = line[len(key):].strip()

                    if key in current_record and current_record:
                        records.append(current_record)
                        current_record = {}

                    current_record[key] = value
                    found = True
                    break

            if not found:
                logger.warning(f"Не удалось распознать строку {line_num}: {line}")

    if current_record:
        records.append(current_record)

    df = pd.DataFrame(records)

    for col in needed_keys:
        if col not in df.columns:
            df[col] = None

    df = df[needed_keys]

    if not df.empty:
        df["Transaction Amount"] = (
            df["Transaction Amount"]
            .astype(str)
            .str.replace(",", ".", regex=False)
        )
        df["Transaction Amount"] = pd.to_numeric(df["Transaction Amount"], errors="coerce")

    logger.info(f"Pindodo: распознано {len(df)} записей")
    return df


def normalize_datetime(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S")


def normalize_amount(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").round(2)


def normalize_text(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.upper()


def prepare_rpa_for_matching(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["match_datetime"] = normalize_datetime(df["Local DateTime"])
    df["match_amount"] = normalize_amount(df["Transaction Amount"])
    df["match_currency"] = normalize_text(df["Currency"])
    df["match_card"] = normalize_text(df["Card Number"])
    df["match_terminal"] = normalize_text(df["Terminal ID"])
    return df


def prepare_pindodo_for_matching(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["match_datetime"] = normalize_datetime(df["Transaction Date"])
    df["match_amount"] = normalize_amount(df["Transaction Amount"])
    df["match_currency"] = normalize_text(df["Transaction Currency"])
    df["match_card"] = normalize_text(df["Retrieval Reference Number"])
    df["match_terminal"] = normalize_text(df["Card Acceptor Terminal ID"])
    return df


def reconcile_reports(rpa_df: pd.DataFrame, pindodo_df: pd.DataFrame):
    logger.info("Начинаю сверку отчетов")

    rpa = prepare_rpa_for_matching(rpa_df)
    pindodo = prepare_pindodo_for_matching(pindodo_df)

    match_cols = [
        "match_datetime",
        "match_amount",
        "match_currency",
        "match_card",
        "match_terminal"
    ]

    successful = rpa.merge(
        pindodo,
        on=match_cols,
        how="inner",
        suffixes=("_RPA", "_PINDODO")
    )

    rpa_unsuccessful = rpa.merge(
        pindodo[match_cols].drop_duplicates(),
        on=match_cols,
        how="left",
        indicator=True
    )
    rpa_unsuccessful = rpa_unsuccessful[rpa_unsuccessful["_merge"] == "left_only"].drop(columns=["_merge"])

    pindodo_unsuccessful = pindodo.merge(
        rpa[match_cols].drop_duplicates(),
        on=match_cols,
        how="left",
        indicator=True
    )
    pindodo_unsuccessful = pindodo_unsuccessful[pindodo_unsuccessful["_merge"] == "left_only"].drop(columns=["_merge"])

    logger.info(f"Успешные: {len(successful)}")
    logger.info(f"RpaBank_неуспешные: {len(rpa_unsuccessful)}")
    logger.info(f"Pindodo_неуспешные: {len(pindodo_unsuccessful)}")

    return successful, rpa_unsuccessful, pindodo_unsuccessful


def main():
    setup_logger()

    base_dir = Path(__file__).resolve().parent.parent
    input_dir = base_dir / "input"
    output_dir = base_dir / "output"

    output_dir.mkdir(exist_ok=True)

    rpa_file = input_dir / "RPA" / "RpaBank_report.txt"
    pindodo_file = input_dir / "PINDODO" / "Pindodo_report.txt"

    if not rpa_file.exists():
        logger.error(f"Файл не найден: {rpa_file}")
        return

    if not pindodo_file.exists():
        logger.error(f"Файл не найден: {pindodo_file}")
        return

    rpa_df = parse_rpabank_report(str(rpa_file))
    pindodo_df = parse_pindodo_report(str(pindodo_file))

    rpa_excel = output_dir / "RpaBank_report.xlsx"
    pindodo_excel = output_dir / "Pindodo_report.xlsx"

    rpa_df.to_excel(rpa_excel, index=False)
    pindodo_df.to_excel(pindodo_excel, index=False)

    logger.info(f"Сохранен Excel: {rpa_excel}")
    logger.info(f"Сохранен Excel: {pindodo_excel}")

    successful, rpa_unsuccessful, pindodo_unsuccessful = reconcile_reports(rpa_df, pindodo_df)

    result_file = output_dir / "reconciliation_result.xlsx"

    with pd.ExcelWriter(result_file, engine="openpyxl") as writer:
        successful.to_excel(writer, sheet_name="Успешные", index=False)
        rpa_unsuccessful.to_excel(writer, sheet_name="RpaBank_неуспешные", index=False)
        pindodo_unsuccessful.to_excel(writer, sheet_name="Pindodo_неуспешные", index=False)

    logger.info(f"Сохранен итоговый файл: {result_file}")
    logger.info("Работа завершена")


if __name__ == "__main__":
    main()