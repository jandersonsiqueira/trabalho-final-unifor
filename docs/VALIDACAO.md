# Registro de validação

**Janderson Siqueira — Matrícula 2515965**

Ambiente local utilizado: macOS Intel e Docker Desktop.

## 1. Status final

A implementação foi validada localmente e posteriormente executada de ponta a ponta por meio do GitHub Actions.

A execução final utilizada como evidência foi:

* GitHub Actions Run #4;
* Run ID `35643067274`;
* branch `main`;
* evento `workflow_dispatch`;
* conclusão: `success`;
* commit do workflow: `f16f73d09537f3cdaedd86f2063f2741a4aecfbc`;

Os quatro jobs foram concluídos com sucesso:

| Job                      | Resultado |
| ------------------------ | --------- |
| 1 - SAST e SARIF         | Sucesso   |
| 2 - SCA e SBOM do fonte  | Sucesso   |
| 3 - SCA e SBOM da imagem | Sucesso   |
| 4 - Integrações locais   | Sucesso   |

O alvo utilizado nas análises foi o VAmPI no commit:

`f16052dce83f05847133ec98f01c5193a41de7d8`

## 2. Implementado e verificado

| Item                        | Resultado observado                                             |
| --------------------------- | --------------------------------------------------------------- |
| YAML                        | Workflow, configuração actionlint e Compose carregados sem erro |
| Workflow                    | `actionlint 1.7.12` aprovado                                    |
| Bash                        | `bash -n` aprovado em `prepare.sh` e `scan.sh`                  |
| Python                      | Arquivos analisados pelo parser e testes executados             |
| Testes de contrato          | 10 testes aprovados                                             |
| Docker Compose              | `docker compose config --quiet` aprovado                        |
| DefectDojo                  | Serviços inicializados e integração confirmada                  |
| Dependency-Track            | API e frontend inicializados e integração confirmada            |
| Build VAmPI                 | Imagem Docker construída com sucesso sem iniciar a API          |
| Semgrep                     | 332 regras, 22 arquivos e 8 findings                            |
| SARIF                       | SARIF 2.1.0 válido                                              |
| cdxgen fonte                | CycloneDX 1.6 com 26 componentes                                |
| cdxgen imagem               | CycloneDX 1.6 com 388 componentes                               |
| DefectDojo                  | 8 findings ativos: 4 High e 4 Medium                            |
| Dojo recorrente             | Importação/reimportação utilizando Test 1                       |
| Dependency-Track fonte      | SBOM aceito, processado e componentes presentes                 |
| Dependency-Track imagem     | SBOM aceito, processado e componentes presentes                 |
| Análise de vulnerabilidades | Concluída para os dois projetos no Dependency-Track             |
| GitHub Actions              | Quatro jobs da Run #4 concluídos com sucesso                    |
| Self-hosted runner          | Job de integrações executado com label `devsecops-lab`          |

Os testes automatizados de contrato utilizam respostas simuladas para validar caminhos de erro.

Os uploads registrados na execução final foram realizados contra as plataformas reais executadas localmente.

## 3. SAST — Semgrep

Versão utilizada:

`Semgrep 1.177.0`

Resultado da execução final:

| Métrica                                   |   Resultado |
| ----------------------------------------- | ----------: |
| Arquivos analisados                       |          22 |
| Regras executadas                         |         332 |
| Findings                                  |           8 |
| Findings bloqueantes reportados pelo scan |           8 |
| Formato                                   | SARIF 2.1.0 |

O SARIF foi validado antes de ser utilizado na integração.

O artifact correspondente ao SAST foi produzido com sucesso e posteriormente recuperado pelo job de integrações locais.

## 4. SCA — código-fonte

Versão utilizada:

`cdxgen 12.8.4`

Resultado:

* formato CycloneDX 1.6;
* 26 componentes;
* arquivo `reports/sbom.json`;
* upload aceito pelo Dependency-Track.

Projeto:

`VAmPI / fonte`

UUID:

`b68d1eb3-d2c3-4c45-9699-0e4b7d478f25`

Após o processamento do SBOM, o Dependency-Track apresentou:

