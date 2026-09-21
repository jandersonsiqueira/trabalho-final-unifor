"""Upload validated reports. Credentials are read only from the environment."""
import argparse
import base64
import json
import os
import sys
import time
import uuid
from pathlib import Path
from urllib.parse import urlsplit

import requests

from validate_report import validate


def required(name):
    value = os.environ.get(name, "").strip()
    if not value:
        raise ValueError(f"Configure {name}")
    return value


def base_url(name):
    value = required(name).rstrip("/")
    parsed = urlsplit(value)
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError(f"{name} deve conter apenas a URL base")
    if parsed.scheme != "https" and not (
        parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1", "::1"}
    ):
        raise ValueError(f"{name}: use HTTPS; HTTP permitido somente em loopback")
    return value


def call(method, url, **kwargs):
    response = requests.request(method, url, timeout=(10, 120), allow_redirects=False, **kwargs)
    if not 200 <= response.status_code < 300:
        # API responses can reflect credentials; do not print their bodies.
        raise RuntimeError(f"API retornou HTTP {response.status_code}; consulte a configuracao e os logs do servico")
    try:
        return response.json()
    except ValueError as exc:
        raise RuntimeError("API retornou resposta sem JSON") from exc


def dojo(path):
    url = base_url("DOJO_URL")
    engagement = required("DOJO_ENGAGEMENT_ID")
    if not engagement.isdigit() or int(engagement) < 1:
        raise ValueError("DOJO_ENGAGEMENT_ID deve ser um inteiro positivo")
    headers = {"Authorization": f"Token {required('DOJO_API_KEY')}"}
    fields = {
        "scan_type": "SARIF",
        "engagement": engagement,
        "test_title": "VAmPI - Semgrep SARIF",
        "minimum_severity": "Info",
        "active": "true",
        "verified": "false",
        "close_old_findings": "false",
    }
    test = os.environ.get("DOJO_TEST_ID", "").strip()
    if not test:
        tests = call("GET", f"{url}/api/v2/tests/", headers=headers,
                     params={"engagement": engagement, "title": fields["test_title"], "limit": 100})
        matches = [item for item in tests.get("results", []) if item.get("title") == fields["test_title"]]
        if len(matches) > 1 or tests.get("next"):
            raise ValueError("Mais de um Test candidato; configure DOJO_TEST_ID explicitamente")
        if matches:
            test = str(matches[0]["id"])
    if test:
        if not test.isdigit() or int(test) < 1:
            raise ValueError("DOJO_TEST_ID deve ser um inteiro positivo")
        fields["test"] = test
    with path.open("rb") as stream:
        endpoint = "reimport-scan" if test else "import-scan"
        result = call("POST", f"{url}/api/v2/{endpoint}/", headers=headers,
                      data=fields, files={"file": (path.name, stream, "application/json")})
    test_id = result.get("test")
    if not test_id:
        raise RuntimeError("DefectDojo nao confirmou o Test de destino")
    print(f"DefectDojo: importacao aceita; Test {test_id}; confira findings e triagem no painel.")
    return {"destination": "DefectDojo", "test": test_id, "engagement": engagement,
            "status": "accepted", "file": path.name}


def dtrack(path, project_env, poll_seconds=300):
    url = base_url("DTRACK_URL")
    project = str(uuid.UUID(required(project_env)))
    headers = {"X-Api-Key": required("DTRACK_API_KEY")}
    result = call("PUT", f"{url}/api/v1/bom", headers=headers, json={
        "project": project, "bom": base64.b64encode(path.read_bytes()).decode("ascii")
    })
    token = str(uuid.UUID(result["token"]))
    print(f"Dependency-Track: SBOM aceito para {project}; aguardando processamento.", flush=True)
    deadline = time.monotonic() + poll_seconds
    while True:
        state = call("GET", f"{url}/api/v1/bom/token/{token}", headers=headers)
        if state.get("processing") is False:
            break
        if state.get("processing") is not True:
            raise RuntimeError("Resposta inesperada ao consultar processamento do SBOM")
        if time.monotonic() >= deadline:
            raise TimeoutError("SBOM aceito, mas processamento excedeu o prazo; confira o projeto antes de reenviar")
        time.sleep(5)
    components = call("GET", f"{url}/api/v1/component/project/{project}",
                      headers=headers, params={"pageNumber": 1, "pageSize": 1})
    if not isinstance(components, list) or not components:
        raise RuntimeError("Processamento terminou, mas nenhum componente foi confirmado no projeto")
    print("Dependency-Track: processamento encerrado e componentes presentes. Analise de CVEs e assincrona.")
    return {"destination": "Dependency-Track", "project": project,
            "status": "processed-components-present", "file": path.name,
            "vulnerability_analysis": "verify-in-dashboard"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", choices=["dojo", "dtrack"])
    parser.add_argument("file", type=Path)
    parser.add_argument("--project-env", default="DTRACK_PROJECT_UUID")
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()
    args.receipt.unlink(missing_ok=True)
    validate(args.file)
    result = dojo(args.file) if args.destination == "dojo" else dtrack(args.file, args.project_env)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError, OSError, KeyError, requests.RequestException) as exc:
        if isinstance(exc, requests.RequestException):
            print("Falha de conexao, TLS ou timeout. Verifique URL e disponibilidade do servico.", file=sys.stderr)
        else:
            print(f"Falha: {exc}", file=sys.stderr)
        sys.exit(1)
