import sys, os, glob
os.environ["PYTHONIOENCODING"] = "utf-8"
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from trace_full_pipeline import trace

project_root = r"E:\Code\ai-teaching-ppt"
candidates = glob.glob(os.path.join(project_root, "uploads", "**", "*.pptx"), recursive=True)
if not candidates:
    print("No PPTX found!")
    sys.exit(1)
test_file = candidates[0]
print(f"Using: {test_file}")
trace(test_file)
