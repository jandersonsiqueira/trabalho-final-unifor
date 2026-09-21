"""Check report structure and reject empty inventories or failed scans."""
import argparse
import json
from pathlib import Path


def validate(path):
    data = json.loads(Path(path).read_text())
    if str(path).endswith(".sarif"):
        if data.get("version") != "2.1.0" or not data.get("runs"):
            raise ValueError("SARIF 2.1.0 com pelo menos um run e obrigatorio")
        count = 0
        for run in data["runs"]:
            if not run.get("tool", {}).get("driver", {}).get("name"):
                raise ValueError("SARIF sem identificacao da ferramenta")
            for invocation in run.get("invocations", []):
                if invocation.get("executionSuccessful") is False:
                    raise ValueError("SARIF informa falha de execucao")
                if any(n.get("level") == "error" for n in invocation.get("toolExecutionNotifications", [])):
                    raise ValueError("SARIF contem erro de analise")
            count += len(run.get("results", []))
        message = f"{path}: SARIF valido; {count} findings (triagem pendente)"
    else:
        if data.get("bomFormat") != "CycloneDX" or data.get("specVersion") != "1.6":
            raise ValueError("Esperado CycloneDX 1.6")
        components = data.get("components", [])
        if not components:
            raise ValueError("SBOM sem componentes; verificar resolucao das dependencias")
        if not all(c.get("name") and c.get("type") for c in components):
            raise ValueError("SBOM possui componente sem nome ou tipo")
        message = f"{path}: CycloneDX valido; {len(components)} componentes (nao e contagem de CVEs)"
    print(message)
    return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+")
    args = parser.parse_args()
    for file in args.files:
        validate(file)

