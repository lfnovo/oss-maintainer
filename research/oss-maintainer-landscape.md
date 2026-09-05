# Panorama: plugins e agentes para mantenedores de projetos open source

**Data da pesquisa:** 2026-09-05
**Objetivo:** ampliar o campo de visão antes de fechar o desenho do plugin `oss-maintainer` (Claude Code + Codex) e do diretório de perfil por repositório `.maintainer/`.
**Método:** cinco frentes de pesquisa em paralelo (plugins e skills nos ecossistemas de agentes; agentes integrados ao GitHub; baseline não agêntico; padrões de configuração por repositório; processos de mantenedores de referência), com busca web, leitura das páginas primárias (docs oficiais, READMEs, arquivos crus via `raw.githubusercontent.com`) e metadados via API do GitHub (`gh api`) para stars, licença, última release e último push. Contagens de "arquivos no GitHub" vêm do GitHub Code Search e são aproximadas.
**Regra de honestidade:** tudo que não foi confirmado em fonte primária está marcado como **não verificado**. Stars e datas são o valor no dia da coleta.

Os relatórios brutos de cada frente (com todas as URLs e trechos citados) foram gerados no scratchpad da sessão e consolidados aqui; a seção 7 traz a lista completa de fontes.

---

## 1. Resumo executivo

1. **Nenhum ecossistema tem plugin oficial "de mantenedor OSS".** O marketplace oficial do Claude Code (291 plugins) e o comunitário (2.282), o `openai/plugins` do Codex (64), o marketplace do Cursor, as extensões do Gemini CLI e o OpenCode não têm nada de release orchestration, triage de issues, changelog ou Discussions. O que existe oficialmente são GitHub Actions dos vendors (claude-code-action, run-gemini-cli, codex-action, OpenCode) com exemplos de triage e review, produtos SaaS de PR review, e conectores GitHub MCP.
2. **Release orchestration com gates humanos não existe como produto.** Os melhores exemplares são skills escritas dentro de um repositório específico: `final-release-review` e `release-candidate-prep` do OpenAI Agents SDK (resultado binário GREEN LIGHT / BLOCKED, humano dono do push), `opendal-release` do Apache OpenDAL (máquina de 11 estados com voto de 72h em Discussion), `release` do GitTools/GitVersion (fases + `AskUserQuestion` + `allowed-tools`), e o padrão interno do `github/gh-aw` (`changeset.md` + `release.md`, em que o agente só escreve highlights e o gate é um environment approval do Actions).
3. **Facilitação de GitHub Discussions é a lacuna mais clara.** Só Dosu (modos Mention / Auto Draft / Auto Reply por categoria) e Inkeep respondem em Discussions; nenhuma ferramenta qualifica ideias, decompõe em necessidades, verifica alegações no código ou gradua para Issues. As Actions oficiais de Claude, Gemini e OpenCode não têm gatilho `discussion`.
4. **Smoke test e2e como gate de release não existe como skill reutilizável**, e tampouco a publicação de imagem Docker ou pacote npm como skill; PyPI tem cobertura parcial (`python-pypi-package-builder`, `shipit-skill`).
5. **O baseline clássico está consolidado, mas o ecossistema Probot hospedado morreu**: `probot/stale` (arquivado 2023), `no-response` (2021), `lock-threads-app` (2021), Release Drafter app (deprecado 2019), Release Please app desligado em 2025-08-14. O que sobreviveu virou GitHub Action ou tem dono institucional (Renovate, Dependabot, Mergify). release-please, semantic-release, changesets e git-cliff fazem bump, changelog e tag de forma determinística, mas não decidem risco, não testam o artefato e não fazem retro.
6. **O que os agentes adicionam** é leitura de conteúdo (dedupe semântico, triage por intenção, stale que lê a thread, respostas com citação), issue para PR, autofix de CI e de alertas Dependabot ("Assign to Agent", GA 2026-04-07). **Onde são fracos:** gates com critério explícito, estado persistente por repositório, Discussions, segurança contra prompt injection, custo por execução, e dependência de serviços hospedados que fecham (Sweep pivotou, Mentat sumiu, OpenHands resolver saiu do `main`).
7. **Configuração por repositório segue um padrão universal**: descoberta por caminho fixo, camadas com "mais próximo vence", listas somam, chaves sensíveis travadas no nível org, trust gating para tudo executável, e motor pinado a partir do repo (pre-commit `rev`, Renovate `extends`, `extraKnownMarketplaces`, `.agents/plugins/marketplace.json`). Diretórios ocultos são nomeados pela ferramenta; o único neutro é `.agents/`, e apenas para `skills/` e `plugins/`. **Claude Code não lê `.agents/skills/`** (verificado na documentação).
8. **`.maintainer/` tem precedente literal, mas raro** (63 arquivos em cerca de 9 repositórios, com destaque para o "maintainer knowledge bundle" de `sunbeamdotpt/sbbb` e `sunbeamdotpt/cli`) e um **precedente estrutural forte em `.github/maintainer/`** (plugin `open-source-maintainer` do marketplace `numman-ali/n-skills`, 150 arquivos indexados), que faz exatamente "motor genérico + perfil por repo" com `config.json`, `context.md`, `standing-rules.md`, `release-checklist.md`, `decisions.md` e `state.json`. Nenhuma ferramenta auto-descobre nenhum dos dois caminhos.
9. **Os processos de referência convergem** (Kubernetes, CPython, Django, Node.js, Rust, Apache, PyPA, Sentry): go/no-go nominal e numérico ("zero PRs pendentes, zero testes blocking vermelhos, zero issues no milestone", 3 runs verdes consecutivos), cut em ordem estrita com dry-run antes do real, aprovação humana no ponto de publicar (environment approval, label `accepted`, voto de 72h), smoke do artefato instalado a partir do registry, cherry-pick com critérios e quatro perguntas, release notes com fonte estruturada e créditos, e retro institucionalizada.
10. **Recomendação:** manter a hipótese `.maintainer/` (singular) com `profile.toml` para máquina, prosa curta para escopo e gotchas, scripts e checklists do repo, e estado gitignored; ponteiros em `AGENTS.md` e `CLAUDE.md`; motor pinado pelos dois marketplaces. Extrair do plugin atual tudo que é específico do Open Notebook (portas, alvos `make`, IDs GraphQL, âncoras públicas, jornada do smoke) e adotar os padrões dos melhores exemplares: propose-only, resultado binário controlador, `allowed-tools` restritivo, leitura live de labels, verificação em sistemas externos antes de declarar sucesso.

---

## 2. Panorama

Colunas: ferramenta, categoria, o que faz, configuração por repositório, distribuição, maturidade em 2026-09-05, licença, fonte. Em maturidade, "n/v" = não verificado.

### 2.1 Plugins, skills e agentes nos ecossistemas de agentes de código

| Ferramenta | Categoria | O que faz | Config por repo | Distribuição | Maturidade | Licença | Fonte |
|---|---|---|---|---|---|---|---|
| anthropics/claude-plugins-official | marketplace Claude Code | 291 plugins; nenhum de release, changelog, triage, Discussions ou onboarding | `.claude/settings.json` (`enabledPlugins`, `extraKnownMarketplaces`) | marketplace | 35.9k★, push 2026-09-05 | Apache-2.0 | github.com/anthropics/claude-plugins-official |
| anthropics/claude-plugins-community | marketplace Claude Code | 2.282 plugins (espelho read-only com scan de segurança); idem | idem | marketplace | 3.5k★, push 2026-08-25 | Apache-2.0 | github.com/anthropics/claude-plugins-community |
| code-review (Anthropic) | review de PR | 4 agentes paralelos, score 0 a 100, filtra abaixo de 80, `--comment` posta no PR | `CLAUDE.md` | plugin (repo claude-code) | oficial | Apache-2.0 (repo) | github.com/anthropics/claude-code/tree/main/plugins/code-review |
| pr-review-toolkit, commit-commands, security-guidance, claude-security (Anthropic) | review, git, segurança | agentes de review especializados; commit e PR; avisos e review de diff no Stop; scan de vulnerabilidades | — | plugin oficial | oficial | — | marketplace oficial |
| mattpocock/skills `triage` | triage de issues e PRs | máquina de estados de papéis; disclaimer "generated by AI"; `disable-model-invocation: true`; mapeamento de labels via `/setup` | mapeamento de labels do tracker | skills.sh e plugin oficial `mattpocock-skills` | 252k★, push 2026-09-04 | MIT | github.com/mattpocock/skills |
| numman-ali/n-skills `open-source-maintainer` | manutenção OSS com humano no loop | triage, consolidação de duplicatas, extração de intenção de PR externo (nunca mergeia, reimplementa), aprovação humana para qualquer ação pública, memória por repo | `.github/maintainer/` (`config.json`, `context.md`, `standing-rules.md`, `release-checklist.md`, `decisions.md`, `patterns.md`, `contributors.md`, `state.json`, `notes/`) | marketplace n-skills; declara compatibilidade Claude Code e Codex | 1.0k★, push 2026-09-04 | Apache-2.0 | github.com/numman-ali/n-skills |
| OpenAI Agents SDK skills (`final-release-review`, `release-candidate-prep`, `maintainer-review`, `docs-sync`, `changeset-validation`) | release review e prep in-repo | "controlling checker" GREEN LIGHT / BLOCKED; worktree destacado; nunca roda `gh`, nunca faz push; humano dono do PR; `maintainer-review` com "Need status" | `.agents/skills/` + gatilhos em `AGENTS.md` | in-repo | 29.2k★ (python), 3.8k★ (js) | MIT | github.com/openai/openai-agents-python |
| apache/opendal `opendal-release` | release como máquina de estados | 11 estados (planning até official-release) com voto em Discussion ≥72h; "não declare sucesso até o sistema externo confirmar" | `.agents/skills/` | in-repo | 5.4k★ | Apache-2.0 | github.com/apache/opendal |
| GitTools/GitVersion `release` | release em fases | fases numeradas, `AskUserQuestion`, `allowed-tools` restrito a `gh release`, `gh api`, `git tag`; verifica artefatos e PRs downstream | `.agents/skills/`, `GitReleaseManager.yml` | in-repo | 3.1k★ | MIT | github.com/GitTools/GitVersion |
| googleapis/mcp-toolbox `triage-issues`, `stale-sweep` | triage propose-only | nunca edita labels ou comenta; lê `gh label list`, templates e playbook ao vivo; 4 eixos de label; classifica silêncio em stale | `skills/maintainer/`, `.github/blunderbuss.yml` | in-repo | 16.3k★ | Apache-2.0 | github.com/googleapis/mcp-toolbox |
| github/awesome-copilot skills (`github-release`, `dependabot`, `github-issues`, `make-repo-contribution`, `python-pypi-package-builder`, `mcp-release-qa`, `copilot-pr-autopilot`) | release, deps, issues, publicação | `github-release` para no handoff humano antes de tag e publish; PyPI com Trusted Publishing; QA de servidor MCP pré-release | — | `npx skills add`, `gh skill install` | 38.7k★, push 2026-09-04 | MIT | github.com/github/awesome-copilot |
| NVIDIA/skills (suíte NemoClaw `maintainer-*`) | triage, cut de release, comparação de PRs, sweep de issues | `maintainer-triage`, `cut-release-tag`, `pr-comparator`, `cross-issue-sweep`, loops diários | `.claude-plugin`, `.cursor-plugin`, `.agents` | plugin multi-harness | 3.2k★ (paths n/v) | Apache-2.0 | github.com/NVIDIA/skills |
| wshobson/agents `changelog-automation` | changelog | Keep a Changelog + Conventional Commits, release notes | skill | marketplace multi-harness | 39.4k★ | MIT | github.com/wshobson/agents |
| JimLiu/baoyu-skills `release-skills` | release universal | detecta arquivo de versão, changelog multi-idioma, GitHub Release, backfill | `.releaserc.yml` opcional | skill (`npx skills add`) | 25.7k★ | MIT | github.com/jimliu/baoyu-skills |
| garrytan/gstack (`/ship`, `/qa`, `/document-release`, `/canary`) | release engineer, QA em browser | sync main, testes, push, PR; QA em browser real; monitor pós-deploy | `~/.claude/skills/gstack` | skills dir (clone + setup) | 131.5k★ | MIT | github.com/garrytan/gstack |
| addyosmani/agent-skills `shipping-and-launch` | rollout com gates | checklist pré-voo, rollout por estágios, pontos de aprovação humana | skill | `npx skills add` | 92.4k★ | MIT | github.com/addyosmani/agent-skills |
| scarrillo/release | bump, changelog | `/release:release`, `/release:changelog`, `/release:decisions` | `.claude/config.json` | plugin próprio | 9★, v1.3.3 | MIT | github.com/scarrillo/release |
| FlorianBruniaux `issue-triage` | triage local | auditoria (categoria, duplicatas, risco, staleness) com validação do usuário antes de executar | — | skill de exemplo | 5.9k★ | CC-BY-SA-4.0 | github.com/FlorianBruniaux/claude-code-ultimate-guide |
| nativewind `triage`, openwpm `maintain` | triage e saúde in-repo | reprodução contra release e HEAD, rascunho de comentário; passe periódico de saúde | `.claude/skills/` | in-repo | 8.1k★, 1.4k★ | MIT, n/v | github.com/nativewind/nativewind |
| Arenukvern/skill_steward | governança de repo agêntico | ADRs, `release-changelog-harness`, handoff multi-agente | — | `npx skills add` | 11★ | MIT | github.com/Arenukvern/skill_steward |
| wjgilmore/dependabot-skill | Dependabot | `/dependabot` lista alertas via `gh` e atualiza deps | — | skill | 3★ | MIT | github.com/wjgilmore/dependabot-skill |
| agent-sh/sync-docs, drift-detect | drift de docs e CHANGELOG | entradas faltantes no CHANGELOG, refs quebradas | — | `agentsys install` | 3★, 4★ | MIT | github.com/agent-sh/sync-docs |
| affaan-m/ECC e ecc.tools | harness cross-agente + GitHub App | skills, agentes e regras para Claude, Codex, Cursor, OpenCode; `/ecc-tools analyze` | — | skills + App (grátis em públicos) | 249k★ | MIT | github.com/affaan-m/ECC |
| openai/plugins | marketplace Codex | 64 plugins; `github` é só conector (sem skills), `codex-security` tem 14 skills | `.agents/plugins/marketplace.json` | marketplace | 5.4k★, push 2026-08-28 | por plugin (`github` MIT, `codex-security` proprietary) | github.com/openai/plugins |
| openai/skills (DEPRECATED) | skills Codex | `gh-address-comments`, `gh-fix-ci`, `yeet`, `security-*` | `.agents/skills/` | `$skill-installer` | 25.4k★ | por skill | github.com/openai/skills |
| openai/codex-action | Action Codex | roda `codex exec` com prompt; docs citam "release prep" | `.github/codex/prompts/`, `AGENTS.md` | GitHub Action | 1.2k★, v1.12 | Apache-2.0 | github.com/openai/codex-action |
| mturac/everything-openai-codex `github-ops` | GitHub ops | triage, releases e changelog, Dependabot, stale, via `gh` | — | skill | 89★ | MIT | github.com/mturac/everything-openai-codex |
| Cursor Marketplace | marketplace Cursor | conectores (GitLab, Atlassian, Sentry, Mintlify); nenhum de mantenedor | `.cursor-plugin/plugin.json` | marketplace revisado | oficial | — | cursor.com/marketplace |
| Cursor Automations (Assign PR Reviewers, Triage failed Actions, Review PRs, Summarize daily) | automações cloud | classificação de risco do diff, atribuição de reviewers, triage de CI | config vive na nuvem da Cursor, não no repo | cloud agent (cobrança por uso) | oficial | — | cursor.com/docs/cloud-agent/automations |
| PatrickJS/awesome-cursorrules | rules Cursor | 100% frameworks e linguagens; nada de mantenedor | `.cursor/rules/*.mdc` | lista | 40.7k★ | CC0 | github.com/PatrickJS/awesome-cursorrules |
| google-github-actions/run-gemini-cli | Action Gemini | `gemini-dispatch` (roteador), triage em tempo real e por cron, review de PR com severidade, assistente; forks bloqueados por padrão | `.github/workflows/gemini-*.yml`, `.gemini/commands/*.toml`, `GEMINI.md`, `.gemini/settings.json` | GitHub Action (`/setup-github`) | 2.1k★, v0.1.22, beta | Apache-2.0 | github.com/google-github-actions/run-gemini-cli |
| gemini-cli-extensions `security`, `code-review`, `cicd` | extensões Gemini CLI | análise de segurança do diff e deps; review; `cicd` faz release orchestration do Cloud Deploy (não GitHub) | `gemini extensions install <url>` | extensão | 791★, 531★, 50★ | Apache-2.0 | github.com/gemini-cli-extensions |
| OpenCode GitHub Action | Action OpenCode | `/opencode` em issues e PRs: triage, fix com PR, review, schedule | `.github/workflows/opencode.yml`, `opencode.json` | Action + App | oficial | MIT | opencode.ai/docs/github |
| amestsantim/opencode-github-release | release OpenCode | `suggest_bump` por conventional commits e `create_release`, com confirmação | `opencode.json` | plugin npm | 1★ | MIT | github.com/amestsantim/opencode-github-release |
| agentskills.io, skills.sh, `gh skill` | spec e instaladores | formato `SKILL.md` (cerca de 45 clientes); `npx skills add`; `gh skill install` (desde 2026-04-16) | — | spec, CLI | 25.1k★, 30.4k★ | Apache-2.0, MIT | agentskills.io |
| VoltAgent/awesome-agent-skills, ComposioHQ/awesome-claude-skills, hesreallyhim/awesome-claude-code, sickn33/agentic-awesome-skills | listas | entradas de mantenedor raras; VoltAgent lista NemoClaw; AAS menciona bundle "OSS Maintainer" (composição n/v) | — | listas | 33.8k★, 74.5k★, 53.6k★, 46k★ | MIT, Apache-2.0, —, MIT | ver seção 7 |

