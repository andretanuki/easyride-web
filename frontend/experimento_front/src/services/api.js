/*
 * Cliente da API EasyRide — Contrato v3.0 + Atualizacao_Contrato_API.md
 *
 * Formatos de resposta tratados:
 *  - 201: { status: "success", mensagem, dados }
 *  - 400: JSON hierárquico nativo do DRF, ex.:
 *         { "email": ["..."], "dados_fisica": { "cpf": ["..."] } }
 *  - 409: { status: "error", mensagem: "Lead já cadastrado" }
 *  - 404/500: { status: "error", mensagem }
 *  - GETs de listagem: paginados pelo DRF ({ results: [...] }) ou array puro
 */

const BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');

export class ApiError extends Error {
  constructor(status, corpo) {
    const mensagem =
      corpo && typeof corpo === 'object' && typeof corpo.mensagem === 'string'
        ? corpo.mensagem
        : `Erro HTTP ${status}`;
    super(mensagem);
    this.name = 'ApiError';
    this.status = status;
    this.corpo = corpo; // erros 400: objeto hierárquico do DRF por campo
  }
}

async function requisicao(caminho, opcoes = {}) {
  const resposta = await fetch(`${BASE_URL}${caminho}`, {
    ...opcoes,
    headers: {
      'Content-Type': 'application/json', // obrigatório pelo contrato
      ...(opcoes.headers || {}),
    },
  });

  let corpo = null;
  try {
    corpo = await resposta.json();
  } catch {
    /* respostas sem corpo JSON */
  }

  if (!resposta.ok) {
    throw new ApiError(resposta.status, corpo);
  }
  return corpo;
}

/** Desembrulha listagens paginadas do DRF ({count, results}) ou arrays puros. */
function extrairLista(corpo) {
  if (Array.isArray(corpo)) return corpo;
  if (corpo && Array.isArray(corpo.results)) return corpo.results;
  return [];
}

export async function listarModelos() {
  return extrairLista(await requisicao('/api/modelos/'));
}

export async function listarBeneficios() {
  return extrairLista(await requisicao('/api/beneficios/'));
}

export async function listarDepoimentos() {
  return extrairLista(await requisicao('/api/depoimentos/'));
}

export async function listarFaq() {
  return extrairLista(await requisicao('/api/faq/'));
}

export async function criarLead(payload) {
  return requisicao('/api/leads/', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}
