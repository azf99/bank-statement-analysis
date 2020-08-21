import numpy as np
import pandas as pd
import sys

from extract import *
from analysis import *


def main(pdf_path):
    start = time.time()
    # pdf_path = "yes1.pdf"

    print("[INFO] Starting extraction...")
    name, acc_no, bank, ifsc = extract_data(pdf_path)

    data = pd.read_excel(pdf_path[:pdf_path.find(".")] + ".xlsx")

    total_trans, length = summary(data)
    info = {"name": name, "bank": bank, "account_no": acc_no, "ifsc": ifsc, "total_months_statement": length,
            "total_transactions": total_trans}

    print("[INFO] Classifying Transactions...")
    data = classify_trans(data)
    # print("Transaction Labels...\n", data.head())
    data = money(data)
    # print(data.head())
    # print(data.shape)
    processed_path = pdf_path[:pdf_path.find(".")] + "_processed" + ".xlsx"
    data.to_excel(processed_path, index=False)

    salary = redundant_trans(processed_path, length)
    info["salary"] = salary
    print("[INFO] Running balances...")

    bal_data = calculate_balances(data, pdf_path)

    # print(bal_data)

    print("[INFO] Analysing Cash Inflow and Outflow")
    inflow = cash_inflow(data)
    out = cash_outflow(data)

    out_path = pdf_path[:pdf_path.find(".")] + "_outputs.xlsx"

    with pd.ExcelWriter(out_path) as writer:
        inflow.to_excel(writer, sheet_name="Cash Inflow")
        out.to_excel(writer, sheet_name="Cash Outflow")

    inf = {"path_to_fields": out_path, "values": {"cash_inflow": {}, "cash_outflow": {}}}
    for i in inflow.index:
        inf["values"]["cash_inflow"][i] = {"amount": int(inflow["amount"][i]), "count": int(inflow["count"][i])}

    for i in out.index:
        inf["values"]["cash_outflow"][i] = {"amount": int(out["amount"][i]), "count": int(out["count"][i])}

    # print(inf)
    print("Time Taken: ", (time.time() - start), "seconds")

    return ({"basic_info": info, "processed_trans_path": processed_path, "balances": bal_data, "output_fields": inf})

if __name__ == '__main__':
    path = sys.argv[1]
    print("[INFO] Initializing...")
    res = main(path);
    print(res);
    print(type(res))