### 2.2 Agentes integrados ao GitHub

| Ferramenta | Categoria | O que faz | Config por repo | Distribuição | Maturidade | Licença | Fonte |
|---|---|---|---|---|---|---|---|
| GitHub Agentic Workflows (gh-aw) | workflows agênticos | workflows em Markdown compilados para Actions; agente read-only com "safe outputs" (create/update/close issue, add comment, labels, create PR, create/update/close **discussion**, `update-release` só edita corpo); engines copilot, claude, codex, gemini, pi | `.github/workflows/*.md` compilado em `*.lock.yml`; frontmatter `on`, `permissions`, `engine`, `tools`, `safe-outputs`, `roles` | `gh extension` + Actions | public preview 2026-06-11; 5.1k★; releases quase diárias | MIT | github.com/github/gh-aw |
| githubnext/agentics | pacote de workflows gh-aw | cerca de 50 workflows: `issue-triage`, `ci-doctor`, `ai-moderator`, `weekly-research`, `discussion-task-miner`, `pr-fix`, `repo-status` | `gh aw add <nome>` | Actions | 942★ | MIT | github.com/githubnext/agentics |
| Copilot cloud agent, code review, Autofix, automations, custom agents | agente nativo GitHub | issue para PR; review com custo por review; Autofix CodeQL grátis em públicos; automations (draft release notes semanal) **só em repos privados**; Agent HQ com Claude e Codex | `.github/copilot-instructions.md`, `.github/instructions/*.md`, `AGENTS.md`, `.github/agents/*.agent.md`, `.github/skills/`, `copilot-setup-steps.yml` | nativo | GA (agent 2025-09); automations 2026-06 | proprietário | docs.github.com |
| anthropics/claude-code-action | Action Claude | `@claude` em issues e PRs; agent mode com `prompt`; exemplos de triage, dedupe, review, CI fix, `agent-approval-check`; inputs `plugins` e `plugin_marketplaces` instalam plugins no runner; sem gatilho `discussion` documentado, mas aceita `discussions: write` | workflow YAML + `CLAUDE.md`; `allowed_non_write_users` para triage | Action + App | v1.0.216; 8.8k★ | MIT | github.com/anthropics/claude-code-action |
| Anthropic Code Review | review SaaS | research preview Team e Enterprise; US$15 a 25 por review; não bloqueia merge | `CLAUDE.md`, `REVIEW.md` | SaaS | preview | proprietário | code.claude.com/docs/en/code-review |
| Codex no GitHub (cloud, `@codex review`) | review e tarefas SaaS | review manual ou automático focado em P0 e P1; `@codex` abre tarefas; regras em `AGENTS.md` | `AGENTS.md` (`## Code Review Rules`) | SaaS (planos ChatGPT) | GA; sem programa OSS | proprietário | learn.chatgpt.com/docs/third-party/github |
| OpenHands | resolver, Cloud, Agent Canvas | resolver `fix-me` legado (removido do `main`, só até tag 0.62.0); Cloud com label `openhands`; Canvas beta com automations | `.openhands/` (`setup.sh`, `hooks.json`, skills) | Action legado, SaaS, self-host | Canvas beta; 86k★ | MIT | github.com/OpenHands/OpenHands |
| Sweep | (descontinuado) | bot issue para PR descontinuado; pivot para plugin JetBrains | `sweep.yaml` legado | plugin IDE | repo parado 2025-09 | Sweep EE License | github.com/sweepai/sweep |
| Dosu | respostas e triage | responde issues **e Discussions** com citações; modos Mention / Auto Draft / Auto Reply por categoria; self-documenting PRs; auto-label e stale bot migrados para workflows gh-aw open source | tudo no dashboard; workflows `dosu-ai/auto-label` e `better-stale-bot` | GitHub App SaaS | ativo; Free 200 créditos/mês só em públicos | proprietário (workflows Apache-2.0) | dosu.dev |
| Mentat / MentatBot | review e PR | site fora do ar; org parada desde 2025-10 | — | GitHub App | aparentemente inativo (n/v) | Apache-2.0 (CLI antiga) | github.com/AbanteAI |
| PR-Agent (The-PR-Agent) / Qodo Merge | review e descrição de PR | `/review`, `/describe`, `/improve`, `/update_changelog`, `/generate_labels`; migrou para community-owned | `.pr_agent.toml` | Action, App self-host, CLI; Qodo SaaS | v0.44.0; 12.9k★ | MIT; Qodo proprietário (programa OSS por candidatura) | github.com/The-PR-Agent/pr-agent |
| CodeRabbit | review SaaS | review, 60+ linters, chat, issue enrichment; lê `CLAUDE.md`, `AGENTS.md`, `.cursorrules` como guidelines | `.coderabbit.yaml` | GitHub App | GA; Pro grátis em públicos | proprietário | docs.coderabbit.ai |
| Ellipsis | review incremental, cloud para agentes | review por push; pivot para "Claude Code na nuvem" | `code_review.yaml`, agentes YAML | GitHub App SaaS | pivot; OSS n/v | proprietário | ellipsis.dev |
| cubic | review SaaS | review, custom agents, wiki, scans | `cubic.yaml`, `.cubic/review-agent.md` | GitHub App | ativo; grátis em públicos | proprietário | cubic.dev |
| Greptile | review com grafo de código | config em cascata por diretório; `autoApprove.riskCeiling` | `.greptile/` (`config.json`, `rules.md`, `files.json`) | GitHub App | ativo; grátis OSI com 50+ stars | proprietário | greptile.com |
| Sourcery | review SaaS | resumo, reviewer's guide, comandos `@sourcery-ai` | `.sourcery.yaml` | GitHub App | v1.45.0; grátis em públicos | MIT (repo); serviço proprietário | docs.sourcery.ai |
| Cursor Bugbot | review + autofix | bugs e segurança, "Fix in Cursor" | `.cursor/BUGBOT.md` | GitHub App | usage-based; OSS n/v | proprietário | cursor.com/docs/bugbot |
| Gemini Code Assist for GitHub | review SaaS | resumo e review; `/gemini review` | `.gemini/config.yaml`, `.gemini/styleguide.md` | GitHub App | GA (quota grátis; valores conflitantes, n/v) | proprietário | docs.cloud.google.com |
| Jules (Google Labs) | agente assíncrono | issue ou cron para PR; corrige CI dos próprios PRs | `AGENTS.md`; `jules-action` | App + Action | GA; 15 tarefas/dia grátis | MIT (action) | jules.google |
| Devin Review / Devin | review e agente | `/devin review`, bugs por confiança | `REVIEW.md` | App SaaS | early release; US$500 em ACUs para OSS com 100+ forks | proprietário | docs.devin.ai |
| Graphite Agent, Korbit, Bito, Augment | review SaaS | review de PR | dashboard | App | ativo; Korbit Max e Augment grátis OSS; Bito n/v | proprietário | ver seção 7 |
| Amazon Q Developer for GitHub | agente | `/q dev`, `/q review` | — | App | preview | proprietário | docs.aws.amazon.com |
| Semgrep Assistant, Snyk Agent Fix, Socket, Aikido, Pixee | segurança em PRs | auto-triage e fix de achados; Socket e Aikido grátis OSS | app | App SaaS | ativo; Pixee n/v | proprietário | ver seção 7 |
| Inkeep, kapa.ai | respostas RAG | Inkeep responde issues e Discussions com limiar de confiança; kapa só issues | dashboard, Action | SaaS | ativo; preço OSS n/v | proprietário | docs.inkeep.com |
| Dependabot + agentes | remediação | "Assign to Agent" (Copilot, Claude, Codex) em alertas | — | nativo | GA 2026-04-07; requer Code Security + Copilot | — | github.blog |

### 2.3 Baseline não agêntico

