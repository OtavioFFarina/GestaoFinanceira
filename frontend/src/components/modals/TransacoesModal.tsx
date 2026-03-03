"use client";

/**
 * TransacoesModal — shows all transactions for the current cycle with edit/delete.
 */
import { useEffect, useRef, useState } from "react";
import { API_BASE } from "@/lib/apiConfig";

const C = {
    surface: "var(--surface)", elevated: "var(--elevated)", border: "var(--border)",
    muted: "var(--muted)", text: "var(--text)", textSecondary: "var(--text-secondary)",
    avocado: "var(--avocado)", danger: "var(--danger)", warning: "var(--warning)",
};

interface Tx {
    id: number;
    descricao: string;
    valor: number;
    tipo: string;
    data_transacao: string;
    recorrente: boolean;
    observacoes: string | null;
    categoria_nome: string;
    categoria_cor: string | null;
    meta_titulo: string | null;
    created_at: string;
}

interface Props {
    isOpen: boolean;
    onClose: () => void;
    cicloId: number;
    onSuccess: () => void;
    mesLabel: string;
}

export default function TransacoesModal({ isOpen, onClose, cicloId, onSuccess, mesLabel }: Props) {
    const [txs, setTxs] = useState<Tx[]>([]);
    const [loading, setLoading] = useState(false);
    const [editingId, setEditingId] = useState<number | null>(null);
    const [editForm, setEditForm] = useState({ descricao: "", valor: "", observacoes: "" });
    const [saving, setSaving] = useState(false);
    const [deletingId, setDeletingId] = useState<number | null>(null);
    const overlayRef = useRef<HTMLDivElement>(null);

    const fetchTxs = () => {
        setLoading(true);
        fetch(`${API_BASE}/transacoes/${cicloId}`)
            .then(r => r.json()).then(setTxs).catch(console.error).finally(() => setLoading(false));
    };

    useEffect(() => {
        if (isOpen && cicloId) fetchTxs();
    }, [isOpen, cicloId]);

    const startEdit = (tx: Tx) => {
        setEditingId(tx.id);
        setEditForm({ descricao: tx.descricao, valor: String(tx.valor), observacoes: tx.observacoes ?? "" });
    };

    const saveEdit = async () => {
        if (!editingId) return;
        setSaving(true);
        await fetch(`${API_BASE}/transacoes/${editingId}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                descricao: editForm.descricao,
                valor: parseFloat(editForm.valor.replace(",", ".")),
                observacoes: editForm.observacoes || null,
            }),
        });
        setSaving(false);
        setEditingId(null);
        fetchTxs();
        onSuccess();
    };

    const deleteTx = async (id: number) => {
        setDeletingId(id);
        await fetch(`${API_BASE}/transacoes/${id}`, { method: "DELETE" });
        setDeletingId(null);
        fetchTxs();
        onSuccess();
    };

    const fmt = (v: number) => v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

    if (!isOpen) return null;

    return (
        <div ref={overlayRef}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
            style={{ backgroundColor: "rgba(0,0,0,0.75)", backdropFilter: "blur(4px)" }}
            onClick={e => { if (e.target === overlayRef.current) onClose(); }}>
            <div className="w-full max-w-2xl rounded-2xl p-6 shadow-2xl flex flex-col max-h-[90vh]"
                style={{ backgroundColor: "var(--bg)", border: `1px solid ${C.border}`, animation: "modal-in 0.2s ease-out" }}
                onClick={e => e.stopPropagation()}>

                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4" style={{ borderBottom: `1px solid ${C.border}` }}>
                    <div>
                        <h2 className="text-sm font-semibold">Transações — {mesLabel}</h2>
                        <p className="text-xs mt-0.5" style={{ color: C.muted }}>{txs.length} transações registradas</p>
                    </div>
                    <button onClick={onClose} className="w-7 h-7 rounded-lg flex items-center justify-center hover:opacity-70"
                        style={{ backgroundColor: C.elevated, color: C.muted }}>✕</button>
                </div>

                {/* List */}
                <div className="overflow-y-auto flex-1 px-4 py-3 space-y-2">
                    {loading ? (
                        <div className="text-center py-8" style={{ color: C.muted }}>Carregando...</div>
                    ) : txs.length === 0 ? (
                        <div className="text-center py-8" style={{ color: C.muted }}>Nenhuma transação neste mês.</div>
                    ) : txs.map(tx => (
                        <div key={tx.id} className="rounded-xl p-4" style={{ backgroundColor: C.surface, border: `1px solid ${C.border}` }}>
                            {editingId === tx.id ? (
                                /* Edit form */
                                <div className="space-y-3">
                                    <div className="grid grid-cols-2 gap-3">
                                        <div>
                                            <label className="text-xs block mb-1" style={{ color: C.muted }}>Descrição</label>
                                            <input value={editForm.descricao} onChange={e => setEditForm(f => ({ ...f, descricao: e.target.value }))}
                                                className="w-full rounded-lg px-3 py-2 text-sm text-white outline-none"
                                                style={{ backgroundColor: C.elevated, border: `1px solid ${C.border}` }} />
                                        </div>
                                        <div>
                                            <label className="text-xs block mb-1" style={{ color: C.muted }}>Valor (R$)</label>
                                            <input value={editForm.valor} onChange={e => setEditForm(f => ({ ...f, valor: e.target.value }))}
                                                className="w-full rounded-lg px-3 py-2 text-sm text-white outline-none"
                                                style={{ backgroundColor: C.elevated, border: `1px solid ${C.border}` }} />
                                        </div>
                                    </div>
                                    <div>
                                        <label className="text-xs block mb-1" style={{ color: C.muted }}>Observações</label>
                                        <textarea value={editForm.observacoes} onChange={e => setEditForm(f => ({ ...f, observacoes: e.target.value }))}
                                            rows={2} className="w-full rounded-lg px-3 py-2 text-sm text-white outline-none resize-none"
                                            style={{ backgroundColor: C.elevated, border: `1px solid ${C.border}` }} />
                                    </div>
                                    <div className="flex gap-2">
                                        <button onClick={() => setEditingId(null)} className="flex-1 py-2 rounded-lg text-xs hover:opacity-70"
                                            style={{ backgroundColor: C.elevated, color: C.muted, border: `1px solid ${C.border}` }}>Cancelar</button>
                                        <button onClick={saveEdit} disabled={saving} className="flex-1 py-2 rounded-lg text-xs font-semibold text-white hover:opacity-90 disabled:opacity-50"
                                            style={{ backgroundColor: C.avocado }}>{saving ? "..." : "Salvar"}</button>
                                    </div>
                                </div>
                            ) : (
                                /* View row */
                                <div className="flex items-start gap-3">
                                    <div className="w-2.5 h-2.5 rounded-full mt-1.5 flex-shrink-0"
                                        style={{ backgroundColor: tx.categoria_cor ?? C.muted }} />
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center justify-between gap-2">
                                            <span className="text-sm font-medium truncate">{tx.descricao}</span>
                                            <span className="text-sm font-semibold flex-shrink-0" style={{ color: tx.tipo === "entrada" ? C.avocado : C.text }}>
                                                {tx.tipo === "entrada" ? "+" : "-"}{fmt(tx.valor)}
                                            </span>
                                        </div>
                                        <div className="flex items-center gap-2 mt-0.5 text-xs flex-wrap" style={{ color: C.muted }}>
                                            <span style={{ color: tx.categoria_cor ?? C.muted }}>{tx.categoria_nome}</span>
                                            <span>·</span>
                                            <span>{new Date(tx.data_transacao).toLocaleDateString("pt-BR")}</span>
                                            {tx.recorrente && <><span>·</span><span className="text-yellow-400">↻ Recorrente</span></>}
                                            {tx.meta_titulo && <><span>·</span><span style={{ color: C.avocado }}>🎯 {tx.meta_titulo}</span></>}
                                        </div>
                                        {tx.observacoes && (
                                            <p className="text-xs mt-1.5 italic rounded-lg px-2 py-1.5"
                                                style={{ backgroundColor: C.elevated, color: C.muted }}>
                                                💬 {tx.observacoes}
                                            </p>
                                        )}
                                    </div>
                                    <div className="flex gap-1.5 flex-shrink-0">
                                        <button onClick={() => startEdit(tx)}
                                            className="w-7 h-7 rounded-lg flex items-center justify-center text-sm hover:opacity-80 transition-opacity"
                                            style={{ backgroundColor: `${C.avocado}20`, color: C.avocado }}>✏️</button>
                                        <button onClick={() => deleteTx(tx.id)} disabled={deletingId === tx.id}
                                            className="w-7 h-7 rounded-lg flex items-center justify-center text-sm hover:opacity-80 transition-opacity disabled:opacity-30"
                                            style={{ backgroundColor: `${C.danger}20`, color: C.danger }}>
                                            {deletingId === tx.id ? "..." : "🗑️"}
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    ))}
                </div>

                {/* Footer summary */}
                {txs.length > 0 && (
                    <div className="px-6 py-3 flex justify-between text-sm" style={{ borderTop: `1px solid ${C.border}`, color: C.muted }}>
                        <span>Total de saídas:</span>
                        <span className="font-semibold">
                            {fmt(txs.filter(t => t.tipo === "saida").reduce((a, t) => a + t.valor, 0))}
                        </span>
                    </div>
                )}
            </div>

            <style>{`
        @keyframes modal-in {
          from { opacity: 0; transform: scale(0.97) translateY(8px); }
          to { opacity: 1; transform: scale(1) translateY(0); }
        }
      `}</style>
        </div>
    );
}
