"""Brazil Downturn, passo 9: dados da parte 1 para a página (bd_data.json) a partir dos resultados do passo 3.
Uso: python3 09_dados_pagina.py <resultado.json> <resultado_rep.json> <saida bd_data.json>"""
import sys, json
R = json.load(open(sys.argv[1])); Q = json.load(open(sys.argv[2]))
anos = [dict(y=a['y'], fr=a['fr'], flow_bi=a['flow'] / 1e9, pl0_bi=a['pl0'] / 1e9, ibov=a['ibov'], cdi_fim=a['cdi_fim'], dcdi=a['dcdi'], pos=a['pos'], ng=a['ng'], regime=R['regime'][a['y']]) for a in R['anos']]
men = [dict(ym=m['ym'], fr12=m['fr12'], cdi=m['cdi_aa'], ibov12=m['ibov12']) for m in R['mensal']]
D = dict(anos=anos, mensal=men, decomp=R['decomp_anual'], decomp_n=R['decomp_n'], dolar=R['dolar'], fm=R['fm'], quintis=R['quintis'], quintis_ano=R['quintis_ano'],
         perfil_seca=R['perfil_seca'], perfil_cheia=R['perfil_cheia'], p_size=R['p_size'], p_alpha=R['p_alpha'], p_size_cheia=R['p_size_cheia'], p_alpha_cheia=R['p_alpha_cheia'],
         ganhadores=R['ganhadores'], depois=R['depois_seca'], logit=dict(seca=R['logit_seca'], cheia=R['logit_cheia'], estilo=R['logit_seca_estilo'], cli_seca=R['logit_seca_cliente'], cli_cheia=R['logit_cheia_cliente']),
         agg_anual=R['agg_anual'], agg_reg=R['agg_reg'], anos_seca=R['anos_seca'], anos_cheia=R['anos_cheia'],
         rob=dict(decomp=Q['decomp_anual'], agg=Q['agg_anual']['juros'], fm=Q['fm'], logit=Q['logit_seca'], perfil=Q['perfil_seca']['tab'], depois=Q['depois_seca']))
open(sys.argv[3], 'w').write(json.dumps(D, ensure_ascii=False, separators=(',', ':'), default=str))
