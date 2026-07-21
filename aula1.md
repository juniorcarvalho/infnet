# Aula 1 - Coleta de Dados: Conceitos Iniciais - 20.07.2026

## Objetivo da Aula

Esta aula apresenta os conceitos iniciais sobre dados, informação e categorias de dados.

Ao final, você deve ser capaz de:

1. Entender a diferença entre dado e informação.
2. Reconhecer dados estruturados, semiestruturados, desestruturados e temporais.

## Dado x Informação

Um dos primeiros conceitos importantes em coleta de dados é entender a diferença entre `dado` e `informação`.

### O Que É Um Dado?

Dado é a forma mais bruta de um registro. Ele ainda não foi interpretado, organizado ou analisado.

Exemplos de dados:

```text
20/07/2026
8.2%
GoodComp
Rio de Janeiro
42
```

Sozinhos, esses valores podem não dizer muita coisa. Eles precisam de contexto.

### O Que É Informação?

Informação é o dado depois de ser organizado, interpretado ou contextualizado.

Exemplo:

```text
As ações da empresa GoodComp subiram 8.2% em 07/01/2021 após o anúncio de resultados positivos em testes de uma vacina.
```

Agora os dados possuem significado, pois sabemos:

1. Qual empresa foi analisada.
2. Qual foi a variação.
3. Em qual data isso aconteceu.
4. Qual foi o possível motivo da variação.

### Resumo

| Conceito | Explicação | Exemplo |
| --- | --- | --- |
| Dado | Registro bruto, sem interpretação completa | `8.2%` |
| Informação | Dado com contexto e significado | `A ação subiu 8.2% após anúncio positivo` |

Em projetos de dados, normalmente coletamos dados para transformá-los em informação útil.

## Pirâmide da Informação

A pirâmide da informação ajuda a entender como um dado bruto pode evoluir até gerar conhecimento.

```text
Sabedoria
Conhecimento
Informação
Dado
```

### Dado

É o registro bruto.

Exemplo:

```text
8.2%
```

### Informação

É o dado com contexto.

Exemplo:

```text
A ação da empresa subiu 8.2%.
```

### Conhecimento

É a interpretação da informação com base em análise, experiência ou comparação.

Exemplo:

```text
A ação subiu porque o mercado reagiu positivamente ao anúncio da empresa.
```

### Sabedoria

É a capacidade de tomar decisões melhores com base no conhecimento.

Exemplo:

```text
Decidir acompanhar empresas do mesmo setor, pois anúncios semelhantes podem impactar o mercado.
```

## Categorias de Dados

Os dados podem aparecer em diferentes formatos. Entender a categoria do dado ajuda a escolher a melhor forma de coletar, armazenar, limpar e analisar.

As principais categorias são:

1. Dados desestruturados.
2. Dados semiestruturados.
3. Dados estruturados.
4. Dados temporais.

## Dados Desestruturados

Dados desestruturados são dados que não possuem uma estrutura fixa ou um formato pré-definido.

Eles não estão organizados em linhas, colunas ou campos padronizados.

### Exemplos

```text
Imagens
Vídeos
Áudios
Textos corridos
Postagens em redes sociais
Comentários de usuários
Documentos PDF escaneados
```

### Exemplo Prático

Considere o texto abaixo:

```text
As ações da GoodComp subiram 8.2% em 2021-01-07 depois que a empresa anunciou resultados positivos nos testes iniciais de sua vacina.
```

Esse texto é desestruturado porque as informações estão dentro de uma frase. Não existe uma tabela separando empresa, data, percentual e motivo.

Mesmo assim, o texto contém dados importantes:

| Informação extraída | Valor |
| --- | --- |
| Empresa | GoodComp |
| Data | 2021-01-07 |
| Variação da ação | 8.2% |
| Motivo | Resultado positivo nos testes da vacina |

### Onde Aparecem Em Web Scraping?

Em web scraping, dados desestruturados podem aparecer em:

```text
Notícias
Descrições de produtos
Avaliações de clientes
Comentários em páginas web
Textos de blogs
```

## Dados Semiestruturados

Dados semiestruturados possuem alguma organização, mas não seguem uma estrutura totalmente rígida.

Normalmente usam marcações, tags ou pares de chave e valor.

### Exemplos

```text
JSON
XML
HTML
YAML
```

### Características

1. Possuem marcações ou chaves.
2. Podem ter registros com estruturas diferentes.
3. São muito comuns em APIs e páginas web.
4. São mais fáceis de interpretar do que textos totalmente soltos.

### Exemplo Em JSON

```json
{
  "empresa": "GoodComp",
  "data": "2021-01-07",
  "variacao": 8.2,
  "detalhes": "A empresa anunciou resultados positivos nos testes iniciais de sua vacina."
}
```

