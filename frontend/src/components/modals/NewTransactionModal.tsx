"use client";

import { useEffect, useState } from "react";
import type { Categoria } from "@/hooks/useDashboard";
import { API_BASE } from "@/lib/apiConfig";

const C = {
    surface: "var(--surface)", elevated: "var(--elevated)", border: "var(--border)",
    muted: "var(--muted)", text: "var(--text)", avocado: "var(--avocado)", danger: "#F85149",
};

interface Props {
    isOpen: boolean;
    onClose: () => void;
    cicloId: number;
    categorias: Categoria[];
    usuarioId?: string;
    onSuccess: () => void;
}

interface ParcelaPendente {
    id: number;
    label: string;
    valor: number;
    data_vencimento: string;
    status: string;
}

// ID virtual para a categoria "Dívidas" — não precisa existir no banco para o modal funcionar
const DIVIDAS_VIRTUAL_ID = -999;

export default function NewTransactionModal({ isOpen, onClose, cicloId, categorias, usuarioId, onSuccess }: Props) {
    const [descricao, setDescricao] = useState("");
    const [valor, setValor] = useState("");
    const [categoriaId, setCategoriaId] = useState<number | "">(categorias[0]?.id ?? "");
    const [tipo, setTipo] = useState<"saida" | "entrada">("saida");
    const [data, setData] = useState(new Date().toISOString().split("T")[0]);
    const [recorrente, setRecorrente] = useState(false);
    const [obs, setObs] = useState("");
    const [metaId, setMetaId] = useState<number | "">("")
    const [metas, setMetas] = useState<{ id: number; titulo: string }[]>([]);
    const [loading, setLoading] = useState(false);
    const [erro, setErro] = useState<string | null>(null);

    // Dívidas
    const [parcelaId, setParcelaId] = useState<number | "">("");
    const [parcelasPendentes, setParcelasPendentes] = useState<ParcelaPendente[]>([]);
    const [fetchingParcelas, setFetchingParcelas] = useState(false);

    // Detect selected category. A category with slug='dividas' from DB OR the virtual injection
    const selectedCat = categorias.find(c => c.id === categoriaId);
    const isInvestimento = selectedCat?.slug === "investimentos";
    // "Dívidas" matched either via slug (if migration ran) or virtual ID
    const isDividas = categoriaId === DIVIDAS_VIRTUAL_ID || selectedCat?.slug === "dividas";

    // Categoria 'Dívidas' exists in DB already (from migration)?
    const dividasDbId = categorias.find(c => c.slug === "dividas")?.id ?? null;

    // Build the final list of categories to show: inject virtual "Dívidas" if not in DB yet
    const categoriasExibicao = dividasDbId
        ? categorias  // already has Dívidas from DB
        : [...categorias, { id: DIVIDAS_VIRTUAL_ID, nome: "Dívidas", slug: "dividas", cor_hex: "#F85149", icone: "💸", tipo: "saida" }];

    // When virtual Dívidas is selected, the actual categoria_id to send to the API
    // is null (no DB category) — we'll still mark tipo=saida and record the transaction
    const realCategoriaId = categoriaId === DIVIDAS_VIRTUAL_ID ? (dividasDbId ?? categorias.find(c => c.slug === "gastos-fixos")?.id ?? categorias[0]?.id) : categoriaId;

    // Fetch parcelas-pendentes when modal opens (pre-load) or when isDividas toggles true
    useEffect(() => {
        if (isDividas && usuarioId) {
            setFetchingParcelas(true);
            fetch(`${API_BASE}/contratos/${usuarioId}/parcelas-pendentes`)
                .then(r => r.json())
                .then((data: ParcelaPendente[]) => setParcelasPendentes(data))
                .catch(() => setParcelasPendentes([]))
                .finally(() => setFetchingParcelas(false));
        } else {
            setParcelasPendentes([]);
            setParcelaId("");
        }
    }, [isDividas, usuarioId]);

    // Fetch metas when investimentos is selected
    useEffect(() => {
        if (isInvestimento && usuarioId) {
            fetch(`${API_BASE}/metas/${usuarioId}`)
                .then(r => r.json())
                .then((data: { id: number; titulo: string; status: string }[]) =>
                    setMetas(data.filter(m => m.status === "ativa"))
                )
                .catch(() => setMetas([]));
        } else {
            setMetas([]);
            setMetaId("");
        }
    }, [isInvestimento, usuarioId]);

    // Auto-fill valor + descrição when a parcela is chosen
    useEffect(() => {
        if (parcelaId) {
            const p = parcelasPendentes.find(p => p.id === parcelaId);
            if (p) {
                setValor(p.valor.toFixed(2).replace(".", ","));
                const nomeDivida = p.label.split(" —")[0];
                setDescricao(nomeDivida);
            }
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [parcelaId]);

    const resetForm = () => {
        setDescricao(""); setValor(""); setObs(""); setErro(null);
        setRecorrente(false); setTipo("saida"); setMetaId(""); setParcelaId("");
    };

    const handleClose = () => { resetForm(); onClose(); };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        const valorNum = parseFloat(valor.replace(",", "."));
        if (isNaN(valorNum) || valorNum <= 0) { setErro("Informe um valor válido."); return; }
        if (!realCategoriaId) { setErro("Selecione uma categoria."); return; }

        setLoading(true); setErro(null);
        try {
            const res = await fetch(`${API_BASE}/transacoes`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    ciclo_id: cicloId,
                    categoria_id: realCategoriaId,
                    meta_id: metaId || null,
                    descricao,
                    valor: valorNum,
                    tipo,
                    data_transacao: data,
                    recorrente,
                    observacoes: obs || null,
                }),
            });
            if (!res.ok) {
                const body = await res.json().catch(() => ({}));
                throw new Error(body?.detail ?? `Erro ${res.status}`);
            }

            // Se uma dívida foi vinculada, dar baixa automaticamente na parcela
            if (isDividas && parcelaId) {
                await fetch(`${API_BASE}/parcelas/${parcelaId}/baixa`, { method: "PATCH" });
            }

            onSuccess();
            handleClose();
        } catch (err) {
            setErro(err instanceof Error ? err.message : "Erro ao registrar.");
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div
            className="fixed inset-0 z-50 flex items-end sm:items-center justify-center sm:p-4"
            style={{ backgroundColor: "rgba(0,0,0,0.65)", backdropFilter: "blur(4px)" }}
            onClick={(e) => e.target === e.currentTarget && handleClose()}
        >
            <div
                className="w-full sm:max-w-md rounded-t-2xl sm:rounded-2xl p-5 sm:p-6 shadow-2xl max-h-[92dvh] overflow-y-auto"
                style={{
                    backgroundColor: C.surface,
                    border: `1px solid ${C.border}`,
                    animation: "modal-in 0.2s ease-out",
                }}
            >
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h2 className="text-lg font-bold">Nova Transação</h2>
                        <p className="text-xs mt-0.5" style={{ color: C.muted }}>Registre um gasto ou recebimento</p>
                    </div>
                    <button
                        onClick={handleClose}
                        className="w-8 h-8 rounded-lg flex items-center justify-center hover:opacity-70 transition-opacity"
                        style={{ backgroundColor: C.elevated, color: C.muted }}
                    >✕</button>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    {/* Tipo toggle */}
                    <div
                        className="flex rounded-xl p-1 gap-1"
                        style={{ backgroundColor: C.elevated, border: `1px solid ${C.border}` }}
                    >
                        {(["saida", "entrada"] as const).map((t) => (
                            <button
                                key={t}
                                type="button"
                                onClick={() => setTipo(t)}
                                className="flex-1 py-2 rounded-lg text-sm font-medium transition-all"
                                style={{
                                    backgroundColor: tipo === t ? (t === "saida" ? C.danger : C.avocado) : "transparent",
                                    color: tipo === t ? "white" : C.muted,
                                }}
                            >
                                {t === "saida" ? "💸 Saída" : "💰 Entrada"}
                            </button>
                        ))}
                    </div>

                    {/* Descrição */}
                    <div>
                        <label className="text-xs font-medium mb-1.5 block" style={{ color: C.muted }}>Descrição</label>
                        <input
                            type="text"
                            placeholder="Ex: Aluguel, Supermercado..."
                            value={descricao}
                            onChange={(e) => setDescricao(e.target.value)}
                            required
                            className="w-full rounded-xl px-3 py-2.5 text-sm outline-none"
                            style={{ backgroundColor: C.elevated, border: `1px solid ${C.border}` }}
                        />
                    </div>

                    {/* Valor + Categoria */}
                    <div className="grid grid-cols-2 gap-3">
                        <div>
                            <label className="text-xs font-medium mb-1.5 block" style={{ color: C.muted }}>Valor (R$)</label>
                            <div className="relative">
                                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm font-semibold" style={{ color: C.avocado }}>R$</span>
                                <input
                                    type="text"
                                    inputMode="decimal"
                                    placeholder="0,00"
                                    value={valor}
                                    onChange={(e) => setValor(e.target.value)}
                                    required
                                    className="w-full rounded-xl pl-9 pr-3 py-2.5 text-sm outline-none"
                                    style={{ backgroundColor: C.elevated, border: `1px solid ${C.border}` }}
                                />
                            </div>
                        </div>
                        <div>
                            <label className="text-xs font-medium mb-1.5 block" style={{ color: C.muted }}>Categoria</label>
                            <select
                                value={categoriaId}
                                onChange={(e) => setCategoriaId(Number(e.target.value))}
                                required
                                className="w-full rounded-xl px-3 py-2.5 text-sm outline-none"
                                style={{ backgroundColor: C.elevated, border: `1px solid ${C.border}` }}
                            >
                                <option value="">Selecionar...</option>
                                {categoriasExibicao.map((c) => (
                                    <option key={c.id} value={c.id}>{c.nome}</option>
                                ))}
                            </select>
                        </div>
                    </div>

                    {/* ── Dívidas: selector de parcela ─────────────────────── */}
                    {isDividas && (
                        <div
                            className="rounded-xl p-4 space-y-3"
                            style={{ backgroundColor: `${C.danger}10`, border: `1px solid ${C.danger}30` }}
                        >
                            <div className="flex items-center gap-2">
                                <span className="text-base">💸</span>
                                <p className="text-xs font-semibold" style={{ color: C.danger }}>Vincular Dívida (opcional)</p>
                            </div>
                            <p className="text-xs" style={{ color: C.muted }}>
                                Selecione a qual dívida este pagamento pertence. A parcela será marcada como paga automaticamente.
                            </p>

                            {fetchingParcelas ? (
                                <div className="animate-pulse h-10 rounded-xl" style={{ backgroundColor: C.elevated }} />
                            ) : parcelasPendentes.length === 0 ? (
                                <p className="text-xs rounded-lg px-3 py-2" style={{ backgroundColor: C.elevated, color: C.muted }}>
                                    Nenhuma parcela pendente encontrada. Crie uma dívida na página <strong>Dívidas</strong>.
                                </p>
                            ) : (
                                <select
                                    value={parcelaId}
                                    onChange={e => setParcelaId(e.target.value ? Number(e.target.value) : "")}
                                    className="w-full rounded-xl px-3 py-2.5 text-sm outline-none"
                                    style={{ backgroundColor: C.elevated, border: `1px solid ${C.border}` }}
                                >
                                    <option value="">— Nenhuma (transação livre) —</option>
                                    {parcelasPendentes.map(p => (
                                        <option key={p.id} value={p.id}>{p.label}</option>
                                    ))}
                                </select>
                            )}

                            {parcelaId && (
                                <div className="flex items-center gap-2 text-xs font-medium" style={{ color: C.danger }}>
                                    <span>✓</span>
                                    <span>A parcela será marcada como <strong>paga</strong> ao registrar.</span>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Meta selector (only for investimentos category) */}
                    {isInvestimento && (
                        <div>
                            <label className="text-xs font-medium mb-1.5 block" style={{ color: C.muted }}>🎯 Vincular à Meta (opcional)</label>
                            <select value={metaId} onChange={e => setMetaId(e.target.value ? Number(e.target.value) : "")}
                                className="w-full rounded-xl px-3 py-2.5 text-sm outline-none"
                                style={{ backgroundColor: C.elevated, border: `1px solid ${C.border}` }}>
                                <option value="">Sem meta vinculada</option>
                                {metas.map(m => <option key={m.id} value={m.id}>{m.titulo}</option>)}
                            </select>
                            {metaId && <p className="text-xs mt-1" style={{ color: C.avocado }}>✓ O valor será adicionado ao progresso da meta.</p>}
                        </div>
                    )}

                    {/* Data + Recorrente */}
                    <div className="grid grid-cols-2 gap-3 items-end">
                        <div>
                            <label className="text-xs font-medium mb-1.5 block" style={{ color: C.muted }}>Data</label>
                            <input
                                type="date"
                                value={data}
                                onChange={(e) => setData(e.target.value)}
                                required
                                className="w-full rounded-xl px-3 py-2.5 text-sm outline-none"
                                style={{ backgroundColor: C.elevated, border: `1px solid ${C.border}` }}
                            />
                        </div>
                        <label className="flex items-center gap-2 cursor-pointer pb-2.5">
                            <div
                                onClick={() => setRecorrente(!recorrente)}
                                className="w-10 h-6 rounded-full relative transition-colors cursor-pointer"
                                style={{ backgroundColor: recorrente ? C.avocado : C.elevated, border: `1px solid ${C.border}` }}
                            >
                                <div
                                    className="absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform"
                                    style={{ transform: recorrente ? "translateX(18px)" : "translateX(2px)" }}
                                />
                            </div>
                            <span className="text-xs" style={{ color: C.muted }}>Recorrente</span>
                        </label>
                    </div>

                    {/* Observações */}
                    <div>
                        <label className="text-xs font-medium mb-1.5 block" style={{ color: C.muted }}>Observações (opcional)</label>
                        <textarea
                            value={obs}
                            onChange={(e) => setObs(e.target.value)}
                            rows={2}
                            placeholder="Detalhes adicionais..."
                            className="w-full rounded-xl px-3 py-2.5 text-sm outline-none resize-none"
                            style={{ backgroundColor: C.elevated, border: `1px solid ${C.border}` }}
                        />
                    </div>

                    {erro && <p className="text-xs text-red-400 bg-red-400/10 px-3 py-2 rounded-lg">{erro}</p>}

                    <div className="flex gap-3 pt-2">
                        <button
                            type="button"
                            onClick={handleClose}
                            className="flex-1 py-2.5 rounded-xl text-sm font-medium transition-opacity hover:opacity-80"
                            style={{ backgroundColor: C.elevated, color: C.muted, border: `1px solid ${C.border}` }}
                        >Cancelar</button>
                        <button
                            type="submit"
                            disabled={loading}
                            className="flex-1 py-2.5 rounded-xl text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-50"
                            style={{ backgroundColor: tipo === "saida" ? C.danger : C.avocado }}
                        >
                            {loading
                                ? "Salvando..."
                                : isDividas && parcelaId
                                    ? "Registrar + Dar Baixa"
                                    : "Registrar"}
                        </button>
                    </div>
                </form>
            </div>

            <style>{`
        @keyframes modal-in {
          from { opacity: 0; transform: scale(0.95) translateY(8px); }
          to   { opacity: 1; transform: scale(1) translateY(0); }
        }
      `}</style>
        </div>
    );
}
