# actual-qfx-importer-py

Python web application for importing QFX/OFX bank transaction files into [Actual Budget](https://actualbudget.org/).

Built with [Reflex](https://reflex.dev/) and [actualpy](https://github.com/bvanelli/actualpy).

## Features

- **First-time setup**: A one-time setup token is printed to the server logs on first launch. Use the token at `/setup` to create an app password.
- **Authentication**: Single-password login (no user management). Session is stored in browser localStorage.
- **Settings page** (`/settings`): Configure all Actual Budget connection parameters – server URL, password, budget file, encryption password, data directory, and TLS certificate.
- **API key management** (`/api-key`): Generate / regenerate an API key for external integrations; change the app password.
- **QFX / OFX import** (`/import`): Drag-and-drop or browse for `.qfx` / `.ofx` files and import their transactions directly into your Actual Budget.

## Requirements

- Python 3.10+
- A running [Actual Budget server](https://actualbudget.org/docs/install/)

## Installation

```bash
pip install -r requirements.txt
```

## Running

```bash
reflex run
```

On the first run the server prints a setup token to the console:

```
================================================================
  QFX IMPORTER – FIRST-TIME SETUP
  Setup token: <your-token-here>
  Visit /setup in your browser to complete setup.
================================================================
```

Open `http://localhost:3000/setup` in your browser, enter the token, and set a password.

## Technology Stack

| Library | Purpose |
|---------|---------|
| [Reflex](https://reflex.dev/) | Full-stack Python web framework |
| [actualpy](https://github.com/bvanelli/actualpy) | Actual Budget Python client (`import actual`) |
| [ofxparse](https://github.com/jseutter/ofxparse) | QFX / OFX file parser |
| [SQLModel](https://sqlmodel.tiangolo.com/) | SQLite persistence |
| [passlib](https://passlib.readthedocs.io/) | Password hashing (bcrypt) |
