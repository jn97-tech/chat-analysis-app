import pandas as pd
import numpy as np
import re
from io import TextIOWrapper

def run_analysis(file):
    text = TextIOWrapper(file, encoding="utf-8").read()

    # Parse messages
    pattern = r"\[(\d{1,2}/\d{1,2}/\d{4}), (\d{1,2}:\d{2}:\d{2})\]([^:]+): (.+)"
    matches = re.findall(pattern, text)
    data = [{"Name": s.strip(), "Message": m.strip(), "Date": f"{d}, {t}"} for d,t,s,m in matches]
    df = pd.DataFrame(data)

    # Filtering
    df = df[~df["Message"].str.contains("end-to-end encrypted", case=False, na=False)]
    group_name_match = re.search(r"\]([^:]+):\s*[\u200e]*Messages and calls are end-to-end encrypted", text)
    if group_name_match:
        group_name = group_name_match.group(1).strip()
        df = df[df["Name"] != group_name]

    # Dates
    df["datetime"] = pd.to_datetime(df["Date"], format="%d/%m/%Y, %H:%M:%S", errors="coerce", dayfirst=True)
    df = df.dropna(subset=["datetime"])

    # Features
    df["word_count"] = df["Message"].apply(lambda x: len(str(x).split()))
    df["hour"] = df["datetime"].dt.hour
    df["period"] = df["hour"].apply(lambda h: "morning" if 5 <= h < 12 else "evening" if 18 <= h < 24 else "other")
    df["message_length"] = df["Message"].astype(str).apply(len)

    # Sorted with gaps
    df_sorted = df.sort_values("datetime")
    df_sorted["prev_time"] = df_sorted["datetime"].shift()
    df_sorted["prev_sender"] = df_sorted["Name"].shift()
    df_sorted["gap"] = (df_sorted["datetime"] - df_sorted["prev_time"]).dt.total_seconds() / 3600  # hours

    # MESSAGE_COUNTS
    message_counts = df.groupby("Name")["Message"].count().reset_index(name="message_count").sort_values(by="message_count", ascending=False).to_dict(orient="records")

    # WORD_COUNTS
    word_counts = df.groupby("Name")["word_count"].sum().reset_index().sort_values(by="word_count", ascending=False).to_dict(orient="records")

    # MOST_ACTIVE_HOUR (per user)
    most_active_hour = df.groupby(["Name","hour"])["Message"].count().reset_index(name="count").to_dict(orient="records")

    # LONGEST_GAP_HOURS (per user)
    longest_gap_hours = df_sorted.groupby("Name")["gap"].max().reset_index().to_dict(orient="records")

    # ABSENCE_PERIODS
    absence_periods = []
    for name, group in df_sorted.groupby("Name"):
        if group.shape[0] > 1:
            group = group.sort_values("datetime")
            group["prev_time"] = group["datetime"].shift()
            group["gap"] = (group["datetime"] - group["prev_time"]).dt.total_seconds() / 60
            idx = group["gap"].idxmax()
            row = group.loc[idx]
            absence_periods.append({
                "Name": name,
                "gap": float(row["gap"]),
                "absence_start": row["prev_time"].isoformat() if pd.notna(row["prev_time"]) else None,
                "absence_end": row["datetime"].isoformat() if pd.notna(row["datetime"]) else None
            })

    # MORNING_EVENING (counts by user)
    morning_evening = {
        "morning": df[df["period"]=="morning"].groupby("Name")["Message"].count().to_dict(),
        "evening": df[df["period"]=="evening"].groupby("Name")["Message"].count().to_dict()
    }

    # AVERAGE_MESSAGE_LENGTH
    avg_message_length = df.groupby("Name")["message_length"].mean().to_dict()

    # LONGEST_MESSAGE_BY_CHAR
    longest_char_row = df.loc[df["message_length"].idxmax()] if not df.empty else None
    longest_message_by_char = {
        "sender": longest_char_row["Name"] if longest_char_row is not None else None,
        "char_count": int(longest_char_row["message_length"]) if longest_char_row is not None else None,
        "preview": longest_char_row["Message"][:200] if longest_char_row is not None else None,
        "full": longest_char_row["Message"] if longest_char_row is not None else None
    }

    # LONGEST_MESSAGE_BY_WORD
    df["word_count"] = df["Message"].apply(lambda x: len(str(x).split()))
    longest_word_row = df.loc[df["word_count"].idxmax()] if not df.empty else None
    longest_message_by_word = {
        "sender": longest_word_row["Name"] if longest_word_row is not None else None,
        "word_count": int(longest_word_row["word_count"]) if longest_word_row is not None else None,
        "preview": longest_word_row["Message"][:200] if longest_word_row is not None else None,
        "full": longest_word_row["Message"] if longest_word_row is not None else None
    }

    # KEYWORD_MENTIONS
    keywords = ["changed the group name","photo","video","gif"]
    keyword_mentions = {}
    for kw in keywords:
        keyword_mentions[kw] = df["Message"].str.contains(kw, case=False, na=False).groupby(df["Name"]).sum().to_dict()

    # FIRST_MESSAGE
    first_row = df_sorted.iloc[0] if not df_sorted.empty else None
    first_message = {
        "sender": first_row["Name"] if first_row is not None else None,
        "message": first_row["Message"] if first_row is not None else None,
        "timestamp": first_row["datetime"].isoformat() if first_row is not None else None
    }

    # SWEAR_WORD_COUNTS
    swear_words = ["shit","fuck","cunt","sexotheque"]
    swear_counts = {}
    for sw in swear_words:
        swear_counts[sw] = df["Message"].str.contains(rf"\b{sw}\b", case=False, na=False).groupby(df["Name"]).sum().to_dict()

    # Return
    return {
        "message_counts": message_counts,
        "word_counts": word_counts,
        "most_active_hour": most_active_hour,
        "longest_gap_hours": longest_gap_hours,
        "absence_periods": absence_periods,
        "morning_evening": morning_evening,
        "avg_message_length": avg_message_length,
        "longest_message_by_char": longest_message_by_char,
        "longest_message_by_word": longest_message_by_word,
        "keyword_mentions": keyword_mentions,
        "first_message": first_message,
        "swear_word_counts": swear_counts
    }
