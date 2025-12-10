import sys
import os
import textwrap

# 1. Setup Path to find 'src' modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.orchestrator import orchestrator
from src.models.chat_schema import ChatRequest
from src.config import settings

# ANSI Colors for nicer console output
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_box(title, content, color=RESET):
    print(f"\n{color}┌{'─' * 60}┐")
    print(f"│ {BOLD}{title.ljust(58)}{RESET}{color} │")
    print(f"├{'─' * 60}┤")
    for line in content.split("\n"):
        # Wrap long lines
        wrapped = textwrap.wrap(line, width=58)
        if not wrapped:  # Handle empty lines
            print(f"│ {' ' * 58} │")
        for w in wrapped:
            print(f"│ {w.ljust(58)} │")
    print(f"└{'─' * 60}┘{RESET}")


def main():
    print(f"{BOLD}{GREEN}🚀 MynEra Aira Console (v{settings.VERSION}){RESET}")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Search Enabled: {settings.SEARCH_ENABLED}")
    print("Type 'exit', 'quit', or 'clear' to reset history.\n")

    # Mock Conversation History
    history = []
    user_id = "console_tester_001"

    while True:
        try:
            user_input = input(f"\n{CYAN}👤 You: {RESET}").strip()

            if user_input.lower() in ["exit", "quit"]:
                print("👋 Goodbye!")
                break

            if user_input.lower() == "clear":
                history = []
                print(f"{YELLOW}🧹 History cleared.{RESET}")
                continue

            if not user_input:
                continue

            print(f"{YELLOW}🤖 Aira is thinking...{RESET}", end="\r")

            # --- THE CORE LOGIC ---
            req = ChatRequest(
                query=user_input, user_id=user_id, conversation_history=history
            )

            response = orchestrator.handle_chat(req)
            # ----------------------

            # Clear "thinking" line
            print(" " * 50, end="\r")

            # 1. Print Main Answer
            print(f"\n{GREEN}🗣️  Aira:{RESET}")
            print(response.answer)

            # 2. Print Follow-up Questions (Coach Mode)
            if response.needs_clarification and response.follow_up_questions:
                print(f"\n{CYAN}💡 Suggested Buttons (Chips):{RESET}")
                for idx, q in enumerate(response.follow_up_questions, 1):
                    print(f"   [{idx}] {q}")

            # 3. Print Recommendations (Expert Mode)
            if response.recommendations:
                print(f"\n{BOLD}📌 Recommended Cards:{RESET}")
                for rec in response.recommendations:
                    print(f"   • [{rec.type.upper()}] {rec.title}")
                    print(f"     {rec.description}")
                    if rec.meta:
                        print(f"     {rec.meta}")

            # 4. Print Citations (Expert Mode)
            if response.sources:
                print(f"\n{BOLD}🌍 Sources (Tavily):{RESET}")
                for src in response.sources:
                    print(f"   🔗 {src.title} -> {src.url}")

            # Update History
            history.append({"role": "user", "content": user_input})
            history.append({"role": "assistant", "content": response.answer})

        except KeyboardInterrupt:
            print("\n👋 Exiting...")
            break
        except Exception as e:
            print(f"\n{RED}❌ CRITICAL ERROR: {e}{RESET}")


if __name__ == "__main__":
    main()
