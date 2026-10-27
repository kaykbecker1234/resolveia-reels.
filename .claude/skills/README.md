# Skills da Resolve IA

## noticia-anuncio
Transforma notícias reais sobre IA no atendimento em Reels 9:16 com narração (voz Gabriel, ElevenLabs), música, efeitos e CTA "comenta QUERO".

**Como usar em qualquer sessão do Claude Code:** abra uma sessão com este repositório selecionado e peça, por exemplo:
- `/noticia-anuncio faz um vídeo desta notícia: <link>`
- `/noticia-anuncio busca 10 notícias de IA no atendimento e faz os vídeos`

**Para usar no claude.ai (fora do Claude Code):** compacte a pasta `noticia-anuncio` em .zip e suba em Configurações → Capacidades → Skills.

Requisitos: node + playwright, ffmpeg, Python 3 e o conector do ElevenLabs. Os vídeos prontos ficam na branch `videos`.
