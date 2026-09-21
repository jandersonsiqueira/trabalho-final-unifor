"""Generate local Compose credentials without overwriting an existing environment."""
import os
import secrets
from pathlib import Path


def main():
    target = Path(__file__).resolve().parents[1] / ".env"
    values = {
        "DD_DATABASE_PASSWORD": secrets.token_hex(24),
        "DD_SECRET_KEY": secrets.token_hex(32),
        "DD_CREDENTIAL_AES_256_KEY": secrets.token_hex(16),
        "DD_ADMIN_PASSWORD": secrets.token_hex(24),
    }
    try:
        fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        print(".env ja existe; nenhuma credencial foi alterada.")
        return
    with os.fdopen(fd, "w") as stream:
        for key, value in values.items():
            stream.write(f"{key}={value}\n")
    print(".env criado com permissoes 0600. Consulte DD_ADMIN_PASSWORD localmente.")


if __name__ == "__main__":
    main()

