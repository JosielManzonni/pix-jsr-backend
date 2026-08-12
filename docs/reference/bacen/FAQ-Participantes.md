# FAQ Participantes do Pix

## Sumário

Pix Saque e Pix Troco............................................................................................ 3 Mecanismo Especial de Devolução (MED)........................................................... 5

## Pix Saque e Pix Troco

*Informações complementares mais gerais sobre Pix Saque e Pix Troco podem ser acessadas na <u>FAQ do Pix</u> e no <u>Guia de Implementação do Pix Saque e Pix Troco</u>.

**1. Quais as responsabilidades do facilitador de serviço de saque na relação contratual com o agente de saque?** Nesse contexto, o facilitador de serviço de saque, deverá: o avaliar a necessidade de estabelecer limites transacionais aos agentes de saque, conforme as características e o perfil de cada agente, localização, horários e outros critérios de segurança, observados os limites de valor definidos pelo Banco Central; o prestar informações sobre os agentes de saque ao Banco Central para fins de monitoramento e de divulgação de informações relacionadas à prestação do serviço; e o publicar, no formato indicado pelo Banco Central do Brasil, informações dos agentes de saque com os quais possui relação contratual.
**2. A API Pix será sempre provida pelo participante com o qual o agente de saque mantém relação** **contratual para facilitar o serviço de saque?** Não. O agente de saque pode estabelecer relação contratual para a facilitar o serviço de saque com participante distinto daquele que atua como seu provedor de conta transacional, que é o responsável por disponibilizar as funcionalidades da API Pix.
**3. A facilitação do serviço de saque é obrigatória para os participantes do Pix provedores de conta transacional?** Não. A facilitação desse serviço é facultativa aos participantes autorizados pelo BC que se enquadrem nos requisitos mínimos estabelecidos.
**4. Como é a estrutura de ressarcimento de custos entre os agentes envolvidos na facilitação do serviço?** Uma vez que o serviço de saque é prestado pelo participante provedor de conta transacional do usuário pagador, ele deve ressarcir os custos operacionais que as outras instituições participantes da transação Pix com finalidade de saque ou troco incorrem para viabilizar a disponibilização dos recursos em espécie (facilitador de serviço de saque e participante provedor de conta transacional do usuário recebedor). O FSS, por sua vez, irá distribuir parte do valor ao agente de saque.
#### 5. E qual o valor do ressarcimento de custos operacionais?

Depende de onde se dá a disponibilização do Pix Saque ou Pix Troco: o Nas transações em que o Pix Saque ou Pix Troco for disponibilizado diretamente pelo facilitador de serviço de saque, o ressarcimento de custos operacionais recebido por ele será se R$ 1,50. o Quando o Pix Saque ou Pix Troco for disponibilizado por um estabelecimento comercial no papel de agente de saque, o ressarcimento de custos operacionais será de R$ 1,00 (um real) ao FSS. O provedor de contra transacional do agente de saque, se instituição distinta do FSS, será ressarcido em R$ 0,05 (cinco centavos de real) e o facilitador do serviço de saque, em R$ 0,95 (noventa e cinco centavos de real). Deste montante, o FSS deverá distribuir ao estabelecimento comercial um valor mínimo de R$ 0,25 (vinte e cinco centavos de real). Caso o facilitador de serviço de saque e o provedor da conta transacional sejam a mesma instituição,

este será ressarcido pelo valor total (R$1,00) e deve distribuir o mínimo de R$0,25 ao estabelecimento comercial. o Já se o agente de saque que disponibiliza o Pix Saque ou Pix Troco for uma pessoa jurídica que tenha como atividade principal ou secundária a prestação de serviços auxiliares a serviços financeiros ou afins ou se for um correspondente bancário no país, o ressarcimento dos custos operacionais será de R$ 2,00 por transação Pix com finalidade saque ou troco, destinada ao facilitador de serviço de saque. A parcela desse valor distribuída ao agente de saque deve ser pactuada junto ao facilitador de serviço de saque.

## Mecanismo Especial de Devolução (MED)

#### 1. O que é o MED?

É o conjunto de regras e de procedimentos operacionais destinado a viabilizar a devolução de um Pix a partir do próprio participante recebedor. Ou seja, é o mecanismo que permite que o participante recebedor debite recursos recebidos por meio de um Pix da conta do seu cliente sem pedir a sua autorização a cada devolução.

#### 2. Em quais casos se aplica?

o Fundada suspeita do uso do Pix para a prática de fraude o Falha operacional no sistema de tecnologia da informação de qualquer dos participantes envolvidos na transação

