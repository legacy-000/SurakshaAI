"""Reset demo dataset to deterministic state."""
import sys

def reset_demo():
    confirm = "--confirm" in sys.argv
    if not confirm:
        print("Usage: python reset_demo.py --confirm")
        print("This will truncate all data and reload 500 deterministic records.")
        return

    from database.seed_data import generate_seed_data
    data = generate_seed_data()
    print(f"Demo data reset complete: {len(data['cases'])} cases, {len(data['accused'])} accused records")


if __name__ == "__main__":
    reset_demo()