| Ferramenta | Categoria | O que faz | Config por repo | Distribuição | Maturidade | Licença | Fonte |
|---|---|---|---|---|---|---|---|
| Probot | framework | GitHub Apps por webhook; adapter para Actions | por app | lib Node | v14.3.2 (2026-04); 9.6k★ | ISC | github.com/probot/probot |
| probot/stale | stale | fecha inativos | `.github/stale.yml` | GitHub App | **arquivado 2023-05** | ISC | github.com/probot/stale |
| actions/stale | stale | idem; só issues e PRs, **não Discussions** | inputs no workflow | Action | v11.0.0 (2026-07); 1.7k★ | MIT | github.com/actions/stale |
| release-please | release PR + changelog + release | Conventional Commits, Release PR, manifest, monorepo | `release-please-config.json`, `.release-please-manifest.json` | Action v5, CLI (App desligado 2025-08-14) | v17.11.2 (2026-08); 7.5k★ | Apache-2.0 | github.com/googleapis/release-please |
| semantic-release | release do CI | sem Release PR; plugins npm, github, changelog, exec | `.releaserc*`, `release.config.js` | CLI Node em CI | v25.0.9 (2026-08); 24k★ | MIT | github.com/semantic-release/semantic-release |
| changesets | versionamento por arquivos | `.changeset/*.md` por PR; bot + action "Version Packages" | `.changeset/config.json` | CLI + App + Action v2.1.1 | 12.4k★ | MIT | github.com/changesets/changesets |
| all-contributors | créditos | tabela no README por comentário `@all-contributors` | `.all-contributorsrc` | App + CLI | app v1.19.2 (2024) | MIT | github.com/all-contributors/app |
| behaviorbot/welcome, request-info | boas-vindas, pedir info | comentários em issue e PR | `.github/config.yml` | GitHub App (Probot) | hospedagem n/v | MIT | github.com/behaviorbot |
| actions/first-interaction | boas-vindas | mensagem no primeiro issue e PR | inputs | Action | v3.1.0 (2025-10) | MIT | github.com/actions/first-interaction |
| probot/no-response, lee-dohm/no-response | fecha sem resposta | fecha issue sem resposta do autor | `.github/no-response.yml`; inputs | App **arquivado 2021**; Action | v0.5.0 | ISC; MIT | github.com/lee-dohm/no-response |
| dessant/lock-threads | lock | tranca issues, PRs **e discussions** inativas | inputs | Action (App arquivado 2021) | v6.0.2 (2026-05) | MIT | github.com/dessant/lock-threads |
| Dependabot | dependências | alerts, security e version updates; grupos, cooldown; auto-merge via `fetch-metadata` + `gh pr merge --auto` | `.github/dependabot.yml` | nativo | ativo | — | docs.github.com |
| Renovate | dependências | PRs multi-gerenciador, presets, Merge Confidence; sem feature de IA na doc | `renovate.json`, `.github/renovate.json`, `.renovaterc` | App Mend (grátis), CLI, Docker, Action | 44.x (releases diárias); 22.4k★ | AGPL-3.0 | github.com/renovatebot/renovate |
| github-changelog-generator | changelog por issues e PRs | gem Ruby via API | `.github_changelog_generator` | gem | v1.18.0 (2026-03); 7.5k★ | MIT | github.com/github-changelog-generator |
| git-cliff | changelog por commits | templates, `--bump`, `--bumped-version` | `cliff.toml` | binário Rust, Action | v2.14.1 (2026-09); 12.2k★ | MIT / Apache-2.0 | github.com/orhun/git-cliff |
| `.github/release.yml` (GitHub) | release notes nativas | categorias por label, contributors, "Full Changelog" | `.github/release.yml` | nativo | ativo | — | docs.github.com |
| release-drafter | draft release por PRs | categorias, `version-resolver`, autolabeler | `.github/release-drafter.yml` | Action v7 (App deprecado 2019) | v7.7.0 (2026-07); 3.9k★ | ISC | github.com/release-drafter/release-drafter |
| standard-version, commit-and-tag-version | bump local | deprecado; fork mantido | `.versionrc*` | CLI Node | deprecado (2022); v13.1.2 | ISC | github.com/absolute-version/commit-and-tag-version |
| commitizen (Python), cz-cli (Node) | commits e bump | `cz bump`, `cz changelog`; prompt de commit | `pyproject [tool.commitizen]`, `.czrc` | CLI | v4.18.0; v4.3.2 | MIT | github.com/commitizen-tools/commitizen |
| bump-my-version (sucessor de bump2version) | bump | SemVer e CalVer | `.bumpversion.toml`, `pyproject` | CLI Python | 1.5.1 (2026-08) | MIT | callowayproject.github.io/bump-my-version |
| cargo-release | release Rust | dry-run por padrão; config em cascata | `release.toml`, `Cargo.toml` | subcomando cargo | v1.1.5 | Apache-2.0 | github.com/crate-ci/cargo-release |
| GoReleaser | build e publish | multi-plataforma, pacotes, Docker, Homebrew; Pro tem "AI-powered changelog enhancement" (pago) | `.goreleaser.yaml` | CLI, Action | v2.18.0; 16k★ | MIT (OSS) | goreleaser.com |
| python-semantic-release | release Python | porta do semantic-release | `pyproject [tool.semantic_release]` | CLI, Action | v10.6.2 | MIT | python-semantic-release.readthedocs.io |
| towncrier, scriv | news fragments | changelog escrito pelo autor do PR; `scriv github-release` | `towncrier.toml`, `changelog.d/scriv.ini` | CLI Python | 26.9.0; 1.8.0 | MIT; Apache-2.0 | github.com/twisted/towncrier |
| Mergify | regras de PR e merge queue | `pull_request_rules`, `queue_rules`, `extends` | `.mergify.yml` | SaaS + App | ativo; grátis OSS | proprietário | docs.mergify.com |
| Kodiak | automerge | `merge.automerge_label` | `.kodiak.toml` | App (US$ 0) | v0.59.1 (2026-03) | AGPL-3.0 | github.com/chdsbd/kodiak |
| bors-ng, GitHub merge queue | merge | bors arquivado 2024 e aponta para merge queue nativo (GA 2023-07) | `bors.toml`; ruleset | App; nativo | arquivado; GA | Apache-2.0; — | github.com/bors-ng/bors-ng |
| actions/labeler, github/issue-labeler | labels | por path e branch (PRs); por regex (issues) | `.github/labeler.yml` | Action | v7.0.0; v3.5 | MIT | github.com/actions/labeler |
| CODEOWNERS, OWNERS (Kubernetes), MAINTAINERS (Moby) | ownership | reviewers obrigatórios; OWNERS em cascata consumido pelo Prow; MAINTAINERS do Moby hoje é CSV, não TOML | `.github/CODEOWNERS`; `OWNERS`; `MAINTAINERS` | nativo; Prow; texto | ativo | — | docs.github.com |
| repository-settings/app | settings como código | labels, branch protection, rulesets | `.github/settings.yml` | App | v5.0.14 (2026-08) | ISC | github.com/repository-settings/app |
| Issue forms, discussion category forms, health files | templates | `.github/ISSUE_TEMPLATE/*.yml`, `.github/DISCUSSION_TEMPLATE/<slug>.yml`; precedência `.github/` > raiz > `docs/` | `.github/` | nativo | ativo | — | docs.github.com |

---

## 3. O que os agênticos fazem que os bots clássicos não fazem, e onde ainda são fracos

### 3.1 O que os agentes adicionam

| Capacidade | Baseline clássico | Agêntico (exemplos verificados) |
|---|---|---|
| Triage por conteúdo | regex no corpo (`github/issue-labeler`), glob no path (`actions/labeler`), "corpo vazio" (`request-info`) | labels por intenção com aprendizado de correções (`dosu-ai/auto-label`, JSONL em branch `memory/auto-label`); triage com 4 eixos lendo labels ao vivo (`mcp-toolbox`); `claude-issue-triage` no repo do Claude Code; `run-gemini-cli` em tempo real e por cron |
| Duplicatas | inexistente | `claude-dedupe-issues` + `auto-close-duplicates` (dogfooding da Anthropic); `issue-deduplication.yml` de exemplo; Jaccard em `FlorianBruniaux/issue-triage` |
| Stale | por tempo e label (`actions/stale`) | stale que lê a thread antes de agir e classifica o silêncio (`dosu-ai/better-stale-bot`, `mcp-toolbox/stale-sweep`) |
| Respostas em issues e Discussions | templates e lock | respostas com citações e modos de supervisão (Dosu Mention / Auto Draft / Auto Reply; Inkeep com limiar de confiança) |
| Issue para PR | inexistente | Copilot cloud agent, Claude e Codex no Agent HQ, Jules, OpenHands Cloud, `@claude implement` |
| Dependências | bump e agrupamento (Dependabot, Renovate) | "Assign to Agent" em alertas Dependabot para correções além do bump (GA 2026-04-07); Renovate Enterprise se posiciona como governança do volume de PRs de agentes, não como agente |
| CI | status checks, merge queue | diagnóstico e fix de falhas (`ci-doctor`, `ci-failure-auto-fix.yml`, Jules corrige CI dos próprios PRs) |
| Review de PR | Danger, linters | dezenas de revisores com contexto de codebase, grátis em repos públicos (CodeRabbit, cubic, Greptile, Sourcery, Korbit, Augment, Gemini Code Assist) |
| Versão e changelog | derivado do rótulo do commit (`feat:` = minor), sem olhar o diff | decisão de semver por conteúdo do PR (`gh-aw/changeset.md`, 78% de acerto reportado); release highlights em prosa (`update-release`); `changeset-validation` confere changelog contra diffs (OpenAI Agents SDK) |
| Segurança | scanners e alertas | triage e fix de achados via PR (Copilot Autofix grátis em públicos, Semgrep Assistant, Snyk Agent Fix, Aikido, `codex-security`) |

### 3.2 Onde ainda são fracos

1. **Gates com critério.** Nenhum produto implementa GO / NO-GO com critérios explícitos. O gh-aw resolve delegando o gate a um environment approval do Actions e restringindo o agente a escrever highlights; o safe output `update-release` não cria releases. Nos plugins genéricos de release (scarrillo, baoyu, opencode-github-release, `github-release`) o gate humano é implícito ("confirme o bump") ou um handoff textual antes do `gh release create`.
2. **Discussions.** Só Dosu e Inkeep atuam; o gh-aw tem safe outputs de discussion e o sample `discussion-task-miner`, mas nenhum workflow de facilitação. Copilot, Codex, CodeRabbit, Greptile e cubic não têm nada para Discussions. A `claude-code-action` não documenta gatilho `discussion`, embora o App peça a permissão.
3. **Estado e memória por repositório.** A memória de agente fica fora do repo (auto-memory do Claude Code em `~/.claude/projects/`, Knowledge do Devin no app, Dosu no dashboard). As exceções são `state.json` e `decisions.md` do n-skills e o branch de memória do `auto-label`. Sem estado, o agente usa labels, arquivos e PRs como memória, que é exatamente a limitação do baseline.
4. **Segurança.** Conteúdo de issue e PR é entrada não confiável: `allowed_non_write_users` e bloqueio de forks são obrigatórios; o gh-aw nasceu read-only com safe outputs por causa disso; a Cursor trata a descrição do PR como adversarial na automation "Assign PR Reviewers". Uma reportagem de agosto de 2026 sobre falhas em Claude Code e Gemini CLI que permitiriam a uma issue alcançar secrets de CI **não foi verificada em detalhe**.
5. **Confiabilidade.** A skill do OpenDAL codifica a regra "não declare sucesso até o sistema externo confirmar"; o `agent-approval-check` da claude-code-action exige aprovações humanas em PRs com commits de agente. Isso indica que os próprios autores não confiam no relato do agente.
6. **Custo e quotas.** Copilot code review custa entre US$0,05 e US$5 por review em créditos; Anthropic Code Review, US$15 a 25; Bugbot é usage-based; Dosu Free dá 200 créditos por mês; Gemini tem quotas com valores conflitantes entre docs. Para um mantenedor solo, a conta por execução importa.
7. **Disponibilidade e longevidade.** Copilot Automations não funcionam em repositórios públicos. Sweep pivotou, Mentat sumiu sem anúncio, o resolver do OpenHands saiu do `main`. O padrão de 2021 a 2025 (apps Probot morrendo, Actions sobrevivendo) se repete com agentes hospedados.
8. **Artefato e retro.** Nenhum agente roda smoke do artefato instalado, valida imagem Docker fresh e upgrade, nem conduz retro. O único toque de IA no baseline de release é o "AI-powered changelog enhancement" do GoReleaser Pro, pago.
9. **Comunicação pública.** Há duas políticas opostas em uso: disclaimer "generated by AI" em todo comentário (mattpocock) e proibição de atribuição de agente em texto público (OpenDAL; Ruff exige AI policy). O tom e a alucinação em respostas públicas continuam sendo risco humano-gerido.

---

## 4. Padrões de configuração por repositório

### 4.1 Três padrões de localização

| Padrão | Exemplos | Quando é usado |
|---|---|---|
| Arquivo único na raiz | `.releaserc`, `renovate.json`, `.coderabbit.yaml`, `.pr_agent.toml`, `ellipsis.yaml` (sem ponto), `.mergify.yml`, `.kodiak.toml`, `cliff.toml`, `.all-contributorsrc`, `release-please-config.json`, `.pre-commit-config.yaml` | configuração de máquina (JSON, TOML, YAML), sem prosa nem scripts |
| Dentro de `.github/` | `dependabot.yml`, `release.yml`, `settings.yml`, `CODEOWNERS`, templates, `copilot-instructions.md`, `instructions/`, `agents/`, `skills/`, `workflows/*.md` (gh-aw), `copilot-setup-steps.yml` | o que a forge consome; ferramentas de terceiros usam como fallback para "não poluir a raiz" (Renovate, Mergify, Kodiak) |
| Diretório oculto próprio | `.changeset/`, `.greptile/` (em cascata), `.mergify/`, `.circleci/`, `.devcontainer/`, `.openhands/`, `.ona/`, `.claude/`, `.codex/`, `.cursor/`, `.gemini/`, `.opencode/`, `.kiro/`, `.junie/`, `.devin/` | vários arquivos (config + prosa + scripts + estado) ou cascata por diretório |

Não existe pasta neutra de forge: Forgejo lê `.forgejo/`, depois `.gitea/`, depois `.github/`; GitLab e Bitbucket só as próprias.

### 4.2 Arquivos de instrução para agentes (estado em setembro de 2026)

| Ferramenta | Instruções sempre ativas | Skills | Lê `AGENTS.md`? | Lê `.agents/skills/`? |
|---|---|---|---|---|
| Claude Code | `CLAUDE.md`, `.claude/CLAUDE.md`, `CLAUDE.local.md`, `.claude/rules/*.md` com `paths:` | `.claude/skills/`, `~/.claude/skills/`, plugins, enterprise (nested `.claude/skills/` em subdirs) | não nativamente; recomenda `@AGENTS.md` no `CLAUDE.md` | **não** (verificado na documentação) |
| Codex | `AGENTS.md` da raiz até o cwd (concatenado, 32 KiB), `AGENTS.override.md` | `.agents/skills/`, `~/.agents/skills/` | sim (formato nativo) | sim (primário) |
| Cursor | `AGENTS.md`; `.cursor/rules/*.mdc` | `.agents/skills/`, `.cursor/skills/`; legado `.claude/skills/`, `.codex/skills/` | sim | sim |
| GitHub Copilot | `.github/copilot-instructions.md`, `.github/instructions/*.instructions.md`, `AGENTS.md` | `.github/skills/`, `.claude/skills/`, `.agents/skills/` | sim | sim |
| Gemini CLI | `GEMINI.md` hierárquico | `.gemini/skills/` ou alias `.agents/skills/` (alias tem precedência) | só com `context.fileName` | sim |
| OpenCode | `AGENTS.md`; `instructions` em `opencode.json` | `.opencode/skills/`, `.claude/skills/`, `.agents/skills/` | sim | sim |
| OpenHands | `AGENTS.md` | `.agents/skills/` (novo); legado `.openhands/skills/`, `microagents/` | sim | sim |
| Devin Desktop (ex-Windsurf), Junie, Kiro, Cline, Jules | `AGENTS.md` mais `.devin/rules/`, `.junie/`, `.kiro/steering/`, `.clinerules` | vários | sim | n/v |

