# Governador Local de Memória

O KAWA-AI calcula um orçamento operacional para seus próprios trabalhadores; ele não cria partições físicas de RAM, não altera a configuração do kernel e não converte swap em memória reservada. A swap continua pertencendo ao sistema operacional e deve ser tratada como contingência lenta, não como capacidade normal da IA.

| RAM instalada | Orçamento máximo da IA | Reserva preservada para o sistema |
|---:|---:|---:|
| Até 12 GiB | 50% da RAM total | 50% da RAM total |
| Acima de 12 GiB | 6 GiB | Todo o restante |

Em um dispositivo com 8 GiB, o teto da IA é 4 GiB. Com quatro trabalhadores ativos e memória disponível suficiente, cada trabalhador recebe uma recomendação de 1 GiB. Em um dispositivo com 16 GiB, o teto da IA é 6 GiB e 10 GiB ficam preservados; com quatro trabalhadores, a recomendação é 1,5 GiB por trabalhador.

Antes de iniciar novos trabalhadores, o governador também lê `MemAvailable` no Linux e preserva pelo menos 512 MiB livres. Em pressão de memória, ele reduz a quantidade recomendada de trabalhadores ou bloqueia novos inícios. O resultado é consultivo: provedores externos e processos que não respeitam limites de processo não podem ser limitados fisicamente apenas por Python.

O perfil `auto` é o padrão. Com até 16 GiB de RAM total, o KAWA-AI classifica o ambiente como `desktop`; acima de 16 GiB, classifica-o como `server` automaticamente. O perfil pessoal protege computador com a regra de 50% até 12 GiB e teto de 6 GiB acima disso. No perfil de servidor, ele libera até 90% da RAM, preservando pelo menos 10% ou 1 GiB para o sistema. Mesmo em servidor, nunca usa literalmente toda a RAM, pois o próprio sistema, cache e processos de infraestrutura precisam de margem.

Quando a memória disponível cai abaixo de 25% da RAM, o KAWA-AI reduz progressivamente o número de trabalhadores, os lotes de conhecimento para 50 itens e a janela de contexto recuperado para 4.000 caracteres. Sob pressão crítica, não inicia novo trabalhador e preserva o histórico no Obsidian; a tarefa pode continuar posteriormente sem perder a linha de raciocínio.

Use `kawa --memory-budget` para consultar o plano real do dispositivo ou `kawa --memory-budget --memory-workers 4` para ver a divisão para quatro trabalhadores. O perfil de servidor é escolhido automaticamente acima de 16 GiB; `--resource-profile` continua disponível apenas como ajuste explícito quando necessário.
