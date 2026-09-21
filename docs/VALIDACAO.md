# Registro de validacao

Validacao local: 19/09/2026. Ambiente: macOS Intel, Docker Desktop 29.2.0.

Publicacao no GitHub: 21/09/2026. A primeira execucao concluiu o SAST, mas os dois jobs SCA falharam por permissoes nos volumes do cdxgen. A correcao utiliza o UID/GID do host no scanner e exportacao da imagem pelo usuario local. A execucao completa com integracoes permanece pendente.

Na retomada do ambiente em 21/09/2026, o Dependency-Track falhou ao abrir o banco H2 (`MVStoreException: Chunk 4657 not found`). O volume foi preservado. A recuperacao do banco e necessaria antes de novos uploads.

## Implementado e verificado

| Item | Resultado observado |
| --- | --- |
| YAML | Workflow, configuracao actionlint e Compose carregados sem erro |
| Workflow | `actionlint 1.7.12` aprovado, incluindo expressoes e label personalizado |
| Bash | `bash -n` aprovado em `prepare.sh` e `scan.sh` |
| Python | Arquivos analisados pelo parser e testes executados |
| Testes de contrato | 10 testes aprovados, incluindo falhas HTTP, redirects, timeout, SBOM vazio e reimportacao |
| Docker Compose | `docker compose config --quiet` aprovado; todos os servicos iniciados |
| Inicializacao Dojo | Migracoes concluidas; initializer terminou com codigo 0 |
| Build VAmPI | Dockerfile original construido com sucesso, sem iniciar a API |
| Semgrep | 332 regras executadas, 22 arquivos analisados, 8 resultados; SARIF 2.1.0 gerado |
| SARIF formal | Validado contra schema SARIF 2.1.0 do SchemaStore |
| cdxgen fonte | CycloneDX 1.6, 26 componentes; execucao final com `--fail-on-error` concluida |
| cdxgen imagem | CycloneDX 1.6, 388 componentes de software, gerado a partir de `docker save`, sem socket no scanner |
| SBOMs formais | Ambos validados contra schema oficial CycloneDX 1.6, incluindo referencias SPDX usadas nos arquivos |
| DefectDojo | Importacao real aceita: Engagement 1, Test 1, 8 findings; consulta retornou 4 High e 4 Medium |
| Dojo recorrente | Reimportacao real confirmou o mesmo Test 1 |
| Dependency-Track fonte | Upload, token de processamento e presenca de componentes confirmados |
| Dependency-Track imagem | Upload, token de processamento e presenca de componentes confirmados apos ajuste de compatibilidade |
| Fonte de vulnerabilidades | OSV/PyPI habilitado; reinicio iniciou importacao de 25.644 advisories. Conclusao ainda deve ser conferida |

Os testes automatizados usam respostas simuladas para caminhos de erro. Os uploads listados acima foram realizados nas plataformas Docker reais, separadamente desses testes.

## Arquivos e acesso local

- DefectDojo: http://localhost:8080. Usuario `admin`, senha em `DD_ADMIN_PASSWORD` no `.env`.
- Dependency-Track: http://localhost:8082. Usuario `admin`, senha alterada e salva em `DTRACK_ADMIN_PASSWORD` no `.env`.
- API do Dependency-Track: http://localhost:8081.
- Projetos: `VAmPI / fonte` e `VAmPI / imagem`, com UUIDs diferentes em `.env.integrations`.
- Configuracoes e chaves locais: `.env.integrations`, permissao 0600, ignorado pelo Git. Nao compartilhar esse arquivo.
- Resultados: `reports/semgrep.sarif`, `reports/sbom.json`, `reports/sbom-image.json`.
- Logs: `reports/semgrep.log`, `reports/cdxgen-source.log`, `reports/cdxgen-image.log`, `reports/image-build.log` e logs de upload.
- Comprovantes: `reports/uploads/dojo.json`, `reports/uploads/dtrack-source.json`, `reports/uploads/dtrack-image.json`.
- Identificacao da imagem: `reports/image-id.txt`; commit do alvo em `config/tools.env` e arquivos `*-commit.txt`.

`docker compose up -d` inicia as plataformas e `docker compose down` encerra o laboratorio preservando volumes. O VAmPI nao e executado como servidor.

## Limites e ajustes observados

1. Semgrep `auto` nao aceita metricas desligadas nessa versao. O comando usa `--metrics=auto`; findings nao interrompem o scan, mas falhas reais permanecem visiveis.
2. No Dojo testado, reimportar sem Test ID inicialmente retornou `product_name parameter missing`. O cliente agora consulta o Test, importa quando ausente e reimporta pelo ID quando existente.
3. O inventario inicial da imagem tinha 512 componentes, incluindo 124 ativos criptograficos. Dependency-Track 4.14 rejeitou esse classificador durante o processamento, embora o upload tivesse sido aceito. O inventario final limita tipos pelo proprio cdxgen e tem 388 componentes: 92 bibliotecas, 289 arquivos, 3 frameworks e 4 aplicacoes. A ingestao final foi confirmada.
4. O scan da imagem usa arquivo exportado em vez de acesso ao daemon Docker. A exportacao permanece em `.work/images/`, ignorada pelo Git e fora dos artifacts da pipeline.
5. O fonte inclui um componente declarado sem versao e outro resolvido para `swagger-ui-bundle`. O Dependency-Track tambem registrou aviso de grafo sem raiz correspondente. As contagens brutas nao equivalem a bibliotecas unicas; relacoes diretas/transitivas devem ser revisadas.
6. A imagem oficial do cdxgen emite aviso sobre seu proprio `NODE_PATH`, configurado pelo wrapper da ferramenta. Nenhum Secret de upload e passado ao scanner. O aviso nao e finding do VAmPI.
7. A base NVD estava sincronizando e registrou avisos de alguns CPEs externos; OSS Index requer credencial e foi ignorado pela plataforma. OSV/PyPI foi habilitado para analise sem chave externa. A contagem final de CVEs depende da conclusao da sincronizacao.
8. O banco do Dependency-Track e embarcado e tem limite de memoria adequado apenas a este laboratorio pequeno. A primeira inicializacao do Dojo levou varios minutos.

## Ainda necessario para entregar

- Recuperar o banco local do Dependency-Track e conferir projetos e credenciais.
- Cadastrar o runner temporario com label `devsecops-lab`. Os dois Secrets e as cinco Variables obrigatorias foram configurados em 21/09/2026.
- Executar o workflow na branch padrao com uploads habilitados; registrar URL, run ID e SHA.
- Confirmar sincronizacao OSV/NVD e reanalisar/reenviar os SBOMs. Registrar os componentes e vulnerabilidades realmente exibidos.
- Capturar os prints do Actions e dos paineis, baixar logs e artifacts.
- Revisar a triagem dos tres findings reais no relatorio; preencher responsaveis, datas e evidencia da execucao final.
- Preencher nome/matricula, remover marcadores pendentes e exportar o relatorio para PDF.

O relatorio inclui a analise de tres achados SAST da execucao local. As evidencias da pipeline completa serao anexadas apos a validacao das integracoes no CI.
