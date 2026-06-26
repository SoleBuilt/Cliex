# Cliex

<p align="center">
  <img src="Panel Cliex.png" alt="Cliex — One command. Ready to build." width="100%" />
</p>

**Cliex** is a Python CLI tool that helps you bootstrap projects quickly using **setup profiles** defined in YAML. Instead of retyping dozens of install commands every time you start a new project, you run one command — Cliex executes the entire setup workflow for you.

The source code is **free and open** for the community. You may use, modify, and share it freely under the MIT license.

## Features

- Bootstrap a new project with a single command
- Support for multiple setup profiles (Next.js, FastAPI, Razor, etc.)
- Create or customize your own profiles via YAML files
- Rich step types — run commands, copy/move files, and edit generated files
  with idempotent `insert` / `replace`
- Platform-specific steps via `when` (Windows / macOS / Linux)
- Save a default git identity so the commit step never fails
- List and manage available profiles
- Colorful terminal output for easy progress tracking
- Automatic checks for required tools before running

## Requirements

- Python 3.11+
- Node.js, npm, npx (for frontend profiles such as Next.js)
- Git

## Installation

### Option 1 — PyPI (recommended for end users)

Requires Python 3.11+.

```bash
# Recommended: isolated install
pipx install cliex

# Or with pip
pip install cliex
```

Verify:

```bash
cliex list
```

**Update to the latest version:**

```bash
pipx upgrade cliex
# or
pip install -U cliex
```

### Option 2 — GitHub Releases

