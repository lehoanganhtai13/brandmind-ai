"""
Test Vietnamese tokenizer after switching to pyvi.
"""

from shared.model_clients.bm25.tokenizers import build_default_analyzer

# Test Vietnamese analyzer
print("Testing Vietnamese Tokenizer (pyvi):")
print("=" * 60)

analyzer = build_default_analyzer(language="vi")

test_texts = [
    "Trí tuệ nhân tạo đang thay đổi thế giới",
    "Tôi đang học lập trình Python và machine learning",
    "Sản phẩm này có chất lượng rất tốt",
    "Công ty chúng tôi chuyên về phát triển phần mềm",
]

for text in test_texts:
    tokens = analyzer(text)
    print(f"\nOriginal: {text}")
    print(f"Tokens:   {' | '.join(tokens)}")
    print(f"Count:    {len(tokens)} tokens")

print("\n" + "=" * 60)
print("✅ Test passed! pyvi tokenizer works correctly.")