Esse exemplo é semiestruturado porque usa chaves como `empresa`, `data`, `variacao` e `detalhes` para identificar os dados.

### Exemplo Com Estruturas Diferentes

```json
[
  {
    "empresa": "GoodComp",
    "data": "2021-01-07",
    "variacao": 8.2
  },
  {
    "empresa": "GoodComp",
    "produto": "vacina",
    "fase": "teste inicial"
  }
]
```

Os dois objetos falam sobre a mesma empresa, mas possuem campos diferentes. Isso é comum em dados semiestruturados.

### Relação Com HTML

HTML também é um tipo de dado semiestruturado. Uma página web possui tags como:

```html
<h1>Título da notícia</h1>
<p>Texto da notícia</p>
<a href="https://exemplo.com">Link</a>
```

No web scraping, usamos essas tags para localizar e extrair dados.

## Dados Estruturados

Dados estruturados possuem formato fixo e bem definido.

Normalmente são organizados em linhas e colunas, como em uma tabela.

### Exemplos

```text
Planilhas XLSX
Arquivos CSV
Tabelas de banco de dados
DataFrames
```

### Exemplo Em Tabela

| Empresa | Data | Variação |
| --- | --- | --- |
| GoodComp | 2021-01-07 | 8.2% |
| DataTech | 2021-01-08 | 3.1% |
| ACME | 2021-01-09 | -1.4% |

Cada coluna representa um campo. Cada linha representa um registro.

### Exemplo Em CSV

```csv
empresa,data,variacao
GoodComp,2021-01-07,8.2
DataTech,2021-01-08,3.1
ACME,2021-01-09,-1.4
```

Esse formato é muito usado porque pode ser aberto em planilhas, lido por Python e importado para bancos de dados.

## Tipos Dentro Dos Dados Estruturados

Dentro dos dados estruturados, é comum separar os dados em dois tipos principais: numéricos e categóricos.

### Dados Numéricos

São dados representados por números que podem ser usados em cálculos matemáticos.

Exemplos:

```text
Preço
Idade
Quantidade
Temperatura
Percentual de crescimento
```

Exemplo:

```text
Preço médio = 100.50
Quantidade vendida = 300
```

### Dados Categóricos

São dados que representam categorias ou classificações.

Exemplos:

```text
Nome da empresa
Cidade
Estado civil
Tipo de produto
Status do pedido
```

Importante: nem todo número é um dado numérico para cálculo.

Exemplos como CEP, CPF e telefone usam números, mas não devem ser usados para operações matemáticas como média ou soma.

```text
CEP: 20000-000
Telefone: 21999999999
CPF: 12345678900
```

Esses valores funcionam como identificadores ou categorias.

## Dados Temporais

Dados temporais são dados registrados ao longo do tempo.

Eles são importantes quando queremos analisar evolução, tendência, frequência ou comportamento histórico.

### Exemplos

```text
Preço de uma ação por dia
Temperatura por hora
Localização de um veículo por minuto
Número de acessos a um site por mês
Vendas diárias de uma loja
```

### Exemplo Em Tabela

| Data | Produto | Vendas |
| --- | --- | --- |
| 2026-07-01 | Camiseta | 20 |
| 2026-07-02 | Camiseta | 35 |
| 2026-07-03 | Camiseta | 28 |

Nesse caso, a coluna `Data` permite analisar a evolução das vendas ao longo do tempo.

### Dados Temporais Podem Ter Formatos Diferentes

Um dado temporal pode ser estruturado:

```csv
data,temperatura
2026-07-20,28
2026-07-21,30
```

Também pode ser semiestruturado:

```json
[
  {
    "data": "2026-07-20",
    "temperatura": 28
  },
  {
    "data": "2026-07-21",
    "temperatura": 30
  }
]
```

O que define um dado temporal é a presença de uma sequência ordenada no tempo.

## Comparação Entre Categorias

| Categoria | Estrutura | Exemplos | Facilidade de análise |
| --- | --- | --- | --- |
| Desestruturado | Sem formato fixo | Texto, imagem, áudio, vídeo | Mais difícil |
| Semiestruturado | Possui marcações ou chaves | JSON, XML, HTML | Intermediária |
| Estruturado | Linhas e colunas | CSV, XLSX, SQL | Mais fácil |
| Temporal | Ordenado pelo tempo | Série de preços, sensores | Depende do formato |

## Fontes de Dados

Fonte de dados é o local de onde os dados são obtidos.

Em projetos de coleta e análise, as fontes mais comuns são:

1. Arquivos.
2. APIs.
3. Páginas web.
4. Bancos de dados.
