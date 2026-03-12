import re
from pathlib import Path
from decimal import Decimal, InvalidOperation

import pandas as pd
from loguru import logger

BASE_DIR = Path(__file__).resolve().parent
RPA_FILE = BASE_DIR / "input" / "RpaBank_report.txt"
PINDODO_FILE = BASE_DIR / "input" / "Pindodo_report.txt"
OUTPUT_DIR = BASE_DIR / "output"
LOG_DIR = BASE_DIR / "logs"

RPA_EXCEL = OUTPUT_DIR / "RpaBank_report.xlsx"
PINDODO_EXCEL = OUTPUT_DIR / "Pindodo_report.xlsx"
RECON_EXCEL = OUTPUT_DIR / "reconciliation_result.xlsx"
LOG_FILE = LOG_DIR / "app.log"


def setup_logger() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger.remove()
    logger.add(LOG_FILE, level="INFO", encoding="utf-8", rotation="1 MB")
    logger.add(lambda msg: print(msg, end=""), level="INFO")


def normalize_amount(value: str) -> str:
    if value is None:
        return ""

    s = str(value).strip().replace(" ", "").replace(",", ".")
    if not s:
        return ""

    try:
        dec = Decimal(s)
        return f"{dec:.2f}"
    except InvalidOperation:
        return s


def normalize_datetime_to_date(value: str) -> str:
    if value is None:
        return ""

    s = str(value).strip()

    if re.fullmatch(r"\d{14}", s):
        return f"{s[0:4]}-{s[4:6]}-{s[6:8]}"

    if re.fullmatch(r"\d{8}", s):
        return f"{s[0:4]}-{s[4:6]}-{s[6:8]}"

    m = re.match(r"(\d{4}-\d{2}-\d{2})", s)
    if m:
        return m.group(1)

    return s


def save_df_to_excel(df: pd.DataFrame, path: Path, sheet_name: str = "Sheet1") -> None:
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    logger.info(f"Excel saved: {path}")


def parse_pindodo_report(file_path: Path) -> pd.DataFrame:
    logger.info(f"Parsing Pindodo report: {file_path}")

    text = file_path.read_text(encoding="utf-8", errors="ignore")

    lines = [line.rstrip("\n") for line in text.splitlines()]

    records = []
    current_record = {}

    for raw_line in lines:
        line = raw_line.strip()

        if not line:
            continue

        if re.fullmatch(r"\d{4}-\d{2}-\d{2},\s*[A-Z]{3}", line):
            continue


        if set(line) == {"-"}:
            if current_record:
                records.append(current_record)
                current_record = {}
            continue

        parts = re.split(r"\s{2,}", line, maxsplit=1)
        if len(parts) == 2:
            key, value = parts[0].strip(), parts[1].strip()
            current_record[key] = value
        else:
            continue

    if current_record:
        records.append(current_record)

    df = pd.DataFrame(records)

    logger.info(f"Pindodo parsed rows: {len(df)}")
    return df


def parse_rpa_report(file_path):
    rows = []

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            parts = re.split(r"\s+", line)

            number = parts[0]
            index = parts[1]

            # 20250625id5291047836204958173620
            dt_tx = parts[2]

            m = re.match(r"(\d{8})(id.+)", dt_tx)
            local_datetime = m.group(1)
            transaction_id = m.group(2)

            # 10000.00KGS249400
            amount_block = parts[3]

            m2 = re.match(r"(\d+\.\d{2})([A-Z]{3})(\d+)", amount_block)

            amount = m2.group(1)
            currency = m2.group(2)
            card_number = m2.group(3)

            terminal_id = parts[4]

            rows.append({
                "Number": number,
                "Index": index,
                "Local DateTime": local_datetime,
                "Transaction ID": transaction_id,
                "Transaction Amount": amount,
                "Currency": currency,
                "Card Number": card_number,
                "Terminal ID": terminal_id
            })

    return pd.DataFrame(rows)


