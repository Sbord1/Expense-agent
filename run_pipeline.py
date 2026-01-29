import subprocess
import sys

STEPS = [
    ("Ingest CSV", "python src/ingest/revolut_csv.py"),
    ("Clean transactions", "python src/transform/clean_transactions.py"),
    ("Run classification", "python src/classify/run_classification.py"),
    ("Compute metrics", "python src/analytics/metrics.py"),
]

def run_step(name, command):
    print(f"\n- {name}")
    result = subprocess.run(command, shell=True)
    if result.returncode != 0:
        print(f" Failed at step: {name}")
        sys.exit(1)
    print(f" {name} completed")

def main():
    print("Starting Expense Agent pipeline")
    for name, cmd in STEPS:
        run_step(name, cmd)
    print("\nPipeline completed successfully")

if __name__ == "__main__":
    main()