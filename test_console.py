"""
MynEra Aira - Interactive Chat Console
Pure chat testing interface with conversation history.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.orchestrator import Orchestrator
from src.models.chat_schema import ChatRequest

def display_response(response):
    """Display chatbot response in a clean, readable format."""
    print("\n" + "=" * 80)
    print("🤖 AIRA:")
    print("=" * 80)
    print(response.answer)
    
    # Display sources if available
    if response.sources:
        print("\n" + "-" * 80)
        print("📚 SOURCES:")
        for i, source in enumerate(response.sources, 1):
            print(f"\n{i}. {source.get('title', 'Unknown')}")
            if 'url' in source:
                print(f"   🔗 {source['url']}")
    
    # Display recommendations if available
    if response.recommendations:
        print("\n" + "-" * 80)
        print("💡 RECOMMENDATIONS:")
        for i, rec in enumerate(response.recommendations, 1):
            print(f"\n{i}. {rec.title}")
            print(f"   Type: {rec.type}")
            if rec.description:
                print(f"   {rec.description[:100]}...")
            if rec.meta:
                meta_items = [f"{k}: {v}" for k, v in list(rec.meta.items())[:3]]
                print(f"   {' | '.join(meta_items)}")
    
    print("=" * 80)

def main():
    """Run interactive chat console."""
    print("\n" + "=" * 80)
    print("🎓 MynEra Aira - Interactive Chat Console")
    print("=" * 80)
    print("\n💡 Tips:")
    print("   • Type your questions naturally in Azerbaijani or English")
    print("   • Type 'exit' or 'quit' to end the session")
    print("   • Type 'clear' to reset conversation history")
    print("\n" + "=" * 80)
    
    # Initialize orchestrator
    try:
        orchestrator = Orchestrator()
        print("\n✅ System initialized successfully!")
    except Exception as e:
        print(f"\n❌ Failed to initialize system: {e}")
        print("\n💡 Make sure to run: python src/scripts/ingest_data.py first")
        sys.exit(1)
    
    # Conversation history
    conversation_history = []
    
    # Main chat loop
    while True:
        try:
            # Get user input
            print("\n" + "-" * 80)
            user_input = input("👤 YOU: ").strip()
            
            # Handle special commands
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Goodbye! See you next time.")
                break
            
            if user_input.lower() == 'clear':
                conversation_history = []
                print("\n🔄 Conversation history cleared.")
                continue
            
            if not user_input:
                continue
            
            # Create chat request
            request = ChatRequest(
                user_id="console_user",
                query=user_input,
                conversation_history=conversation_history
            )
            
            # Get response from orchestrator
            response = orchestrator.handle_chat(request)
            
            # Display response
            display_response(response)
            
            # Update conversation history
            conversation_history.append({
                "role": "user",
                "content": user_input
            })
            conversation_history.append({
                "role": "assistant",
                "content": response.answer
            })
            
            # Limit history to last 10 exchanges (20 messages)
            if len(conversation_history) > 20:
                conversation_history = conversation_history[-20:]
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye! See you next time.")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            print("\n💡 Continuing... Type 'exit' to quit.")

if __name__ == "__main__":
    main()
