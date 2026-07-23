import { useEffect, useId, useState } from 'react';
import { criarLead, listarModelos, ApiError } from '../services/api.js';
import './LeadCaptureForm.css';

/*
 * LeadCaptureForm (Arquitetura 1.2.1)
 * Props: origem (ex.: "hero", "popup", "whatsapp"), campanhaId
 * POST /api/leads/ com payload polimórfico (Atualizacao_Contrato_API.md):
 * tipo_pessoa FISICA -> dados_fisica | JURIDICA -> dados_juridica, + interesse.
 * Estados: Inicial / Carregando / Sucesso 201 / Erro 400 (destaca campos,
 * formato hierárquico DRF) / Conflito 409 / Erro 500.
 */

const PERFIS = [
  { valor: 'paciente', rotulo: 'Paciente' },
  { valor: 'familiar', rotulo: 'Familiar' },
  { valor: 'cuidador', rotulo: 'Cuidador(a)' },
];

const TIPOS_INSTITUICAO = [
  { valor: 'clinica', rotulo: 'Clínica' },
  { valor: 'hospital', rotulo: 'Hospital' },
  { valor: 'ong', rotulo: 'ONG' },
  { valor: 'outro', rotulo: 'Outro' },
];

const ORIGENS = [
  { valor: 'google', rotulo: 'Google' },
  { valor: 'instagram', rotulo: 'Instagram' },
  { valor: 'facebook', rotulo: 'Facebook' },
  { valor: 'indicacao', rotulo: 'Indicação' },
  { valor: 'evento', rotulo: 'Evento' },
  { valor: 'outro', rotulo: 'Outro' },
];

const FORM_INICIAL = {
  tipo_pessoa: 'FISICA',
  nome: '',
  email: '',
  telefone: '',
  estado: '',
  cidade: '',
  // Pessoa Física
  cpf: '',
  data_nascimento: '',
  tipo_deficiencia: '',
  perfil: 'paciente',
  comunicacao_verbal_preservada: true,
  // Pessoa Jurídica
  cnpj: '',
  tipo_instituicao: 'clinica',
  contato_responsavel: '',
  cargo_responsavel: '',
  // Interesse
  modelo_id: '',
  quantidade_estimada: 1,
  mensagem: '',
  origem_lead: 'outro',
  aceite_termos: false,
  possui_cadeira: false,
};

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/** Achata o erro hierárquico do DRF em chaves tipo "dados_fisica.cpf". */
function achatarErros(corpo, prefixo = '') {
  const erros = {};
  if (!corpo || typeof corpo !== 'object') return erros;
  for (const [chave, valor] of Object.entries(corpo)) {
    const caminho = prefixo ? `${prefixo}.${chave}` : chave;
    if (Array.isArray(valor)) {
      erros[caminho] = valor.join(' ');
    } else if (valor && typeof valor === 'object') {
      Object.assign(erros, achatarErros(valor, caminho));
    } else if (typeof valor === 'string') {
      erros[caminho] = valor;
    }
  }
  return erros;
}

/* Definido fora do componente para manter a identidade estável entre
   renders (evita remontagem e perda de foco dos inputs ao digitar). */
function Campo({ erro, children }) {
  return (
    <div className={`campo ${erro ? 'campo-invalido' : ''}`}>
      {children}
      {erro && (
        <span className="campo-erro" role="alert">
          {erro}
        </span>
      )}
    </div>
  );
}

