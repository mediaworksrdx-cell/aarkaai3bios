from llama_cpp import Llama
model = Llama(
    model_path="/home/ubuntu/aarkaai3b/aarkaa-3b-q8.gguf",
    vocab_only=True,
    verbose=False,
)
print("Tokenizing <|im_start|> (special=True):")
print(model.tokenize(b"<|im_start|>", special=True))
print("Tokenizing <|im_end|> (special=True):")
print(model.tokenize(b"<|im_end|>", special=True))
print("Tokenizing prompt (special=True):")
prompt = b"<|im_start|>system\nYou are AARKAA, a helpful and precise AI assistant.<|im_end|>\n"
print(model.tokenize(prompt, special=True))
