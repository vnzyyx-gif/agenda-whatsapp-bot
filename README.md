# Agenda WhatsApp Bot

Bot de agendamento via WhatsApp desenvolvido em Python. O sistema interpreta mensagens em linguagem natural com IA, cria e cancela compromissos no Google Agenda e mantém um histórico local dos agendamentos usando SQLite.

## Visão geral

Este projeto foi criado para automatizar o processo de agendamento por WhatsApp. O usuário pode enviar mensagens como:

```text
Quero marcar amanhã às 15h
```

ou:

```text
Cancelar meu compromisso de amanhã às 15h
```

O bot interpreta a mensagem, verifica a disponibilidade no Google Agenda e responde automaticamente ao usuário.

## Funcionalidades

* Interpretação de mensagens com IA usando Groq
* Criação de eventos no Google Agenda
* Cancelamento de compromissos
* Consulta de compromissos criados pelo bot
* Verificação de conflito de horários
* Memória de conversa com SQLite
* Histórico local dos eventos criados pelo bot
* Integração com WhatsApp via Twilio ou WhatsApp Cloud API
* Servidor Flask para receber webhooks
* Suporte a testes locais com ngrok

## Tecnologias utilizadas

* Python
* Flask
* Groq API
* Google Calendar API
* SQLite
* Twilio WhatsApp Sandbox
* WhatsApp Cloud API da Meta
* ngrok
* python-dotenv
* dateparser

## Estrutura do projeto

```text
agenda-whatsapp-bot/
├── ai.py
├── app.py
├── database.py
├── google_calendar.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Pré-requisitos

Antes de executar o projeto, é necessário ter instalado:

* Python 3.10 ou superior
* Git
* Conta na Groq
* Projeto configurado no Google Cloud com Google Calendar API
* Credenciais OAuth do Google Calendar
* Conta Twilio ou configuração da WhatsApp Cloud API
* ngrok para testes locais

## Instalação

Clone o repositório:

```bash
git clone https://github.com/seu-usuario/agenda-whatsapp-bot.git
```

Acesse a pasta do projeto:

```bash
cd agenda-whatsapp-bot
```

Crie um ambiente virtual:

```bash
python -m venv venv
```

Ative o ambiente virtual.

No Windows:

```bash
venv\Scripts\activate
```

No Linux ou macOS:

```bash
source venv/bin/activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

## Variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto com base no arquivo `.env.example`.

Exemplo:

```env
GROQ_API_KEY=sua_chave_groq_aqui
GROQ_MODEL=llama-3.1-8b-instant

META_ACCESS_TOKEN=seu_token_meta_aqui
META_PHONE_NUMBER_ID=seu_phone_number_id_aqui
META_VERIFY_TOKEN=seu_verify_token_aqui
META_API_VERSION=v23.0
```

Nunca envie o arquivo `.env` para o GitHub.

## Configuração do Google Agenda

Para utilizar a integração com o Google Agenda:

1. Acesse o Google Cloud Console.
2. Crie um projeto.
3. Ative a Google Calendar API.
4. Configure a tela de consentimento OAuth.
5. Crie uma credencial do tipo OAuth Client ID.
6. Escolha o tipo de aplicativo como Desktop App.
7. Baixe o arquivo JSON.
8. Renomeie o arquivo para:

```text
credentials.json
```

9. Coloque o arquivo na raiz do projeto.

Na primeira execução, o Google solicitará autorização da conta. Após a autorização, será criado automaticamente o arquivo:

```text
token.json
```

Os arquivos `credentials.json` e `token.json` não devem ser enviados para o GitHub.

## Executando o projeto

Inicie o servidor Flask:

```bash
python app.py
```

O servidor será iniciado em:

```text
http://127.0.0.1:5000
```

Para expor o servidor local usando ngrok:

```bash
ngrok http 5000
```

Copie a URL HTTPS gerada pelo ngrok e configure no webhook da plataforma de WhatsApp utilizada.

Exemplo:

```text
https://seu-link-ngrok.ngrok-free.app/whatsapp
```

## Exemplos de uso

Agendar um compromisso:

```text
Quero marcar amanhã às 15h
```

Consultar compromissos:

```text
Quais são meus compromissos?
```

Cancelar um compromisso:

```text
Cancelar amanhã às 15h
```

Agendar um compromisso com descrição:

```text
Quero marcar sexta às 10h: reunião com cliente
```

## Segurança

Este projeto utiliza arquivos sensíveis que não devem ser enviados para repositórios públicos:

```text
.env
credentials.json
token.json
agenda.db
venv/
__pycache__/
```

Certifique-se de que o arquivo `.gitignore` contém essas entradas antes de fazer qualquer commit.

## Arquivo `.gitignore` recomendado

```gitignore
venv/
.env
token.json
credentials.json
__pycache__/
*.pyc
*.db
```

## Arquivo `.env.example`

O arquivo `.env.example` deve conter apenas nomes de variáveis, sem valores reais:

```env
GROQ_API_KEY=sua_chave_groq_aqui
GROQ_MODEL=llama-3.1-8b-instant

META_ACCESS_TOKEN=seu_token_meta_aqui
META_PHONE_NUMBER_ID=seu_phone_number_id_aqui
META_VERIFY_TOKEN=seu_verify_token_aqui
META_API_VERSION=v23.0
```

## Status do projeto

Projeto em desenvolvimento.

Funcionalidades já implementadas:

* Integração com IA
* Criação de eventos no Google Agenda
* Cancelamento de eventos
* Consulta de compromissos
* Memória local com SQLite
* Webhook com Flask
* Testes com WhatsApp via Twilio

Funcionalidades planejadas:

* Migração completa para WhatsApp Cloud API da Meta
* Envio automático de lembretes
* Templates de mensagens aprovados pela Meta
* Painel administrativo web
* Melhor tratamento de linguagem natural
* Deploy em ambiente de produção
* Autenticação e controle de usuários

## Observações

Este projeto foi desenvolvido inicialmente como um MVP para validação de fluxo de agendamento automatizado. Para uso em produção, recomenda-se configurar um ambiente seguro de hospedagem, utilizar tokens permanentes, proteger variáveis de ambiente e revisar as políticas de uso da API do WhatsApp.

## Licença

Este projeto está licenciado sob a licença MIT. Consulte o arquivo [LICENSE](LICENSE) para mais detalhes.
