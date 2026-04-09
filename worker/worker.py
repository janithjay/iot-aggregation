import statistics
import time


def compute_summary(values):
    if not values:
        return {"min": None, "max": None, "avg": None}
    return {
        "min": min(values),
        "max": max(values),
        "avg": round(statistics.mean(values), 2),
    }


def start_worker_loop():
    # Placeholder loop. Replace with queue consumer logic.
    print("Worker started (starter mode).")
    while True:
        time.sleep(10)


if __name__ == "__main__":
    start_worker_loop()
