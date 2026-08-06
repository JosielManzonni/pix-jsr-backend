---
id: rfc-decoding-001
type: rfc
ontology: openpix-architecture-v1
title: Pix Payload Decoding Boundary
status: accepted
context: decoding
created: 2026-08-05
updated: 2026-08-05
tags: [rfc, decoding, pix, br-code, tlv, crc16]
relations:
  - type: belongs_to
    target: ctx-decoding
  - type: decided_by
    target: adr-decoding-001
  - type: governed_by
    target: rfc-platform-001
  - type: produces_for
    target: ctx-payment
  - type: observed_by
    target: ctx-observability
---

# RFC-DECODING-001: Pix Payload Decoding Boundary

## Summary

O contexto de decodificação valida e normaliza payloads Pix/BR Code. A saída é
uma instrução interpretada (`DecodedInstruction`); criar ou persistir um
pagamento pertence ao Payment Context. A decodificação é stateless e expõe um
único endpoint estrito, sem modos "talvez" nem leniência.

## Motivation

Um payload Pix bruto é opaco: contém chave, modo, valor, txid e metadados do
comerciante em um TLV ASCII. Consumidores (inclusive o futuro Payment context)
precisam de uma resposta determinística e validada, não de parsing ad hoc.
Sem uma fronteira explícita, cada serviço reimplementaria regras de Pix e
divergiriam em CRC, charset e formatos de chave.

## Proposal

- `decoding-service/contracts/openapi.yaml` é a única interface do serviço; o
  app FastAPI o serve verbatim via override de `custom_openapi` (nunca gera
  schema no runtime que possa divergir do contrato).
- Endpoint único e estrito: `POST /decode/v1/pix-payloads`.
- Saída `DecodedInstruction`: `key`, `key_type`, `location`, `mode`, `amount`,
  `txid`, `description`, `merchant_name`, `merchant_city`, `mcc`, `crc_valid`.
- Erros via Problem Details com códigos estáveis `DECODING_*` e
  `CONTEXT_INVALID_REQUEST` (shape de requisição).
- Correlação via header `X-Correlation-ID`: aceita e gerada quando ausente;
  todas as respostas carregam o header `X-Correlation-ID`; respostas Problem
  Details (400/422) carregam adicionalmente `correlationId` no corpo (o corpo
  `DecodedInstruction` de sucesso não tem campo `correlationId`).
- Payload e material de chave nunca são logados.
- Constantes de spec provenientes do manual BACEN Pix e do EMVCo QRCPS
  (https://www.bcb.gov.br/acessoinformacao/legislacao_normativas/manual-de-padroes-para-iniciacao-do-pix e
  https://www.emvco.com/specifications/emv-qr-code/):
  - envelope: payloads com mais de 512 caracteres são rejeitados com
    `DECODING_PAYLOAD_TOO_LONG`;
  - formato TLV ASCII bruto: tag de 2 dígitos, length decimal de 2 dígitos,
    valor em ASCII cru (sem hex encoding no payload);
  - CRC16-CCITT-FALSE: poly `0x1021`, init `0xFFFF`, MSB-first, sem reflection
    e sem xor-out; escopo sobre o payload INCLUINDO os bytes literais `6304`,
    EXCLUINDO apenas os 4 caracteres finais de CRC (uppercase).
- Estrita: CRC inválido, moeda não-BRL, TLV malformado e chave desconhecida
  resultam em 422, sem fallback leniente.
- Suporte a QR dinâmico por localização: tag 26.25 (recipiente key XOR
  location; dinâmico exige exatamente uma fonte, estático exige 26.01 e ignora
  26.25).
- Regras de strictness (revisão do conselho pós-implementação): ordenação de
  tags não-descendente por nível (CRC final 63 isento da comparação), check
  digits de CPF/CNPJ, EVP UUID v4 RFC-4122 canônico, `MCC` com 4 dígitos quando
  presente, nome/cidade do comerciante não-vazios.
- CRC16 via stdlib (`binascii.crc_hqx`, mesmos parâmetros e escopo).

## Alternatives

### Parser leniente com warnings na resposta

Um serviço que responde "talvez" é uma fábrica de bugs; clientes precisam de uma
única resposta determinística. Foi rejeitado.

### Decodificar + iniciar pagamento no mesmo serviço

Criar ou persistir pagamento pertence ao Payment context. Juntar as duas coisas
acopla parsing a ciclo de vida e viola o princípio de um bounded context por
serviço.

## Compatibility

A instrução é um primeiro chute de schema; evolução aditiva é a regra da
plataforma. Mudanças incompatíveis exigem nova versão pública. Valores
desconhecidos em enums (`key_type`, `mode`) devem ser tratados com segurança
por clientes antigos.

## Security

Contratos não tornam dados confiáveis. O payload é contexto não confiável:
deve ser validado estritamente antes de qualquer interpretação. Payloads Pix,
chaves e dados pessoais não podem aparecer em logs ou exemplos reais.

## Rollout

1. Publicar `decoding-service/contracts/openapi.yaml`.
2. Validar YAML e referências em CI.
3. Validar exemplos contra schemas.
4. Adicionar contract tests por consumidor.
5. Criar o endpoint como fonte do schema (override) antes de expor a clientes.

## Knowledge graph

- Contexto: [[CTX-DECODING]]
- Decisão: [[ADR-DECODING-001-stateless-payload-decoding]]
- Governado por: [[RFC-PLATFORM-001-contract-first-service-boundaries]]
- Produz para: [[CTX-PAYMENT]]
- Observado por: [[CTX-OBSERVABILITY]]

> Nota (derivação): `docs/architecture/generated/knowledge-graph.jsonld` NÃO é
> reconstruído por esta mudança — `scripts/` não existe neste repositório. O
> artefato é uma projeção derivada e não deve ser editado à mão; o grafo não
> refletirá as novas notas até que um script de build exista.
