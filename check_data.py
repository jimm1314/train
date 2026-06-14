import sys, os
sys.path.insert(0, os.path.dirname(__file__))

# Test _load_from_files directly
from utils.data_loader import _load_from_files
df = _load_from_files()
print(f"Loaded {len(df)} questions from files")
if not df.empty:
    print(f"Columns: {list(df.columns)}")
    print(f"Sample questions: {df['问题'].head(3).tolist()}")
else:
    print("No data loaded!")