Convergências reais: `AGENTS.md` (spec sob a Agentic AI Foundation da Linux Foundation, "mais de 60k projetos"), `SKILL.md` (agentskills.io, cerca de 45 clientes), `.agents/skills/` (322.560 arquivos indexados contra 391.168 em `.claude/skills/`) e os pares `.agents/plugins/marketplace.json` (Codex) e `.claude-plugin/marketplace.json` (Claude; Codex lê como legado). Todas as propostas de um `.agents/` completo (`rules/`, `memory/`) estão abertas e sem decisão (agentsmd/agents.md issues 9, 71 e 179; dotagents; dotagentsprotocol).

### 4.3 Como as ferramentas separam motor e perfil

1. **Descoberta por caminho fixo**, nunca por conteúdo; às vezes com 2 ou 3 fallbacks (CODEOWNERS, Renovate, Mergify).
2. **Camadas com "mais próximo vence" e merge aditivo** para listas: Claude Code (managed > CLI > local > project > user; `permissions.allow` faz merge), Codex (`.codex/config.toml` mais próximo do cwd vence; `model_provider` bloqueado no nível projeto), Copilot (personal > repo > org, todas fornecidas), Cursor (Team > Project > User), Greptile (`.greptile/` em cascata; regras combinam, `disabledRules` remove), OWNERS (herda salvo `no_parent_owners`), EditorConfig (`root=true` interrompe).
3. **Trust gating** para tudo que executa ou libera permissão a partir do repo: Codex só carrega `.codex/` em projeto trusted; Claude Code só honra `allow`, `hooks` e `extraKnownMarketplaces` após confiar na pasta; mise tem `trusted_config_paths`.
4. **Motor pinado a partir do perfil**: pre-commit `repo` + `rev`, Renovate `extends: github>org/config#tag`, CircleCI orbs, Claude `extraKnownMarketplaces` + `enabledPlugins`, Codex `.agents/plugins/marketplace.json`.
5. **Orçamento de contexto sempre ativo**: Codex 32 KiB; Claude recomenda menos de 200 linhas; Ona recomenda menos de 60. Procedimentos longos vão para skill ou arquivo carregado sob demanda.

Exemplo concreto de "o repo pede o motor" no Claude Code (`.claude/settings.json`):

```json
{
  "extraKnownMarketplaces": {
    "oss-maintainer": { "source": { "source": "github", "repo": "lfnovo/open-notebook-mgmt" } }
  },
  "enabledPlugins": { "oss-maintainer@oss-maintainer": true }
}
```

### 4.4 Exemplos concretos de "perfil do projeto para agentes"

**`.github/maintainer/` do plugin `open-source-maintainer` (n-skills), usado em `numman-ali/openskills`:**

```
.github/maintainer/
├── config.json          # settings de máquina (schemaVersion, stateFile, noMergeExternalPRs, semantics.intent)
├── context.md           # Vision, Current Priorities, Success Metrics, Areas, Tone, Out of Scope
├── standing-rules.md    # Stale Policy (tabela condição/dias/ação), Auto-Labels, External PR Handling
├── release-checklist.md # comandos concretos (npm version, build, test, git tag, npm publish)
├── decisions.md         # "### [RELEASE:1.5.0] … Date / Decision / Reasoning"
├── patterns.md, contributors.md, notes/, work/, index/, runs.md
└── state.json           # estado técnico para runs incrementais
```

O SKILL.md diz: "Stage 0 — Setup: Ensure `.github/maintainer/` exists (create via templates if missing)" e "Human approval required for any public action".

**`.maintainer/` do `sunbeamdotpt/sbbb` ("maintainer knowledge bundle"):** `index.md` ("Instructions live in charter.md; conventions live in the repo's `AGENTS.md`; this bundle holds knowledge"), `charter.md` (what you own / what you do NOT own / never edit), `architecture.md`, `deployment.md`, `secrets-model.md`, `interfaces.md`, `known-issues.md`, `fragile-areas.md` (derivado de postmortems), `state.md` (atualizado a cada handoff), `log.md` (append-only), `verification.md`. A divisão explícita é: AGENTS.md = convenções; `.maintainer/` = autoridade, escopo e conhecimento.

**Outros `.maintainer/`:** `PrunaAI/pruna-skills` (scripts `release/release.sh`, `validate_release.sh`, `smoke_install.sh`, `skills.catalog.json` referenciado do AGENTS.md como "source of truth"); `nuonco/nuon-plugin` (`UPGRADE.md` é um prompt "You are a maintainer agent… This is maintainer-only tooling. It is NOT a plugin skill", mais `baseline.json` de SHAs); `dustinkirkland/byobu` (`release.py`; lição registrada: `export-ignore` só afeta `git archive`, não `git push`, e o diretório vazou para o branch Debian).

**Frontmatter do gh-aw** (o perfil de permissão vive no próprio workflow): `on`, `permissions` (read-only por padrão), `engine`, `tools: {github: {toolsets}, bash, playwright}`, `network`, `roles: [admin, maintainer]`, `safe-outputs: {create-issue: {max: 1}, add-labels: {allowed: [...]}}`, `timeout-minutes`.

**Ambiente:** Copilot `.github/workflows/copilot-setup-steps.yml` (job obrigatoriamente chamado `copilot-setup-steps`); OpenHands `.openhands/setup.sh` e `hooks.json` (stop hooks como quality gate); devcontainer lifecycle; Codex, Jules e Devin guardam ambiente e secrets na UI, fora do repo.

**Mapeamento de papéis canônicos para labels reais** (`mattpocock/skills triage`): "These are canonical role names. The actual label strings used in the issue tracker may differ. The mapping should have been provided to you. If not, tell the user to run `/setup-matt-pocock-skills`."

Denominador comum de todo perfil: comandos canônicos; ambiente e setup; permissões e ferramentas; gotchas e áreas frágeis; políticas (stale, labels, PR externo, gates); ownership, canais e interfaces; estado e memória; tom.

### 4.5 Precedentes para um diretório de perfil de mantenedor (GitHub Code Search, 2026-09-05)

| Caminho | Arquivos indexados | Observação |
|---|---|---|
| `path:.maintainer/` | 63 | cerca de 9 repos: pruna-skills (33), sbbb (11), cli (8), nuon-plugin (5), byobu (2), hollywood, go-mock-api-server, voice-to-agent, agent-threads |
| `path:.maintainers/` | 1 | `trust.json` de um único repo |
| `path:.github/maintainer/` | 150 | dominado por `numman-ali/openskills` (plugin n-skills) |
| `path:.github/maintainers/` | amostra de 8 repos | documentação de pessoas, não perfil de automação |
| `maintainer.yml`, `maintainer.toml`, `MAINTAINERS.toml`, `.github/MAINTAINERS.md`, `.project/`, `.release/` | 0 | sem precedente |
| referência: `.claude/skills/`, `.agents/skills/`, `.cursor/rules/`, `.codex/config.toml`, `.devin/rules/` | 391.168, 322.560, 184.064, 7.632, 622 | diretórios nomeados pela ferramenta dominam por três ordens de grandeza |

Precedentes clássicos: `MAINTAINERS` do Moby (era TOML "consumível por programas" na v20.10; hoje é CSV com seções COMMITTERS e REVIEWERS apontando para `GOVERNANCE.md`), `OWNERS` do Kubernetes (YAML por diretório, cascata, consumido pelo Prow para `/lgtm` e `/approve`; único formato de papéis com enforcement acoplado), `CODEOWNERS` (3 locais, primeiro vence), `.well-known/` (RFC 8615 é para URIs web; OpenCode usa `.well-known/opencode` como config remota de org). `.forge` é um arquivo de CLI, não uma convenção Rust.

### 4.6 Avaliação da ideia do `.maintainer/`

**A favor**
- Neutro de ferramenta: serve Claude Code, Codex e qualquer motor; não colide com `.claude/` e `.codex/`, que são do motor, não do perfil.
- Tem precedente literal com o mesmo significado (sunbeam, nuon, pruna) e precedente estrutural com a mesma divisão motor/perfil (`.github/maintainer/` do n-skills).
- Comporta os quatro tipos de conteúdo (config, prosa, scripts, estado) e subestrutura; um arquivo único não comporta.
- O nome por papel diz a humanos "isto é de quem mantém". Singular tem 63 vezes mais uso que plural.

**Contra**
- Nenhuma ferramenta auto-descobre; o plugin precisa conhecer o caminho, e `AGENTS.md` e `CLAUDE.md` precisam apontar para ele, senão agentes fora do plugin ignoram.
- Risco de drift com `AGENTS.md` (comandos de build e teste duplicados). A regra em OpenAI, Ona e Claude é que `AGENTS.md` seja a fonte dos comandos gerais.
- Mais um dot-dir na raiz; vazamento em tarballs e branches de empacotamento (lição do byobu); confusão com o arquivo `MAINTAINERS` (lista de pessoas).
- `.github/` tem affordances de UI (templates, CODEOWNERS, agents) que `.maintainer/` não tem.
- IDs de canal commitados em repositório público: sem precedente encontrado (Devin guarda no app).

**Alternativas**

| Alternativa | Veredito |
|---|---|
| `.github/maintainer/` | equivalente funcional, com precedente direto; amarra ao GitHub e polui um `.github/` já lotado; igualmente não auto-descoberto. Boa se o projeto é e será GitHub-only. |
| `.github/maintainer.yml` único | espelha `dependabot.yml`; só máquina, sem gotchas, scripts ou estado. Bom como parte, ruim sozinho. |
| `.claude/` + `.codex/` duplicados | auto-descoberta nativa, mas formatos diferentes, `.codex/` exige trust, e é o lugar do motor. Usar para empacotar e pinar o plugin, não para o perfil. |
| seção "Maintainer" em `AGENTS.md` | máxima descoberta, mas consome orçamento sempre ativo e `AGENTS.md` é de todos os contribuidores. Usar só como ponteiro. |
| `.agents/maintainer/` | elegante, vizinho de `.agents/skills/`; nada lê, Claude Code não lê `.agents/` nem para skills, e a spec está em disputa. |
| `MAINTAINERS.md` estendido | tradição é pessoas e governança; o Moby abandonou até o TOML. Não. |
| `maintainer.toml` na raiz | como `.kodiak.toml`; perde prosa e scripts. Bom como `profile.toml` dentro do diretório. |

**Veredito:** `.maintainer/` é defensável e é a melhor opção entre as neutras. A condição é tratar as fraquezas de frente: ponteiros obrigatórios em `AGENTS.md` e `CLAUDE.md`, `README.md` interno, `schema_version`, sem duplicar comandos que já estão em `AGENTS.md` ou no `Makefile`, `export-ignore` documentado, estado gitignored e um comando de bootstrap no plugin que cria a estrutura quando ela não existe.

### 4.7 O que hoje está embutido nas skills do `on-maintainer` e deveria virar perfil

Leitura do plugin atual neste repositório (`plugins/on-maintainer/skills/`):

| Hoje, no texto da skill | Campo candidato no `.maintainer/` |
|---|---|
| `.github/RELEASE_PROCESS.md` como "source of truth" | `[release] process_doc` |
| `uv run pytest`, `ruff check`, `mypy`, `npm run lint/test/build`, `npm ci` | `[commands]` ou ponteiro para `AGENTS.md` e `Makefile` |
| portas 5055, 3000 e 3001; ordem de subida database, api, worker, frontend; `.env` pode apontar para SurrealDB standalone | `[smoke] api_url, frontend_url, stack_up, gotchas` |
| `make docker-build-local`, `make release-test TAG OLD_TAG`, `make tag`, `make release-stack`, `make release-stack-down` | `[release.commands]` |
| `gh workflow run build-and-release.yml -f push_latest=false`; `v1-latest` promovido na publicação | `[artifacts.ci] workflow, inputs, latest_tag` |
| registries `lfnovo/open_notebook` e `ghcr.io/lfnovo/open-notebook`, sufixo `-single`, arquiteturas amd64 e arm64, tag `v1-dev` para testers | `[artifacts.docker] registries, variants, platforms, dev_tag` |
| Dependabot highs resolvidos ou aceitos como critério de GO | `[release.gates]` |
| labels `released`, `ready`, `bug` | `[labels]` (canônicas para reais) |
| IDs GraphQL das categorias Ideas e Feedback Requests e id do repositório | `[discussions] categories` (regeneráveis por comando) |
| âncoras públicas `VISION.md`, `docs/7-DEVELOPMENT/decisions/`, PDR-001; proibição de citar `.tmp-context/` | `[discussions] public_anchors, never_cite` |
| checkouts locais de esperanto, content-core, podcast-creator, surreal-commands (via `CLAUDE.local.md`) | `[upstreams]` |
| texto do post no Discord | `[channels] announce` |
| `.harness/smoke-report.md` | `[smoke] report_path` |
| regra "interagir na língua do owner, publicar em inglês"; formato "uma decisão por vez" | `[comms]` |
| jornada notebook, sources, chat, ask, transform, podcast, search, cleanup (cerca de 400 linhas específicas do produto) | `smoke/journey.md` (a skill genérica fica com health checks, relatório, verificação Playwright e veredito) |
| matriz A/B/C e gates | template genérico no plugin; instância por repo em `release/` |

