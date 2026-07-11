from datetime import datetime

from src.market_engine import get_market_snapshot


WIDTH = 76


def num(value):
    if value is None:
        return "N/A"
    return f"{value:,.2f}"


def short_state(value):
    states = {
        "REGULAR": "OPEN",
        "PRE": "PRE",
        "POST": "POST",
        "CLOSED": "CLOSED",
        "UNKNOWN": "UNKNOWN",
    }
    return states.get(str(value).upper(), str(value).upper())


def show_market_dashboard():
    market = get_market_snapshot()

    up_count = 0
    down_count = 0
    flat_count = 0
    error_count = 0

    print("=" * WIDTH)
    print("TRINETRA MARKET DASHBOARD")
    print("Updated:", datetime.now().strftime("%d-%m-%Y %H:%M:%S"))
    print("=" * WIDTH)

    print(
        f"{'ASSET':10}"
        f"{'PREV':>10}"
        f"{'OPEN':>10}"
        f"{'HIGH':>10}"
        f"{'LOW':>10}"
        f"{'CURR':>10}"
        f"{'CHG%':>8}"
    )
    print("-" * WIDTH)

    for name, data in market.items():
        if "error" in data:
            error_count += 1
            print(f"{name:10}{'DATA ERROR':>66}")
            print(f"Reason: {data['error'][:68]}")
            continue

        previous = data.get("previous_close")
        open_price = data.get("open")
        high = data.get("high")
        low = data.get("low")
        current = data.get("current")
        change = data.get("change")
        change_percent = data.get("change_percent")

        if change is not None:
            if change > 0:
                up_count += 1
            elif change < 0:
                down_count += 1
            else:
                flat_count += 1

        percent_text = (
            f"{change_percent:+.2f}%"
            if change_percent is not None
            else "N/A"
        )

        print(
            f"{name:10}"
            f"{num(previous):>10}"
            f"{num(open_price):>10}"
            f"{num(high):>10}"
            f"{num(low):>10}"
            f"{num(current):>10}"
            f"{percent_text:>8}"
        )

        print(
            f"  State:{short_state(data.get('market_state', 'UNKNOWN'))}"
            f" | Source:{data.get('source', 'N/A')}"
            f" | Data:{data.get('state', 'N/A').upper()}"
        )

    print("-" * WIDTH)
    print(
        f"UP:{up_count} | DOWN:{down_count} | "
        f"FLAT:{flat_count} | ERR:{error_count}"
    )
    print("=" * WIDTH)


if __name__ == "__main__":
    show_market_dashboard()
