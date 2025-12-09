# Métodos de Análise do Grafo

Este documento descreve os 5 métodos de análise de grafos implementados e aplicados ao repositório Next.js.

---

## 1. Grau de Entrada (In-Degree Centrality)

Para identificar os usuários mais centrais e ativos na rede de colaboração, foi implementado o método `degree_centrality()`, que calcula o grau de entrada de cada usuário. O grau de entrada representa quantas interações um usuário recebeu de outros colaboradores, como comentários em seus pull requests, reviews recebidas, issues fechadas por outros, e merges realizados por mantenedores em seus PRs.

O método percorre todos os vértices do grafo e, para cada usuário, conta quantas arestas direcionadas apontam para ele, utilizando o método `getVertexInDegree()` da classe AbstractGraph. Essa métrica identifica usuários que são alvos frequentes de interação, geralmente mantenedores ou core contributors cujo trabalho é constantemente revisado e comentado pela comunidade.

Usuários com alto grau de entrada são considerados centrais no projeto, pois seu código e suas contribuições atraem atenção e envolvimento de muitos outros colaboradores, refletindo sua relevância técnica na rede de desenvolvimento.

---

## 2. PageRank

Para identificar os usuários mais influentes do projeto, foi implementado o método `pagerank()`, que calcula a importância de cada colaborador não apenas pela quantidade de interações que recebe, mas pela qualidade dessas interações. Um usuário é considerado influente quando recebe interações de outros usuários que também são importantes na rede.

O método utiliza o algoritmo Power Iteration com um damping factor de 0.85, executando 100 iterações até convergir. Inicialmente, todos os usuários começam com o mesmo valor de PageRank (1/n). A cada iteração, o PageRank de um usuário é calculado somando as contribuições dos usuários que interagem com ele, onde cada contribuição é ponderada pelo PageRank do usuário que a fez dividido pelo número de interações que ele realiza.

O algoritmo também trata casos especiais de usuários sem interações de saída (sink nodes), distribuindo seu PageRank uniformemente para todos os outros usuários. Essa métrica identifica não apenas usuários ativos, mas aqueles cuja influência se propaga pela rede através de conexões com outros colaboradores importantes, refletindo hierarquias naturais de liderança técnica e reconhecimento dentro do projeto.

---

## 3. Centralidade de Proximidade (Closeness Centrality)

Para identificar os usuários mais bem posicionados na rede de colaboração, foi implementado o método `closeness_centrality()`, que calcula quão próximo cada usuário está de todos os outros colaboradores. Usuários com alta proximidade conseguem alcançar rapidamente qualquer outro usuário através de caminhos curtos de interação, posicionando-se estrategicamente no centro da rede.

O método utiliza o algoritmo BFS (Busca em Largura) para calcular a distância mais curta de cada usuário para todos os outros usuários alcançáveis no grafo. Para cada usuário, soma-se todas essas distâncias e aplica-se a fórmula de Wasserman e Faust, que é apropriada para grafos que podem conter partes desconectadas. A fórmula pondera a centralidade considerando tanto o número de usuários alcançáveis quanto a soma total das distâncias até eles.

Essa métrica identifica usuários centralmente localizados na rede, que servem como pontos de convergência para a comunicação e colaboração. Usuários com alta closeness centrality podem disseminar informação rapidamente pelo projeto, facilitando a coordenação entre diferentes áreas e contribuidores.

---

## 4. Detecção de Comunidades (Label Propagation)

Para identificar a estrutura organizacional emergente do projeto, foi implementado o método `detect_communities_label_propagation()`, que detecta grupos de usuários densamente conectados entre si, formando comunidades naturais dentro da rede de colaboração. Essas comunidades podem representar sub-equipes informais, áreas funcionais do projeto (como frontend, backend, documentação), ou grupos que trabalham frequentemente juntos.

O método utiliza o algoritmo Label Propagation, que inicializa cada usuário como sua própria comunidade e, iterativamente, propaga os rótulos de comunidade pela rede. A cada iteração, os usuários são processados em ordem aleatória e cada um adota o rótulo de comunidade mais comum entre seus vizinhos (tanto predecessores quanto sucessores nas arestas direcionadas). O processo se repete até que os rótulos parem de mudar ou até atingir o limite de 20 iterações, garantindo convergência.

Essa métrica revela a estrutura modular do projeto, identificando clusters de colaboradores que interagem intensamente entre si. Comunidades grandes geralmente representam equipes principais do projeto, enquanto comunidades menores podem indicar grupos especializados ou contribuidores periféricos que trabalham em áreas específicas com menor integração com o restante da rede.

---

## 5. Usuários-Ponte (Bridging Ties)

Para identificar os usuários que conectam diferentes partes do projeto, foi implementado o método `analyze_bridging_ties()`, que calcula quantas interações cada usuário realiza com membros de comunidades diferentes da sua. Esses usuários-ponte são fundamentais para integrar o conhecimento entre sub-equipes e evitar que grupos trabalhem isoladamente.

O método recebe como entrada o grafo e a atribuição de comunidades calculada pelo Label Propagation. Para cada usuário, identifica-se sua comunidade de origem e examina-se todos os seus sucessores (usuários com quem ele interage diretamente). Conta-se quantos desses sucessores pertencem a comunidades diferentes, gerando uma pontuação de bridging para cada usuário. Os usuários são então ranqueados de forma decrescente por essa pontuação, identificando os top 5 usuários-ponte.

Essa métrica revela tech leads, desenvolvedores full-stack e coordenadores que trabalham transversalmente em múltiplas áreas do projeto. Usuários com alto bridging score facilitam a transferência de conhecimento entre equipes, atuam como mediadores em discussões técnicas envolvendo diferentes especialidades, e são pontos críticos para manter a coesão geral do projeto, evitando a fragmentação da colaboração em silos isolados.