| Severidade | Quantidade |
| ---------- | ---------: |
| Critical   |          0 |
| High       |          9 |
| Medium     |         14 |
| Low        |          3 |
| Unassigned |          1 |

Risk Score:

`95`

Último BOM Import observado:

`21/09/2026 16:14:28`

Última Vulnerability Analysis observada:

`21/09/2026 16:14:29`

Última Measurement observada:

`21/09/2026 16:14:33`

## 5. SCA — imagem Docker

A imagem utilizada para análise foi construída com sucesso.

Image ID registrado na execução:

`sha256:6a686ebc02eec3b1b3945b09397861725f368897289320ac3b8fe81a2eee3e0d`

O scan da imagem foi realizado sobre uma exportação local da imagem, evitando fornecer o socket do Docker ao scanner.

Resultado:

* formato CycloneDX 1.6;
* 388 componentes;
* arquivo `reports/sbom-image.json`;
* upload aceito pelo Dependency-Track.

Projeto:

`VAmPI / imagem`

UUID:

`e91927db-1fa1-4bc1-a6b8-010bf4b81480`

Após o processamento do SBOM, o Dependency-Track apresentou:

| Severidade | Quantidade |
| ---------- | ---------: |
| Critical   |          0 |
| High       |         11 |
| Medium     |         26 |
| Low        |          5 |
| Unassigned |          1 |

Risk Score:

`143`

Último BOM Import observado:

`21/09/2026 16:14:34`

Última Vulnerability Analysis observada:

`21/09/2026 16:14:35`

Última Measurement observada:

`21/09/2026 16:14:45`

## 6. DefectDojo

O SARIF produzido pelo Semgrep foi enviado ao DefectDojo.

Configuração utilizada na execução final:

* Engagement ID: `1`;
* Test ID: `1`;
* findings ativos: `8`;
* High: `4`;
* Medium: `4`;
* fechados: `0`;
* risco aceito: `0`.

O log da integração confirmou:

`DefectDojo: importacao aceita; Test 1`

A reimportação foi validada anteriormente utilizando o mesmo Test, evitando a criação de um novo teste a cada execução.

## 7. Dependency-Track

Os dois SBOMs foram aceitos pelo Dependency-Track.

O cliente de integração realizou:

1. envio do SBOM;
2. recebimento do token de processamento;
3. acompanhamento do processamento;
4. confirmação da presença dos componentes.

O log final registrou para os dois projetos:

`Dependency-Track: SBOM aceito; processamento encerrado e componentes presentes. Analise de CVEs e assincrona.`

Posteriormente, a interface confirmou a conclusão da análise de vulnerabilidades para os dois projetos.

### Comparação final

| Projeto        | Componentes | Critical | High | Medium | Low | Unassigned | Risk Score |
| -------------- | ----------: | -------: | ---: | -----: | --: | ---------: | ---------: |
| VAmPI / fonte  |          26 |        0 |    9 |     14 |   3 |          1 |         95 |
| VAmPI / imagem |         388 |        0 |   11 |     26 |   5 |          1 |        143 |

## 8. Artifacts da execução final

A execução final produziu e recuperou os artifacts necessários para as integrações.

Entre eles:

* relatório SARIF do Semgrep;
* SBOM CycloneDX do código-fonte;
* SBOM CycloneDX da imagem;
* recibos das integrações.

Os principais arquivos locais utilizados são:

* `reports/semgrep.sarif`;
* `reports/sbom.json`;
* `reports/sbom-image.json`;
* `reports/image-id.txt`;
* `reports/uploads/dojo.json`;
* `reports/uploads/dtrack-source.json`;
* `reports/uploads/dtrack-image.json`.

Os artifacts da execução possuem retenção configurada no GitHub Actions.

## 9. Arquivos e acesso local

DefectDojo:

`http://localhost:8080`

Dependency-Track frontend:

`http://localhost:8082`

Dependency-Track API:

`http://localhost:8081`

As senhas e API Keys não são versionadas.

As credenciais locais são mantidas nos arquivos `.env` e `.env.integrations`, que estão ignorados pelo Git.

O arquivo `.env.integrations` utiliza permissão `0600`.

