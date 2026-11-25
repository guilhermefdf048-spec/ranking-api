--!strict
-- Exemplo: enviar a pontuação de uma partida do Roblox para a API de ranking.
-- Coloque em ServerScriptService. Ative HTTP em Game Settings > Security > Allow HTTP Requests.
-- A API precisa estar hospedada num endereço público (o Roblox não acessa localhost).

local HttpService = game:GetService("HttpService")

local API_URL = "https://SEU-ENDERECO-DA-API"
local API_KEY = "troque-pela-sua-chave" -- mantenha só em scripts do servidor, nunca no cliente

local function request(method: string, path: string, body: any?): (boolean, any)
	local ok, response = pcall(HttpService.RequestAsync, HttpService, {
		Url = API_URL .. path,
		Method = method,
		Headers = {
			["Content-Type"] = "application/json",
			["X-API-Key"] = API_KEY,
		},
		Body = if body then HttpService:JSONEncode(body) else nil,
	})
	if not ok then
		warn("Falha na requisição:", response)
		return false, nil
	end
	local data = if response.Body ~= "" then HttpService:JSONDecode(response.Body) else nil
	return response.Success, data
end

-- Registra o jogador (se já existir, a API responde 409 e seguimos em frente)
local function registerPlayer(player: Player)
	request("POST", "/jogadores", { nome = player.Name })
end

-- Mostra o top 5 no Output
local function printRanking()
	local ok, ranking = request("GET", "/ranking?limite=5")
	if ok and ranking then
		for _, entry in ranking do
			print(`{entry.posicao}º {entry.nome} - {entry.pontos} pts`)
		end
	end
end

game.Players.PlayerAdded:Connect(registerPlayer)
printRanking()

-- Para registrar uma partida, guarde o id devolvido pela API e chame:
-- request("POST", `/jogadores/{id}/partidas`, { pontos = 150 })
