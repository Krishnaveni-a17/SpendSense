# analyser.py
# Business logic layer for SpendSense API.
# Handles all spending analysis — grouping, percentages,
# personality classification, and savings nudge generation.
# Completely independent of Flask and database — pure Python logic.


def group_by_category(expenses):

    grouped = {}
    for expense in expenses:
        category = expense["category"]
        if category in grouped:
            grouped[category] += expense["amount"]
        else:
            grouped[category] = expense["amount"]
    return grouped


def calculate_percentages(grouped):

    total = sum(grouped.values())

    if total == 0:
        return {}

    percentages = {}
    for category, amount in grouped.items():
        percentages[category] = round((amount / total) * 100, 1)

    return percentages


def get_personality(percentages):

    food  = percentages.get("Food", 0)
    subs  = percentages.get("Subscriptions", 0)
    shop  = percentages.get("Shopping", 0)
    utils = percentages.get("Utilities", 0)

    comfort = food + subs

    if comfort > 50:
        return (
            "Comfort Seeker",
            "Over half your money goes to food and subscriptions. "
            "You prioritise daily comfort and enjoyment over saving."
        )
    elif shop > 35:
        return (
            "Impulse Buyer",
            "Shopping dominates your spending. "
            "You tend to spend on wants more than needs."
        )
    elif utils > 40:
        return (
            "Homebody",
            "Most of your money goes to utilities and essentials. "
            "Life runs smoothly but little is left for enjoyment."
        )
    elif max(percentages.values(), default=0) < 35:
        return (
            "Balanced Saver",
            "No single category dominates your spending. "
            "You spread money evenly — a healthy financial habit."
        )
    else:
        return (
            "Chaotic Spender",
            "Spending is spread across many categories "
            "with no single clear pattern."
        )


def generate_nudge(personality_name, grouped):

    if "Comfort" in personality_name:
        food_amount = grouped.get("Food", 0)
        saving      = round(food_amount * 0.20 * 12, 2)
        return (f"Cut Food spending by 20% and save "
                f"₹{saving:.2f} extra per year.")

    elif "Impulse" in personality_name:
        shop_amount = grouped.get("Shopping", 0)
        saving      = round(shop_amount * 0.20 * 12, 2)
        return (f"Cut Shopping by 20% and save "
                f"₹{saving:.2f} extra per year.")

    elif "Homebody" in personality_name:
        return "Allocate ₹500/month toward a hobby or experience."

    elif "Balanced" in personality_name:
        total  = sum(grouped.values())
        saving = round(total * 0.10 * 12, 2)
        return (f"You're balanced! Saving 10% monthly "
                f"could grow to ₹{saving:.2f} per year.")

    else:
        return "Track one more month to reveal your clearest spending pattern."


def run_analysis(expenses):

    if not expenses:
        return None

    grouped     = group_by_category(expenses)
    percentages = calculate_percentages(grouped)
    name, desc  = get_personality(percentages)
    nudge       = generate_nudge(name, grouped)

    return {
        "total_spent"   : round(sum(grouped.values()), 2),
        "total_expenses": len(expenses),
        "breakdown"     : [
            {
                "category"  : category,
                "amount"    : round(amount, 2),
                "percentage": percentages[category],
                "bar"       : build_bar(percentages[category])
            }
            for category, amount in grouped.items()
        ],
        "personality": {
            "type"       : name,
            "description": desc
        },
        "nudge": nudge
    }


def build_bar(percentage, width=20):

    filled = int((percentage / 100) * width)
    empty  = width - filled
    return "█" * filled + "░" * empty


def calculate_stats(expenses):

    if not expenses:
        return None

    amounts   = [e["amount"]   for e in expenses]
    dates     = [e["date"]     for e in expenses]
    categories = [e["category"] for e in expenses]

    # Total and count
    total = round(sum(amounts), 2)
    count = len(amounts)

    # Highest and lowest single expense
    highest = max(amounts)
    lowest  = min(amounts)

    # Average per expense
    average = round(total / count, 2)

    # Top category by total amount spent
    grouped  = group_by_category(expenses)
    top_cat  = max(grouped, key=lambda c: grouped[c])
    top_amt  = round(grouped[top_cat], 2)

    # Date range
    earliest = min(dates)
    latest   = max(dates)

    # Daily average — only if date range spans more than one day
    if earliest == latest:
        daily_average = total
    else:
        from datetime import datetime
        d1   = datetime.strptime(earliest, "%Y-%m-%d")
        d2   = datetime.strptime(latest,   "%Y-%m-%d")
        days = (d2 - d1).days + 1
        daily_average = round(total / days, 2)

    return {
        "total_spent"   : total,
        "expense_count" : count,
        "highest_expense": highest,
        "lowest_expense" : lowest,
        "average_per_expense": average,
        "daily_average"  : daily_average,
        "top_category"   : {
            "name"  : top_cat,
            "amount": top_amt
        },
        "date_range": {
            "from": earliest,
            "to"  : latest
        }
    }