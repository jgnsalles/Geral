# Monitor de anúncios de carros

Script em Python que busca anúncios no Webmotors, compara com a Tabela FIPE,
guarda tudo num banco local e avisa sobre **anúncios novos** e **quedas de preço**.

## Instalação

```bash
cd carros
pip install -r requirements.txt     # opcional (curl_cffi), mas reduz bloqueios
cp config.exemplo.json config.json  # depois edite com os carros que você quer
```

## Uso

```bash
python monitor_carros.py buscar                 # roda as buscas e mostra novidades
python monitor_carros.py importar anuncios.csv  # importa anúncios de outros sites, à mão
python monitor_carros.py relatorio              # só gera o CSV
```

O resultado vai para `anuncios.csv` (abre direto no Excel), ordenado do mais
barato em relação à FIPE para o mais caro.

## Configurando uma busca (`config.json`)

| Campo | Exemplo | O que faz |
|---|---|---|
| `marca`, `modelo` | `"honda"`, `"civic"` | carro buscado |
| `estado` | `"sp"` | opcional |
| `ano_min`, `ano_max` | `2019`, `2021` | ano-modelo |
| `preco_max`, `km_max` | `130000`, `80000` | limites |
| `versao_contem` | `"exl"` | filtra pela versão (texto) |
| `paginas` | `2` | páginas de 24 anúncios (use poucas) |
| `fipe_codigo` | `"014093-1"` | código FIPE da versão (veja em veiculos.fipe.org.br) |
| `combustivel` | `"flex"` | ajuda a escolher o valor FIPE certo |
| `fipe_manual` | `{"2020": 118500}` | valor FIPE à mão por ano, se a consulta falhar |
| `url` | link da busca do site | **jeito mais confiável**: filtre no site, copie o link e cole aqui |

## Importação manual

Para anúncios da OLX, iCarros etc., monte um CSV (`;` ou `,`) com as colunas:
`titulo;ano_modelo;km;preco;link` e, se quiser, `versao;cidade;uf;fipe;busca`.

## Rodar todo dia automaticamente

- **Linux/Mac** (`crontab -e`): `0 8,18 * * * cd /caminho/carros && python3 monitor_carros.py buscar >> log.txt`
- **Windows**: Agendador de Tarefas → ação `python` com argumento `monitor_carros.py buscar`.

## Limitações

- O Webmotors não tem API pública. O script usa o endpoint interno do site, que
  pode mudar ou ser bloqueado pelo Cloudflare. Se parar de funcionar, os nomes
  dos campos em `converter_anuncio_webmotors` são o primeiro lugar a revisar.
- Os termos de uso desses sites costumam proibir coleta automatizada. Use
  apenas para uso pessoal, com poucas páginas e intervalo entre requisições.
- O link de cada anúncio é montado a partir dos dados; se algum abrir errado,
  procure o carro pelo ID no final do link.