def prepare_rpa_for_reconciliation(df: pd.DataFrame) -> pd.DataFrame:
    work = df.copy()

    work["match_date"] = work["Local DateTime"].apply(normalize_datetime_to_date)
    work["match_amount"] = work["Transaction Amount"].apply(normalize_amount)
    work["match_currency"] = work["Currency"].astype(str).str.strip()
    work["match_rrn"] = work["Card Number"].astype(str).str.strip()
    work["match_terminal"] = work["Terminal ID"].astype(str).str.strip()

    work["match_key"] = (
        work["match_date"].astype(str)
        + "|"
        + work["match_amount"].astype(str)
        + "|"
        + work["match_currency"].astype(str)
        + "|"
        + work["match_rrn"].astype(str)
        + "|"
        + work["match_terminal"].astype(str)
    )

    return work


def prepare_pindodo_for_reconciliation(df: pd.DataFrame) -> pd.DataFrame:
    work = df.copy()

    work["match_date"] = work["Transaction Date"].apply(normalize_datetime_to_date)
    work["match_amount"] = work["Transaction Amount"].apply(normalize_amount)
    work["match_currency"] = work["Transaction Currency"].astype(str).str.strip()
    work["match_rrn"] = work["Retrieval Reference Number"].astype(str).str.strip()
    work["match_terminal"] = work["Card Acceptor Terminal ID"].astype(str).str.strip()

    work["match_key"] = (
        work["match_date"].astype(str)
        + "|"
        + work["match_amount"].astype(str)
        + "|"
        + work["match_currency"].astype(str)
        + "|"
        + work["match_rrn"].astype(str)
        + "|"
        + work["match_terminal"].astype(str)
    )

    return work


def reconcile_reports(rpa_df: pd.DataFrame, pindodo_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    logger.info("Starting reconciliation")

    rpa = prepare_rpa_for_reconciliation(rpa_df)
    pindodo = prepare_pindodo_for_reconciliation(pindodo_df)

    successful = rpa.merge(
        pindodo,
        on="match_key",
        how="inner",
        suffixes=("_RPA", "_PINDODO"),
    )

    rpa_unsuccessful = rpa[~rpa["match_key"].isin(pindodo["match_key"])].copy()

    pindodo_unsuccessful = pindodo[~pindodo["match_key"].isin(rpa["match_key"])].copy()

    logger.info(f"Successful rows: {len(successful)}")
    logger.info(f"RPA unsuccessful rows: {len(rpa_unsuccessful)}")
    logger.info(f"Pindodo unsuccessful rows: {len(pindodo_unsuccessful)}")

    return successful, rpa_unsuccessful, pindodo_unsuccessful


def save_reconciliation_result(
    successful: pd.DataFrame,
    rpa_unsuccessful: pd.DataFrame,
    pindodo_unsuccessful: pd.DataFrame,
    output_path: Path,
) -> None:
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        successful.to_excel(writer, index=False, sheet_name="Успешные")
        rpa_unsuccessful.to_excel(writer, index=False, sheet_name="RpaBank_неуспешные")
        pindodo_unsuccessful.to_excel(writer, index=False, sheet_name="Pindodo_неуспешные")

    logger.info(f"Reconciliation result saved: {output_path}")


def main() -> None:
    setup_logger()

    logger.info("=== START ===")

    if not RPA_FILE.exists():
        logger.error(f"File not found: {RPA_FILE}")
        return

    if not PINDODO_FILE.exists():
        logger.error(f"File not found: {PINDODO_FILE}")
        return

    rpa_df = parse_rpa_report(RPA_FILE)
    pindodo_df = parse_pindodo_report(PINDODO_FILE)

    save_df_to_excel(rpa_df, RPA_EXCEL, sheet_name="RpaBank_report")
    save_df_to_excel(pindodo_df, PINDODO_EXCEL, sheet_name="Pindodo_report")

    successful, rpa_unsuccessful, pindodo_unsuccessful = reconcile_reports(rpa_df, pindodo_df)

    save_reconciliation_result(
        successful=successful,
        rpa_unsuccessful=rpa_unsuccessful,
        pindodo_unsuccessful=pindodo_unsuccessful,
        output_path=RECON_EXCEL,
    )

    logger.info("=== DONE ===")


if __name__ == "__main__":
    main()