---

## 5. Lacunas do mercado

1. **Release orchestration com gates humanos.** Confirmada. Não há produto; há padrões (gh-aw `release.md` com environment approval, OpenAI `final-release-review`, OpenDAL state machine, GitVersion em fases) e há a camada determinística (release-please, semantic-release, changesets, git-cliff, GoReleaser) que executa cut e changelog sem julgar risco, sem testar artefato e sem retro. A hipótese do plugin se sustenta: o valor está no que acontece antes e depois do comando (matriz por risco, gate de imagem, fix loop, verificação pós-publicação, retro), e o comando em si pode continuar sendo o baseline.
2. **Facilitação de Discussions.** Confirmada e é a lacuna mais vazia. Baseline: templates por categoria, lock por inatividade, labels manuais, close reasons. Agentes: Dosu e Inkeep respondem; gh-aw pode criar, atualizar e fechar; ninguém qualifica, decompõe, verifica alegações no código, propõe outcomes ou gradua. Também não existe taxonomia pública de estados em Discussions em nenhum dos projetos pesquisados (Next.js, Vite, Tailwind, Ruff, Deno, Home Assistant); as taxonomias reutilizáveis vêm de RFCs e PEPs (Ember `Exploring`, Rust `postpone`, PEP `Deferred`, KEP `deferred`).
3. **Smoke test e2e como gate.** Confirmada. Os análogos são `mcp-release-qa`, `examples-run-analysis`, `runtime-behavior-probe` e `/qa` do gstack; nenhum é um gate de release reutilizável com veredito.
4. **Publicação de imagem Docker e GHCR, e de npm, como skill.** Não encontrada. PyPI tem `python-pypi-package-builder` e `shipit-skill`.
5. **Estado persistente do mantenedor no repositório.** Só o n-skills (`state.json`, `decisions.md`) e o `auto-label` da Dosu (branch de memória).
6. **Retro institucionalizada.** Só como processo humano (Kubernetes); nenhuma ferramenta a conduz ou aplica o resultado no processo.
7. **Plugin de mantenedor cross-harness.** Não existe oficial; o mais próximo é o `open-source-maintainer` do n-skills (Claude e Codex).

Temas saturados, a evitar como diferenciação: changelog e semver (12.160 `SKILL.md` no GitHub com release, changelog e semver), review de PR (dezenas de SaaS grátis em repos públicos), triage de issues por Action (exemplos oficiais de todos os vendors, mais Dosu).

---

## 6. Recomendações concretas para o `oss-maintainer`

### 6.1 O que reaproveitar

- **Divisão de arquivos do n-skills**: config de máquina, contexto e intenção, regras permanentes, memória de decisões e padrões, estado técnico. É a mesma divisão que o `charter.md`, `known-issues.md`, `log.md` e `state.md` do sunbeam fazem com outros nomes.
- **"Controlling checker" do OpenAI Agents SDK**: o resultado binário (GREEN LIGHT / BLOCKED) é separado do relatório, e "produzir o texto do relatório não é um resultado positivo". É o GO / NO-GO do `smoke-e2e` formalizado; vale para o gate de imagem também.
- **Propose-only por padrão** (mcp-toolbox, nativewind, mattpocock, n-skills): já é a regra do `process-discussions`; estendê-la a tudo que muda estado público e formalizar como lista de mutações permitidas por fase, inspirada no `safe-outputs` do gh-aw. O `references/gates.md` atual é essa lista em prosa.
- **`allowed-tools` no frontmatter** (GitVersion, nativewind) e `disable-model-invocation` para skills que só rodam sob comando explícito (mattpocock). O `release` e o `process-discussions` deveriam ser `user-invocable` apenas.
- **Máquina de estados com confirmação externa** (OpenDAL): não marcar fase concluída sem checar tag, manifest, release ou CI de verdade. O runbook atual já faz isso para manifests; generalizar.
- **Papéis canônicos e mapeamento para labels reais** (mattpocock) e **leitura live de labels, templates e CONTRIBUTING** (mcp-toolbox, `make-repo-contribution`), em vez de IDs e nomes memorizados na skill.
- **Critérios de GO numéricos e nominais** (Kubernetes): zero PRs pendentes, zero testes blocking vermelhos, zero issues abertas no milestone; sinal dado no mesmo dia por dono nomeado; regra de adiamento explícita. E o **cut em ordem obrigatória com dry-run** (mock antes de nomock), cada passo como critério de entrada do próximo.
- **Smoke do artefato instalado** (Django: `pip install`, `startproject`, `migrate`, `runserver` para tarball e wheel; Node: `process.version`; CPython: `make distclean; ./configure; make test` do tarball baixado). O gate de imagem fresh e upgrade do Open Notebook é a versão Docker disso.
- **Aprovação humana no ponto de publicar** com token efêmero (PyPA environment approval + OIDC; Sentry issue com label `accepted` em repo read-only; `force` auditável para override de blockers). **Draft primeiro, flip depois** (Django `is_active`, GitHub immutable releases).
- **Camada determinística como executor**: `gh release create --generate-notes` e `.github/release.yml` para créditos e "New Contributors"; git-cliff para o esqueleto do changelog; API de alertas do Dependabot; `actions/stale` e `lock-threads` para higiene. O agente orquestra, não substitui.
- **Escada de supervisão da Dosu** como modelo de maturidade para Discussions: Mention, depois Auto Draft; nunca Auto Reply para Ideas.
- **Vocabulário de outcomes validado por precedentes**: `exploring` (Ember RFC stage 1, label `Exploring`), `parked` e `incubating` (Rust `postpone`, PEP `Deferred`, KEP `deferred`), `graduated` (GitHub "create issue from discussion" quando "ready to be worked on"), `answer` (Q&A "mark as answer"), fechamento com razão `resolved`, `outdated`, `duplicate`. A regra "graduação é pull, não push" tem apoio empírico: o motivo dominante de discussion para issue é pedir ao autor que clarifique a ideia (arXiv 2307.07117).
- **Inputs `plugins` e `plugin_marketplaces` da claude-code-action** para rodar o plugin em CI no futuro (por exemplo, o mapa da fila de Discussions por cron), e **`agent-approval-check`** como required check em PRs com commits de agente.
- **Distribuição cross-harness já validada** por NVIDIA/skills, wshobson/agents e gstack: um `skills/` compartilhado, `.claude-plugin/plugin.json` + `.codex-plugin/plugin.json`, dois catálogos de marketplace. É o que este repositório já faz. Skills também instaláveis por `npx skills add` e `gh skill install`.

### 6.2 O que evitar

- Construir GitHub App hospedado: o cemitério Probot e os pivôs de Sweep, Mentat e OpenHands mostram o custo. Plugin local e Actions no repo do mantenedor herdam a longevidade das Actions.
- Depender de Copilot Automations (só repositórios privados) ou de qualquer feature que exija plano Enterprise.
- Postar automaticamente em Discussions ou Issues. Manter aprovação por texto, uma decisão por vez, como já ratificado.
- Duplicar comandos de build e teste no perfil. `AGENTS.md` e `Makefile` são a fonte; o perfil aponta e só adiciona o que é de mantenedor.
- Arquivo YAML único como perfil; nome plural `.maintainers/`; usar `MAINTAINERS.md` como perfil.
- Contar com descoberta automática de `.agents/` no Claude Code, ou com `.codex/` sem trust.
- Commitar tokens. IDs GraphQL de categoria e id de repo são públicos e podem ir no perfil com o comando que os regenera; IDs de canal Discord podem ir em `profile.local.toml` gitignored se o mantenedor preferir.
- Atribuição de agente em texto público quando a política do repo proíbe (regra atual do owner), mas oferecer a política oposta (disclaimer) como opção do perfil, porque projetos como o mattpocock a exigem.

### 6.3 Nomes e convenções propostos

Plugin `oss-maintainer`; skills `release`, `process-discussions`, `smoke-e2e` e uma nova `init` que cria o `.maintainer/` a partir de templates quando não existe (Stage 0 do n-skills, `/setup` do mattpocock). Invocação `/oss-maintainer:release` no Claude Code e por nome no Codex.

```
.maintainer/
├── README.md              # o que é isto, para humanos; evita confusão com MAINTAINERS
├── profile.toml           # schema_version = 1; [project], [commands] (ponteiros), [labels],
│                          # [release], [release.gates], [artifacts], [smoke], [discussions],
│                          # [channels], [comms], [upstreams]
├── PROFILE.md             # escopo (own / do NOT own), tom, o que nunca citar   (sunbeam charter)
├── gotchas.md             # áreas frágeis e known issues derivados de postmortems
├── release/
│   ├── runbook.md         # comandos exatos do repo (o que hoje está em references/runbook.md)
│   └── test-matrix.md     # instância da matriz A/B/C para este repo
├── smoke/
│   └── journey.md         # a jornada e2e do produto (o que hoje ocupa 400 linhas da skill)
├── decisions.md           # log append-only de decisões de release e de Discussions
├── profile.local.toml     # gitignored: IDs de canal privados, overrides pessoais
└── state/                 # gitignored: último run, hashes, relatórios
```

Regras de convivência:
- `AGENTS.md` ganha uma linha: "Maintainer profile lives in `.maintainer/`; do not run release or discussion workflows without it". `CLAUDE.md` faz `@AGENTS.md` e repete a linha.
- O repo pina o motor: `.claude/settings.json` com `extraKnownMarketplaces` e `enabledPlugins`; `.agents/plugins/marketplace.json` para o Codex.
- `profile.toml` traz `schema_version`; o plugin valida e recusa versões desconhecidas (Kodiak `version = 1`, n-skills `schemaVersion`).
- `.gitattributes` com `.maintainer/ export-ignore` quando o projeto publica tarballs, com a nota de que isso não afeta `git push`.
- Para monorepos, permitir `.maintainer/` aninhado com semântica "mais próximo vence, listas somam" (OWNERS, `.greptile/`), mas só quando houver caso real.
- As skills leem labels, categorias de Discussions e templates ao vivo na sessão e usam o perfil para o que não é derivável (gates, canais, âncoras, gotchas).

### 6.4 Riscos

- **Prompt injection** por issues, Discussions e PRs de terceiros: tratar todo conteúdo lido do GitHub como dado; nunca executar instruções vindas dele; manter `allowed-tools` estreito e propose-only.
- **Segredos e IDs no perfil**: sem tokens; overlay local gitignored; lembrar que Codex, Jules e Copilot removem secrets do ambiente do agente.
- **Drift entre perfil, `AGENTS.md` e `RELEASE_PROCESS.md`**: o retro (Phase 9) já atualiza os três; formalizar qual é fonte de cada campo.
- **Churn de formatos**: plugins Codex são recentes; `.agents/` está em disputa; Claude Code adiciona campos não padrão ao `SKILL.md` que quebram uploads para claude.ai. Manter o frontmatter das skills no subconjunto comum e validar com `claude plugin validate` e o agent-smith.
- **Custo e quota** se parte do fluxo migrar para CI (Actions minutos mais tokens); o gh-aw resolve com `timeout-minutes` e `max` por safe output.
- **Vazamento do diretório** em branches de empacotamento (byobu).
- **Confiança excessiva no relato do agente**: por isso confirmação externa por fase e `agent-approval-check` em PRs de agente.
- **Generalização prematura**: o perfil deve nascer dos três repositórios reais (open-notebook, esperanto, content-core), como as skills nasceram, e não de um schema idealizado; o YAML ilustrativo da pesquisa de processos (14 grupos de campos) serve de lista de verificação, não de spec.

---

## 7. Fontes

As URLs abaixo foram consultadas em 2026-09-05. Estão agrupadas pela frente de pesquisa em que foram usadas. Páginas que retornaram 404, 402, 403 ou 429 estão listadas separadamente ao fim de cada bloco quando o pesquisador as registrou, com a fonte substituta indicada no corpo dos relatórios.

### 7.1 Plugins, skills e agentes nos ecossistemas de agentes de código

