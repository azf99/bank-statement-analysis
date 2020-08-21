'''
Common functions for data transforation and analysis from the extracted transations data
'''

import re
import time
from datetime import datetime

import numpy as np
import pandas as pd

#from sklearn.feature_extraction.text import CountVectorizer

import re
#import matplotlib.pyplot as plt
#import seaborn as sns

from extract import *

#sns.set()


def conv_date(x):
    '''
    Function for correcting the date format
    '''
    x = datetime.strftime(datetime.strptime(x, "%d/%m/%Y"), "%m/%d/%Y")
    return (x)


def balances(data, pdf_path):
    '''
    The function takes the original transaction table and creates a dummy table
    consisting of blank transactions for calculations of average balances over different
    periods of time
    '''

    df = data

    for i in df.index:
        df["Transaction Date"][i] = conv_date(df["Transaction Date"][i])

    df["Transaction Date"] = pd.to_datetime(df["Transaction Date"])
    test = pd.DataFrame(columns=["Transaction Date", "day", "month", "year", "Balance"], index=df.index)

    for i in df.index:
        test["Transaction Date"][i] = df["Transaction Date"][i]
        test["day"][i] = df["Transaction Date"][i].day
        test["month"][i] = df["Transaction Date"][i].month
        test["year"][i] = df["Transaction Date"][i].year
        test["Balance"][i] = df["Balance"][i]

    # print(test.shape)

    bal = pd.DataFrame(columns=["day", "month", "year", "week", "Balance"])
    dels = []
    for i in range(len(test.index) - 1):
        if test["day"][i] != test["day"][i + 1]:
            rng = pd.date_range(test["Transaction Date"][i], test["Transaction Date"][i + 1])
            t = pd.DataFrame(columns=bal.columns, index=rng)
            for j in rng:
                t["day"][j] = j.day
                t["month"][j] = j.month
                t["year"][j] = j.year
                t["week"][j] = j.week
                t["Balance"][j] = test["Balance"][i]

            bal = pd.concat([bal, t], axis=0)
    bal = bal[~bal.index.duplicated(keep='first')]

    print("[INFO] Exporting balances")
    out_path = pdf_path[:pdf_path.find(".")] + "_balances.xlsx"

    bal.to_excel(out_path, sheet_name="Daily Closing Balances")
    return (bal)


def calculate_balances(data, pdf_path):
    '''
    Function takes the transactions and calculates average balances(daily, weekly, monthly, etc.)
    and exports the final results to an excelsheet
    '''

    bal = balances(data, pdf_path)

    # Weekly
    weekly = bal.groupby("week").last().Balance
    weekly_avg = sum(weekly) // len(weekly)
    weekly_volume = bal.groupby("week").sum().Balance
    weekly_volume_avg = sum(weekly_volume) // len(weekly_volume)

    # Monthly
    monthly = bal.groupby("month").last().Balance
    monthly_avg = sum(monthly) // len(monthly)
    monthly_volume = bal.groupby("month").sum().Balance
    monthly_volume_avg = sum(monthly_volume) // len(monthly_volume)

    # Daily
    daily_avg = sum(bal.Balance) // len(bal)

    dic = {"Avg Daily Closing Balance": daily_avg, "Average Weekly Closing Balance": weekly_avg,
           "Avg Weekly Volume": weekly_volume_avg, "Avg Monthly Closing Balance": monthly_avg,
           "Avg Monthly Volume": monthly_volume_avg}
    avgs = pd.DataFrame(dic, index = [1])

    out_path = pdf_path[:pdf_path.find(".")] + "_balances.xlsx"

    with pd.ExcelWriter(out_path, mode="a") as writer:
        avgs.to_excel(writer, sheet_name="Outputs")

    inf = {"path_to_balances": out_path, "values": {}}

    for i in avgs.columns:
        inf["values"][i] = int(avgs[i][1])
    
    return(inf)

def summary(data):
    '''
    A little summary of transactions
    '''
    # data = pd.read_excel("yes.xlsx")
    #print("Total Transations=", data.shape[0])

    d1 = data["Transaction Date"][0]
    d2 = data["Transaction Date"][len(data) - 1]
    d1 = datetime(int(d1[-4:]), int(d1[-7:-5]), int(d1[:2]))
    d2 = datetime(int(d2[-4:]), int(d2[-7:-5]), int(d2[:2]))

    #print("Length of statement: ", month_diff(d1, d2), "months")

    return(data.shape[0], month_diff(d1, d2))
    '''
    monthly = data.groupby("Value Date").sum()
    print("Average monthly debit = Rs.", np.mean(monthly.Debit))
    print("Average monthly credit = Rs.", np.mean(monthly.Credit))
    '''