export default function LeadCaptureForm({ origem = 'landing', campanhaId }) {
  const idBase = useId();
  const [form, setForm] = useState(FORM_INICIAL);
  const [estado, setEstado] = useState('inicial'); // inicial | carregando | sucesso | erro400 | erro409 | erro500
  const [errosCampos, setErrosCampos] = useState({});
  const [erroEmail, setErroEmail] = useState('');
  const [erroModelo, setErroModelo] = useState('');
  const [modelos, setModelos] = useState([]);

  const fisica = form.tipo_pessoa === 'FISICA';
  const carregando = estado === 'carregando';

  useEffect(() => {
    let ativo = true;
    listarModelos()
      .then((lista) => ativo && setModelos(lista))
      .catch(() => ativo && setModelos([]));
    return () => {
      ativo = false;
    };
  }, []);

  // Cards B2C/B2B (AudienceSection) pré-selecionam o tipo de cadastro
  useEffect(() => {
    const aoSelecionarTipo = (evento) => {
      if (evento.detail === 'FISICA' || evento.detail === 'JURIDICA') {
        setForm((f) => ({ ...f, tipo_pessoa: evento.detail }));
      }
    };
    window.addEventListener('easyride:tipo-pessoa', aoSelecionarTipo);
    return () => window.removeEventListener('easyride:tipo-pessoa', aoSelecionarTipo);
  }, []);

  const atualizar = (campo) => (evento) => {
    const { type, checked, value } = evento.target;
    setForm((f) => ({ ...f, [campo]: type === 'checkbox' ? checked : value }));
    // Validação de e-mail em tempo real (RF05)
    if (campo === 'email') {
      setErroEmail(value && !EMAIL_REGEX.test(value) ? 'Formato de e-mail inválido.' : '');
    }
    if (campo === 'modelo_id' && value) {
      setErroModelo('');
    }
  };

  const montarPayload = () => {
    const incluirSePreenchido = (objeto, chave, valor) => {
      if (valor !== '' && valor !== null && valor !== undefined) objeto[chave] = valor;
    };

    const payload = {
      tipo_pessoa: form.tipo_pessoa,
      nome: form.nome,
      email: form.email,
      interesse: {
        modelo_id: Number(form.modelo_id),
        quantidade_estimada: Number(form.quantidade_estimada) || 1,
        origem: form.origem_lead,
        aceite_termos: form.aceite_termos,
        possui_cadeira: form.possui_cadeira,
      },
    };
    incluirSePreenchido(payload, 'telefone', form.telefone);
    incluirSePreenchido(payload, 'estado', form.estado);
    incluirSePreenchido(payload, 'cidade', form.cidade);
    incluirSePreenchido(payload.interesse, 'mensagem', form.mensagem);
    if (campanhaId) payload.interesse.campanha_id = campanhaId;

    if (fisica) {
      payload.dados_fisica = {
        perfil: form.perfil,
        comunicacao_verbal_preservada: form.comunicacao_verbal_preservada,
      };
      incluirSePreenchido(payload.dados_fisica, 'cpf', form.cpf);
      incluirSePreenchido(payload.dados_fisica, 'data_nascimento', form.data_nascimento);
      incluirSePreenchido(payload.dados_fisica, 'tipo_deficiencia', form.tipo_deficiencia);
    } else {
      payload.dados_juridica = {
        tipo_instituicao: form.tipo_instituicao,
      };
      incluirSePreenchido(payload.dados_juridica, 'cnpj', form.cnpj);
      incluirSePreenchido(payload.dados_juridica, 'contato_responsavel', form.contato_responsavel);
      incluirSePreenchido(payload.dados_juridica, 'cargo_responsavel', form.cargo_responsavel);
    }
    return payload;
  };

  const enviar = async (evento) => {
    evento.preventDefault();
    setErroModelo(form.modelo_id ? '' : 'Selecione um modelo.');
    if (erroEmail || !form.modelo_id) return;

    setEstado('carregando');
    setErrosCampos({});
    try {
      await criarLead(montarPayload());
      setEstado('sucesso');
      setForm(FORM_INICIAL); // limpa o formulário (comportamento exigido)
    } catch (erro) {
      if (erro instanceof ApiError && erro.status === 400) {
        setErrosCampos(achatarErros(erro.corpo));
        setEstado('erro400');
      } else if (erro instanceof ApiError && erro.status === 409) {
        setEstado('erro409');
      } else {
        setEstado('erro500');
      }
    }
  };

  const erroDe = (chave) => errosCampos[chave];

  return (
    <form className="lead-form" onSubmit={enviar} noValidate data-origem={origem}>
      <fieldset disabled={carregando}>
        <legend className="sr-only">Formulário de interesse na EasyRide</legend>

        {/* Seletor polimórfico FISICA / JURIDICA */}
        <div className="tipo-pessoa" role="radiogroup" aria-label="Tipo de cadastro">
          <label className={fisica ? 'ativo' : ''}>
            <input
              type="radio"
              name={`${idBase}-tipo`}
              checked={fisica}
              onChange={() => setForm((f) => ({ ...f, tipo_pessoa: 'FISICA' }))}
            />
            Pessoa Física
          </label>
          <label className={!fisica ? 'ativo' : ''}>
            <input
              type="radio"
              name={`${idBase}-tipo`}
              checked={!fisica}
              onChange={() => setForm((f) => ({ ...f, tipo_pessoa: 'JURIDICA' }))}
            />
            Instituição (Pessoa Jurídica)
          </label>
        </div>

        <Campo erro={erroDe('nome')}>
          <label htmlFor={`${idBase}-nome`}>Nome completo *</label>
          <input
            id={`${idBase}-nome`}
            type="text"
            value={form.nome}
            onChange={atualizar('nome')}
            required
            autoComplete="name"
            aria-invalid={Boolean(erroDe('nome'))}
          />
        </Campo>

        <Campo erro={erroDe('email')}>
          <label htmlFor={`${idBase}-email`}>E-mail *</label>
          <input
            id={`${idBase}-email`}
            type="email"
            value={form.email}
            onChange={atualizar('email')}
            required
            autoComplete="email"
            aria-invalid={Boolean(erroDe('email') || erroEmail)}
            aria-describedby={erroEmail ? `${idBase}-email-erro` : undefined}
          />
          {erroEmail && (
            <span id={`${idBase}-email-erro`} className="campo-erro" role="alert">
              {erroEmail}
            </span>
          )}
        </Campo>

        <div className="linha-dupla">
          <Campo erro={erroDe('telefone')}>
            <label htmlFor={`${idBase}-telefone`}>Telefone</label>
            <input
              id={`${idBase}-telefone`}
              type="tel"
              value={form.telefone}
              onChange={atualizar('telefone')}
              autoComplete="tel"
              placeholder="11999999999"
            />
          </Campo>

          <Campo erro={erroDe('estado')}>
            <label htmlFor={`${idBase}-estado`}>Estado (UF)</label>
            <input
              id={`${idBase}-estado`}
              type="text"
              maxLength={2}
              value={form.estado}
              onChange={atualizar('estado')}
              placeholder="SE"
            />
          </Campo>
        </div>

        <Campo erro={erroDe('cidade')}>
          <label htmlFor={`${idBase}-cidade`}>Cidade</label>
          <input
            id={`${idBase}-cidade`}
            type="text"
            value={form.cidade}
            onChange={atualizar('cidade')}
            autoComplete="address-level2"
          />
        </Campo>

        {fisica ? (
          <fieldset className="subgrupo">
            <legend>Dados pessoais</legend>

            <div className="linha-dupla">
              <Campo erro={erroDe('dados_fisica.cpf')}>
                <label htmlFor={`${idBase}-cpf`}>CPF</label>
                <input
                  id={`${idBase}-cpf`}
                  type="text"
                  value={form.cpf}
                  onChange={atualizar('cpf')}
                  placeholder="123.456.789-00"
                  aria-invalid={Boolean(erroDe('dados_fisica.cpf'))}
                />
              </Campo>

              <Campo erro={erroDe('dados_fisica.data_nascimento')}>
                <label htmlFor={`${idBase}-nascimento`}>Data de nascimento</label>
                <input
                  id={`${idBase}-nascimento`}
                  type="date"
                  value={form.data_nascimento}
                  onChange={atualizar('data_nascimento')}
                />
              </Campo>
            </div>

            <div className="linha-dupla">
              <Campo erro={erroDe('dados_fisica.tipo_deficiencia')}>
                <label htmlFor={`${idBase}-deficiencia`}>Tipo de deficiência</label>
                <input
                  id={`${idBase}-deficiencia`}
                  type="text"
                  value={form.tipo_deficiencia}
                  onChange={atualizar('tipo_deficiencia')}
                  placeholder="Ex.: Motora"
                />
              </Campo>

              <Campo erro={erroDe('dados_fisica.perfil')}>
                <label htmlFor={`${idBase}-perfil`}>Seu perfil *</label>
                <select id={`${idBase}-perfil`} value={form.perfil} onChange={atualizar('perfil')}>
                  {PERFIS.map((p) => (
                    <option key={p.valor} value={p.valor}>
                      {p.rotulo}
                    </option>
                  ))}
                </select>
              </Campo>
            </div>

            <div className="campo campo-checkbox">
              <label>
                <input
                  type="checkbox"
                  checked={form.comunicacao_verbal_preservada}
                  onChange={atualizar('comunicacao_verbal_preservada')}
                />
                Comunicação verbal preservada (consegue falar comandos de voz)
              </label>
            </div>
          </fieldset>
        ) : (
          <fieldset className="subgrupo">
            <legend>Dados da instituição</legend>

            <div className="linha-dupla">
              <Campo erro={erroDe('dados_juridica.cnpj')}>
                <label htmlFor={`${idBase}-cnpj`}>CNPJ</label>
                <input
                  id={`${idBase}-cnpj`}
                  type="text"
                  value={form.cnpj}
                  onChange={atualizar('cnpj')}
                  placeholder="12.345.678/0001-90"
                  aria-invalid={Boolean(erroDe('dados_juridica.cnpj'))}
                />
              </Campo>

              <Campo erro={erroDe('dados_juridica.tipo_instituicao')}>
                <label htmlFor={`${idBase}-instituicao`}>Tipo de instituição *</label>
                <select
                  id={`${idBase}-instituicao`}
                  value={form.tipo_instituicao}
                  onChange={atualizar('tipo_instituicao')}
                >
                  {TIPOS_INSTITUICAO.map((t) => (
                    <option key={t.valor} value={t.valor}>
                      {t.rotulo}
                    </option>
                  ))}
                </select>
              </Campo>
            </div>

            <div className="linha-dupla">
              <Campo erro={erroDe('dados_juridica.contato_responsavel')}>
                <label htmlFor={`${idBase}-responsavel`}>Contato responsável</label>
                <input
                  id={`${idBase}-responsavel`}
                  type="text"
                  value={form.contato_responsavel}
                  onChange={atualizar('contato_responsavel')}
                />
              </Campo>

              <Campo erro={erroDe('dados_juridica.cargo_responsavel')}>
                <label htmlFor={`${idBase}-cargo`}>Cargo do responsável</label>
                <input
                  id={`${idBase}-cargo`}
                  type="text"
                  value={form.cargo_responsavel}
                  onChange={atualizar('cargo_responsavel')}
                />
              </Campo>
            </div>
          </fieldset>
        )}

        <fieldset className="subgrupo">
          <legend>Seu interesse</legend>

          <div className="linha-dupla">
            <Campo erro={erroModelo || erroDe('interesse.modelo_id')}>
              <label htmlFor={`${idBase}-modelo`}>Modelo de cadeira *</label>
              <select
                id={`${idBase}-modelo`}
                value={form.modelo_id}
                onChange={atualizar('modelo_id')}
                required
              >
                <option value="" disabled>
                  Selecione um modelo
                </option>
                {modelos.map((modelo) => (
                  <option key={modelo.id} value={modelo.id}>
                    {modelo.nome_modelo} — {modelo.marca}
                    {modelo.motorizada ? ' (motorizada)' : ''}
                  </option>
                ))}
              </select>
            </Campo>

            <Campo erro={erroDe('interesse.quantidade_estimada')}>
              <label htmlFor={`${idBase}-quantidade`}>Quantidade estimada *</label>
              <input
                id={`${idBase}-quantidade`}
                type="number"
                min={1}
                value={form.quantidade_estimada}
                onChange={atualizar('quantidade_estimada')}
                required
              />
            </Campo>
          </div>

          <Campo erro={erroDe('interesse.origem')}>
            <label htmlFor={`${idBase}-origem`}>Como conheceu a EasyRide? *</label>
            <select
              id={`${idBase}-origem`}
              value={form.origem_lead}
              onChange={atualizar('origem_lead')}
            >
              {ORIGENS.map((o) => (
                <option key={o.valor} value={o.valor}>
                  {o.rotulo}
                </option>
              ))}
            </select>
          </Campo>

          <Campo erro={erroDe('interesse.mensagem')}>
            <label htmlFor={`${idBase}-mensagem`}>Mensagem</label>
            <textarea
              id={`${idBase}-mensagem`}
              value={form.mensagem}
              onChange={atualizar('mensagem')}
              rows={4}
              placeholder="Conte um pouco sobre a sua necessidade"
            />
          </Campo>

          <div className="campo campo-checkbox">
            <label>
              <input
                type="checkbox"
                checked={form.possui_cadeira}
                onChange={atualizar('possui_cadeira')}
              />
              Já possuo cadeira de rodas motorizada
            </label>
          </div>

          <div className={`campo campo-checkbox ${erroDe('interesse.aceite_termos') ? 'campo-invalido' : ''}`}>
            <label>
              <input
                type="checkbox"
                checked={form.aceite_termos}
                onChange={atualizar('aceite_termos')}
                required
                aria-invalid={Boolean(erroDe('interesse.aceite_termos'))}
              />
              Li e aceito os termos de uso e a política de privacidade (LGPD) *
            </label>
            {erroDe('interesse.aceite_termos') && (
              <span className="campo-erro" role="alert">
                {erroDe('interesse.aceite_termos')}
              </span>
            )}
          </div>
        </fieldset>

        <button type="submit" className="btn-enviar" disabled={carregando || !form.aceite_termos}>
          {carregando ? (
            <>
              <span className="spinner" aria-hidden="true" /> Enviando…
            </>
          ) : (
            'Enviar Interesse'
          )}
        </button>
      </fieldset>

      {/* Mensagens de estado (aria-live para leitores de tela) */}
      <div aria-live="polite" className="form-mensagens">
        {estado === 'sucesso' && (
          <p className="mensagem mensagem-sucesso">Obrigado! Entraremos em contato em breve.</p>
        )}
        {estado === 'erro400' && (
          <p className="mensagem mensagem-erro">
            Verifique os campos destacados e tente novamente.
          </p>
        )}
        {estado === 'erro409' && (
          <p className="mensagem mensagem-erro">
            Você já está cadastrado. Em breve nossa equipe entrará em contato!
          </p>
        )}
        {estado === 'erro500' && (
          <p className="mensagem mensagem-erro">Erro interno. Tente novamente mais tarde.</p>
        )}
      </div>
    </form>
  );
}
