#!/usr/bin/env python3
"""Script interactif RodiumAi sans SDK (Module 3, exercice 2)."""

from __future__ import annotations

import base64
import json
import os
import sys
from typing import Literal

import requests
from dotenv import load_dotenv

load_dotenv(override=True)

BASE_URL = os.getenv("RODIUMAI_BASE_URL", "https://api.rodiumai.io/v1")
CHAT_MODEL = os.getenv("RODIUMAI_CHAT_MODEL", "openai/gpt-4o-mini")
IMAGE_MODEL = os.getenv("RODIUMAI_IMAGE_MODEL", "openai/gpt-image-1-mini")
VIDEO_MODEL = os.getenv("RODIUMAI_VIDEO_MODEL", "google/veo-3.1-fast")
VIDEO_SECONDS = float(os.getenv("RODIUMAI_VIDEO_SECONDS", "4"))

TIMEOUT_CHAT = 120
TIMEOUT_IMAGE = 120
TIMEOUT_VIDEO = 150

IMAGE_OUTPUT = "image.png"
VIDEO_OUTPUT = "video.mp4"

StepChoice = Literal["stay", "next", "back", "quit"]


def load_api_key() -> str:
    load_dotenv(override=True)
    api_key = os.getenv("RODIUMAI_API_KEY", "").strip()
    if not api_key:
        print(
            "Clé API absente. Copiez .env.example vers .env et renseignez RODIUMAI_API_KEY."
        )
        sys.exit(1)
    return api_key


def auth_headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def print_api_error(response: requests.Response) -> None:
    try:
        payload = response.json()
    except json.JSONDecodeError:
        print(f"Erreur HTTP {response.status_code} : {response.text[:500]}")
        return

    err = payload.get("error")
    if isinstance(err, dict):
        code = err.get("error_code") or err.get("code") or "inconnu"
        message = err.get("message") or str(err)
    else:
        code = payload.get("error_code") or "inconnu"
        message = payload.get("message") or str(payload)

    print(f"Erreur HTTP {response.status_code} (error_code : {code}) : {message}")


def ask_navigation(step: int) -> StepChoice:
    while True:
        if step == 1:
            label = "Rester sur cette étape (r) ou passer à la suivante (s) ? "
            valid = {"r": "stay", "s": "next"}
        elif step == 2:
            label = "Revenir en arrière (b), rester (r) ou passer à la suivante (s) ? "
            valid = {"b": "back", "r": "stay", "s": "next"}
        else:
            label = "Revenir en arrière (b), rester (r) ou quitter (q) ? "
            valid = {"b": "back", "r": "stay", "q": "quit"}

        choice = input(label).strip().lower()
        if choice in valid:
            return valid[choice]  # type: ignore[return-value]
        print("Choix invalide, réessayez.")


def run_chat_step(api_key: str) -> StepChoice:
    while True:
        print("=== Étape 1 : Chat ===")
        question = input("Votre question : ").strip()
        if not question:
            print("Question vide.")
            continue

        response = requests.post(
            f"{BASE_URL}/chat/completions",
            headers=auth_headers(api_key),
            json={
                "model": CHAT_MODEL,
                "messages": [{"role": "user", "content": question}],
            },
            timeout=TIMEOUT_CHAT,
        )
        if response.status_code != 200:
            print_api_error(response)
            nav = ask_navigation(1)
            if nav != "stay":
                return nav
            continue

        data = response.json()
        print(data["choices"][0]["message"]["content"])
        cost = data.get("cost_rodi")
        if cost is not None:
            print(f"Coût : {cost} RODI")

        nav = ask_navigation(1)
        if nav != "stay":
            return nav


def save_b64_file(b64_data: str, path: str) -> None:
    raw = base64.b64decode(b64_data)
    with open(path, "wb") as handle:
        handle.write(raw)


def download_url_file(url: str, path: str, api_key: str) -> None:
    file_response = requests.get(
        url,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=TIMEOUT_VIDEO,
    )
    file_response.raise_for_status()
    with open(path, "wb") as handle:
        handle.write(file_response.content)


def run_image_step(api_key: str) -> StepChoice:
    while True:
        print("=== Étape 2 : Image ===")
        prompt = input("Décrivez l'image : ").strip()
        if not prompt:
            print("Description vide.")
            continue

        response = requests.post(
            f"{BASE_URL}/images/generations",
            headers=auth_headers(api_key),
            json={
                "model": IMAGE_MODEL,
                "prompt": prompt,
                "n": 1,
                "size": "1024x1024",
                "quality": "medium",
            },
            timeout=TIMEOUT_IMAGE,
        )
        if response.status_code != 200:
            print_api_error(response)
            nav = ask_navigation(2)
            if nav != "stay":
                return nav
            continue

        item = response.json()["data"][0]
        b64_json = item.get("b64_json")
        if not b64_json:
            print("Réponse sans b64_json.")
            nav = ask_navigation(2)
            if nav != "stay":
                return nav
            continue

        save_b64_file(b64_json, IMAGE_OUTPUT)
        print(f"Image enregistrée : {IMAGE_OUTPUT}")

        nav = ask_navigation(2)
        if nav != "stay":
            return nav


def run_video_step(api_key: str) -> StepChoice:
    while True:
        print("=== Étape 3 : Vidéo ===")
        prompt = input("Décrivez la vidéo : ").strip()
        if not prompt:
            print("Description vide.")
            continue

        response = requests.post(
            f"{BASE_URL}/videos/generations",
            headers=auth_headers(api_key),
            json={
                "model": VIDEO_MODEL,
                "prompt": prompt,
                "duration_seconds": VIDEO_SECONDS,
            },
            timeout=TIMEOUT_VIDEO,
        )
        if response.status_code != 200:
            print_api_error(response)
            nav = ask_navigation(3)
            if nav != "stay":
                return nav
            continue

        item = response.json()["data"][0]
        b64_json = item.get("b64_json")
        url = item.get("url")

        try:
            if b64_json:
                save_b64_file(b64_json, VIDEO_OUTPUT)
            elif url:
                download_url_file(url, VIDEO_OUTPUT, api_key)
            else:
                print("Réponse vidéo sans b64_json ni url.")
                nav = ask_navigation(3)
                if nav != "stay":
                    return nav
                continue
        except requests.RequestException as exc:
            print(f"Impossible d'enregistrer la vidéo : {exc}")
            nav = ask_navigation(3)
            if nav != "stay":
                return nav
            continue

        print(f"Vidéo enregistrée : {VIDEO_OUTPUT}")

        nav = ask_navigation(3)
        if nav != "stay":
            return nav


def main() -> None:
    api_key = load_api_key()
    step = 1

    while step >= 1:
        if step == 1:
            choice = run_chat_step(api_key)
        elif step == 2:
            choice = run_image_step(api_key)
        else:
            choice = run_video_step(api_key)

        if choice == "next":
            step += 1
        elif choice == "back":
            step = max(1, step - 1)
        elif choice == "quit":
            print("Fin du programme.")
            break
        # "stay" relance la même étape via la boucle interne


if __name__ == "__main__":
    main()