Download a wheel from [Releases](https://github.com/DucHuynhTrung/cliex-quick/releases) or install directly:

```bash
pip install https://github.com/DucHuynhTrung/cliex-quick/releases/download/v0.1.0/cliex-0.1.0-py3-none-any.whl
```

Replace `v0.1.0` with the latest tag.

### Option 3 — Install from source (development)

```bash
git clone https://github.com/DucHuynhTrung/cliex-quick.git
cd cliex-quick

pip install -e .
```

### Using uv (optional)

```bash
uv venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

uv pip install -e .
```

After installation, the `cliex` command is available in your terminal.

> **Maintainers:** see [docs/RELEASE.md](docs/RELEASE.md) for the full GitLab → GitHub mirror → PyPI + Releases workflow.

## Usage

### Create a new project

```bash
# Create a project in the "my-app" folder (uses the default profile)
cliex new my-app

# Create a project in the current directory
cliex new .

# No name provided → defaults to the current directory
cliex new
```

### Choose a specific setup profile

```bash
# Use the Next.js profile
cliex new my-app --setup nextjs-setup

# Short form
cliex new my-app -s fastapi

# Force the built-in version (ignore your custom override)
cliex new my-app -s b:nextjs-setup

# Force your custom version
cliex new my-app -s u:nextjs-setup

# Use a custom YAML file directly
cliex new my-app --setup path/to/my-setup.yaml
```

When you have a custom profile and a built-in profile with the same key, the
custom one wins by default. Use the `b:` prefix to force the built-in, or `u:`
to force the user version.

### Pass variables

If a profile declares variables, you can provide them on the command line or
let Cliex prompt you:

```bash
# Provide values (skips the prompt for those)
cliex new my-app -s my-profile --var git_user=Duc --var app_title="My App"

# Use declared defaults without prompting
cliex new my-app -s my-profile --yes
```

### Set the git identity for the commit step

Profiles that initialize git need a `user.name` / `user.email`, otherwise the
commit step fails with *"unable to auto-detect email address"*. Cliex resolves
the identity in this order:

> `--username` / `--useremail` flag  →  saved default (`cliex config`)  →  your global git config

Per-project (overrides the saved default for this run only):

```bash
cliex new my-app -s tauri-setup --username "Your Name" --useremail "you@example.com"
# Short form
cliex new my-app -s tauri-setup -un "Your Name" -ue "you@example.com"
```

Save a default once, then every `cliex new` reuses it:

```bash
# Set the default git identity
cliex config --git-username "Your Name" --git-email "you@example.com"

# Show current defaults (default profile + git identity)
cliex config
```

The identity is stored per-user in `config.yaml` (never inside a shared
profile). Inside a profile, the resolved values are available as the
`{{ git_username }}` and `{{ git_email }}` variables — typically used by a
`git` step that runs `git config --local` right after `git init`:

```yaml
- type: run
  name: git-init
  cmd: git init
- type: git
  name: git-config
  username: "{{ git_username }}"
  email: "{{ git_email }}"
```

If both flag and saved default are empty, the `git` step is skipped and git
falls back to your global config.

### List available profiles

```bash
cliex list
```

This displays all registered profiles, their source (package or user), and which one is the default.

### Create, fork, or edit a profile

```bash
# Create a new profile, fork a built-in to customize it, or open an existing one
cliex registry my-custom-setup

# Fork the built-in nextjs-setup into an editable local copy
cliex registry nextjs-setup
```

`cliex registry <key>` always writes to your user setup directory and:

1. If you already have a user profile with that key → opens it.
2. Else if a built-in with that key exists → copies it into your user directory
   as a local override, then opens it. Future app updates won't touch your copy.
3. Else → creates a new `<key>.yaml` template (with `name`, `description`, and a
   sample step) and opens it.

The file is opened in your system's default text editor. Profile metadata
(`name`, `description`) lives inside the file itself, so profiles are
self-describing and easy to share.

### Set the default profile

```bash
cliex set-default fastapi
```

`cliex new` with no `--setup` uses this default. The setting is stored per-user
in `config.yaml` (it is never embedded in a shared profile).

### Revert a customized built-in

```bash
cliex reset nextjs-setup
```

Removes your local override and goes back to the built-in profile.

### Validate profiles

```bash
# Validate one profile
cliex validate nextjs-setup

# Validate all profiles
cliex validate
```

### Run without installing

```bash
python -m cliex new my-app
python -m cliex list
```

## Commands

| Command | Description |
|---------|-------------|
| `cliex new [PROJECT_NAME]` | Create a new project using a setup profile |
| `cliex new --setup <profile>` | Select a profile (`b:`/`u:` prefix or YAML file) |
| `cliex new --var k=v` `--yes` | Provide profile variables / skip prompts |
| `cliex new -un <name> -ue <email>` | Set git identity for this project's commit step |
| `cliex config` | Show persistent defaults (default profile + git identity) |
| `cliex config --git-username <n> --git-email <e>` | Save the default git identity |
| `cliex list` | List all setup profiles |
| `cliex registry <name>` | Create, fork, or edit a profile YAML file |
| `cliex set-default <name>` | Set the default profile |
| `cliex reset <name>` | Remove a custom override, revert to built-in |
| `cliex validate [name]` | Validate one or all profiles |

## Built-in setup profiles

| Profile | Description |
|---------|-------------|
| `nextjs-setup` *(default)* | Next.js + TypeScript + Tailwind + ESLint + shadcn/ui + Firebase + agent skills |
| `fastapi` | FastAPI with a virtual environment |
| `razor` | Razor project setup |

Step-by-step details for each profile live in `cliex/templates/setups/`.

### What does the Next.js profile do?

When you run `cliex new my-app -s nextjs-setup`, Cliex will:

1. Check for `node`, `npm`, `npx`, and `git`
2. Create a Next.js project (TypeScript, Tailwind, ESLint, App Router)
3. Install packages: Firebase, Zod, TanStack Query, Zustand, etc.
4. Initialize shadcn/ui and add common components
5. Install agent skills for Claude
6. Initialize git and commit the changes
7. Add your customizations.

And you're ready to write code.

## Customizing setup profiles

Each profile is a YAML file with top-level `name`, `description`, an optional
`variables` list, and a list of `steps`. Supported step types:

| Type | Description | Example fields |
|------|-------------|----------------|
| `run` | Run a shell command | `cmd: npm install` |
| `copy` | Copy a file or directory | `src`, `dest` |
| `move` | Move/rename a file or directory | `src`, `dest` |
| `mkdir` | Create a directory | `path` |
| `remove` | Delete a file or directory | `path`, `ignore_missing` |
| `append` | Append content to the end of a file | `file`, `content` |
| `insert` | Insert content at a line number or anchor | `file`, `content`, one of `line`/`after`/`before`, `skip_if_present` |
| `replace` | Replace a literal string inside a file | `file`, `find`, `replace`, `count`, `skip_if_missing` |
| `git` | Git operations | `add`, `commit_message`, `username`, `email` |

#### `insert` and `replace` (editing generated files)

Use these to tweak files a scaffolder created, without shipping template
copies. Both are **idempotent** — re-running a setup won't duplicate changes.

```yaml
# Insert a line right after the line that matches an anchor
- type: insert
  file: src/main.tsx
  after: 'import App from "./App";'   # or: before: '<text>'  /  line: 3
  content: |
    import "./index.css";

# Replace a literal string (e.g. add a plugin to an array)
- type: replace
  file: vite.config.ts
  find: "plugins: [react()]"
  replace: "plugins: [react(), tailwindcss()]"
```

- `insert`: pick **one** of `line` (1-based, inserts *before* that line),
  `after` (inserts on the next line after the match), or `before`. With none,
  it appends at the end. `skip_if_present: true` (default) skips when the
  content already exists; a missing `after`/`before` anchor raises an error.
- `replace`: replaces all occurrences by default (`count: N` limits it). If
  `find` is absent but `replace` is already present, the step is skipped
  (safe re-runs); set `skip_if_missing: true` to ignore a genuinely missing
  `find` instead of erroring.

### Platform-specific steps (`when`)

Any step may include a `when` field so it only runs on matching platforms —
this is how you express "if/else by OS" (write one step per platform; the
non-matching ones are skipped):

| `when` | Runs on |
|--------|---------|
| `windows` | Windows only |
| `unix` | Any non-Windows OS (Linux, macOS, BSD) |
| `linux` | Linux only |
| `macos` / `darwin` | macOS only |

A step with no `when` runs everywhere (the "else" branch).

```yaml
- type: run
  name: redirect-stdin
  when: windows
  cmd: some-cli < NUL
- type: run
  name: redirect-stdin
  when: unix
  cmd: some-cli < /dev/null
```

Minimal profile example:

```yaml
name: My Profile
description: A tiny example profile.
steps:
  - type: run
    name: say-hello
    cmd: echo "Hello from Cliex!"
```

### Variables

Declare variables and reference them with `{{ name }}` in any step string.
`project_name` and `project_path` are always available.

```yaml
name: My Profile
description: Example with variables.
variables:
  - name: app_title
    prompt: "App title"
    default: "My App"
steps:
  - type: append
    file: README.md
    content: "# {{ app_title }} ({{ project_name }})\n"
```

Provide values with `--var app_title="..."`, accept defaults with `--yes`, or
answer the interactive prompt.

### Where profiles are stored

- **Package** (bundled with Cliex): `cliex/templates/setups/`
- **User** (your custom profiles):
  - Windows: `%APPDATA%\cliex\setups\` (i.e. `...\AppData\Roaming\cliex\setups\`)
  - macOS / Linux: `~/.config/cliex/setups/`

User-created profiles override package profiles with the same key (filename).
Updating Cliex never touches your user profiles. Per-user settings — the
default profile and the default git identity — are stored in `config.yaml` next
to your setups directory (never inside a shared profile).

## Project structure

```
cliex/
├── cliex/
│   ├── main.py              # CLI entry point (Typer)
│   ├── cli/
│   │   └── new.py           # New project creation logic
│   ├── setup/
│   │   ├── registry.py      # Profile registry, default, validation
│   │   ├── loader.py        # YAML file loader
│   │   ├── variables.py     # Variable prompts + {{ }} substitution
│   │   └── executor.py      # Step executor
│   ├── runner/
│   │   └── runner.py        # Subprocess runner
│   ├── checker/
│   │   └── checker.py       # System requirement checker
│   └── templates/
│       └── setups/          # Default profiles + metadata
├── pyproject.toml
├── LICENSE
└── README.md
```

## Troubleshooting

### Missing required tools

```
Missing required commands: node, npm
```

Install the missing tools:

- **Node.js / npm**: https://nodejs.org/
- **Git**: https://git-scm.com/

### Target directory already exists

```
Target folder already exists
```

Choose a different folder name or remove the existing directory before running again.

### Git commit failed

```
*** Please tell me who you are.
fatal: unable to auto-detect email address
```

The commit step has no git identity. Fix it with any of these (highest
precedence first):

```bash
# Per project, for this run only
cliex new my-app -un "Your Name" -ue "you@example.com"

# Saved default, reused by every future run
cliex config --git-username "Your Name" --git-email "you@example.com"

# Or your machine-wide global git identity
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

### Profile not found

Run `cliex list` to see available profiles, or create a new one with `cliex registry <name>`.

## Development

```bash
# Install in editable mode
pip install -e .

# Run directly
python -m cliex list
```

## Contributing

Contributions are welcome! You can:

- Report bugs or request features via [Issues](https://github.com/DucHuynhTrung/cliex-quick/issues)
- Submit Pull Requests with new setup profiles or code improvements
- Share your YAML profiles with the community

## License

This project is released under the **MIT** license — completely **free** and open source for the community.

You are free to use, copy, modify, distribute, and use it commercially without permission. See [LICENSE](LICENSE) for details.

## Author

**DucHuynhTrung** — [huynhtrungduc.growth@gmail.com](mailto:huynhtrungduc.growth@gmail.com)
