
# 🪄 AI-Project-Features  
_A self-contained multi-agent **refactor assistant** powered by BeeAI + IBM Watson x.ai_

---

##  Why?

Maintaining a large code base often means “small” chores—adding a logging helper, bumping a dependency, cloning an
existing agent—tasks that are repetitive but risky to do by hand.  
**AI-Project-Features** automates those edits end-to-end while enforcing a *non-destructive* gate:

* deterministic zip-scanner →  
* intent extraction →  
* task planning →  
* code generation →  
* import-time lint gate →  
* human-readable recap

You hand it a `.zip` of any Python project and a natural-language instruction; it returns a patch and a recap you can
review or apply directly.

---

##  How it works – the 10-phase pipeline

```mermaid
flowchart TD
    classDef phase fill:#f5f5f5,stroke:#555,stroke-width:1,color:#111;
    classDef io    fill:#d9e8ff,stroke:#1e56d6,stroke-width:1,color:#111;

    Z["file_search.tree(zip)\n(deterministic tool)"]:::phase
    LST["Directory tree +\nfile previews   ← tokens"]:::io

    P0["P0  – Attach prompt + tree\n      to shared context"]:::phase
    P1["P1  – Constraint / intent\n      extraction"]:::phase
    P2["P2  – Architecture recall\n      (token lookup)"]:::phase
    P3["P3  – Task decomposition\n      (derive numbered edits)"]:::phase
    P4["P4  – Feature instantiation\n      (pick / design agent)"]:::phase
    P5["P5  – Code & diff writer\n      (generate patch)"]:::phase
    D1{"D1  – Static import check\n      (py_compile + pytest)"}:::phase
    P6["P6  – Recap / re-enumerate\n      modified tree"]:::phase
    OUT["Answer → final\nstep-by-step recap"]:::io

    Z --> LST --> P0
    P0 --> P1 --> P2 --> P3 --> P4 --> P5 --> D1
    D1 -- OK --> P6 --> OUT
    D1 -- needs-fix --> P5
````

* **Z** – Deterministic zip scan (`src/tools/file_scanner.py`)
* **P1** – LLM parses prompt → JSON constraints (`request_parser_agent`)
* **P5 ⇄ D1** – BeeAI CodeAssistant writes/patches code **until** import passes
* **P6** – Markdown recap with patch summary & new tree (`doc_assembler_agent`)

---

## Project layout (depth ≤ 2)

```
ai-project-features/
├─ app.py                    # optional Flask façade
├─ scripts/
│   ├─ install.sh            # venv + deps
│   └─ start.sh              # run CLI / server
├─ src/
│   ├─ main.py               # CLI driver
│   ├─ workflows.py          # declarative DAG map
│   ├─ config.py             # env validation via pydantic
│   ├─ memory.py             # tiny blackboard
│   ├─ llm/
│   │   ├─ __init__.py
│   │   └─ watson_client.py  # thin Watsonx wrapper
│   ├─ tools/
│   │   ├─ file_scanner.py
│   │   └─ diff_generator.py
│   ├─ agents/               # one .py per phase
│   │   ├─ request_parser_agent.py
│   │   ├─ architecture_lookup_agent.py
│   │   ├─ task_planner_agent.py
│   │   ├─ feature_instantiation_agent.py
│   │   ├─ code_writer_agent.py
│   │   ├─ static_checker_agent.py
│   │   ├─ self_refine_agent.py
│   │   └─ doc_assembler_agent.py
│   └─ templates/flowchart.mmd
└─ tests/
   └─ test_workflow.py
```

---

## Quick start

```bash
# 1 · Clone & bootstrap
git clone https://github.com/ruslanmv/ai-project-features.git
cd ai-project-features
./scripts/install.sh        # creates .venv + installs deps

# 2 · Fill in .env  (WatsonX + BeeAI keys)
$EDITOR .env

# 3 · Run the assistant on a sample repo
python -m src \
  --zip tests/sample_project.zip \
  --prompt "Add a new logging agent that writes INFO to stdout"
```

Output ends with a **Markdown recap** similar to:

```
## New agent added
* Class: LoggingAgent
* Purpose: Write INFO messages
* File: src/agents/loggingagent.py

## What was changed
Created src/agents/loggingagent.py  (83 lines)

## Updated directory tree (depth ≤3)
...
```

---

## API mode (optional)

```bash
export MODE=server          # `scripts/start.sh` checks this
./scripts/start.sh          # Flask runs on :9000
```

* **POST /apply** – `multipart/form-data` (`file=` zip, `prompt=` text)
  → JSON `{ recap: "...markdown..." }`
* **GET /health** – returns `OK`

---

## Environment variables (`.env.sample`)

```
# Watson x.ai
WATSONX_API_KEY=
WATSONX_PROJECT_ID=
WATSONX_URL=https://us-south.ml.cloud.ibm.com

# BeeAI defaults
DEFAULT_LLM_MODEL_ID=granite-20b-chat
LLM_TEMPERATURE=0.2

# Workflow knobs
MAX_P5_ATTEMPTS=4
LOG_LEVEL=INFO
```

---

## Security model

| Gate                    | What we check                                  | Mitigation                                |
| ----------------------- | ---------------------------------------------- | ----------------------------------------- |
| **AST validation**      | no top-level exec statements in generated code | abort P5 if found                         |
| **py\_compile**         | syntax errors                                  | loop back to P5                           |
| **pytest collect-only** | import-time errors / missing deps              | auto-append to `requirements.txt` or loop |
| **nonDestructive flag** | prevents overwriting existing files            | hard fail                                 |

---

## Contributing

1. Fork → feature branch
2. `pytest -q` must stay green
3. Send PR; CI will run the sample workflow + lint checks

---

## License

Apache 2.0 ― free for commercial & academic use. See [LICENSE](LICENSE).

---

### Stay in touch

* **Issues** → GitHub issues
* **Chat** → Slack #ai-project-features

Happy refactoring! 🚀