**Claude Code**
- https://github.com/anthropics/claude-plugins-official
- https://raw.githubusercontent.com/anthropics/claude-plugins-official/main/.claude-plugin/marketplace.json
- https://github.com/anthropics/claude-plugins-community
- https://raw.githubusercontent.com/anthropics/claude-plugins-community/main/.claude-plugin/marketplace.json
- https://github.com/anthropics/claude-code (plugins/, .github/workflows/)
- https://raw.githubusercontent.com/anthropics/claude-code/main/.github/workflows/claude-issue-triage.yml
- https://raw.githubusercontent.com/anthropics/claude-code/main/.github/workflows/claude-dedupe-issues.yml
- https://raw.githubusercontent.com/anthropics/claude-code/main/.github/workflows/auto-close-duplicates.yml
- https://raw.githubusercontent.com/anthropics/claude-code/main/.github/workflows/lock-closed-issues.yml
- https://raw.githubusercontent.com/anthropics/claude-code/main/.github/workflows/issue-lifecycle-comment.yml
- https://raw.githubusercontent.com/anthropics/claude-code/main/.github/workflows/sweep.yml
- https://raw.githubusercontent.com/anthropics/claude-code/main/plugins/code-review/README.md
- https://github.com/anthropics/claude-code-action
- https://github.com/anthropics/claude-code-action/blob/main/docs/solutions.md
- https://raw.githubusercontent.com/anthropics/claude-code-action/main/examples/issue-deduplication.yml
- https://raw.githubusercontent.com/anthropics/claude-code-action/main/examples/ci-failure-auto-fix.yml
- https://raw.githubusercontent.com/anthropics/claude-code-action/main/examples/agent-approval-check.yml
- https://code.claude.com/docs/en/github-actions
- https://code.claude.com/docs/en/code-review
- https://code.claude.com/docs/en/plugins-reference
- https://github.com/anthropics/skills
- https://github.com/anthropics/knowledge-work-plugins
- https://github.com/scarrillo/release
- https://github.com/hesreallyhim/awesome-claude-code (README raw)
- https://github.com/ComposioHQ/awesome-claude-skills
- https://github.com/karanb192/awesome-claude-skills
- https://github.com/travisvn/awesome-claude-skills
- https://github.com/rohitg00/awesome-claude-code-toolkit (README raw)
- https://github.com/alirezarezvani/claude-skills (README raw)
- https://github.com/wshobson/agents e .../plugins/documentation-generation/skills/changelog-automation/SKILL.md
- https://github.com/jimliu/baoyu-skills
- https://github.com/garrytan/gstack
- https://github.com/addyosmani/agent-skills e .../skills/shipping-and-launch/SKILL.md
- https://github.com/terrylica/cc-skills
- https://github.com/mhattingpete/claude-skills-marketplace
- https://github.com/cathy-kim/skill-semver
- https://github.com/JetBrains/skills/blob/main/changelog/SKILL.md
- https://github.com/numman-ali/n-skills (skills/workflow/open-source-maintainer/.../SKILL.md)
- https://github.com/FlorianBruniaux/claude-code-ultimate-guide (examples/skills/issue-triage/SKILL.md)
- https://github.com/mattpocock/skills (skills/engineering/triage/SKILL.md)
- https://github.com/jeremylongshore/tons-of-skills-marketplace
- https://www.claudedirectory.org/plugins/x-bug-triage-plugin
- https://github.com/costajohnt/oss-autopilot
- https://github.com/gvzq/githubclip
- https://github.com/OMARVII/open-source-launch-skill
- https://github.com/wjgilmore/dependabot-skill
- https://github.com/MaTriXy/github-review-skill
- https://github.com/srackley/claude-setup
- https://github.com/agent-sh/sync-docs
- https://github.com/agent-sh/drift-detect
- https://github.com/Arenukvern/skill_steward
- https://github.com/affaan-m/ECC e https://ecc.tools/
- https://github.com/openwpm/OpenWPM (.claude/skills/maintain/SKILL.md)
- https://github.com/nativewind/nativewind (.claude/skills/triage/SKILL.md)
- https://mcpmarket.com/tools/skills/open-source-maintainer (429)
- https://github.com/davila7/claude-code-templates
- https://www.petegypps.uk/blog/claude-code-official-plugin-marketplace-complete-guide-36-plugins-december-2025

**Codex**
- https://developers.openai.com/codex/plugins → https://learn.chatgpt.com/docs/plugins
- https://github.com/openai/plugins e .../.agents/plugins/marketplace.json, plugins/github/.codex-plugin/plugin.json, plugins/codex-security/.codex-plugin/plugin.json
- https://github.com/openai/skills (skills/.system, skills/.curated)
- https://developers.openai.com/blog/skills-agents-sdk
- https://github.com/openai/openai-agents-python (.agents/skills/final-release-review, release-candidate-prep, maintainer-review)
- https://github.com/openai/openai-agents-js (.agents/skills/changeset-validation)
- https://github.com/openai/codex-action
- https://developers.openai.com/codex/github-action
- https://learn.chatgpt.com/docs/third-party/github
- https://github.com/openai/codex-security
- https://developers.openai.com/codex/security
- https://github.com/mturac/everything-openai-codex (skills/github-ops/SKILL.md)
- https://codex.danielvaughan.com/2026/04/24/codex-cli-plugin-marketplace-building-distributing-extending/
- https://thenewstack.io/openais-codex-gets-plugins/
- https://www.codex-marketplace.com/

**Cursor**
- https://cursor.com/docs/plugins
- https://cursor.com/marketplace
- https://cursor.com/marketplace/automations/assign-pr-reviewers
- https://cursor.com/docs/cloud-agent/automations
- https://cursor.com/blog/marketplace · https://cursor.com/blog/new-plugins · https://cursor.com/changelog/03-11-26
- https://github.com/PatrickJS/awesome-cursorrules (README raw)
- https://github.com/sanjeed5/awesome-cursor-rules-mdc · https://github.com/tugkanboz/awesome-cursorrules · https://github.com/nedcodes-ok/cursorrules-collection
- https://getoptimal.ai/blog/cursor-bugbot-pricing · https://stackpick.net/tools/bugbot/ (imprensa; não verificado)

**Gemini CLI**
- https://github.com/google-github-actions/run-gemini-cli (README, examples/workflows/, issue-triage/README.md, pr-review/README.md, AWESOME.md, docs/)
- https://github.com/marketplace/actions/run-gemini-cli
- https://blog.google/technology/developers/introducing-gemini-cli-github-actions/
- https://geminicli.com/extensions/ · https://geminicli.com/docs/extensions/ · https://geminicli.com/docs/extensions/reference/
- https://github.com/gemini-cli-extensions
- https://github.com/gemini-cli-extensions/security
- https://github.com/gemini-cli-extensions/code-review
- https://github.com/gemini-cli-extensions/cicd
- https://github.com/github/github-mcp-server (README, docs/installation-guides/install-gemini-cli.md)
- https://github.com/jasmeetsb/gemini-github-actions
- https://docs.cloud.google.com/gemini/docs/code-review/set-up-code-assist-github
- https://github.com/apps/gemini-code-assist
- https://github.com/jgunnink/gemini-review-bot
- https://github.com/google-gemini/gemini-cli
- https://thehackernews.com/2026/08/claude-code-and-gemini-cli-flaws-let.html (não verificado em detalhe)

**OpenCode**
- https://github.com/anomalyco/opencode
- https://opencode.ai/docs/plugins/ · https://opencode.ai/docs/skills/ · https://opencode.ai/docs/agents/ · https://opencode.ai/docs/github/
- https://github.com/marketplace/actions/opencode-github-action
- https://github.com/awesome-opencode/awesome-opencode (README raw)
- https://github.com/amestsantim/opencode-github-release
- https://github.com/sun-praise/opencode-review
- https://github.com/joshuadavidthomas/opencode-agent-skills · https://github.com/malhashemi/opencode-skills · https://github.com/zenobi-us/opencode-skillful

**Coleções de Agent Skills**
- https://agentskills.io/ · https://github.com/agentskills/agentskills
- https://skills.sh/ · https://github.com/vercel-labs/skills
- https://github.blog/changelog/2026-04-16-manage-agent-skills-with-github-cli/
- https://github.com/VoltAgent/awesome-agent-skills (README raw)
- https://github.com/github/awesome-copilot (skills/: github-release, dependabot, github-issues, make-repo-contribution, python-pypi-package-builder, copilot-pr-autopilot, mcp-release-qa)
- https://mcpservers.org/agent-skills/github/github-release
- https://github.com/sickn33/agentic-awesome-skills
- https://github.com/skillmatic-ai/awesome-agent-skills · https://github.com/gmh5225/awesome-skills · https://github.com/Prat011/awesome-llm-skills · https://github.com/heilcheng/awesome-agent-skills · https://github.com/itgoyo/awesome-agent-skills · https://github.com/scienceaix/agentskills
- https://github.com/CodeAtCode/oss-ai-skills
- https://github.com/NVIDIA/skills
- https://github.com/googleapis/mcp-toolbox (skills/maintainer/triage-issues, stale-sweep)
- https://github.com/apache/opendal (.agents/skills/opendal-release/SKILL.md)
- https://github.com/GitTools/GitVersion (.agents/skills/release/SKILL.md)
- https://officialskills.sh/WordPress/skills/wp-project-triage · https://github.com/WordPress/agent-skills
- https://pypi.org/project/shipit-skill/ · https://github.com/skyzhao1223/shipit-skill
- https://market.lobehub.com/s/skills/neversight-skills_feed-semver-changelog · https://github.com/NeverSight/learn-skills.dev
- https://claudeskills.info/skills/category/release-management/
- https://skills-hub.ai/skills/repo-onboarding (não verificado)
- https://github.com/netresearch/docker-development-skill · https://github.com/wrsmith108/claude-code-docker-skill (Docker; não específicos de release)
- GitHub code search API (`search/code` com `filename:SKILL.md`) para contagens e descoberta de skills in-repo
- GitHub REST API (`repos/{owner}/{repo}`) para stars, `pushed_at` e licença de todos os repositórios citados

### 7.2 Agentes integrados ao GitHub

#### Buscadas e lidas (fontes primárias)
- https://github.github.com/gh-aw/
- https://github.github.com/gh-aw/reference/engines/
- https://github.github.com/gh-aw/reference/safe-outputs/
- https://github.github.com/gh-aw/blog/2026-01-13-meet-the-workflows-operations-release/
- https://github.com/github/gh-aw
- https://github.com/github/gh-aw/releases
- https://raw.githubusercontent.com/github/gh-aw/main/README.md
- https://raw.githubusercontent.com/github/gh-aw/main/.github/workflows/changeset.md
- https://raw.githubusercontent.com/github/gh-aw/main/.github/workflows/release.md
- https://raw.githubusercontent.com/githubnext/agentics/main/README.md
- https://github.blog/changelog/2026-02-13-github-agentic-workflows-are-now-in-technical-preview/
- https://github.blog/changelog/2026-06-11-github-agentic-workflows-is-now-in-public-preview/
- https://docs.github.com/copilot/concepts/agents/coding-agent/about-coding-agent
- https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/create-custom-agents
- https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills
- https://docs.github.com/en/copilot/concepts/agents/code-review
- https://docs.github.com/en/copilot/concepts/agents/cloud-agent/about-automations
- https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/create-automations
- https://docs.github.com/en/copilot/get-started/plans
- https://docs.github.com/en/copilot/concepts/billing/copilot-requests
- https://docs.github.com/en/code-security/code-scanning/managing-code-scanning-alerts/responsible-use-autofix-code-scanning
- https://github.blog/changelog/2024-09-17-now-available-for-free-on-all-public-repositories-copilot-autofix-for-codeql-code-scanning-alerts/
- https://github.blog/changelog/2025-09-25-copilot-coding-agent-is-now-generally-available/
- https://github.blog/changelog/2026-06-02-schedule-and-automate-tasks-with-copilot-cloud-agent/
- https://github.blog/changelog/2026-08-03-trigger-copilot-automations-with-comments/
- https://github.blog/news-insights/company-news/pick-your-agent-use-claude-and-codex-on-agent-hq/
- https://github.blog/changelog/2026-04-07-dependabot-alerts-are-now-assignable-to-ai-agents-for-remediation/
- https://github.blog/changelog/2026-06-18-generated-release-notes-credit-you-for-copilot-pull-requests/
- https://github.com/github/copilot-release-notes
- https://github.com/anthropics/claude-code-action
- https://raw.githubusercontent.com/anthropics/claude-code-action/main/docs/usage.md
- https://raw.githubusercontent.com/anthropics/claude-code-action/main/docs/solutions.md
- https://raw.githubusercontent.com/anthropics/claude-code-action/main/docs/faq.md
- https://raw.githubusercontent.com/anthropics/claude-code-action/main/examples/issue-triage.yml
- https://github.com/openai/codex-action
- https://learn.chatgpt.com/docs/github-action
- https://learn.chatgpt.com/docs/third-party/github
- https://learn.chatgpt.com/docs/cloud
- https://learn.chatgpt.com/docs/pricing
- https://docs.openhands.dev/openhands/usage/cloud/github-installation
- https://github.com/OpenHands/OpenHands (README, árvore, tags via `gh api`)
- https://github.com/All-Hands-AI/openhands-resolver
- https://github.com/sweepai/sweep
- https://raw.githubusercontent.com/sweepai/sweep/main/LICENSE
- https://dosu.dev/pricing
- https://dosu.dev/oss
- https://dosu.dev/blog/an-ai-stale-bot-that-you-can-trust
- https://raw.githubusercontent.com/dosu-ai/better-stale-bot/main/README.md
- https://raw.githubusercontent.com/dosu-ai/auto-label/main/README.md
- https://app.dosu.dev/9affd04a-e6a9-452c-b927-c639e979994c/documents/222de567-e12f-499d-a153-0b7a05c0faf4
- https://github.com/AbanteAI
- https://github.com/apps/mentatbot
- https://github.com/The-PR-Agent/pr-agent (redirect de qodo-ai/pr-agent)
- https://www.qodo.ai/pricing/
- https://docs.coderabbit.ai/reference/configuration
- https://kb.coderabbit.ai/articles/8856795235-how-do-i-activate-coderabbit-pro-for-my-open-source-project
- https://www.coderabbit.ai/pricing
- https://www.ellipsis.dev/
- https://www.ellipsis.dev/docs/features/code-review
- https://www.ellipsis.dev/docs/code-review
- https://www.ellipsis.dev/pricing
- https://www.cubic.dev/pricing-plans
- https://docs.cubic.dev/ai-review/custom-agents
- https://www.greptile.com/docs/code-review/greptile-config-reference
- https://www.greptile.com/pricing
- https://www.greptile.com/open-source
- https://github.com/sourcery-ai/sourcery
- https://docs.sourcery.ai/Code-Review/
- https://docs.sourcery.ai/reviews/commands/
- https://cursor.com/docs/bugbot
- https://docs.cloud.google.com/gemini/docs/code-review/customize-repo-review
- https://docs.cloud.google.com/gemini/docs/code-review/review-repo-code
- https://docs.cloud.google.com/gemini/docs/quotas
- https://github.com/google-github-actions/run-gemini-cli/tree/main/examples/workflows
- https://raw.githubusercontent.com/google-github-actions/run-gemini-cli/main/README.md
- https://github.com/google-labs-code/jules-action
- https://jules.google/docs/
- https://jules.google/docs/usage-limits/
- https://cognition.com/blog/open-source-initiative-is-back
- https://docs.devin.ai/work-with-devin/devin-review
- https://graphite.com/blog/introducing-graphite-agent-and-pricing
- https://www.korbit.ai/pricing.html
- https://bito.ai/pricing/
- https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/amazon-q-for-github.html
- https://www.augmentcode.com/changelog/introducing-augment-code-review
- https://www.pixee.ai/
- https://github.com/pixeeai
- https://docs.semgrep.dev/semgrep-assistant/overview
- https://updates.snyk.io/snyk-agent-fix-in-prs-is-coming-to-early-access-317978/
- https://docs.socket.dev/docs/faq
- https://docs.inkeep.com/cloud/integrations/github
- https://www.kapa.ai/blog/automating-github-issues-responses-with-kapa