As credenciais utilizadas pela pipeline são armazenadas como GitHub Secrets, enquanto URLs e identificadores não sensíveis são configurados como Variables.

## 10. Ajustes e problemas encontrados durante a validação

### 10.1 Permissões do cdxgen

Na primeira execução publicada no GitHub, o SAST foi concluído, porém os jobs de SCA apresentaram falha relacionada às permissões dos volumes utilizados pelo cdxgen.

A solução foi executar o scanner utilizando UID/GID compatível com o host e ajustar o processo de exportação da imagem.

Após a correção, os dois jobs SCA foram concluídos com sucesso.

### 10.2 Reimportação no DefectDojo

Durante a validação, uma tentativa de reimportação sem Test ID apresentou erro relacionado ao `product_name`.

O cliente foi ajustado para localizar o Test existente e realizar `reimport-scan` utilizando seu identificador.

A execução final confirmou o uso do Test ID `1`.

### 10.3 Componentes da imagem

O inventário inicial da imagem continha 512 componentes, incluindo 124 ativos criptográficos.

O Dependency-Track 4.14 apresentou incompatibilidade com esse classificador durante o processamento.

O inventário foi ajustado por meio das opções do próprio cdxgen, resultando em **388 componentes de software** compatíveis com a plataforma:

* 92 bibliotecas;
* 289 arquivos;
* 3 frameworks;
* 4 aplicações.

A ingestão final foi confirmada.

### 10.4 Banco do Dependency-Track

Durante a retomada do laboratório em 21/09/2026, o banco H2 do Dependency-Track apresentou:

`MVStoreException: Chunk 4657 not found`

Como se tratava de ambiente acadêmico descartável, os volumes específicos do Dependency-Track foram recriados e a plataforma foi inicializada novamente.

Novos projetos e credenciais foram gerados.

Após a recuperação:

* API respondeu HTTP 200;
* projetos foram recriados;
* nova API Key foi configurada;
* SBOM do fonte foi enviado com sucesso;
* SBOM da imagem foi enviado com sucesso;
* análise de vulnerabilidades foi concluída.

### 10.5 API Key após a recriação

A primeira execução da pipeline após recriar o Dependency-Track apresentou HTTP 401 nos dois uploads de SBOM.

O problema foi identificado como uma API Key antiga armazenada no GitHub Secret `DTRACK_API_KEY`.

O Secret foi atualizado com a nova chave gerada pelo ambiente recriado.

Após a atualização, a Run #4 concluiu todas as integrações com sucesso.

## 11. Limitações conhecidas

O Semgrep em modo `auto` depende do conjunto de regras disponibilizado pelo registry, portanto a quantidade de regras pode variar em execuções futuras.

O SAST identifica padrões potencialmente inseguros, mas não comprova explorabilidade.

O SCA depende da qualidade do inventário e das bases de vulnerabilidades utilizadas pelo Dependency-Track.

A quantidade de componentes não deve ser interpretada como quantidade de CVEs.

O projeto de fonte contém componente declarado sem versão e uma ocorrência resolvida de `swagger-ui-bundle`. Também foi observado aviso relacionado ao grafo de dependências, portanto classificações entre dependências diretas e transitivas devem ser interpretadas com cautela.

O VAmPI não foi iniciado como servidor durante as análises deste trabalho.

DAST não faz parte do escopo final.

## 12. Resultado final

A validação foi concluída com sucesso.

Foram confirmados:

* execução do SAST;
* geração e validação do SARIF;
* geração dos dois SBOMs;
* construção e análise da imagem;
* armazenamento e recuperação dos artifacts;
* upload real para o DefectDojo;
* upload real dos dois SBOMs para o Dependency-Track;
* processamento dos componentes;
* análise das vulnerabilidades;
* execução do job de integração por self-hosted runner;
* conclusão dos quatro jobs da pipeline.

A Run #4 representa a execução final validada do trabalho.

Não permanecem pendências técnicas necessárias para demonstrar a integração solicitada. As evidências visuais capturadas do GitHub Actions, DefectDojo e Dependency-Track complementam este registro e o relatório final.
