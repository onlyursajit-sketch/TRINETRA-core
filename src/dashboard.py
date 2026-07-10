from datetime import datetime

from src.market_engine import get_market_snapshot


def format_number(value):
    if value is None:
        return "N/A"

    if isinstance(value, (int, float)):
        return f"{value:,.2f}"

    return str(value)


def calculate_change(current, previous):
    if current is None or previous in (None, 0):
        return None, None

    change = current - previous
    change_percent = (change / previous) * 100
    return change, change_percent


def get_direction(change):
    if change is None:
        return "UNKNOWN"

    if change > 0:
        return "UP"

    if change < 0:
        return "DOWN"

    return "FLAT"


def show_market_dashboard():
    market = get_market_snapshot()

    up_count = 0
    down_count = 0
    flat_count = 0
    error_count = 0

    print("=" * 92)
    print("TRINETRA LIVE MARKET DASHBOARD")
    print("Updated:", datetime.now().strftime("%d-%m-%Y %H:%M:%S"))
    print("=" * 92)

    print(
        f"{'ASSET':12}"
        f"{'PREVIOUS':>14}"
        f"{'CURRENT':>14}"
        f"{'CHANGE':>14}"
        f"{'CHANGE %':>12}"
        f"{'STATUS':>12}"
        f"{'SOURCE':>14}"
    )

    print("-" * 92)

    for name, data in market.items():
        if "error" in data:
            error_count += 1
            print(
                f"{name:12}"
                f"{'N/A':>14}"
                f"{'N/A':>14}"
                f"{'N/A':>14}"
                f"{'N/A':>12}"
                f"{'ERROR':>12}"
                f"{'Unavailable':>14}"
            )
            print(f"  Reason: {data['error']}")
            continue

        current = data.get("regular_market_price")
        previous = data.get("previous_close")
        source = data.get("source", "Unknown")

        change, change_percent = calculate_change(current, previous)
        direction = get_direction(change)

        if direction == "UP":
            up_count += 1
        elif direction == "DOWN":
            down_count += 1
        elif direction == "FLAT":
            flat_count += 1

        change_text = (
            f"{change:+,.2f}"
            if change is not None
            else "N/A"
        )

        percent_text = (
            f"{change_percent:+.2f}%"
            if change_percent is not None
            else "N/A"
        )

        print(
            f"{name:12}"
            f"{format_number(previous):>14}"
            f"{format_number(current):>14}"
            f"{change_text:>14}"
            f"{percent_text:>12}"
            f"{direction:>12}"
            f"{source:>14}"
        )

    print("-" * 92)
    print(
        f"Summary: UP={up_count} | DOWN={down_count} | "
        f"FLAT={flat_count} | ERRORS={error_count}"
    )
    print("=" * 92)


if __name__ == "__main__":
    show_market_dashboard()
