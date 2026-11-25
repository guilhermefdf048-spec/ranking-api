# 🏆 Ranking de Jogadores API

API REST em Python com **FastAPI** para cadastrar jogadores, registrar partidas e consultar o placar dos melhores. Pode ser usada por qualquer jogo, inclusive no **Roblox** (há um exemplo em Luau na pasta `exemplos/`).

![Testes](../../actions/workflows/testes.yml/badge.svg)

## Funcionalidades

- Cadastro de jogadores com nome único (sem diferenciar maiúsculas/minúsculas)
- Registro de partidas, com soma automática dos pontos
- Ranking com posição, desempate por quem se cadastrou primeiro e limite configurável
- Histórico de partidas de cada jogador
- Validação dos dados de entrada com Pydantic (nome de 3 a 20 caracteres, pontos não negativos)
- Chave de API opcional para proteger as rotas que alteram dados
- Documentação interativa gerada automaticamente em `/docs`
- Testes automatizados com pytest, rodando no GitHub Actions

## Tecnologias

Python 3.10+ · FastAPI · Pydantic · SQLite · Uvicorn · pytest · GitHub Actions

## Como rodar

```bash
git clone https://github.com/guilhermefdf048-spec/ranking-api
cd ranking-api
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Abra **http://127.0.0.1:8000/docs** no navegador. Dá para testar todas as rotas por ali, clicando em **Try it out**.

## Rotas

| Método | Rota | O que faz |
| --- | --- | --- |
| `POST` | `/jogadores` | Cadastra um jogador `{"nome": "Ana"}` |
| `GET` | `/jogadores` | Lista todos os jogadores |
| `GET` | `/jogadores/{id}` | Mostra um jogador |
| `DELETE` | `/jogadores/{id}` | Remove o jogador e suas partidas |
| `POST` | `/jogadores/{id}/partidas` | Registra uma partida `{"pontos": 150}` |
| `GET` | `/jogadores/{id}/partidas` | Histórico de partidas do jogador |
| `GET` | `/ranking?limite=10` | Os melhores jogadores |

### Exemplo de resposta: `GET /ranking`

```json
[
  { "posicao": 1, "id": 2, "nome": "Bia", "pontos": 250, "partidas": 1 },
  { "posicao": 2, "id": 1, "nome": "Ana", "pontos": 100, "partidas": 1 }
]
```

### Erros

| Código | Quando acontece |
| --- | --- |
| `401` | Chave de API ausente ou errada (quando `API_KEY` está definida) |
| `404` | Jogador não encontrado |
| `409` | Nome de jogador já está em uso |
| `422` | Dados inválidos (nome curto demais, pontos negativos etc.) |

## Configuração

| Variável | Padrão | Para que serve |
| --- | --- | --- |
| `RANKING_DB` | `ranking.db` | Arquivo do banco SQLite |
| `API_KEY` | *(vazia)* | Se definida, `POST` e `DELETE` exigem o cabeçalho `X-API-Key` |

No Windows (Prompt de Comando):

```
set API_KEY=minha-chave-secreta
uvicorn app.main:app --reload
```

## Usando no Roblox

O arquivo [`exemplos/roblox_ranking.server.lua`](exemplos/roblox_ranking.server.lua) mostra como cadastrar jogadores e ler o ranking com o `HttpService`. Para funcionar no Roblox, a API precisa estar hospedada num endereço público, porque o Roblox não acessa o `localhost` do seu computador.

## Estrutura

```
app/
├── main.py       # rotas da API e chave de acesso
├── schemas.py    # formatos de entrada e saída (Pydantic)
└── database.py   # acesso ao SQLite: jogadores, partidas, ranking
tests/
├── test_database.py
└── test_api.py
exemplos/
└── roblox_ranking.server.lua
```

As rotas não falam direto com o banco: elas usam a classe `Repository` do `database.py`. Assim, a regra de negócio pode ser testada sozinha, e trocar o SQLite por outro banco mexe em um arquivo só.

## Testes

```bash
python -m pytest -v
```

## Licença

Distribuído sob a licença MIT. Veja o arquivo [LICENSE](LICENSE).