def classify_trans(df):
    '''
    Takes the transactions and classifies them into categories
    1. IMPS
    2. ATM
    3. FOOD
    4. SHOPPING
    5. CASH
    and others

    TODO: Make it less complicated and reusable
    '''
    # df = pd.read_excel("all_bank.xlsx")
    t = df["Description"]

    t = t.apply(lambda x: x.lower())

    # Removing numbers and special characters
    text = t.replace(to_replace="[0-9]", value="", regex=True).apply(
        lambda x: x.replace("/", "").replace("\\", "").replace(":", "").replace("\n", " ").replace("-", " ")
        .replace("/", " "))

    # Removing extra spaces created due to the above step
    for i in range(len(text)):
        x = text[i].split()
        for j in range(len(x)):
            x[j] = x[j].strip()
        text[i] = " ".join(x)

    #### TODO: Rewriting the dictionary in a better implementation

    labels = {"imps": "imps", "rrn": "imps", "loan": "loan", "emi": "emi", "amazon": "shopping", "flipkart": "shopping",
              "mutualfund": "invest", "txn paytm": "trf", "restaurant": "food", "paytm": "trf",
              "atd": "atm", "atm": "atm", "net txn": "nettxn", "cash": "cash", "funds trf": "trf", "neft": "neft",
              "interest": "interest",
              "metro": "travel", "swiggy": "food", "faasos": "food", "zomato": "food", "upi": "trf", "ola": "travel",
              "refund": "refund",
              "charge": "bank_charges", "pca": "trf"}

    labs = []

    # Labelling the transaction according to the dictionary defined
    for i in text:
        f = 0
        for j in list(labels.keys()):
            if j in i:
                labs.append(labels[j])
                f = 1
                break
        if f == 0:
            labs.append("miscellaneous")
    df["Label"] = pd.DataFrame(labs)

    x = df.Description.apply(lambda x: re.findall(r'[\w\.-]+@[\w\.-]+', x))
    df["Remark"] = pd.DataFrame(x)

    return (df)


def money(df):
    '''
    Creates a column for depicting the Credit and Debit numerically
    '''

    money = []
    type = []
    for i in df.index:
        if df["Debit"][i] > 0:
            money.append(-df["Debit"][i])
            type.append("Debit")
        else:
            money.append(df["Credit"][i])
            type.append("Credit")

    return (pd.concat([df, pd.DataFrame(money, columns=["flow"]), pd.DataFrame(type, columns=["type"])], axis=1))


def analyse(df):
    labels = df["Label"].unique()
    counts = df.groupby("Label").size()

    sums = df.groupby("Label").sum()["flow"]
    plt.figure(figsize=(16, 10))
    plt.bar(counts.index, counts)
    plt.show()

    plt.figure(figsize=(16, 10))
    plt.bar(sums.index, sums)
    plt.show()

    plt.figure(figsize=(16, 10))
    plt.pie(counts, labels=counts.index)
    plt.show()

    plt.figure(figsize=(16, 10))
    plt.pie(sums, labels=sums.index)
    plt.show()


def cash_inflow(df):
    print("[INFO] For cash Inflow...")
    df = df[df.type == "Credit"]
    # analyse(df)

    labels = df["Label"].unique()
    counts = df.groupby("Label").size().to_frame()

    sums = df.groupby("Label").sum()["flow"].to_frame()

    # print(counts)
    # print(sums)
    res = pd.merge(sums, counts, on="Label")
    res.columns = ["amount", "count"]
    return (res)
    '''
    plt.figure(figsize=(16, 10))
    plt.bar(counts.index, counts)
    plt.title("Cash Inflow count")
    plt.show()

    plt.figure(figsize=(16, 10))
    plt.bar(sums.index, sums)
    plt.title("Cash Inflow amount")
    plt.show()

    plt.figure(figsize=(16, 10))
    plt.pie(counts, labels = counts.index)
    plt.title("Cash Inflow count")
    plt.show()

    plt.figure(figsize=(16, 10))
    plt.pie(sums, labels = sums.index)
    plt.title("Cash Inflow amount")
    plt.show()
    '''


def cash_outflow(df):
    print("[INFO] For cash outflow")
    df = df[df.type == "Debit"]

    # analyse(df)
    labels = df["Label"].unique()
    counts = df.groupby("Label").size().to_frame()

    sums = df.groupby("Label").sum()["flow"]
    sums = sums.apply(lambda x: abs(x)).to_frame()

    res = pd.merge(sums, counts, on="Label")
    res.columns = ["amount", "count"]
    return (res)

    # print(counts)
    # print(sums)

    '''
    plt.figure(figsize=(16, 10))
    plt.bar(counts.index, counts)
    plt.title("Cash Outflow count")
    plt.show()

    plt.figure(figsize=(16, 10))
    plt.bar(sums.index, sums)
    plt.title("Cash Outflow amount")
    plt.show()

    plt.figure(figsize=(16, 10))
    plt.pie(counts, labels = counts.index)
    plt.title("Cash Outflow count")
    plt.show()

    plt.figure(figsize=(16, 10))
    plt.pie(sums, labels = sums.index)
    plt.title("Cash Outflow amount")
    plt.show()
    '''


def redundant_trans(processed_path, length):
    try:
        print("AT SALARY")
        x = pd.read_excel(processed_path)
        y = x[(x.type == "Credit") & (x.flow >= 20000) & (x.Label.isin(["cash", "imps"]) == False)]
        text = y["Description"].replace(to_replace="[0-9]", value="", regex=True).apply(
            lambda x: x.replace("/", "").replace("\\", "").replace(":", "").replace("\n", " ").replace("-", " ")
            .replace("/", " "))

        w = []
        for i in text:
            w.extend(list(set(i.split(" "))))
        most = pd.Series(w).value_counts() <= length
        most = most.index[0]

        s = []

        for i in y["Description"].index:
            if most in y["Description"][i]:
                s.append(y["Credit"][i])

        avg = sum(s)/len(s)

        return(avg)
    except:
        return("Salary not found!")
    

