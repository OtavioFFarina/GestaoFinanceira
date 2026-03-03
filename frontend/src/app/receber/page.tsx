"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import AppNav from "@/components/layout/AppNav";
import GlobalLoader from "@/components/ui/GlobalLoader";
import { API_BASE } from "@/lib/apiConfig";

const C = {
    bg: "var(--bg)", surface: "var(--surface)", elevated: "var(--elevated)",
    border: "var(--border)", muted: "var(--muted)", text: "var(--text)",
    avocado: "var(--avocado)", avocadoLight: "var(--avocado-light)",
    danger: "var(--danger)", warning: "var(--warning)", success: "var(--success)",
};


interface Parcela {
    id: number;
    contrato_id: number;
    numero_parcela: number;
    valor_parcela: number;
    data_vencimento: string;
    data_pagamento: string | null;
    status: "pendente" | "paga" | "atrasada";
}

interface Contrato {
    id: number;
    descricao: string;
    valor_total: number;
    num_parcelas: number;
    status: string;
    data_primeiro_vencimento: string;
    parcelas_pagas: number;
    parcelas_pendentes: number;
    parcelas_atrasadas: number;
    proximo_vencimento: string | null;
    proximo_valor: number | null;
}

interface Resumo {
    total_pagar_mes: number;
    contratos_pagar_ativos: number;
    proximo_vencimento_pagar: string | null;
    total_receber_mes: number;
    contratos_receber_ativos: number;
    proximo_vencimento_receber: string | null;
}

const fmt = (v: number) => v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
const fmtDate = (d: string) => new Date(d + "T00:00:00").toLocaleDateString("pt-BR");

function StatusBadge({ status }: { status: string }) {
    const map: Record<string, { bg: string; color: string; label: string }> = {
        pendente: { bg: `${C.warning}22`, color: C.warning, label: "Pendente" },
        paga: { bg: `${C.success}22`, color: C.success, label: "Recebido" },
        atrasada: { bg: `${C.danger}22`, color: C.danger, label: "Atrasado" },
        ativo: { bg: `${C.avocado}22`, color: C.avocado, label: "Ativo" },
        quitado: { bg: `${C.success}22`, color: C.success, label: "Quitado" },
        cancelado: { bg: `${C.muted}22`, color: C.muted, label: "Cancelado" },
    };
    const cfg = map[status] ?? { bg: `${C.muted}22`, color: C.muted, label: status };
    return (
        <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-semibold"
            style={{ backgroundColor: cfg.bg, color: cfg.color }}>
            {cfg.label}
        </span>
    );
}

function Skeleton({ className = "" }: { className?: string }) {
    return <div className={`animate-pulse rounded-xl ${className}`} style={{ backgroundColor: C.elevated }} />;
}

function SummaryCard({ icon, label, value, sub, highlight }: {
    icon: string; label: string; value: string; sub?: string; highlight?: boolean;
}) {
    return (
        <div className="rounded-2xl p-5 flex flex-col gap-2"
            style={{ backgroundColor: C.surface, border: `1px solid ${highlight ? C.avocado + "60" : C.border}` }}>
            <div className="flex items-center gap-2" style={{ color: C.muted }}>
                <span className="text-lg">{icon}</span>
                <span className="text-xs font-medium">{label}</span>
            </div>
            <p className="text-2xl font-bold" style={{ color: highlight ? C.avocado : C.text }}>{value}</p>
            {sub && <p className="text-xs" style={{ color: C.muted }}>{sub}</p>}
        </div>
    );
}

