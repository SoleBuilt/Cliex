# Cliex

**Cliex** is a Python CLI tool that helps you bootstrap projects quickly using **setup profiles** defined in YAML. Instead of retyping dozens of install commands every time you start a new project, you run one command — Cliex executes the entire setup workflow for you.

The source code is **free and open** for the community. You may use, modify, and share it freely under the MIT license.

## Features

- Bootstrap a new project with a single command
- Support for multiple setup profiles (Next.js, FastAPI, Razor, etc.)
- Create or customize your own profiles via YAML files
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

# Use a custom YAML file directly
cliex new my-app --setup path/to/my-setup.yaml
```

### List available profiles

```bash
cliex list
```

This displays all registered profiles, their source (package or user), and which one is the default.

### Create or edit a profile

```bash
# Create a new profile (or open the file if it already exists)
cliex registry my-custom-setup

# Edit profile metadata
cliex metadata
```

When creating a new profile, Cliex will:

1. Create a `my-custom-setup.yaml` file with a sample template
2. Automatically register the profile in `cliex-metadata.yaml`
3. Open the file in your system's default text editor

### Run without installing

```bash
python -m cliex new my-app
python -m cliex list
```

## Commands

| Command | Description |
|---------|-------------|
| `cliex new [PROJECT_NAME]` | Create a new project using a setup profile |
| `cliex new --setup <profile>` | Select a specific profile or YAML file |
| `cliex list` | List all setup profiles |
| `cliex registry <name>` | Create or edit a profile YAML file |
| `cliex metadata` | Open `cliex-metadata.yaml` to edit metadata |

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

## Customizing setup profiles

Each profile is a YAML file with a list of `steps`. Supported step types:

| Type | Description | Example |
|------|-------------|---------|
| `run` | Run a shell command | `cmd: npm install` |
| `copy` | Copy a file | `src`, `dest` |
| `append` | Append content to a file | `file`, `content` |
| `git` | Git operations | `add`, `commit_message`, `username`, `email` |

Minimal profile example:

```yaml
steps:
  - type: run
    name: say-hello
    cmd: echo "Hello from Cliex!"
```

### Where profiles are stored

- **Package** (bundled with Cliex): `cliex/templates/setups/`
- **User** (your custom profiles):
  - Windows: `%APPDATA%\cliex\setups\`
  - macOS / Linux: `~/.config/cliex/setups/`

User-created profiles override package profiles with the same name.

## Project structure

```
cliex/
├── cliex/
│   ├── main.py              # CLI entry point (Typer)
│   ├── cli/
│   │   └── new.py           # New project creation logic
│   ├── setup/
│   │   ├── registry.py      # Setup profile registry
│   │   ├── loader.py        # YAML file loader
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

Configure git first:

```bash
git config --global user.name "Your Name"
git config --global user.email "email@example.com"
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
