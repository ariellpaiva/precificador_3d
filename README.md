# Precificador 3D

## Descrição

Sistema para **precificar impressões 3D**. Ele calcula o preço sugerido de cada peça a partir do tempo de impressão,
do filamento, da energia, do desgaste da impressora, do seu trabalho e da margem de lucro. Também controla o estoque de
filamentos, acessórios e peças, registra vendas e mostra um resumo da produção.

Tudo roda **no seu próprio computador**: não precisa de conta, assinatura nem servidor na internet. Os dados ficam na
pasta `data/`, dentro do projeto.

## Como funciona

O projeto tem duas partes:

- **`server.py`**: um pequeno servidor em Python (FastAPI) que guarda os dados num banco SQLite em `data/` e entrega a página.
- **`static/index.html`**: a interface, que você usa pelo navegador.

Os arquivos `.bat` existem para você não precisar digitar comandos. Ao dar dois cliques num deles:

1. Na primeira vez, ele cria um ambiente Python isolado (pasta `.venv`) e instala as dependências. Leva 1 ou 2 minutos.
2. Nas vezes seguintes, só confere as dependências e liga o servidor.
3. O navegador abre sozinho na página do sistema.

**A janela preta do terminal precisa ficar aberta enquanto você usa o sistema.** Fechar a janela desliga o servidor.
Os dados continuam salvos e voltam na próxima vez que você iniciar.

Existem dois jeitos de iniciar:

| Arquivo | Quem acessa | Endereço |
|---|---|---|
| `iniciar.bat` | Dessa forma fica acessível paenas neste computador | http://localhost:8000 |
| `iniciar-rede.bat` | Fica acessível neste computador e outros aparelhos **da mesma rede** (celular, tablet, outro PC) | http://localhost neste PC; http://precificador.local ou http://IP-DO-PC nos outros aparelhos |

## Primeiros passos