#### Apenas via resultados de busca (snippets; não lidas integralmente)
- https://docs.dosu.dev/pages/settings · https://docs.dosu.dev/
- https://www.openhands.dev/pricing · https://www.openhands.dev/blog/open-source-coding-agents-in-your-github-fixing-your-issues
- https://pypi.org/project/openhands-resolver/ (não carregou)
- https://docs.sweep.dev/ (HTTP 402) · https://sweep.dev/ · https://plugins.jetbrains.com/plugin/26860-sweep-ai-autocomplete--coding-agent
- https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan (HTTP 403)
- https://developers.openai.com/codex/use-cases/github-code-reviews
- https://blog.google/innovation-and-ai/technology/developers-tools/gemini-code-assist-free/
- https://graphite.com/blog/startup-program-announcement
- https://www.aikido.dev/open-source · https://www.aikido.dev/code-quality/free-open-source-ai-code-review2
- https://socket.dev/blog/free-team-plan-upgrades-for-open-source-projects (HTTP 403)
- https://semgrep.dev/blog/2026/semgrep-autofix-public-beta/ · https://semgrep.dev/docs/semgrep-pro-vs-oss
- https://www.mend.io/blog/mend-renovate-enterprise-agentic-scale/
- https://github.blog/changelog/2026-04-01-research-plan-and-code-with-copilot-cloud-agent/ · https://github.blog/changelog/2026-04-10-copilot-usage-metrics-now-aggregate-copilot-cloud-agent-active-user-counts/
- https://github.com/orgs/community/discussions/165153 (Copilot Pro para mantenedores OSS)
- https://stacker.news/items/1195586 (Bugbot cobrança por contribuidor OSS)
- https://inkeep.com/integrations/github
- Diversos reviews de terceiros (aicoolies, dev.to, weavai, hackup.ai, medium) usados apenas como pista, não como fonte de fatos.

### 7.3 Baseline não agêntico

**Repositórios e páginas de projeto**
- https://github.com/probot/probot
- https://github.com/probot/probot/releases
- https://github.com/probot/stale
- https://github.com/probot/stale/blob/master/README.md
- https://github.com/actions/stale
- https://github.com/actions/stale/blob/main/README.md
- https://github.com/probot/settings (redireciona) / https://github.com/repository-settings/app
- https://github.com/probot/no-response
- https://github.com/lee-dohm/no-response
- https://github.com/behaviorbot/welcome
- https://github.com/behaviorbot/request-info
- https://github.com/dessant/lock-threads
- https://github.com/dessant/lock-threads-app
- https://github.com/actions/first-interaction
- https://github.com/tunnckoCore/triage-new-issues
- https://github.com/probot/adapter-github-actions
- https://probot.github.io/apps/
- https://jasonet.co/posts/probot-app-or-github-action-v2/
- https://github.com/googleapis/release-please
- https://raw.githubusercontent.com/googleapis/release-please/main/README.md
- https://github.com/googleapis/release-please/blob/main/docs/manifest-releaser.md
- https://github.com/googleapis/release-please/issues/2569
- https://github.com/googleapis/release-please-action
- https://github.com/googleapis/release-please-action/releases/tag/v5.0.0
- https://github.com/semantic-release/semantic-release
- https://semantic-release.gitbook.io/semantic-release/extending/plugins-list
- https://github.com/changesets/changesets
- https://github.com/changesets/changesets/blob/main/docs/config-file-options.md
- https://github.com/changesets/action
- https://github.com/changesets/bot
- https://github.com/apps/changeset-bot
- https://github.com/all-contributors/all-contributors (→ allcontributors.org)
- https://github.com/all-contributors/app
- https://github.com/all-contributors/cli
- https://github.com/apps/allcontributors
- https://allcontributors.org/docs/en/bot/usage
- https://allcontributors.org/docs/en/bot/configuration
- https://github.com/apps/welcome
- https://github.com/apps/request-info
- https://github.com/renovatebot/renovate
- https://github.com/apps/renovate
- https://docs.renovatebot.com/
- https://docs.renovatebot.com/configuration-options/
- https://docs.renovatebot.com/presets-config/
- https://docs.renovatebot.com/getting-started/running/
- https://docs.renovatebot.com/merge-confidence/
- https://github.com/renovatebot/renovate/issues/12024 (rename config:base → config:recommended)
- https://www.mend.io/blog/mend-renovate-enterprise-agentic-scale/
- https://github.com/github-changelog-generator/github-changelog-generator
- https://github.com/orhun/git-cliff
- https://git-cliff.org/docs/
- https://git-cliff.org/docs/usage/bump-version/
- https://github.com/conventional-changelog/standard-version
- https://github.com/absolute-version/commit-and-tag-version
- https://github.com/commitizen/cz-cli
- https://github.com/commitizen-tools/commitizen
- https://github.com/c4urself/bump2version
- https://callowayproject.github.io/bump-my-version/
- https://github.com/crate-ci/cargo-release/blob/master/docs/reference.md
- https://github.com/goreleaser/goreleaser
- https://goreleaser.com/intro/
- https://goreleaser.com/pro/
- https://python-semantic-release.readthedocs.io/en/latest/configuration/configuration.html
- https://github.com/your-tools/tbump
- https://github.com/twisted/towncrier
- https://towncrier.readthedocs.io/en/stable/configuration.html
- https://raw.githubusercontent.com/pypa/pip/main/pyproject.toml
- https://raw.githubusercontent.com/pytest-dev/pytest/main/pyproject.toml
- https://scriv.readthedocs.io/en/latest/
- https://scriv.readthedocs.io/en/latest/configuration.html
- https://docs.mergify.com/configuration/file-format/
- https://mergify.com/pricing
- https://github.com/chdsbd/kodiak
- https://kodiakhq.com/docs/config-reference
- https://github.com/marketplace/kodiakhq
- https://github.com/bors-ng/bors-ng
- https://github.com/actions/labeler
- https://github.com/github/issue-labeler
- https://github.com/release-drafter/release-drafter
- https://github.com/release-drafter/release-drafter/issues/335
- https://raw.githubusercontent.com/moby/moby/master/MAINTAINERS
- https://raw.githubusercontent.com/moby/moby/master/project/GOVERNANCE.md
- https://raw.githubusercontent.com/docker/cli/master/MAINTAINERS
- https://raw.githubusercontent.com/docker/opensource/master/MAINTAINERS
- https://github.com/docker/opensource
- https://www.kubernetes.dev/docs/guide/owners/
- https://github.com/cncf/project-template

**Documentação do GitHub**
- https://docs.github.com/en/code-security/dependabot/working-with-dependabot/dependabot-options-reference
- https://docs.github.com/en/code-security/dependabot/working-with-dependabot/automating-dependabot-with-github-actions
- https://docs.github.com/en/code-security/dependabot/dependabot-version-updates/optimizing-pr-creation-version-updates
- https://docs.github.com/en/code-security/dependabot/dependabot-version-updates/controlling-dependencies-updated
- https://docs.github.com/en/code-security/dependabot/dependabot-auto-triage-rules/about-dependabot-auto-triage-rules
- https://github.blog/changelog/2026-04-07-dependabot-alerts-are-now-assignable-to-ai-agents-for-remediation/
- https://docs.github.com/en/repositories/releasing-projects-on-github/automatically-generated-release-notes
- https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue
- https://github.blog/changelog/2023-07-12-pull-request-merge-queue-is-now-generally-available/
- https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners
- https://docs.github.com/en/code-security/getting-started/adding-a-security-policy-to-your-repository
- https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/creating-a-default-community-health-file
- https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms
- https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/creating-a-pull-request-template-for-your-repository
- https://docs.github.com/en/discussions/managing-discussions-for-your-community/syntax-for-discussion-category-forms
- https://docs.github.com/en/discussions/managing-discussions-for-your-community/managing-discussions
- https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/displaying-a-sponsor-button-in-your-repository

API do GitHub (via `gh api` e `curl`): `repos/{owner}/{repo}` e `repos/{owner}/{repo}/releases/latest` para todos os repositórios da tabela; `repos/moby/moby/commits?path=MAINTAINERS`.

Páginas que retornaram 404 ou não confirmaram o ponto (registradas para transparência): https://probot.github.io/docs/github-actions/ (404), https://allcontributors.org/docs/en/bot/overview (404), https://commitizen-tools.github.io/commitizen/config/ (404; usado o README).

### 7.4 Padrões de configuração por repositório

**Specs e diretórios de agentes**
- https://agents.md/
- https://github.com/agentsmd/agents.md/issues/9
- https://github.com/agentsmd/agents.md/issues/71
- https://github.com/agentsmd/agents.md/issues/179
- https://github.com/bgreenwell/dotagents
- https://dotagentsprotocol.com/
- https://agentskills.io/specification
- https://agentskills.io/home
- https://code.claude.com/docs/en/claude-directory
- https://code.claude.com/docs/en/memory
- https://code.claude.com/docs/en/skills
- https://code.claude.com/docs/en/settings
- https://code.claude.com/docs/en/plugins
- https://code.claude.com/docs/en/discover-plugins
- https://learn.chatgpt.com/docs/agent-configuration/agents-md (redirect de developers.openai.com/codex/guides/agents-md)
- https://learn.chatgpt.com/docs/build-skills (redirect de developers.openai.com/codex/skills)
- https://learn.chatgpt.com/docs/config-file/config-reference (redirect de developers.openai.com/codex/config-reference)
- https://learn.chatgpt.com/docs/config-file/config-basic.md
- https://learn.chatgpt.com/docs/agent-configuration/rules.md
- https://learn.chatgpt.com/docs/agent-configuration/subagents.md
- https://learn.chatgpt.com/docs/hooks.md
- https://learn.chatgpt.com/docs/plugins.md
- https://learn.chatgpt.com/docs/environments/cloud-environment.md
- https://learn.chatgpt.com/llms.txt
- https://developers.openai.com/plugins/build/plugins
- https://developers.openai.com/blog/skills-agents-sdk
- https://cursor.com/docs/context/rules
- https://cursor.com/docs/context/skills
- https://cursor.com/docs/reference/plugins
- https://docs.github.com/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot
- https://docs.github.com/en/copilot/concepts/agents/about-agent-skills
- https://docs.github.com/en/copilot/reference/custom-agents-configuration
- https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/create-custom-agents
- https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/add-custom-instructions/add-organization-instructions
- https://docs.github.com/en/enterprise-cloud@latest/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/customize-the-agent-environment
- https://github.blog/changelog/2026-04-02-copilot-organization-custom-instructions-are-generally-available/ (via busca)
- https://geminicli.com/docs/cli/gemini-md/
- https://geminicli.com/docs/cli/skills/
- https://geminicli.com/docs/extensions/reference/
- https://opencode.ai/docs/rules/
- https://opencode.ai/docs/config/
- https://docs.devin.ai/desktop/cascade/agents-md (redirect de docs.windsurf.com/windsurf/cascade/agents-md)
- https://docs.devin.ai/product-guides/knowledge
- https://docs.devin.ai/product-guides/creating-playbooks
- https://junie.jetbrains.com/docs/guidelines-and-memory.html
- https://kiro.dev/docs/steering/
- https://docs.cline.bot/customization/cline-rules
- https://roocodeinc.github.io/Roo-Code/features/custom-instructions (redirect de docs.roocode.com)
- https://docs.openhands.dev/overview/skills
- https://docs.openhands.dev/openhands/usage/customization/repository
- https://aider.chat/docs/config/aider_conf.html
- https://jules.google/docs/environment/
- https://ona.com/docs/ona/agents-md
- https://github.github.com/gh-aw/reference/frontmatter/
- https://github.com/OpenAI (via blog acima)

**Mudanças de mercado (status)**
- https://blog.kilo.ai/p/thank-you-roo
- https://thenewstack.io/roo-code-cloud-ides-ai-coding/ (busca)
- https://thenewstack.io/cursor-acquires-continue-coding/ (busca)
- https://dev.to/leobaniak/cursor-acquires-continue-and-gives-its-users-a-july-15-export-deadline-5dkn (busca)
- https://devin.ai/blog/windsurf-is-now-devin-desktop (HTTP 429; não lido)
- https://www.digitalapplied.com/blog/windsurf-becomes-devin-desktop-ide-migration-2026 (busca, secundária)
- https://www.infoq.com/news/2025/09/gitpod-ona/ (busca)
- https://ona.com/stories/gitpod-classic-payg-sunset (busca)
- https://ona.com/docs/ona/reference/automations-yaml-schema (busca)
- https://docs.sweep.dev/usage/config (HTTP 402; não lido)

