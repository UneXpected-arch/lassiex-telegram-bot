import os

def load_dotenv(filepath=".env"):
    if not os.path.exists(filepath):
        print(f"[.env] File not found at {filepath}")
        return

    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ[key] = value
