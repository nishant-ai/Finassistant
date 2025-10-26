import sys
import traceback

print("Testing imports")

modules_to_test = [
    ("preprocess", ["SECFilingCleaner"]),
    ("vector_store", ["VectorStore"]),
    ("llm", ["get_llama3_groq_response", "get_gemini_flash_llm", "create_vector_query_prompt", "create_synthesis_prompt"]),
]

for module_name, items in modules_to_test:
    try:
        print(f"\n✓ Testing: {module_name}")
        mod = __import__(module_name, fromlist=items)
        for item in items:
            getattr(mod, item)
        print(f"  ✓ All imports successful from {module_name}")
    except Exception as e:
        print(f"\n✗ FAILED importing from {module_name}")
        print(f"  Error: {e}")
        traceback.print_exc()
        print("\n" + "=" * 60)
        sys.exit(1)

print("\n" + "=" * 60)
print("All imports successful!")
print("=" * 60)