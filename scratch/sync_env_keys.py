import os

def main():
    env_path = '/home/ubuntu/aarkaai3b/.env'
    if not os.path.exists(env_path):
        print("No .env file found")
        return

    with open(env_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Parse lines
    env_dict = {}
    for line in content.splitlines():
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            env_dict[k.strip()] = v.strip()

    aarkaa_key = env_dict.get('AARKAAI_API_KEY')
    fingen_key = env_dict.get('FINGENIQ_SERVICE_API_KEY')

    if aarkaa_key:
        print("AARKAAI_API_KEY is present")
        if not fingen_key:
            print("FINGENIQ_SERVICE_API_KEY is missing. Appending it to match AARKAAI_API_KEY...")
            # Append newline if not present
            suffix = ""
            if not content.endswith('\n'):
                suffix = "\n"
            with open(env_path, 'a', encoding='utf-8') as f:
                f.write(f"{suffix}FINGENIQ_SERVICE_API_KEY={aarkaa_key}\n")
            print("FINGENIQ_SERVICE_API_KEY appended successfully!")
        else:
            print("FINGENIQ_SERVICE_API_KEY is already present")
    else:
        print("Warning: AARKAAI_API_KEY not found in .env")

if __name__ == "__main__":
    main()
