"""Bootstrap the local lab through official APIs; keep credentials out of logs."""
import datetime
import getpass
import os
import secrets
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]


def read_env(path):
    return dict(line.split("=", 1) for line in path.read_text().splitlines()
                if line and not line.startswith("#"))


def request(method, url, **kwargs):
    response = requests.request(method, url, timeout=(10, 120), allow_redirects=False, **kwargs)
    if not 200 <= response.status_code < 300:
        raise RuntimeError(f"Configuracao local: HTTP {response.status_code} em {urlsplit_path(url)}")
    return response


def urlsplit_path(url):
    from urllib.parse import urlsplit
    return urlsplit(url).path


def main():
    output = ROOT / ".env.integrations"
    if output.exists():
        print(".env.integrations ja existe. Use os objetos existentes ou configure novos pela interface.")
        return
    values = read_env(ROOT / ".env")
    if "DTRACK_ADMIN_PASSWORD" not in values:
        values["DTRACK_ADMIN_PASSWORD"] = secrets.token_hex(24)
        with (ROOT / ".env").open("a") as stream:
            stream.write(f"DTRACK_ADMIN_PASSWORD={values['DTRACK_ADMIN_PASSWORD']}\n")
    dojo = "http://localhost:8080"
    dtrack = "http://localhost:8081"
    # Try the saved password first, allowing a retry after a partial bootstrap.
    login = requests.post(f"{dtrack}/api/v1/user/login", timeout=(10, 30),
                          data={"username": "admin", "password": values["DTRACK_ADMIN_PASSWORD"]})
    if login.status_code != 200:
        current = getpass.getpass("Senha atual do admin do Dependency-Track (primeiro acesso: senha de fabrica): ")
        login = request("POST", f"{dtrack}/api/v1/user/login",
                        data={"username": "admin", "password": current}) if current == values["DTRACK_ADMIN_PASSWORD"] else None
        if login is None:
            change = requests.post(f"{dtrack}/api/v1/user/forceChangePassword", timeout=(10, 30), data={
                "username": "admin", "password": current,
                "newPassword": values["DTRACK_ADMIN_PASSWORD"], "confirmPassword": values["DTRACK_ADMIN_PASSWORD"]})
            if change.status_code != 200:
                raise RuntimeError("Nao foi possivel trocar a senha inicial. Configure pela interface ou use a senha salva no .env.")
            login = request("POST", f"{dtrack}/api/v1/user/login",
                            data={"username": "admin", "password": values["DTRACK_ADMIN_PASSWORD"]})
    dt_headers = {"Authorization": f"Bearer {login.text}"}
    request("POST", f"{dtrack}/api/v1/configProperty", headers=dt_headers, json={
        "groupName": "vuln-source", "propertyName": "google.osv.enabled",
        "propertyValue": "PyPI", "propertyType": "STRING"})
    token = request("POST", f"{dojo}/api/v2/api-token-auth/", json={
        "username": "admin", "password": values["DD_ADMIN_PASSWORD"]}).json()["token"]
    dj_headers = {"Authorization": f"Token {token}"}

    def dojo_object(endpoint, name, extra):
        existing = request("GET", f"{dojo}/api/v2/{endpoint}/", headers=dj_headers,
                           params={"name": name}).json()["results"]
        matching = [item for item in existing if item["name"] == name]
        if matching:
            return matching[0]
        return request("POST", f"{dojo}/api/v2/{endpoint}/", headers=dj_headers,
                       json={"name": name, **extra}).json()

    product_type = dojo_object("product_types", "Academico", {})
    product = dojo_object("products", "VAmPI", {"description": "Laboratorio DevSecOps UNIFOR", "prod_type": product_type["id"]})
    today = datetime.date.today()
    engagement = dojo_object("engagements", "DevSecOps UNIFOR", {
        "product": product["id"], "target_start": today.isoformat(),
        "target_end": (today + datetime.timedelta(days=90)).isoformat(),
        "engagement_type": "CI/CD", "status": "In Progress"})
    projects = {}
    for version, key in [("fonte", "DTRACK_PROJECT_UUID"), ("imagem", "DTRACK_IMAGE_PROJECT_UUID")]:
        existing = request("GET", f"{dtrack}/api/v1/project", headers=dt_headers,
                           params={"name": "VAmPI"}).json()
        match = next((p for p in existing if p["name"] == "VAmPI" and p.get("version") == version), None)
        project = match or request("PUT", f"{dtrack}/api/v1/project", headers=dt_headers,
                                  json={"name": "VAmPI", "version": version, "active": True}).json()
        projects[key] = project["uuid"]
    teams = request("GET", f"{dtrack}/api/v1/team", headers=dt_headers).json()
    team = next((t for t in teams if t["name"] == "GitHub Actions"), None)
    if team is None:
        team = request("PUT", f"{dtrack}/api/v1/team", headers=dt_headers, json={"name": "GitHub Actions"}).json()
    for permission in ["BOM_UPLOAD", "VIEW_PORTFOLIO"]:
        request("POST", f"{dtrack}/api/v1/permission/{permission}/team/{team['uuid']}", headers=dt_headers)
    api_key = request("PUT", f"{dtrack}/api/v1/team/{team['uuid']}/key", headers=dt_headers).json()["key"]
    integration = {"DOJO_URL": dojo, "DOJO_API_KEY": token, "DOJO_ENGAGEMENT_ID": str(engagement["id"]),
                   "DTRACK_URL": dtrack, "DTRACK_API_KEY": api_key, **projects}
    fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as stream:
        for key, value in integration.items():
            stream.write(f"{key}={value}\n")
    print("Projetos, Engagement e chaves configurados. Credenciais em .env.integrations (0600).")
    print("Senha do Dependency-Track em DTRACK_ADMIN_PASSWORD no .env. Nao publique esses arquivos.")
    print("OSV/PyPI habilitado. Reinicie dtrack-apiserver para iniciar a primeira sincronizacao.")


if __name__ == "__main__":
    try:
        main()
    except (requests.RequestException, RuntimeError, KeyError, OSError, ValueError) as exc:
        if isinstance(exc, requests.RequestException):
            raise SystemExit("Falha de conexao. Aguarde as plataformas e confira suas URLs locais.") from None
        raise SystemExit(str(exc)) from None
