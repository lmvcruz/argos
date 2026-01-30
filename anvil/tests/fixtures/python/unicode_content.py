"""
Test fixture with Unicode content.

This file contains Unicode characters to test UTF-8 encoding handling.
© 2026 Copyright Symbol
"""


def greet(name: str) -> str:
    """Greet someone in multiple languages."""
    greetings = {
        "english": f"Hello, {name}!",
        "spanish": f"¡Hola, {name}!",
        "french": f"Bonjour, {name}!",
        "german": f"Guten Tag, {name}!",
        "japanese": f"こんにちは, {name}!",
        "korean": f"안녕하세요, {name}!",
        "russian": f"Привет, {name}!",
        "chinese": f"你好, {name}!",
    }
    return "\n".join(greetings.values())


# Math symbols: ∑ ∫ ∂ √ ∞ π
# Arrows: → ← ↑ ↓ ⇒ ⇐
# Currency: $ € £ ¥ ₹
# Emoji: 😀 🎉 ✨ 🚀

print("UTF-8 encoding test: ✓")