#### 3. Em quais casos não se aplica?

o Controvérsias comerciais entre os usuários o Transações com fundada suspeita de fraude em que os recursos forem destinados à conta transacional de um terceiro de boa-fé Depreende-se desse não-escopo, que o MED não é um mecanismo de *chargeback*, como o existente nos arranjos de cartões de pagamento.

#### 4. O MED é obrigatório para todos os participantes?

Sim. Para que ele possa ser acionado, contudo, o participante deve ajustar o contrato de relacionamento com todos os seus clientes, prevendo a possibilidade de acionamento do MED no âmbito do Pix. Após o ajuste no contrato, o participante deve informar todos os seus clientes sobre a mudança contratual efetivada. Caso o participante não faça os devidos ajustes contratuais e não possa acionar o MED, ele será responsabilizado por todas as transações em que a solicitação de devolução for recusada.

#### <u>5.</u> Como é a estrutura de responsabilização nas solicitações de devolução?

|Ação do participante recebedor|Responsabilização|
|---|---|
|Aceita solicitação|Participante pagador|
|Rejeita solicitação|Participante recebedor|
|Não pode acionar o MED (por não ter previsto a possibilidade no contrato de relacionamento com seus clientes)|Participante recebedor|

#### 6. É possível fazer mais do que uma solicitação de devolução para cada transação Pix?

Não. É possível fazer apenas uma solicitação de devolução para cada transação Pix.

#### 7. Uma notificação de infração deve sempre gerar uma solicitação de devolução?

Não. Uma notificação por motivo “fraude” tem como único objetivo fazer a marcação da chave Pix e da conta e do CPF ou CNPJ associados a ela para que essa informação seja compartilhada com todos os demais participantes do Pix sempre que a chave for consultada (nos termos do capítulo sobre informações vinculadas às chaves para fins de segurança, no Manual Operacional do DICT).

A notificação por motivo “associada a uma solicitação de devolução”, além de fazer a marcação de fraude, também deve gerar, em geral, uma solicitação de devolução. Contudo, o participante pagador não é obrigado a gerar a solicitação de devolução após esse processo. Caso, após uma análise mais apurada, ele perceba que a chave não está associada a uma fraude, ele deve cancelar a notificação (mesmo que ele tenha sido aceita e fechada pelo participante recebedor) e não iniciar a solicitação de devolução.

A notificação por motivo “cancelamento da devolução” também deve gerar, em geral, uma solicitação de devolução. O fluxo desse tipo de notificação é bastante semelhante ao fluxo da notificação por motivo “associada a uma solicitação de devolução”. A única diferença é que é o participante recebedor o agente que abre a notificação (enquanto na notificação por motivo “associada a uma solicitação de devolução” é o participante pagador quem faz a abertura).

#### 8. Uma solicitação de devolução deve ser sempre precedida de uma notificação de infração?

Não. Existem três motivos para um participante abrir uma solicitação de devolução: o por falha operacional do PSP do pagador; o por fundada suspeita de fraude; ou o para cancelamento da devolução. A solicitação de devolução por falha operacional do PSP do pagador deve ser aberta, pelo participante pagador, sem a necessidade de abertura de uma notificação de infração. A solicitação de devolução por fundada suspeita de fraude e para cancelamento da devolução só pode ser aberta caso uma notificação de infração por motivo, respectivamente, “associada a uma solicitação de devolução” e “cancelamento da devolução” tenha sido previamente aberta. A solicitação de devolução só pode ser aberta após o fechamento da notificação de infração em questão.

#### 9. O participante recebedor deve abrir uma solicitação de devolução para iniciar uma devolução?

Não. O participante recebedor não precisa fazer nenhuma ação no DICT. Ele simplesmente envia uma pacs.004 devolvendo os recursos para o usuário pagador da transação original. Ele pode fazer isso por dois motivos: o conduta fraudulenta de seu cliente; ou o Falha operacional que tenha ocorrido no âmbito de seus sistemas. Em caso de conduta fraudulenta de seu cliente, o participante recebedor deve também abrir uma notificação de infração, com motivo “fraude”, para marcar a chave de seu cliente no DICT.

#### 10. O que o participante pagador deve fazer para solicitar uma devolução para o participante

#### recebedor, em caso de fundada suspeita de fraude?

