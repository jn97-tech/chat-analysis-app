from analysis import run_analysis

# Replace with the path to your WhatsApp .txt export
file_path = r"C:\Users\joshn\OneDrive\Documents\Sycamore.txt"

# Open the file in binary mode (mimics Flask upload)
with open(file_path, "rb") as f:
    results = run_analysis(f)

# Print each section of the results
for key, value in results.items():
    print(f"\n=== {key.upper()} ===")
    print(value)