export default function ReceberPage() {
    const { user, loading: authLoading } = useAuth();
    const router = useRouter();

    const [contratos, setContratos] = useState<Contrato[]>([]);
    const [resumo, setResumo] = useState<Resumo | null>(null);
    const [loading, setLoading] = useState(true);
    const [expandedId, setExpandedId] = useState<number | null>(null);
    const [expandedParcelas, setExpandedParcelas] = useState<Parcela[]>([]);
    const [loadingParcelas, setLoadingParcelas] = useState(false);

    const [showModal, setShowModal] = useState(false);
    const [form, setForm] = useState({ descricao: "", valor_total: "", num_parcelas: "1", data_primeiro_vencimento: "", observacoes: "" });
    const [saving, setSaving] = useState(false);
    const [formErro, setFormErro] = useState<string | null>(null);

    const [baixaTarget, setBaixaTarget] = useState<Parcela | null>(null);
    const [doingBaixa, setDoingBaixa] = useState(false);

    useEffect(() => {
        if (!authLoading && !user) router.replace("/login");
    }, [user, authLoading, router]);

    const fetchData = () => {
        if (!user) return;
        setLoading(true);
        Promise.all([
            fetch(`${API_BASE}/contratos/${user.usuario_id}?tipo=receber`).then(r => r.json()),
            fetch(`${API_BASE}/contratos/${user.usuario_id}/resumo`).then(r => r.json()),
        ])
            .then(([c, r]) => { setContratos(c); setResumo(r); })
            .catch(console.error)
            .finally(() => setLoading(false));
    };

    useEffect(() => { fetchData(); }, [user]);

    const toggleExpand = async (id: number) => {
        if (expandedId === id) { setExpandedId(null); return; }
        setExpandedId(id);
        setLoadingParcelas(true);
        try {
            const res = await fetch(`${API_BASE}/contratos/detalhe/${id}`);
            const data = await res.json();
            setExpandedParcelas(data.parcelas ?? []);
        } catch { setExpandedParcelas([]); }
        setLoadingParcelas(false);
    };

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!user) return;
        setSaving(true); setFormErro(null);
        try {
            const res = await fetch(`${API_BASE}/contratos`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    usuario_id: user.usuario_id,
                    tipo: "receber",
                    descricao: form.descricao,
                    valor_total: parseFloat(form.valor_total.replace(",", ".")),
                    num_parcelas: parseInt(form.num_parcelas),
                    data_primeiro_vencimento: form.data_primeiro_vencimento,
                    observacoes: form.observacoes || null,
                }),
            });
            if (!res.ok) { const e = await res.json(); throw new Error(e.detail ?? "Erro ao criar."); }
            setShowModal(false);
            setForm({ descricao: "", valor_total: "", num_parcelas: "1", data_primeiro_vencimento: "", observacoes: "" });
            setExpandedId(null);
            fetchData();
        } catch (err) {
            setFormErro(err instanceof Error ? err.message : "Erro inesperado.");
        } finally { setSaving(false); }
    };

    const handleBaixa = async () => {
        if (!baixaTarget) return;
        setDoingBaixa(true);
        try {
            await fetch(`${API_BASE}/parcelas/${baixaTarget.id}/baixa`, { method: "PATCH" });
            setBaixaTarget(null);
            if (expandedId) {
                const res = await fetch(`${API_BASE}/contratos/detalhe/${expandedId}`);
                const data = await res.json();
                setExpandedParcelas(data.parcelas ?? []);
            }
            fetchData();
        } catch { alert("Erro ao confirmar recebimento."); }
        setDoingBaixa(false);
    };

    const handleDelete = async (id: number) => {
        if (!confirm("Excluir este recebível e todas as suas parcelas?")) return;
        await fetch(`${API_BASE}/contratos/${id}`, { method: "DELETE" });
        setExpandedId(null);
        fetchData();
    };

    if (authLoading) return <GlobalLoader />;
    if (!user) return null;

    const totalReceber = resumo?.total_receber_mes ?? 0;
    const ativos = resumo?.contratos_receber_ativos ?? 0;
    const proxVcto = resumo?.proximo_vencimento_receber;

    return (
        <div className="min-h-screen font-sans antialiased" style={{ backgroundColor: C.bg, color: C.text }}>
            <AppNav activeItem="Receber" />

            <main className="max-w-5xl mx-auto px-4 md:px-6 py-6 md:py-8">
                {/* ── Header ── */}
                <div className="flex items-end justify-between mt-1 mb-6">
                    <div>
                        <h1 className="text-2xl font-bold">Contas a Receber</h1>
                        <p className="text-sm mt-1" style={{ color: C.muted }}>Valores que terceiros te devem</p>
                    </div>
                    <button onClick={() => setShowModal(true)}
                        className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold text-white hover:opacity-90 transition-opacity"
                        style={{ backgroundColor: C.avocado }}>
                        + Novo Recebível
                    </button>
                </div>

                {/* ── Summary Cards ── */}
                {loading ? (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                        {[...Array(3)].map((_, i) => <Skeleton key={i} className="h-28" />)}
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                        <SummaryCard icon="💰" label="A receber este mês" value={fmt(totalReceber)} highlight={totalReceber > 0} />
                        <SummaryCard icon="📅" label="Próximo recebimento" value={proxVcto ? fmtDate(proxVcto) : "—"} />
                        <SummaryCard icon="👤" label="Devedores ativos" value={String(ativos)} sub="recebíveis em aberto" />
                    </div>
                )}

                {/* ── Contracts table ── */}
                {loading ? (
                    <div className="flex flex-col gap-3">
                        {[...Array(3)].map((_, i) => <Skeleton key={i} className="h-20" />)}
                    </div>
                ) : contratos.length === 0 ? (
                    <div className="text-center py-20" style={{ color: C.muted }}>
                        <p className="text-4xl mb-3">💰</p>
                        <p className="text-lg font-medium" style={{ color: C.text }}>Nenhum recebível cadastrado</p>
                        <p className="text-sm mt-1">Clique em &quot;+ Novo Recebível&quot; para registrar um valor a receber.</p>
                    </div>
                ) : (
                    <div className="flex flex-col gap-3">
                        {contratos.map(c => (
                            <div key={c.id} className="rounded-2xl overflow-hidden"
                                style={{ backgroundColor: C.surface, border: `1px solid ${c.parcelas_atrasadas > 0 ? C.warning + "50" : c.status === "quitado" ? C.avocado + "40" : C.border}` }}>

                                {/* Contract header */}
                                <div className="flex items-center gap-4 px-5 py-4 cursor-pointer hover:opacity-90 transition-opacity"
                                    onClick={() => toggleExpand(c.id)}>
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2 flex-wrap">
                                            <p className="text-sm font-semibold truncate">{c.descricao}</p>
                                            <StatusBadge status={c.status} />
                                            {c.parcelas_atrasadas > 0 && <StatusBadge status="atrasada" />}
                                        </div>
                                        <p className="text-xs mt-0.5" style={{ color: C.muted }}>
                                            {c.parcelas_pagas}/{c.num_parcelas} recebidos
                                            {c.proximo_vencimento && ` · Próximo: ${fmtDate(c.proximo_vencimento)}`}
                                        </p>
                                    </div>
                                    <div className="text-right flex-shrink-0">
                                        <p className="text-sm font-bold" style={{ color: C.avocado }}>{fmt(c.valor_total)}</p>
                                        {c.proximo_valor && (
                                            <p className="text-xs" style={{ color: C.muted }}>Próximo: {fmt(c.proximo_valor)}</p>
                                        )}
                                    </div>
                                    <span className="text-xs flex-shrink-0" style={{ color: C.muted }}>
                                        {expandedId === c.id ? "▲" : "▼"}
                                    </span>
                                </div>

                                {expandedId === c.id && (
                                    <div style={{ borderTop: `1px solid ${C.border}` }}>
                                        {loadingParcelas ? (
                                            <div className="p-4 flex flex-col gap-2">
                                                {[...Array(3)].map((_, i) => <Skeleton key={i} className="h-10" />)}
                                            </div>
                                        ) : (
                                            <div className="overflow-x-auto">
                                                <table className="w-full text-sm">
                                                    <thead>
                                                        <tr className="text-xs" style={{ color: C.muted, borderBottom: `1px solid ${C.border}` }}>
                                                            <th className="px-5 py-2.5 text-left font-medium">#</th>
                                                            <th className="px-5 py-2.5 text-left font-medium">Vencimento</th>
                                                            <th className="px-5 py-2.5 text-left font-medium">Valor</th>
                                                            <th className="px-5 py-2.5 text-left font-medium">Status</th>
                                                            <th className="px-5 py-2.5 text-left font-medium">Recebido em</th>
                                                            <th className="px-5 py-2.5 text-right font-medium">Ação</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody>
                                                        {expandedParcelas.map(p => (
                                                            <tr key={p.id} style={{ borderBottom: `1px solid ${C.border}20` }}>
                                                                <td className="px-5 py-3" style={{ color: C.muted }}>{p.numero_parcela}/{expandedParcelas.length}</td>
                                                                <td className="px-5 py-3">{fmtDate(p.data_vencimento)}</td>
                                                                <td className="px-5 py-3 font-medium">{fmt(p.valor_parcela)}</td>
                                                                <td className="px-5 py-3"><StatusBadge status={p.status} /></td>
                                                                <td className="px-5 py-3 text-xs" style={{ color: C.muted }}>
                                                                    {p.data_pagamento ? fmtDate(p.data_pagamento) : "—"}
                                                                </td>
                                                                <td className="px-5 py-3 text-right">
                                                                    {p.status !== "paga" && (
                                                                        <button onClick={() => setBaixaTarget(p)}
                                                                            className="text-xs px-3 py-1 rounded-lg font-semibold hover:opacity-80 transition-opacity"
                                                                            style={{ backgroundColor: `${C.avocado}22`, color: C.avocado }}>
                                                                            Confirmar
                                                                        </button>
                                                                    )}
                                                                </td>
                                                            </tr>
                                                        ))}
                                                    </tbody>
                                                </table>
                                                {c.status !== "quitado" && (
                                                    <div className="px-5 py-3 flex justify-end">
                                                        <button onClick={() => handleDelete(c.id)}
                                                            className="text-xs px-3 py-1 rounded-lg hover:opacity-80 transition-opacity"
                                                            style={{ backgroundColor: `${C.danger}18`, color: C.danger }}>
                                                            🗑️ Excluir Recebível
                                                        </button>
                                                    </div>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </main>

            {/* ── Modal Novo Recebível ── */}
            {showModal && (
                <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center sm:p-4 bg-black/50 backdrop-blur-sm"
                    onClick={() => setShowModal(false)}>
                    <div className="w-full sm:max-w-md rounded-t-2xl sm:rounded-2xl shadow-2xl overflow-hidden max-h-[92dvh] overflow-y-auto"
                        style={{ backgroundColor: C.elevated, border: `1px solid ${C.border}`, animation: "modal-in 0.2s ease-out" }}
                        onClick={e => e.stopPropagation()}>

                        <div className="px-6 py-4 flex items-center justify-between" style={{ borderBottom: `1px solid ${C.border}` }}>
                            <div>
                                <h2 className="text-base font-bold">Novo Recebível</h2>
                                <p className="text-xs mt-0.5" style={{ color: C.muted }}>Registre um valor que te devem</p>
                            </div>
                            <button onClick={() => setShowModal(false)} className="text-xl w-8 h-8 flex items-center justify-center rounded-lg hover:opacity-70"
                                style={{ color: C.muted }}>×</button>
                        </div>

                        <form onSubmit={handleCreate} className="px-6 py-5 flex flex-col gap-4">
                            <div>
                                <label className="text-xs font-medium block mb-1.5" style={{ color: C.muted }}>Devedor / Descrição *</label>
                                <input value={form.descricao} onChange={e => setForm(f => ({ ...f, descricao: e.target.value }))}
                                    placeholder="Ex: João - empréstimo pessoal, Contrato de serviço..."
                                    required className="w-full rounded-xl px-3 py-2.5 text-sm outline-none"
                                    style={{ backgroundColor: C.surface, border: `1px solid ${C.border}`, color: C.text }} />
                            </div>

                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <label className="text-xs font-medium block mb-1.5" style={{ color: C.muted }}>Valor Total (R$) *</label>
                                    <input value={form.valor_total} onChange={e => setForm(f => ({ ...f, valor_total: e.target.value }))}
                                        placeholder="0,00" required type="text" inputMode="decimal"
                                        className="w-full rounded-xl px-3 py-2.5 text-sm outline-none"
                                        style={{ backgroundColor: C.surface, border: `1px solid ${C.border}`, color: C.text }} />
                                </div>
                                <div>
                                    <label className="text-xs font-medium block mb-1.5" style={{ color: C.muted }}>Nº de Parcelas *</label>
                                    <input value={form.num_parcelas} onChange={e => setForm(f => ({ ...f, num_parcelas: e.target.value }))}
                                        type="number" min="1" max="60" required
                                        className="w-full rounded-xl px-3 py-2.5 text-sm outline-none"
                                        style={{ backgroundColor: C.surface, border: `1px solid ${C.border}`, color: C.text }} />
                                </div>
                            </div>

                            <div>
                                <label className="text-xs font-medium block mb-1.5" style={{ color: C.muted }}>1º Vencimento *</label>
                                <input value={form.data_primeiro_vencimento} onChange={e => setForm(f => ({ ...f, data_primeiro_vencimento: e.target.value }))}
                                    type="date" required className="w-full rounded-xl px-3 py-2.5 text-sm outline-none"
                                    style={{ backgroundColor: C.surface, border: `1px solid ${C.border}`, color: C.text, colorScheme: "dark" }} />
                            </div>

                            <div>
                                <label className="text-xs font-medium block mb-1.5" style={{ color: C.muted }}>Observações</label>
                                <textarea value={form.observacoes} onChange={e => setForm(f => ({ ...f, observacoes: e.target.value }))}
                                    placeholder="Notas adicionais..." rows={2}
                                    className="w-full rounded-xl px-3 py-2.5 text-sm outline-none resize-none"
                                    style={{ backgroundColor: C.surface, border: `1px solid ${C.border}`, color: C.text }} />
                            </div>

                            {form.valor_total && form.num_parcelas && (
                                <div className="rounded-xl px-3 py-2.5 text-xs"
                                    style={{ backgroundColor: `${C.avocado}12`, color: C.avocadoLight, border: `1px solid ${C.avocado}30` }}>
                                    💰 {parseInt(form.num_parcelas)}x de aprox.{" "}
                                    <strong>{fmt(parseFloat(form.valor_total.replace(",", ".") || "0") / parseInt(form.num_parcelas || "1"))}</strong>
                                </div>
                            )}

                            {formErro && (
                                <p className="text-xs rounded-lg px-3 py-2" style={{ backgroundColor: `${C.danger}18`, color: C.danger }}>{formErro}</p>
                            )}

                            <div className="flex gap-3 pt-1">
                                <button type="button" onClick={() => setShowModal(false)}
                                    className="flex-1 py-2.5 rounded-xl text-sm hover:opacity-80"
                                    style={{ backgroundColor: C.surface, color: C.muted, border: `1px solid ${C.border}` }}>
                                    Cancelar
                                </button>
                                <button type="submit" disabled={saving}
                                    className="flex-1 py-2.5 rounded-xl text-sm font-semibold text-white hover:opacity-90 disabled:opacity-50"
                                    style={{ backgroundColor: C.avocado }}>
                                    {saving ? "Salvando..." : "Criar Recebível"}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* ── Modal Confirmar Recebimento ── */}
            {baixaTarget && (
                <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center sm:p-4 bg-black/50 backdrop-blur-sm"
                    onClick={() => setBaixaTarget(null)}>
                    <div className="w-full sm:max-w-sm rounded-t-2xl sm:rounded-2xl p-6 shadow-2xl"
                        style={{ backgroundColor: C.elevated, border: `1px solid ${C.border}`, animation: "modal-in 0.2s ease-out" }}
                        onClick={e => e.stopPropagation()}>
                        <h2 className="text-base font-bold mb-1">Confirmar Recebimento</h2>
                        <p className="text-sm mb-4" style={{ color: C.muted }}>
                            Confirmar recebimento da parcela <strong style={{ color: C.text }}>#{baixaTarget.numero_parcela}</strong> de{" "}
                            <strong style={{ color: C.avocado }}>{fmt(baixaTarget.valor_parcela)}</strong>{" "}
                            (vencimento {fmtDate(baixaTarget.data_vencimento)})?
                        </p>
                        <div className="flex gap-3">
                            <button onClick={() => setBaixaTarget(null)}
                                className="flex-1 py-2.5 rounded-xl text-sm hover:opacity-80"
                                style={{ backgroundColor: C.surface, color: C.muted, border: `1px solid ${C.border}` }}>
                                Cancelar
                            </button>
                            <button onClick={handleBaixa} disabled={doingBaixa}
                                className="flex-1 py-2.5 rounded-xl text-sm font-semibold text-white hover:opacity-90 disabled:opacity-50"
                                style={{ backgroundColor: C.avocado }}>
                                {doingBaixa ? "Confirmando..." : "✓ Recebido"}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            <style>{`
        @keyframes modal-in {
          from { opacity: 0; transform: translateY(10px) scale(0.97); }
          to   { opacity: 1; transform: translateY(0) scale(1); }
        }
      `}</style>
        </div>
    );
}
