# Module 3 RodiumAi - Exercice 2 (API sans SDK)

Script Python interactif : chat, génération d'image et de vidéo via l'API RodiumAi, avec **requests** uniquement (pas de SDK).

## Prérequis

- Python 3.10+
- Compte RodiumAi, clé API (`rd_sk_…`) et crédits RODI

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Éditez `.env` avec votre clé (ne jamais la committer).

## Lancement

```bash
source .venv/bin/activate
python main.py
```

## Partie curl (captures terminal)

```bash
set -a && source .env && set +a
curl https://api.rodiumai.io/v1/wallet -H "Authorization: Bearer $RODIUMAI_API_KEY"
curl https://api.rodiumai.io/v1/chat/completions \
  -H "Authorization: Bearer $RODIUMAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"openai/gpt-4o-mini","messages":[{"role":"user","content":"Explique les crédits RODI."}]}'
```

## Structure

```text
.
├── README.md
├── .env.example
├── .gitignore
├── requirements.txt
└── main.py
```
