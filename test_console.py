"""
MynEra Aira - Premium Interactive Chat Console
Pure chat testing interface with rich animations and polished UX.
"""

import sys
import time
import random
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.orchestrator import Orchestrator
from src.models.chat_schema import ChatRequest


# Spinner characters for thinking animation
SPINNER_CHARS = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"


def thinking_animation():
    """Display premium thinking animation with spinner."""
    duration = random.uniform(1.5, 2.5)
    start_time = time.time()
    
    spinner_idx = 0
    sys.stdout.write("\n")
    sys.stdout.flush()
    
    while time.time() - start_time < duration:
        spinner = SPINNER_CHARS[spinner_idx % len(SPINNER_CHARS)]
        sys.stdout.write(f"\r  {spinner} Aira düşünür...   ")
        sys.stdout.flush()
        time.sleep(0.08)
        spinner_idx += 1
    
    sys.stdout.write("\r" + " " * 30 + "\r")  # Clear line
    sys.stdout.flush()


def typewriter_effect(text, speed=0.003):
    """Print text with smooth typewriter effect."""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(speed)
    sys.stdout.write("\n")


def display_response(response):
    """Display chatbot response with premium animations."""
    print("\n" + "=" * 80)
    print("🤖 AIRA")
    print("=" * 80)
    
    # Typewriter effect for answer (fast but visible)
    for line in response.answer.split('\n'):
        if line.strip():  # Only animate non-empty lines
            typewriter_effect(line, speed=0.003)
        else:
            print()  # Empty line
    
    # Display sources if available
    if response.sources:
        print("\n" + "-" * 80)
        print("📚 MƏNBƏLƏR")
        print("-" * 80)
        for i, source in enumerate(response.sources, 1):
            print(f"\n{i}. {source.title}")
            if source.url:
                print(f"   🔗 {source.url}")
            if source.snippet:
                print(f"   💬 {source.snippet[:100]}...")
    
    # Display recommendations if available
    if response.recommendations:
        print("\n" + "-" * 80)
        print("💡 TÖVSİYƏLƏR")
        print("-" * 80)
        for i, rec in enumerate(response.recommendations, 1):
            print(f"\n{i}. {rec.title}")
            print(f"   Tip: {rec.type}")
            if rec.description:
                print(f"   {rec.description[:100]}...")
            if rec.meta:
                meta_items = [f"{k}: {v}" for k, v in list(rec.meta.items())[:3]]
                print(f"   {' | '.join(meta_items)}")
    
    print("=" * 80)


def main():
    """Run premium interactive chat console."""
    # Header
    print("\n" + "=" * 80)
    print("🎓 MynEra Aira - İnteraktiv Söhbət Konsolu")
    print("=" * 80)
    print("\n💡 İstifadə qaydaları:")
    print("   • Azərbaycan və ya İngilis dilində təbii suallar verin")
    print("   • 'exit' və ya 'quit' yazaraq çıxın")
    print("   • 'clear' yazaraq danışıq tarixçəsini silin")
    print("\n" + "=" * 80)
    
    # Initialize orchestrator
    try:
        orchestrator = Orchestrator()
        print("\n✅ Sistem uğurla işə salındı!")
    except Exception as e:
        print(f"\n❌ Sistem işə salınmadı: {e}")
        print("\n💡 Əvvəlcə işə salın: python src/scripts/ingest_data.py")
        sys.exit(1)
    
    # Conversation history
    conversation_history = []
    
    # Main chat loop
    while True:
        try:
            # Get user input
            print("\n" + "-" * 80)
            user_input = input("👤 SİZ: ").strip()
            
            # Handle special commands
            if user_input.lower() in ['exit', 'quit', 'q', 'çıxış']:
                print("\n👋 Sağ olun! Görüşənədək.")
                break
            
            if user_input.lower() in ['clear', 'təmizlə']:
                conversation_history = []
                print("\n🔄 Danışıq tarixçəsi təmizləndi.")
                continue
            
            if not user_input:
                continue
            
            # Create chat request
            request = ChatRequest(
                user_id="console_user",
                query=user_input,
                conversation_history=conversation_history
            )
            
            # Show thinking animation
            thinking_animation()
            
            # Get response from orchestrator
            response = orchestrator.handle_chat(request)
            
            # Display response with animations
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
            print("\n\n👋 Sağ olun! Görüşənədək.")
            break
        except Exception as e:
            print(f"\n❌ Xəta: {e}")
            import traceback
            traceback.print_exc()
            print("\n💡 Davam edir... 'exit' yazaraq çıxın.")


if __name__ == "__main__":
    main()
