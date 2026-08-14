from huggingface_hub import HfApi
try:
    api = HfApi()
    info = api.model_info('rthshr/aarkaa-3b')
    print("SUCCESS: Model is public or accessible!")
    print(info)
except Exception as e:
    print("FAILED:", str(e))