Após perceber a fraude ou após reclamação de seu cliente, o participante pagador deve abrir uma notificação de infração “associada a uma solicitação de devolução”. Para isso, a transação original deve ter ocorrido há no máximo 80 dias em relação à abertura da notificação. Após a conclusão da “notificação de infração”, o participante pagador tem 72 horas para solicitar a devolução, caso o participante recebedor tenha aceitado a notificação. Na abertura da notificação de infração “para abertura de solicitação de devolução”, o participante deve bloquear imediatamente os recursos na conta de seu cliente, no valor total da transação original. Se não houver recursos suficientes na conta do recebedor no momento do bloqueio, o participante recebedor deve bloquear a totalidade dos recursos disponíveis. O participante recebedor pode realizar múltiplos bloqueios até o limite do valor total ao longo dos sete dias que o participante tem para realizar a análise de mérito da notificação de infração. O usuário recebedor deve ser prontamente avisado sobre o bloqueio e sobre a concretização

da devolução. O usuário recebedor pode solicitar o cancelamento da devolução no prazo de 30 dias (contados a partir da devolução).

#### 11. Quais os prazos envolvidos numa notificação de infração associada a uma solicitação de devolução?

o O participante pagador pode abrir uma notificação de infração para transações que tenham ocorrido há no máximo 80 dias, em relação ao dia de abertura da notificação. o A abertura da notificação de infração pode se dar por iniciativa do próprio participante ou por iniciativa do seu cliente. Ao receber a reclamação do cliente, o participante pagador deve abrir a notificação de infração associada a uma solicitação de devolução após análise de escopo da reclamação de seu cliente (ou seja, se o MED pode ser acionado para o caso específico). Recomenda-se que essa análise seja feita o mais rápido possível para que os recursos possam ser bloqueados na conta do usuário recebedor, aumentando a probabilidade de sucesso da devolução. o O participante recebedor bloqueia imediatamente o valor solicitado (total ou parcial, caso o valor total não esteja disponível na conta do cliente), assim que recebe a notificação de infração. o O participante recebedor tem 7 dias corridos para analisar (aceitar ou rejeitar) a notificação. o Após a aceitação da notificação pelo participante recebedor, o participante pagador tem até 72 horas para solicitar a devolução. o Ao receber a solicitação de devolução, o participante recebedor tem até 24 horas para efetivar a devolução.

#### 12. Qual o tempo para iniciar a notificação de infração após a reclamação do usuário?

A critério de cada participante. Sugere-se que seja efetivado o mais rapidamente possível, para que exista uma maior probabilidade de existirem recursos na conta do usuário recebedor para bloqueio e devolução.

**13. Caso a notificação de infração associada a uma solicitação de devolução seja recebida, porém o** **usuário recebedor não possua saldo em conta, o que deve ser feito? Recusar a notificação ou** **aguardar que ele tenha saldo no período de 7 dias de análise, para realizar bloqueios parciais?** Mesmo que não haja saldo em conta, a notificação de infração pode ser aceita, caso o participante recebedor avalie que se trata, efetivamente, de uma fraude. Caso o participante pagador abra a solicitação de devolução, o participante recebedor poderá rejeitar a solicitação por insuficiência de fundos na conta do usuário. A notificação não se confunde com a solicitação de devolução. A aceitação ou a rejeição da notificação é relacionada à análise do participante recebedor sobre o caráter fraudulento da transação. Se julgar que houve fraude, aceita a notificação. Caso contrário, rejeita a notificação. Isso deve ser feito independentemente da existência de saldo em conta para efetivar o bloqueio. Quando a solicitação de devolução é aberta é que o participante recebedor pode rejeitar a devolução por falta de recursos na conta do cliente. Isso pode ser feito assim que a solicitação é identificada ou o participante pode aguardar as 24 horas para encerrar a solicitação de devolução
**14. No fluxo de notificação de infração "associada a uma solicitação de devolução", caso o usuário** **recebedor não tenha o saldo total do valor da transação, o participante recebedor deve fazer** **o monitoramento de saldo para tentar realizar bloqueios parciais? Ou o participante deve**

#### realizar apenas um único bloqueio com o valor que estiver disponível de recursos assim que

#### recebe o pedido de notificação do DICT?

A obrigação do participante é fazer o primeiro bloqueio com o valor disponível. A critério do participante, ele pode ficar monitorando o saldo na conta de seu cliente para a efetivação de devoluções parciais até o valor total da transação original.

**15. Em casos de golpes e roubos de dispositivos, quais seriam as diretrizes para a tratativa dos** **cenários? Estariam eles contemplados no escopo do Mecanismo Especial de Devolução?** Sim, o MED pode ser acionado em qualquer caso de fundada suspeita de fraude em que o Pix foi utilizado, incluindo golpes e roubos de dispositivos. A orientação é que o cliente entre em contato o mais rapidamente possível com seu prestador de serviços de pagamento (PSP), por meio de qualquer canal de atendimento disponibilizado, relatando o caso. O PSP deve abrir imediatamente uma notificação de infração associada a uma solicitação de devolução, para que os recursos na conta do usuário recebedor possam ser bloqueados.
#### 16. Por quanto tempo o participante recebedor deve ficar tentando fazer a devolução?