**Bots de mantenedor e config de repo**
- https://github.com/googleapis/release-please/blob/main/docs/manifest-releaser.md (busca)
- https://semantic-release.org/usage/configuration/ (busca)
- https://docs.renovatebot.com/configuration-options/ (busca)
- https://docs.renovatebot.com/config-presets/
- https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/creating-a-default-community-health-file
- https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners
- https://docs.github.com/en/code-security/concepts/supply-chain-security/about-the-dependabot-yml-file (busca)
- https://docs.github.com/en/repositories/releasing-projects-on-github/automatically-generated-release-notes (busca)
- https://docs.github.com/en/discussions/managing-discussions-for-your-community/creating-discussion-category-forms (busca)
- https://github.com/probot/settings (busca) / https://probot.github.io/apps/settings/
- https://github.com/probot/stale (busca)
- https://github.com/changesets/changesets/blob/main/docs/config-file-options.md (busca)
- https://allcontributors.org/docs/en/bot/configuration (busca)
- https://git-cliff.org/docs/configuration/ (busca)
- https://docs.coderabbit.ai/reference/configuration
- https://docs.qodo.ai/install-and-configure/configuration-overview/configuration-file
- https://www.ellipsis.dev/docs/config (404); https://raw.githubusercontent.com/567-labs/instructor/main/ellipsis.yaml (verificado)
- https://www.greptile.com/docs/code-review/greptile-config
- https://www.greptile.com/docs/code-review-bot/greptile-json (vazio)
- https://docs.sourcery.ai/References/Legacy-Configuration/sourcery-yaml/ ; https://raw.githubusercontent.com/nilearn/nilearn/main/.sourcery.yaml (verificado)
- https://raw.githubusercontent.com/sweepai/sweep/main/sweep.yaml (verificado)
- https://docs.mergify.com/configuration/file-format/
- https://kodiakhq.com/docs/config-reference
- https://pre-commit.com/
- https://circleci.com/docs/reference/configuration-reference/ (busca; fetch 404)
- https://containers.dev/implementors/spec/
- https://mise.jdx.dev/configuration.html
- https://editorconfig.org/
- https://eslint.org/docs/latest/use/configure/migration-guide (busca)
- https://www.gitpod.io/docs/references/gitpod-yml (busca)
- https://just.systems/man/en/ (busca)
- https://www.rfc-editor.org/rfc/rfc8615
- https://nesbitt.io/2026/02/22/forge-specific-repository-folders.html
- https://github.com/git-pkgs/forge (busca)

**Precedentes de mantenedor**
- https://www.kubernetes.dev/docs/guide/owners/
- https://raw.githubusercontent.com/moby/moby/master/MAINTAINERS
- https://raw.githubusercontent.com/moby/moby/v20.10.0/MAINTAINERS
- https://github.com/numman-ali/openskills (`.github/maintainer/*` via API)
- https://github.com/numman-ali/n-skills (`skills/workflow/open-source-maintainer/**` via API)
- https://github.com/sunbeamdotpt/sbbb e https://github.com/sunbeamdotpt/cli (`.maintainer/*` via API)
- https://github.com/PrunaAI/pruna-skills (`.maintainer/` via API)
- https://github.com/nuonco/nuon-plugin (`.maintainer/UPGRADE.md` via API)
- https://github.com/dustinkirkland/byobu (`.maintainer/DEBIAN_PACKAGING_CONTEXT.md` via API)
- https://github.com/steipete/agent-scripts (skills `maintainer-orchestrator`, `github-project-triage` via API)
- https://github.com/mattpocock/skills (`skills/engineering/triage/SKILL.md` via API)
- https://mcpmarket.com/tools/skills/open-source-maintainer (HTTP 429; não lido)
- GitHub Code Search (`gh api search/code`) para `path:.maintainer/`, `path:.maintainers/`, `path:.github/maintainer/`, `path:.github/maintainers/`, `path:.agents/skills/`, `path:.claude/skills/`, `path:.codex/`, `path:.devin/rules/`, `path:.cursor/rules/`, `path:maintainer.yml`, `path:maintainer.toml`, `path:MAINTAINERS.toml`, `path:.github/MAINTAINERS.md`, `path:.project/`, `path:.release/`

### 7.5 Processos de mantenedores de referência

#### Lidas com sucesso (conteúdo extraído)
- https://github.com/kubernetes/sig-release/blob/master/release-team/README.md
- https://github.com/kubernetes/sig-release/blob/master/releases/release_phases.md
- https://github.com/kubernetes/sig-release/blob/master/releases/EXCEPTIONS.md
- https://github.com/kubernetes/sig-release/blob/master/release-blocking-jobs.md
- https://github.com/kubernetes/sig-release/blob/master/release-team/role-handbooks/release-team-lead/README.md
- https://github.com/kubernetes/sig-release/blob/master/release-team/role-handbooks/release-signal/README.md
- https://github.com/kubernetes/sig-release/blob/master/release-team/role-handbooks/communications/README.md
- https://github.com/kubernetes/sig-release/blob/master/release-team/role-handbooks/docs/relnotes-template.md (via API)
- https://github.com/kubernetes/sig-release/blob/master/release-engineering/handbooks/release-cuts.md (via API)
- https://github.com/kubernetes/sig-release/blob/master/release-engineering/handbooks/release-manager.md (via API)
- https://github.com/kubernetes/sig-release/blob/master/release-engineering/handbooks/security-releases.md (via API)
- https://github.com/kubernetes/sig-release/issues/2779 ("[1.34] Release Team Lead Cycle Progress", via `gh issue view`)
- https://github.com/kubernetes/community/blob/master/contributors/devel/sig-release/cherry-picks.md
- https://github.com/kubernetes/community/blob/master/contributors/guide/release-notes.md
- https://www.kubernetes.dev/docs/guide/release-notes/
- https://www.kubernetes.dev/docs/guide/issue-triage/
- https://kubernetes.io/releases/release/
- https://kubernetes.io/releases/patch-releases/
- https://kubernetes.io/releases/release-managers/
- https://github.com/kubernetes/release/blob/master/docs/krel/README.md
- https://github.com/kubernetes/release/blob/master/docs/krel/release-notes.md
- https://github.com/kubernetes/enhancements/blob/master/keps/NNNN-kep-template/kep.yaml (via API)
- https://docs.djangoproject.com/en/dev/internals/howto-release-django/
- https://docs.djangoproject.com/en/dev/internals/release-process/
- https://docs.djangoproject.com/en/dev/internals/security/
- https://code.djangoproject.com/wiki/ReleaseTestNewVersion
- https://forge.rust-lang.org/release/process.html
- https://forge.rust-lang.org/release/backporting.html
- https://forge.rust-lang.org/release/issue-triaging.html
- https://forge.rust-lang.org/release/triage-procedure.html
- https://forge.rust-lang.org/release/crater.html
- https://forge.rust-lang.org/release/release-notes.html
- https://forge.rust-lang.org/triagebot/index.html
- https://github.com/rust-lang/rust-forge/blob/master/src/compiler/prioritization.md (via API)
- https://github.com/rust-lang/release-team/issues/4 (via `gh issue view`)
- https://raw.githubusercontent.com/Mark-Simulacrum/rfcs/point-releases/text/0000-point-releases-on-a-schedule.md
- https://doc.rust-lang.org/book/appendix-07-nightly-rust.html
- https://github.com/rust-lang/rfcs/blob/master/README.md
- https://github.com/nodejs/node/blob/main/doc/contributing/releases.md
- https://github.com/nodejs/node/blob/main/doc/contributing/backporting-to-release-lines.md
- https://github.com/nodejs/node/blob/main/doc/contributing/collaborator-guide.md
- https://github.com/nodejs/Release/blob/main/README.md
- https://github.com/nodejs/node-core-utils/blob/main/docs/git-node.md
- https://github.com/nodejs/changelog-maker
- https://peps.python.org/pep-0101/
- https://peps.python.org/pep-0001/
- https://devguide.python.org/triage/triaging/
- https://devguide.python.org/triage/labels/
- https://devguide.python.org/developer-workflow/development-cycle/
- https://devguide.python.org/getting-started/pull-request-lifecycle/
- https://github.com/python/bedevere
- https://github.com/python/miss-islington
- https://docs.github.com/en/discussions/managing-discussions-for-your-community/managing-discussions
- https://docs.github.com/en/discussions/managing-discussions-for-your-community/managing-categories-for-discussions
- https://docs.github.com/en/discussions/managing-discussions-for-your-community/moderating-discussions
- https://docs.github.com/en/discussions/managing-discussions-for-your-community/syntax-for-discussion-category-forms
- https://docs.github.com/en/discussions/collaborating-with-your-community-using-discussions/collaborating-with-maintainers-using-discussions
- https://docs.github.com/en/discussions/collaborating-with-your-community-using-discussions/participating-in-a-discussion
- https://docs.github.com/en/discussions/guides/best-practices-for-community-conversations-on-github
- https://docs.github.com/en/repositories/releasing-projects-on-github/automatically-generated-release-notes (+ raw em github/docs)
- https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository
- https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases
- https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases
- https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches
- https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets
- https://github.blog/changelog/2021-05-18-github-discussions-labels-and-announcements-category-format/
- https://github.blog/open-source/maintainers/create-a-home-for-your-community-with-github-discussions/
- https://opensource.guide/best-practices/
- https://opensource.guide/leadership-and-governance/
- https://opensource.guide/building-community/
- https://www.apache.org/legal/release-policy.html
- https://www.apache.org/foundation/voting.html
- https://github.com/apache/airflow/blob/main/dev/README_RELEASE_AIRFLOW.md
- https://contribute.cncf.io/maintainers/
- https://contribute.cncf.io/maintainers/lifecycle/
- https://github.com/cncf/project-template
- https://github.com/cncf/project-template/blob/main/RELEASES.md
- https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/
- https://docs.pypi.org/trusted-publishers/
- https://docs.npmjs.com/generating-provenance-statements
- https://docs.docker.com/build/ci/github-actions/multi-platform/
- https://docs.docker.com/build/ci/github-actions/manage-tags-labels/
- https://github.com/docker/metadata-action
- https://wiki.postgresql.org/wiki/ReleasePrep
- https://wiki.postgresql.org/wiki/UpdateReleaseDrafting
- https://www.postgresql.org/support/versioning/
- https://www.home-assistant.io/faq/release/
- https://developers.home-assistant.io/docs/android/release/
- https://github.com/home-assistant/feature-requests (+ `.github/DISCUSSION_TEMPLATE/core-functionality.yml` via API)
- https://github.com/orgs/home-assistant/discussions/12
- https://community.home-assistant.io/t/heads-up-feature-requests-are-moving/903057
- https://github.com/getsentry/craft
- https://github.com/getsentry/publish
- https://develop.sentry.dev/sdk/getting-started/playbooks/setting-up-release-infrastructure/
- https://wiki.mozilla.org/Release_Management/Release_Process
- https://wiki.mozilla.org/Release_Management/Glossary
- https://firefox-source-docs.mozilla.org/contributing/pocket-guide-shipping-firefox.html
- https://www.bestpractices.dev/en/criteria/0
- https://keepachangelog.com/en/1.1.0/
- https://semver.org/spec/v2.0.0.html
- https://www.conventionalcommits.org/en/v1.0.0/
- https://semantic-release.gitbook.io/semantic-release/
- https://book.the-turing-way.org/collaboration/leadership
- https://book.the-turing-way.org/foreword/governance/
- https://github.com/mozilla/open-leadership-training-series (artigos `_articles/...` via API, branch gh-pages)
- https://nextjs.org/governance
- https://github.com/vercel/next.js/blob/canary/contributing.md
- https://raw.githubusercontent.com/vercel/next.js/canary/contributing/repository/triaging.md
- https://github.com/vercel/next.js `.github/DISCUSSION_TEMPLATE/ideas.yml` (via API)
- https://raw.githubusercontent.com/vitejs/vite/main/CONTRIBUTING.md
- https://github.com/tailwindlabs/tailwindcss/blob/main/.github/CONTRIBUTING.md
- https://docs.astral.sh/ruff/contributing/
- https://docs.deno.com/runtime/contributing/
- https://github.com/community/community
- https://github.com/emberjs/rfcs/blob/master/README.md
- https://arxiv.org/abs/2307.07117

#### Tentadas e indisponíveis (404 / redirect com login) — substituídas pelas acima
- https://github.com/kubernetes/sig-release/blob/master/release-team/role-handbooks/release-notes/README.md (handbook movido para `release-team/deprecated/release-notes`)
- https://github.com/kubernetes/sig-release/blob/master/releases/patch-releases.md (conteúdo vive em kubernetes.io/releases/patch-releases)
- https://github.com/kubernetes/sig-release/blob/master/release-team/role-handbooks/ci-signal/README.md e /bug-triage/README.md (absorvidos por release-signal)
- https://github.com/kubernetes/sig-release/blob/master/release-team/role-handbooks/release-lead/README.md (caminho correto: release-team-lead)
- https://github.com/kubernetes/sig-release/blob/master/release-engineering/role-handbooks/branch-manager.md e patch-release-team.md (links antigos citados em kubernetes.io; conteúdo atual em release-engineering/handbooks/release-cuts.md e release-manager.md)
- https://devguide.python.org/triage/issue-triage/ e /triage/reviewing/ (páginas atuais: /triage/triaging/ e /getting-started/pull-request-lifecycle/)
- https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/best-practices-for-maintainers (não existe)
- https://forge.rust-lang.org/release/point-releases.html (não existe; política de point release é ad hoc, ver seção 4.4 do relatório bruto de processos)
- https://forge.rust-lang.org/release/index.html (página de índice sem conteúdo útil)
- https://forge.rust-lang.org/compiler/prioritization/procedure.html (redirect quebrado; conteúdo lido via `src/compiler/prioritization.md`)
- https://github.com/vitejs/vite/blob/main/CONTRIBUTING.md (render falhou; lido via raw)
- https://mozilla.github.io/open-leadership-training-series/ e subpáginas (404; artigos lidos via API do repositório)
- https://link.springer.com/article/10.1007/s10664-023-10366-z (redirect para login; usado o arXiv)