1. **Instale o Python** pelo site [python.org](https://www.python.org/downloads/). Na instalação, marque a opção
   **"Add python.exe to PATH"**.
2. **Baixe ou clone este repositório** numa pasta do seu computador.
3. **Dê dois cliques em `iniciar.bat`** (uso só no PC) ou **`iniciar-rede.bat`** (para acessar também pelo celular).
   Na primeira vez, aguarde a instalação terminar.
4. O navegador abre o sistema. No primeiro acesso, um **assistente de configuração** pede, em 4 passos:
   1. **Nome da loja e logo** (a logo é opcional; PNG com fundo transparente fica melhor).
   2. **Tema**: 5 opções (Elétrico, Tropical, Algodão-doce, Menta e pêssego, Grafite), cada uma no modo claro,
      escuro ou automático (segue o sistema).
   3. **Impressora**: modelo, preço pago, vida útil estimada (horas) e consumo médio (W).
   4. **Custos e margem**: tarifa de energia, preço do filamento sem cadastro, valor da sua hora, margem de lucro e
      taxa da plataforma de venda.

   O nome da loja é obrigatório. A partir do 2º passo, o botão **"Usar padrão"** encerra o assistente e mantém os
   valores padrão nos passos que faltam. Tudo pode ser alterado a qualquer momento em
   **"Configurar loja"**, no topo da página. O botão ◐ ao lado alterna entre claro e escuro.
5. Cadastre seus **filamentos** e **acessórios** e comece a **cadastrar peças** (veja [Uso do sistema](#uso-do-sistema)).

## Acessar pelo celular (mesma rede)

1. Inicie pelo **`iniciar-rede.bat`**.
2. O terminal mostra os endereços disponíveis, por exemplo:
   ```
   Precificador rodando em http://localhost
   Na rede local:          http://precificador.local/
   Ou pelo IP:             http://192.168.0.15/
   ```
3. No celular, **conectado ao mesmo Wi-Fi do computador**, abra **http://precificador.local** ou o endereço com o IP.
4. Se o Windows perguntar sobre o firewall, permita o acesso **apenas em Redes privadas**.

Observações:

- O computador precisa estar ligado e com a janela do terminal aberta para os outros aparelhos acessarem.
- Alguns aparelhos (principalmente Android) não reconhecem endereços `.local`. Nesse caso, use o endereço com o IP.
- O IP do computador pode mudar quando o roteador reinicia. Confira sempre o que aparece no terminal.
- **Não há login.** Qualquer pessoa conectada à mesma rede consegue ver e alterar os dados. Use o modo rede só em
  redes de confiança (casa, oficina), nunca em Wi-Fi público.

## Opções de inicialização

O `iniciar.bat` repassa ao servidor qualquer opção que você escrever depois dele. Pelo terminal, dentro da pasta do projeto:

```bat
iniciar.bat                                   :: só este PC, porta 8000
iniciar.bat --port 9000                       :: só este PC, porta 9000
iniciar.bat --lan                             :: rede local, porta 8000 (http://IP-DO-PC:8000)
iniciar.bat --lan --nome precificador --port 80   :: o mesmo que o iniciar-rede.bat
```

| Opção | O que faz | Padrão |
|---|---|---|
| `--lan` | Aceita conexões de outros aparelhos da rede local | Desligado (só este computador) |
| `--port N` | Porta do servidor. Com a porta 80, o endereço não precisa de `:porta` | `8000` |
| `--nome X` | Anuncia o endereço `http://X.local` na rede (mDNS/Bonjour). Requer `--lan` | Nenhum |

Se a porta 80 já estiver em uso por outro programa, o `iniciar-rede.bat` não consegue iniciar. Use outra porta, por
exemplo `iniciar.bat --lan --nome precificador --port 8080`, e acesse `http://precificador.local:8080`.

### Rodar sem o `.bat` (Linux, macOS ou terminal)

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt     # no Windows: .venv\Scripts\pip
.venv/bin/python server.py                    # aceita as mesmas opções: --lan, --port, --nome
```

## Uso do sistema

A página é dividida em abas:

### Cadastrar peça

- **Peça**: imagem, nome, categoria, descrição e, opcionalmente, um **projeto** para agrupar peças que fazem parte do
  mesmo conjunto.
- **Impressão**: tempo (horas e minutos) e gramas de cada filamento usado, que você copia do fatiador (ex.: Bambu Studio).
  Escolha um filamento cadastrado ou use o preço padrão de "filamento sem cadastro". Adicione acessórios (ímãs,
  parafusos, insertos…), a quantidade de **peças no lote**, os minutos do **seu trabalho** (acabamento, montagem) e
  quantas unidades ficam **disponíveis em estoque**.
- **Custos fixos e margem** (seção recolhível): tarifa de energia e bandeira tarifária (Verde, Amarela, Vermelha P1 e P2),
  consumo da impressora, preço e vida útil da impressora, manutenção por hora, taxa de falha, valor da hora de trabalho,
  margem de lucro e taxa da plataforma (Shopee, Mercado Livre, cartão). "Restaurar valores padrão" volta aos valores
  iniciais.
- **Preço sugerido**: atualiza na hora, com o detalhamento de cada custo. Ao clicar em **"Cadastrar peça"**, o preço
  fica salvo. Mudanças posteriores nos custos valem só para peças novas.

### Peças cadastradas

Lista com busca por nome ou descrição, filtro por categoria e ordenação (mais recentes, nome, maior ou menor valor).
Cada peça pode ser editada ou excluída. Peças de um mesmo projeto aparecem agrupadas, com opção de renomear ou desfazer
o projeto (as peças continuam cadastradas).

### Filamentos

Cadastre cada rolo com tipo (PLA, PETG, ABS, TPU etc.), marca, cor, valor e peso do rolo. O sistema calcula o preço por kg
usado no cálculo das peças.

### Acessórios

Registre compras de acessórios com tipo, tamanho, quantidade e valor total pago. O sistema calcula o preço unitário.
Se já existir um acessório do mesmo tipo e tamanho, a quantidade é somada ao estoque.

### Venda

- Escolha a categoria, depois as peças e a quantidade, e clique em **"Finalizar venda"**. O estoque é descontado
  automaticamente; não é possível vender mais do que há em estoque.
- Indicadores do período escolhido: peças vendidas, faturamento, custo e lucro, além das vendas por categoria.
- No **histórico**, **"Estornar"** desfaz uma venda e devolve as peças ao estoque.

### Resumo

Visão geral das peças cadastradas no período: quantidade de peças, tempo de impressão, filamento consumido, valor orçado
(custo e lucro), peças por categoria, filamento usado (por rolo e por tipo) e acessórios usados.

## Como o preço é calculado

| Item | Fórmula |
|---|---|
| Energia | consumo (kW) × horas × (tarifa + bandeira) |
| Filamento | soma de (gramas ÷ 1000 × preço por kg) de cada filamento |
| Desgaste da impressora | preço da impressora ÷ vida útil × horas |
| Manutenção | valor por hora × horas |
| Reserva para falhas | (energia + filamento + desgaste + manutenção) × taxa de falha |
| Seu trabalho | minutos ÷ 60 × valor da hora |
| Acessórios | preço unitário × quantidade usada |
| **Custo total** | soma dos itens acima |
| **Preço sugerido** | (custo total + margem de lucro) ÷ (1 − taxa da plataforma) |

Dica: para achar a tarifa de energia com impostos, divida o valor total da conta de luz pelo kWh consumido no mês.

## Dados e backup

- O banco de dados fica em `data/precificador.db` e as imagens (fotos das peças e logo) em `data/blobs/`. A pasta é
  criada na primeira execução.
- **Backup completo**: com o sistema desligado, copie a pasta `data/` inteira para outro lugar (pendrive, nuvem).
  Para restaurar, coloque a pasta de volta no projeto.
- **Backup rápido**: o link **"Baixar backup (JSON)"**, na aba Cadastrar peça, baixa um arquivo com todos os
  cadastros. Esse arquivo **não inclui as imagens** e o sistema ainda não tem opção para importá-lo, então use-o como
  cópia de segurança e consulta.
- Para levar o sistema para outro computador, copie a pasta do projeto junto com a pasta `data/`.

## Estrutura do repositório

```
precificador_3d/
├── iniciar.bat          # inicia para uso só neste computador (porta 8000)
├── iniciar-rede.bat     # inicia para uso na rede local (http://precificador.local)
├── server.py            # servidor: API, banco SQLite e imagens
├── requirements.txt     # dependências Python (fastapi, uvicorn, python-multipart, zeroconf)
├── static/
│   └── index.html       # interface completa (HTML, CSS e JavaScript)
├── data/                # criada ao iniciar: banco de dados e imagens
└── .venv/               # criada ao iniciar: ambiente Python do projeto
```

## Problemas comuns

| Problema | Solução |
|---|---|
| "Python nao encontrado" | Instale o Python pelo python.org marcando "Add python.exe to PATH" e abra o `.bat` de novo. |
| "Falha ao instalar dependencias" | Confira a conexão com a internet (necessária na primeira execução) e tente de novo. |
| A página não abre no celular | Confira se está no mesmo Wi-Fi, se iniciou pelo `iniciar-rede.bat` e se o firewall liberou Redes privadas. Tente pelo IP. |
| `precificador.local` não abre | Use o endereço com o IP mostrado no terminal. |
| Erro ao iniciar o `iniciar-rede.bat` | A porta 80 pode estar ocupada. Use outra porta (veja [Opções de inicialização](#opções-de-inicialização)). |
| Fontes diferentes do esperado | As fontes dos temas vêm da internet. Sem conexão, o sistema funciona normalmente com as fontes padrão. |