O participante recebedor deve fazer a devolução dos recursos em até 24 horas após o pedido de solicitação ter sido realizado. Caso o valor devolvido não corresponda ao valor total da transação original, o participante pode, a seu critério, continuar monitorando a conta do usuário para realizar devoluções parciais, caso recursos sejam creditados na conta.

**17. É possível a abertura de notificações de infração e de solicitações de devolução para transações intraparticipante?** Atualmente, notificações de infração e solicitações de devolução no DICT podem ser feitas apenas para transações liquidadas no SPI. Com a entrada em vigor das alterações dispostas na Resolução BCB nº 147 em 16 de novembro de 2021, será possível também a abertura de notificação de infração para transações liquidadas nos sistemas do próprio participante. Solicitações de devolução, contudo, podem ser abertas somente para transações que forem liquidadas no SPI. A devolução de recursos de transações intraparticipante por meio do Mecanismo Especial de Devolução é possível, mas não é necessária a abertura de uma solicitação de devolução.
**18. Caso a suspeita de fraude tenha sido descoberta pelo participante recebedor, qual procedimento deve ser seguido?** O participante recebedor deve simplesmente debitar o valor correspondente da conta de seu cliente e devolver os recursos para o usuário pagador por meio do envio de uma mensagem pacs.004. Paralelamente à devolução dos recursos, o participante recebedor deve abrir uma notificação de infração por motivo de fraude, para que a chave de seu cliente possa ser marcada no DICT.
#### 19. O participante recebedor pode considerar limite da conta para devolver recursos?

Apenas caso essa possibilidade esteja expressamente prevista no contrato de prestação de serviço entre o participante e seus clientes.

**20. O bloqueio judicial tem prioridade sobre o bloqueio do MED? Se a conta já tiver um ou mais** **bloqueios de saldo por conta do MED, quando chegar um pedido de bloqueio judicial, o sistema** **deve considerar os saldos já bloqueados para o bloqueio judicial?** Sim. Bloqueio judicial tem prioridade. Se houver recursos bloqueado no âmbito do MED, eles devem ser redirecionados para o bloqueio judicial.
**21. O cliente deve autorizar o acionamento do MED ou o participante deve apenas informar seus** **clientes acerca da previsão de acionamento do MED ter sido incluída no contrato entre as partes?** O participante deve ajustar o contrato de prestação de serviços que mantém com seus clientes para prever a possibilidade de acionamento do MED no âmbito do Pix. Após esse ajuste o participante deve informar aos seus clientes acerca dessa alteração contratual.
#### 22. O cliente pode não aceitar a alteração contratual?

Se o cliente não concordar com os termos do contrato, sua conta deverá ser encerrada.

**23. Como deve ser feita a notificação de bloqueio de recursos e de crédito de recursos para o cliente?** A critério de cada participante.
#### 24. Há necessidade de abertura de notificação de infração nos casos de erro operacional?

Não. Não é preciso abrir uma notificação de infração. O participante pagador deve abrir diretamente uma solicitação de devolução por “falha operacional do PSP do pagador”.

**25. O que o participante recebedor deve fazer caso ocorra erro operacional/sistêmico em seu próprio ambiente?** O participante recebedor deve acionar o MED, debitando os recursos da conta de seu cliente e devolvendo-os para o usuário pagador da transação original, por meio do envio da mensagem pacs.004. Não há necessidade de abertura de notificação de infração nem de solicitação de devolução.
#### 26. O que o participante pagador deve fazer caso ocorra erro operacional/sistêmico em seu ambiente?

O participante pagador deve abrir uma “solicitação de devolução por falha operacional do PSP pagador”. Não é necessário abrir uma notificação de infração previamente.

**27. Há a possibilidade de o participante recebedor negar uma solicitação de devolução por erro operacional?** Apenas no caso em que o participante não fez a alteração contratual prevendo o MED. Nesse caso, o participante recebedor será responsabilizado por eventuais acionamentos na justiça por parte do usuário pagador ou do seu prestador de serviços de pagamento.
#### 28. Existe bloqueio imediato dos valores solicitados?

No caso de falha operacional, não há bloqueio prévio de recursos. Os recursos devem ser devolvidos em até 24 horas após o recebimento da solicitação de devolução.
