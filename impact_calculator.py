"""Transparent scenario calculator for CIRCULO."""


def calculate_impact(total_waste, collection_rate, recovery_rate):
    """Return estimated collected, recovered and unrecovered weights in kg.

    Rates are assumptions supplied by the user, not measured environmental data.
    """
    if isinstance(total_waste, bool) or not isinstance(total_waste, (int, float)):
        raise ValueError("Total waste must be a number.")
    if total_waste < 0:
        raise ValueError("Waste cannot be negative.")
    if not 0 <= collection_rate <= 100:
        raise ValueError("Collection rate must be between 0 and 100.")
    if not 0 <= recovery_rate <= 100:
        raise ValueError("Recovery rate must be between 0 and 100.")

    collected = total_waste * collection_rate / 100
    recovered = collected * recovery_rate / 100
    unrecovered = collected - recovered
    return {
        "total_waste_kg": round(total_waste, 2),
        "collected_kg": round(collected, 2),
        "recovered_kg": round(recovered, 2),
        "unrecovered_kg": round(unrecovered, 2),
    }


if __name__ == "__main__":
    result = calculate_impact(200, 80, 75)
    print("===== CIRCULO IMPACT RESULTS =====")
    for name, value in result.items():
        print(f"{name}: {value} kg")