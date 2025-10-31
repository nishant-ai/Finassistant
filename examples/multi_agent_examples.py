"""
Multi-Agent System Example Queries

This file contains example queries demonstrating the capabilities
of the multi-agent financial analysis system.

Run with:
    python examples/multi_agent_examples.py
"""

from agent.app_multi_agent import run_multi_agent


# Example queries organized by complexity and mode
CHAT_EXAMPLES = {
    "Simple Metric": "[Chat] What's Apple's P/E ratio?",
    "Comparison": "[Chat] Compare Microsoft and Google",
    "Current Events": "[Chat] What happened to NVIDIA today?",
    "Brief Length": "[Chat] Quick summary of Tesla - 2 sentences",
    "Custom Length": "[Chat] Give me 5 paragraphs on Amazon's growth",
    "Market News": "[Chat] What's happening in the market today?",
    "Profitability": "[Chat] How profitable is Meta?",
}

REPORT_EXAMPLES = {
    "Single Company": "[Report] Analyze Tesla's financial health",
    "Comparison": "[Report] Comprehensive comparison of Apple vs Microsoft",
    "Industry": "[Report] Deep dive into semiconductor industry",
    "Growth Analysis": "[Report] Evaluate Amazon's growth prospects",
    "Strategy": "[Report] Full analysis of Meta's business strategy",
}


def run_example(name: str, query: str, save_output: bool = False):
    """
    Run a single example query.

    Args:
        name: Example name
        query: Query string
        save_output: Whether to save output to file
    """
    print("\n" + "=" * 80)
    print(f"EXAMPLE: {name}")
    print("=" * 80)
    print(f"Query: {query}\n")

    try:
        output = run_multi_agent(query, verbose=True)

        print("\n" + "-" * 80)
        print("FINAL OUTPUT:")
        print("-" * 80)
        print(output)
        print("-" * 80)

        if save_output:
            # Save to file
            filename = f"output_{name.replace(' ', '_').lower()}.md"
            with open(f"examples/outputs/{filename}", 'w') as f:
                f.write(f"# {name}\n\n")
                f.write(f"**Query**: {query}\n\n")
                f.write("---\n\n")
                f.write(output)
            print(f"\n✅ Saved to examples/outputs/{filename}")

    except Exception as e:
        print(f"\n❌ Error running example: {str(e)}")


def run_all_chat_examples():
    """Run all chat mode examples"""
    print("\n" + "=" * 80)
    print("CHAT MODE EXAMPLES")
    print("=" * 80)

    for name, query in CHAT_EXAMPLES.items():
        run_example(name, query, save_output=True)
        input("\nPress Enter to continue to next example...")


def run_all_report_examples():
    """Run all report mode examples"""
    print("\n" + "=" * 80)
    print("REPORT MODE EXAMPLES")
    print("=" * 80)

    for name, query in REPORT_EXAMPLES.items():
        run_example(name, query, save_output=True)
        input("\nPress Enter to continue to next example...")


def run_quick_demo():
    """
    Run a quick demo with one chat and one report example.
    """
    print("\n" + "=" * 80)
    print("QUICK DEMO - Multi-Agent Financial Analysis System")
    print("=" * 80)

    # Chat example
    print("\n1️⃣  CHAT MODE EXAMPLE")
    run_example(
        "Chat Demo",
        "[Chat] What's Apple's P/E ratio?",
        save_output=False
    )

    input("\n\nPress Enter to see Report mode example...")

    # Report example (using a simpler one to avoid long wait)
    print("\n2️⃣  REPORT MODE EXAMPLE")
    print("Note: Report mode is comprehensive and may take 60-90 seconds...")
    run_example(
        "Report Demo",
        "[Report] Analyze Microsoft's financial performance",
        save_output=False
    )


def interactive_example_selector():
    """
    Interactive menu to select and run examples.
    """
    while True:
        print("\n" + "=" * 80)
        print("MULTI-AGENT EXAMPLE SELECTOR")
        print("=" * 80)
        print("\nSelect an option:")
        print("  1. Run quick demo (1 chat + 1 report)")
        print("  2. Run all chat examples")
        print("  3. Run all report examples")
        print("  4. Run specific chat example")
        print("  5. Run specific report example")
        print("  6. Custom query")
        print("  q. Quit")

        choice = input("\nYour choice: ").strip().lower()

        if choice == 'q':
            break
        elif choice == '1':
            run_quick_demo()
        elif choice == '2':
            run_all_chat_examples()
        elif choice == '3':
            run_all_report_examples()
        elif choice == '4':
            print("\nChat Examples:")
            for i, name in enumerate(CHAT_EXAMPLES.keys(), 1):
                print(f"  {i}. {name}")
            idx = int(input("Select example number: ")) - 1
            name = list(CHAT_EXAMPLES.keys())[idx]
            run_example(name, CHAT_EXAMPLES[name], save_output=True)
        elif choice == '5':
            print("\nReport Examples:")
            for i, name in enumerate(REPORT_EXAMPLES.keys(), 1):
                print(f"  {i}. {name}")
            idx = int(input("Select example number: ")) - 1
            name = list(REPORT_EXAMPLES.keys())[idx]
            run_example(name, REPORT_EXAMPLES[name], save_output=True)
        elif choice == '6':
            query = input("Enter your custom query: ").strip()
            run_example("Custom", query, save_output=False)
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    import sys

    # Check for command-line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "demo":
            run_quick_demo()
        elif sys.argv[1] == "chat":
            run_all_chat_examples()
        elif sys.argv[1] == "report":
            run_all_report_examples()
        else:
            print("Usage:")
            print("  python examples/multi_agent_examples.py demo    # Quick demo")
            print("  python examples/multi_agent_examples.py chat    # All chat examples")
            print("  python examples/multi_agent_examples.py report  # All report examples")
            print("  python examples/multi_agent_examples.py         # Interactive menu")
    else:
        # Interactive mode
        interactive_example_selector()
