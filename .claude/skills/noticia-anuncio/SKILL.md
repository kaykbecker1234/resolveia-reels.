---
name: noticia-anuncio
description: Transforma notícias reais sobre empresas usando IA no atendimento (WhatsApp, chat, SAC) em anúncios de Reels 9:16 com narração (voz Gabriel, ElevenLabs), música de fundo baixa, efeitos sonoros e CTA "comenta QUERO". Use quando pedirem vídeo/anúncio/reels a partir de notícia, "faz um vídeo dessa notícia", "busca notícias de IA no atendimento", ou lote de vários vídeos. Inclui busca e triagem de notícias, roteiro de retenção em 9 batidas e pipeline automático de render e mixagem.
---

# Notícia → Anúncio (Reels)

Objetivo fixo: **reter com uma notícia real de IA no atendimento** e levar a "atendimento automático com IA no seu WhatsApp". Nunca citar a marca de quem anuncia.

## Economia de tokens (regras)
- **Não ler** `assets/template/video.html`, `scripts/*` nem as fontes. Só executar. O único arquivo que você escreve é `roteiro.json`.
- Molde do roteiro: `assets/exemplo/roteiro.json` (ler 1 vez por sessão). Regras de escrita: `references/roteiro.md` (ler 1 vez, só ao escrever roteiros).
- Imagens: olhar **só** `preview.jpg` e `sync.jpg` (folhas de 12 quadros). Nunca abrir quadros soltos nem o mp4.
- Notícia: WebFetch com o prompt de extração de `references/roteiro.md`, nunca a página inteira.
- ElevenLabs: 1 versão de narração (`generations_count: 1`); música vem da biblioteca `assets/musicas/` (não gerar).
- Polling do ElevenLabs a cada ~20s; os scripts imprimem só o resumo. Não repetir saídas no chat.

## Fluxo (por vídeo; em lote, faça cada etapa para todos antes da próxima)
Pasta de trabalho: `anuncios/<AAAA-MM-DD>-<empresa>/` dentro do diretório do usuário. `P=python3 <skill>/scripts/pipeline.py`.

1. **Notícia**: se não vier link, buscar e triar (🟢 forte / 🟡 média / 🔴 descartar) conforme `references/roteiro.md`.
2. **Roteiro** → escrever `roteiro.json` → `$P check <pasta>` (valida campos, ordem das marcas, números por extenso; imprime o texto da voz e a duração estimada).
3. **➜ Aprovação 1**: mostrar ao usuário o texto da narração + fatos-chave + fonte (em lote: uma tabela com todos). Não gastar créditos antes.
4. `$P preview <pasta>` → olhar `preview.jpg`; corrigir texto estourado ou `⟨campo⟩` (campo faltando) só no json.
5. **Narração**: `creative_generate_speech` com `voice_id k3f7zOv6LF88v78QHCNh` (Gabriel - Shorts & Reels), `model_id eleven_v4`, `generations_count 1`, `prompt` = texto impresso pelo check. Em lote, dispare todas e depois faça o polling.
6. `$P voz <pasta> "<url do mp3>"` e então `$P final <pasta> [<pasta2> …]` → gera `<pasta>/<nome>.mp4` e `sync.jpg` (sincroniza cada cena com a fala, acelera a voz 8%, efeitos e música com ducking, -14 LUFS).
7. Olhar `sync.jpg` (cada quadro mostra a cena da frase rotulada). Se o script listar "conferir marcas", verificar essas.
8. **Entrega**: enviar o mp4 + legenda sugerida (com a fonte da notícia). Em lote: tabela com notícia, gancho, duração, créditos.

## Padrões (o usuário pode mudar no `roteiro.json`)
- `audio.tempo` 1.08 · `audio.musica_vol` 0.10 · `audio.musica` null (sorteia da biblioteca pelo nome da pasta).
- `tela.tema`: `navy` | `esmeralda` | `vinho` | `roxo`. Em lote, revezar.
- Duração alvo 50–60s (150–175 palavras). O check avisa se passar.
- Custo por vídeo ≈ 1.200 créditos ElevenLabs (só a narração).

## Requisitos e problemas
- Usa `node` + `playwright` (Chromium), `ffmpeg` e Python 3. Na 1ª execução de `final` o script cria um ambiente em `~/.cache/noticia-anuncio` (faster-whisper, num2words, numpy) e baixa o modelo de transcrição; leva ~1–2 min, uma vez só.
- Sem playwright: `npm i -g playwright` (no ambiente na nuvem já vem instalado; não rode `playwright install`).
- Espaço: os quadros são apagados ao final; cada vídeo final tem ~50 MB.
- Nova música para a biblioteca: só se o usuário pedir. Gerar instrumental de 60s (ElevenLabs Music, prompt em `references/roteiro.md`) e salvar em `assets/musicas/`.
