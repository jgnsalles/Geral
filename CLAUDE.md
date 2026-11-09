# Instruções permanentes

## Price_Tracker_v2.xlsx (e `price_tracker/`): ALERTA OBRIGATÓRIO SOBRE O ROIC

Pedido explícito do usuário: em **qualquer** análise envolvendo o Price Tracker (a planilha, o modelo Python,
as classes, Opportunity of Lifetime etc.), avisar com destaque, logo no início da resposta e de novo onde
o ROIC influenciar uma conclusão, que **o ROIC pode estar errado**. O usuário quer investigar isso a fundo
numa sessão futura. Se ainda não tiver sido investigado, ofereça começar por aí.

**Posição do usuário (2026-11-09):** ROE para financeiras está **correto** (financeiras não têm ROIC).
O problema é o capital investido do Wisesheets = ativo total − passivo circulante, que é conceitualmente
errado. O modelo Python usa por padrão o ROIC clássico, NOPAT ÷ (patrimônio + dívida − caixa), para empresas
operacionais e ROE para financeiras (`ROIC_DEF` em `price_tracker/hybrid.py`). Os cortes (20%/10%) foram
desenhados com a fórmula do Wise: com o ROIC clássico, 52% das operacionais passam de 20% (contra 31%).
Revisar os cortes faz parte da investigação pendente.

O que já se sabe (teste de 2026-11-09, ver `price_tracker/README.md`):
- O ROIC vem do Wisesheets e **não é o ROIC clássico**. Calibrado: NOPAT ÷ (ativo total − passivo circulante),
  com valores de fim de ano. Isso inclui caixa e goodwill no denominador e não trata leasing.
- No setor **Financial Services** o "ROIC" do Wisesheets é na verdade **ROE** (lucro líquido ÷ patrimônio).
  Isso inclui Visa, Mastercard, PayPal, Marsh e as bolsas, não só os bancos.
- Casos que ficam muito distantes de qualquer reconstrução: MA (Wise 173%), V, MRSH, APO, BAM e DPZ
  (patrimônio negativo).
- A série de ROIC pula 2020 (colunas V:AA = 2019, 2021–2025).
- O zROIC tinha um bug (o desvio incluía a coluna U, o `g`). Foi corrigido para V:AA em 2026-11-08.
- O ROIC afeta três coisas: o corte de qualidade (20%/10%), a estabilidade (zROIC 0,7) **e** o P/E justo
  `(1 − g/ROIC)/(8,5% − g)`. Um erro nele muda a classe por mais de um caminho.
