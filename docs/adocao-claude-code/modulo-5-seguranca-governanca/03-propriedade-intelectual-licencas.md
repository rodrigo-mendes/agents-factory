# Propriedade intelectual e licenças

**Perfil:** Dev / Tech Lead  
**Tempo estimado de leitura:** 5 min

---

## O risco com código gerado por IA

O Claude pode gerar trechos de código semelhantes a implementações que existem em repositórios públicos. Se um trecho desses for muito próximo de código com licença copyleft (GPL, LGPL, AGPL), incluí-lo no seu projeto poderia implicar obrigações de licenciamento que afetam o produto da BRX.

Esse risco é **baixo, mas real**, especialmente em:
- Algoritmos ou estruturas de dados pouco comuns
- Código que reproduz implementações muito conhecidas
- Boilerplate de configuração específica de frameworks

---

## O que o Claude Code faz a respeito

Diferente de outros assistentes, o Claude Code **não possui um "filtro de duplicação de código público"** que compare cada sugestão contra repositórios públicos e a bloqueie automaticamente. Não conte com um mecanismo desse tipo para eliminar o risco.

Na prática, o Claude gera código a partir do contexto do seu projeto e raramente reproduz trechos verbatim de repositórios públicos. Ainda assim, **a ausência de um filtro automático torna a verificação humana ainda mais importante**: a responsabilidade de conferir a origem e a licença de trechos suspeitos é do desenvolvedor.

> Em resumo: o cuidado com licenças continua valendo e não há uma "rede de segurança" automática. Trate código gerado com o mesmo critério de origem e licença que você aplicaria a qualquer código de terceiro.

---

## Sinais de que um trecho pode ser problemático

Desconfie de código potencialmente copiado quando:
- O Claude gera um algoritmo complexo de uma só vez, sem erros (incomum para código gerado)
- Um comentário de copyright de outro projeto aparece no código
- O código tem um estilo muito diferente do resto do projeto
- Você reconhece o trecho como um algoritmo muito conhecido implementado de forma muito específica

---

## O que fazer se você suspeitar de um trecho

1. **Busque o trecho no GitHub** usando a busca de código
2. **Verifique a licença** do repositório onde encontrá-lo
3. Se tiver licença **MIT, Apache 2.0 ou BSD**: baixo risco, geralmente compatível
4. Se tiver licença **GPL/LGPL/AGPL**: consulte a equipe jurídica antes de incluí-lo
5. Se não encontrar origem clara e o trecho ainda parecer suspeito: reescreva-o com suas próprias palavras/estilo ou peça ao Claude uma implementação alternativa; em caso de dúvida, consulte a equipe jurídica

---

## Licenças da BRX e código gerado

O código gerado pelo Claude que você escreve em repositórios da BRX segue as políticas de propriedade intelectual padrão da BRX: o código pertence à BRX como produto do trabalho.

Para dúvidas sobre o tratamento legal de código gerado por IA em projetos específicos, contate a equipe jurídica.

---

## Próximos passos

- [5.4 — Métricas de adoção](04-metricas-adocao.md)
- [5.1 — O que não compartilhar com o Claude Code](01-o-que-nao-compartilhar.md)
