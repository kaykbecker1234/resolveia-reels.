# Roteiro: notícia, escrita e checagem

## 1. Achar e triar notícias
**Busca** (WebSearch, várias de uma vez, modo standard): "agente de IA atendimento WhatsApp resultado", "IA atendimento cliente aumentou conversão", "chatbot IA varejo reduziu tempo de resposta", "IA SAC empresa resultados" + mês/ano atual. Veículos bons: Mobile Time, Consumidor Moderno, Exame, Valor, NeoFeed, StartSe, Startups, Época Negócios, Meio & Mensagem.

**Extração** (WebFetch, prompt fixo): "Liste só fatos literais: título, data, veículo, empresa, canal, fornecedor, números antes/depois, como era antes, o que a IA faz, bastidores (prazo, volume, equipe), citações com nome e cargo. Não invente."

**Triagem**
- 🟢 Forte: empresa conhecida no Brasil + IA no atendimento + número antes→depois. Roteiro completo.
- 🟡 Média: resultado sem número claro. Usar contraste "horas → segundos" na cena 1 (`de: "3h"`, `para: "2s"`) e números genéricos verdadeiros na cena 2 (só o que a matéria sustenta).
- 🔴 Descartar: sem resultado concreto, post de fornecedor, mais de ~90 dias, IA fora do atendimento, mesma empresa/ângulo de outro vídeo do lote.

**Ângulos para revezar no lote**: conversão · velocidade · 24h · custo/equipe · volume · satisfação.

## 2. Estrutura (marca → o que a fala diz → campo da tela)
| marca | fala (exemplo) | tela |
|---|---|---|
| s1 | "Saiu na mídia: a EMPRESA fez X sair de" | s1.l1, s1.empresa (≤11 car.) |
| s1_de | "quatro por cento..." | s1.de (≤4 car.); s1.l2 (padrão "foi de") |
| s1_para | "pra setenta por cento." | s1.para (≤4 car.), s1.tarja (≤24) |
| s2 | "E o mais curioso: <comparação>" | s2.r1_*, s2.r2_* (valores numéricos p/ barras) |
| s2_q | "Eles fizeram quase o triplo." | s2.q1, s2.q2 (≤9 car.), s2.nota (fonte do dado) |
| s3 | "O que mudou foi uma coisa só." | (padrão) |
| s3_c | "Mas antes, deixa eu te mostrar como era." | (padrão) |
| s4 | dor do antes (1 frase) | s4.msgs: 4 × [texto ≤30, "hh:mm"] |
| s4_p1 | "A resposta podia levar horas." | s4.p1 (padrão "HORAS PRA RESPONDER") |
| s4_p2 | "E fora do horário comercial, ninguém respondia." | s4.p2 |
| s5 | "Agora imagina <cliente> que precisa de…" | s5.contato, s5.msg (≤80) |
| s5_a | "Ela não vai esperar." | (padrão) |
| s5_b | "Ela compra de quem responder primeiro." | (padrão) |
| s6 | "Foi aí que eles colocaram uma inteligência artificial no WhatsApp." | (padrão) |
| s6_chat | "Ela responde em segundos," | s6.m1–m4 (≤40/≤40/≤15/≤60), s6.tiles 3 × ≤18 |
| s6_p1…p4 | as 4 funções da IA, uma por marca | s6.pills 4 × ≤24 car. |
| s7 | "Mas não foi só ligar e pronto." | (padrão) |
| s7_st1 / s7_st2 | 2 números de bastidor | s7.st1_num (≤4), st2_num (número) + st2_txt (≤6) |
| s7_k / s7_card | "E esse é o detalhe…" / "IA que não conhece o seu negócio não vende." | (padrão) |
| s8, s8_badge, s8_q1, s8_q2 | espelho: "Agora pensa no seu WhatsApp…" | (padrão) |
| s9, s9_b, s9_c | CTA: "…Comenta" / "QUERO que eu te mostro." | (padrão) |

Campos "(padrão)" já existem no modelo; só escreva se quiser mudar. Campos obrigatórios: os do exemplo.

## 3. Regras de escrita
- Total 150–175 palavras (50–60s). Frases curtas, faladas, sem jargão.
- **Números por extenso na narração** ("setenta por cento", "dez mil"); na tela, algarismos.
- Cada trecho da narração começa com palavras **distintas** (o alinhamento usa as primeiras palavras).
- O texto da tela resume a fala; nunca contradiz.
- Se não houver bastidor na matéria, use dois números verdadeiros da própria notícia (lojas, canais, horas, volume). Nunca invente.
- Conversas/notificações são ilustrativas (nomes e horários genéricos); números da notícia, não.

## 4. Checagem (antes da aprovação)
- Cada número e afirmação está na matéria. Fonte e data na tela (`fonte`).
- Não prometer o resultado ao espectador; não sugerir parceria com a empresa citada; sem logo dela.
- Comparações ("mercado") com nota de rodapé dizendo de onde vem o dado (`s2.nota`).

## 5. Aprovação em lote (formato)
| # | empresa · veículo · data | gancho (s1) | ângulo | palavras/duração | tema |
Abaixo da tabela, o texto da narração de cada um (é o que vai para a voz).

## 6. Legenda sugerida do post
1ª linha = gancho. 2–3 linhas com o fato principal. "Fonte: <veículo>, <data>." CTA: "Comenta QUERO que eu te mando como funciona."

## 7. Nova música (só se pedirem)
ElevenLabs Music v2.5, 60s, instrumental: "Instrumental only, no vocals. 60-second background bed for a modern tech/business ad. Minimal, confident, slightly suspenseful, steady ~100 BPM, sparse, no lead melody in the midrange." Conferir que não tem voz e salvar em `assets/musicas/mNN-nome.mp3`.
