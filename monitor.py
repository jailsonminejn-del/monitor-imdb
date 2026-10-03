import json
import os
import re
import requests

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]

FILMES_FILE = "filmes.json"
ESTADO_FILE = "estado.json"


def carregar_json(arquivo, padrao):
    if not os.path.exists(arquivo):
        return padrao

    with open(arquivo, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar_json(arquivo, dados):
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def obter_nota(imdb_id):
    url = f"https://www.imdb.com/title/{imdb_id}/"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9"
    }

    resposta = requests.get(url, headers=headers, timeout=30)
    resposta.raise_for_status()

    html = resposta.text

    padroes = [
        r'"ratingValue":"([0-9.]+)"',
        r'"ratingValue":([0-9.]+)'
    ]

    for padrao in padroes:
        resultado = re.search(padrao, html)

        if resultado:
            return float(resultado.group(1))

    raise RuntimeError("Não foi possível encontrar a nota no IMDb.")


def enviar_discord(nome, imdb_id, nota_antiga, nota_nova):
    mensagem = {
        "content": (
            "🔔 **Nota do IMDb mudou!**\n\n"
            f"🎬 **{nome}**\n"
            f"⭐ **{nota_antiga:.1f} → {nota_nova:.1f}**\n"
            f"https://www.imdb.com/title/{imdb_id}/"
        )
    }

    resposta = requests.post(
        WEBHOOK_URL,
        json=mensagem,
        timeout=30
    )

    resposta.raise_for_status()


def main():
    filmes = carregar_json(FILMES_FILE, [])
    estado = carregar_json(ESTADO_FILE, {})

    for filme in filmes:
        imdb_id = filme["id"]
        nome = filme["nome"]

        try:
            nota_atual = obter_nota(imdb_id)
            nota_anterior = estado.get(imdb_id)

            print(
                f"{nome}: "
                f"{nota_anterior} → {nota_atual}"
            )

            # Primeira consulta: apenas salva a nota.
            if nota_anterior is None:
                estado[imdb_id] = nota_atual
                continue

            # Detecta 5.9 → 6.0 ou mais.
            if nota_anterior == 5.9 and nota_atual >= 6.0:
                enviar_discord(
                    nome,
                    imdb_id,
                    nota_anterior,
                    nota_atual
                )

            estado[imdb_id] = nota_atual

        except Exception as erro:
            print(f"Erro ao verificar {nome}: {erro}")

    salvar_json(ESTADO_FILE, estado)


if __name__ == "__main__":
    main()
