"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import AppNav from "@/components/layout/AppNav";
import GlobalLoader from "@/components/ui/GlobalLoader";
import { API_BASE } from "@/lib/apiConfig";

const C = {
    bg: "var(--bg)", surface: "var(--surface)", elevated: "var(--elevated)",
    border: "var(--border)", muted: "var(--muted)", avocado: "var(--avocado)",
    avocadoLight: "var(--avocado-light)", danger: "var(--danger)", warning: "var(--warning)",
};


interface Meta {
    id: number;
    titulo: string;
    descricao: string | null;
    valor_alvo: number;
    valor_atual: number;
    prazo: string;
    status: string;
    percentual: number;
    ia_dicas: string | null;
}

function Skeleton({ className = "" }: { className?: string }) {
    return <div className={`animate-pulse rounded-xl ${className}`} style={{ backgroundColor: C.elevated }} />;
}

export default function MetasPage() {
    const { user, loading: authLoading } = useAuth();
    const router = useRouter();
    const [metas, setMetas] = useState<Meta[]>([]);
    const [loading, setLoading] = useState(true);
    const [showForm, setShowForm] = useState(false);
    const [form, setForm] = useState({ titulo: "", descricao: "", valor_alvo: "", valor_atual: "0", prazo: "" });
    const [saving, setSaving] = useState(false);
    const [erro, setErro] = useState<string | null>(null);
    const [selectedMeta, setSelectedMeta] = useState<Meta | null>(null);
    const [showConfetti, setShowConfetti] = useState(false);

    useEffect(() => {
        if (!authLoading && !user) router.replace("/login");
    }, [user, authLoading, router]);

    const fetchMetas = () => {
        if (!user) return;
        fetch(`${API_BASE}/metas/${user.usuario_id}`)
            .then(r => r.json()).then(setMetas).catch(console.error).finally(() => setLoading(false));
    };

    useEffect(() => { fetchMetas(); }, [user]);

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!user) return;
        setSaving(true); setErro(null);
        try {
            const res = await fetch(`${API_BASE}/metas/${user.usuario_id}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    titulo: form.titulo,
                    descricao: form.descricao || null,
                    valor_alvo: parseFloat(form.valor_alvo.replace(",", ".")),
                    valor_atual: parseFloat(form.valor_atual.replace(",", ".")) || 0,
                    prazo: form.prazo,
                }),
            });
            if (!res.ok) throw new Error("Erro ao criar meta.");
            setShowForm(false);
            setForm({ titulo: "", descricao: "", valor_alvo: "", valor_atual: "0", prazo: "" });
            fetchMetas();
        } catch (err) {
            setErro(err instanceof Error ? err.message : "Erro.");
        } finally { setSaving(false); }
    };

    const updateStatus = async (status: string) => {
        if (!user || !selectedMeta) return;
        try {
            const res = await fetch(`${API_BASE}/metas/${user.usuario_id}/${selectedMeta.id}`, {
                method: "PATCH", headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ status })
            });
            if (!res.ok) throw new Error();
            setSelectedMeta(null);
            fetchMetas();
            if (status === "concluida") {
                setShowConfetti(true);
                setTimeout(() => setShowConfetti(false), 3000);
            }
        } catch { alert("Erro ao atualizar."); }
    };

    const deleteMeta = async () => {
        if (!user || !selectedMeta) return;
        if (!confirm("Excluir esta meta permanentemente?")) return;
        try {
            await fetch(`${API_BASE}/metas/${user.usuario_id}/${selectedMeta.id}`, { method: "DELETE" });
            setSelectedMeta(null);
            fetchMetas();
        } catch { alert("Erro ao excluir."); }
    };

    const fmt = (v: number) => v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
    const daysLeft = (prazo: string) => Math.ceil((new Date(prazo).getTime() - Date.now()) / 86400000);


    if (authLoading) return <GlobalLoader />;
    if (!user) return null;

    return (
        <div className="min-h-screen font-sans antialiased" style={{ backgroundColor: "var(--bg)", color: "var(--text)" }}>
            <AppNav activeItem="Metas" />

            <main className="max-w-5xl mx-auto px-4 md:px-6 py-6 md:py-8">
                <div className="flex items-end justify-between mt-1 mb-6">
                    <h1 className="text-2xl font-bold">Metas Financeiras</h1>
                    <button onClick={() => setShowForm(s => !s)}
                        className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium text-white hover:opacity-90 transition-opacity"
                        style={{ backgroundColor: C.avocado }}>
                        + Nova Meta
                    </button>
                </div>

                {/* New Goal Form */}
                {showForm && (
                    <div className="rounded-2xl p-5 mb-6" style={{ backgroundColor: C.surface, border: `1px solid ${C.border}`, animation: "modal-in 0.2s ease-out" }}>
                        <h2 className="text-sm font-semibold text-white mb-4">Criar Nova Meta</h2>
                        <form onSubmit={handleCreate} className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            <div className="md:col-span-2">
                                <label className="text-xs font-medium block mb-1" style={{ color: C.muted }}>Título *</label>
                                <input value={form.titulo} onChange={e => setForm(f => ({ ...f, titulo: e.target.value }))}
                                    placeholder="Ex: Fundo de emergência" required
                                    className="w-full rounded-xl px-3 py-2.5 text-sm text-white outline-none"
                                    style={{ backgroundColor: C.elevated, border: `1px solid ${C.border}` }} />
                            </div>
                            <div>
                                <label className="text-xs font-medium block mb-1" style={{ color: C.muted }}>Valor Alvo (R$) *</label>
                                <input value={form.valor_alvo} onChange={e => setForm(f => ({ ...f, valor_alvo: e.target.value }))}
                                    placeholder="0,00" required
                                    className="w-full rounded-xl px-3 py-2.5 text-sm text-white outline-none"
                                    style={{ backgroundColor: C.elevated, border: `1px solid ${C.border}` }} />
                            </div>
                            <div>
                                <label className="text-xs font-medium block mb-1" style={{ color: C.muted }}>Já tenho (R$)</label>
                                <input value={form.valor_atual} onChange={e => setForm(f => ({ ...f, valor_atual: e.target.value }))}
                                    placeholder="0,00"
                                    className="w-full rounded-xl px-3 py-2.5 text-sm text-white outline-none"
                                    style={{ backgroundColor: C.elevated, border: `1px solid ${C.border}` }} />
                            </div>
                            <div>
                                <label className="text-xs font-medium block mb-1" style={{ color: C.muted }}>Prazo *</label>
                                <input type="date" value={form.prazo} onChange={e => setForm(f => ({ ...f, prazo: e.target.value }))} required
                                    className="w-full rounded-xl px-3 py-2.5 text-sm text-white outline-none"
                                    style={{ backgroundColor: C.elevated, border: `1px solid ${C.border}`, colorScheme: "dark" }} />
                            </div>
                            <div>
                                <label className="text-xs font-medium block mb-1" style={{ color: C.muted }}>Descrição (opcional)</label>
                                <input value={form.descricao} onChange={e => setForm(f => ({ ...f, descricao: e.target.value }))}
                                    placeholder="Ex: Para emergências..."
                                    className="w-full rounded-xl px-3 py-2.5 text-sm text-white outline-none"
                                    style={{ backgroundColor: C.elevated, border: `1px solid ${C.border}` }} />
                            </div>
                            {erro && <p className="md:col-span-2 text-xs text-red-400 bg-red-400/10 px-3 py-2 rounded-lg">{erro}</p>}
                            <div className="md:col-span-2 flex gap-3">
                                <button type="button" onClick={() => setShowForm(false)}
                                    className="flex-1 py-2.5 rounded-xl text-sm hover:opacity-80"
                                    style={{ backgroundColor: C.elevated, color: C.muted, border: `1px solid ${C.border}` }}>Cancelar</button>
                                <button type="submit" disabled={saving}
                                    className="flex-1 py-2.5 rounded-xl text-sm font-semibold text-white hover:opacity-90 disabled:opacity-50"
                                    style={{ backgroundColor: C.avocado }}>{saving ? "Salvando..." : "Criar Meta"}</button>
                            </div>
                        </form>
                    </div>
                )}

                {/* Goals list */}
                {loading ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-52" />)}
                    </div>
                ) : metas.length === 0 ? (
                    <div className="text-center py-20" style={{ color: C.muted }}>
                        <p className="text-4xl mb-3">🎯</p>
                        <p className="text-lg font-medium text-white">Nenhuma meta criada</p>
                        <p className="text-sm mt-1">Defina metas para organizar seu futuro financeiro.</p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {metas.map(m => {
                            const days = daysLeft(m.prazo);
                            const completed = m.status === "concluida";
                            const barColor = completed ? C.avocado : m.percentual >= 100 ? C.avocado : m.percentual >= 50 ? C.warning : C.danger;
                            return (
                                <div key={m.id} onClick={() => setSelectedMeta(m)} className="rounded-2xl p-5 flex flex-col gap-3 cursor-pointer transition-transform hover:scale-[1.02]"
                                    style={{ backgroundColor: "var(--surface)", border: `1px solid ${completed ? "var(--avocado)40" : "var(--border)"}` }}>
                                    <div className="flex items-start justify-between gap-2">
                                        <div>
                                            <p className="text-sm font-semibold">{m.titulo}</p>
                                            {m.descricao && <p className="text-xs mt-0.5 line-clamp-1" style={{ color: C.muted }}>{m.descricao}</p>}
                                        </div>
                                        <span className="text-xs px-2 py-1 rounded-md flex-shrink-0 font-medium"
                                            style={{
                                                backgroundColor: completed ? `${C.avocado}20` : m.status === "cancelada" ? `${C.danger}20` : `${C.warning}20`,
                                                color: completed ? C.avocado : m.status === "cancelada" ? C.danger : C.warning,
                                            }}>
                                            {completed ? "✓ Concluída" : m.status === "cancelada" ? "Cancelada" : "Ativa"}
                                        </span>
                                    </div>

                                    {/* Progress */}
                                    <div>
                                        <div className="flex justify-between text-xs mb-1.5">
                                            <span style={{ color: C.muted }}>{fmt(m.valor_atual)} de {fmt(m.valor_alvo)}</span>
                                            <span className="font-semibold" style={{ color: barColor }}>{m.percentual.toFixed(1)}%</span>
                                        </div>
                                        <div className="h-2 rounded-full overflow-hidden" style={{ backgroundColor: C.elevated }}>
                                            <div className="h-full rounded-full transition-all"
                                                style={{ width: `${Math.min(m.percentual, 100)}%`, backgroundColor: barColor }} />
                                        </div>
                                    </div>

                                    {/* Deadline */}
                                    <div className="flex justify-between items-center text-xs" style={{ color: C.muted }}>
                                        <span>Prazo: {new Date(m.prazo).toLocaleDateString("pt-BR")}</span>
                                        {!completed && (
                                            <span style={{ color: days < 30 ? C.danger : days < 90 ? C.warning : C.muted }}>
                                                {days > 0 ? `${days} dias restantes` : "Prazo vencido"}
                                            </span>
                                        )}
                                    </div>

                                    {/* AI tips */}
                                    {m.ia_dicas && (
                                        <div className="rounded-xl px-3 py-2.5 text-xs" style={{ backgroundColor: `${C.avocado}14`, color: C.avocadoLight, border: `1px solid ${C.avocado}30` }}>
                                            🤖 <strong>Dica da IA:</strong>{" "}
                                            {(() => {
                                                try { const arr = JSON.parse(m.ia_dicas!); return Array.isArray(arr) ? arr[0] : m.ia_dicas; }
                                                catch { return m.ia_dicas; }
                                            })()}
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                )}
            </main>

            {/* Meta Action Modal */}
            {selectedMeta && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm" onClick={() => setSelectedMeta(null)}>
                    <div className="w-full max-w-sm rounded-2xl p-6 shadow-2xl" style={{ backgroundColor: "var(--elevated)", border: "1px solid var(--border)", animation: "modal-in 0.2s ease-out" }} onClick={e => e.stopPropagation()}>
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-lg font-bold leading-tight" style={{ color: "var(--text)" }}>{selectedMeta.titulo}</h2>
                            <button onClick={() => setSelectedMeta(null)} className="text-xl" style={{ color: "var(--muted)" }}>&times;</button>
                        </div>
                        <p className="text-sm mb-6" style={{ color: "var(--text-secondary)" }}>O que deseja fazer com esta meta?</p>

                        <div className="flex flex-col gap-3">
                            {selectedMeta.status !== "concluida" && (
                                <button onClick={() => updateStatus("concluida")} className="py-3 rounded-xl text-sm font-semibold flex items-center justify-center gap-2 transition-opacity hover:opacity-90"
                                    style={{ backgroundColor: "var(--avocado)", color: "white" }}>
                                    🎯 Marcar como Concluída
                                </button>
                            )}
                            {selectedMeta.status === "ativa" && (
                                <button onClick={() => updateStatus("cancelada")} className="py-3 rounded-xl text-sm font-medium transition-opacity hover:opacity-90"
                                    style={{ backgroundColor: "var(--elevated)", color: "var(--warning)", border: "1px solid var(--warning)40" }}>
                                    ⏸️ Desativar Meta
                                </button>
                            )}
                            {selectedMeta.status === "cancelada" && (
                                <button onClick={() => updateStatus("ativa")} className="py-3 rounded-xl text-sm font-medium transition-opacity hover:opacity-90"
                                    style={{ backgroundColor: "var(--elevated)", color: "var(--avocado)", border: "1px solid var(--avocado)40" }}>
                                    ▶️ Reativar Meta
                                </button>
                            )}
                            <button onClick={deleteMeta} className="py-3 rounded-xl text-sm font-medium transition-opacity hover:opacity-90"
                                style={{ backgroundColor: "var(--danger)20", color: "var(--danger)", border: "1px solid var(--danger)40" }}>
                                🗑️ Excluir Meta
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Confetti Animation */}
            {showConfetti && (
                <div className="fixed inset-0 pointer-events-none z-[100] flex items-center justify-center overflow-hidden">
                    <div className="text-9xl animate-bounce">🎉🏆✨</div>
                </div>
            )}

            <style>{`
        @keyframes modal-in {
          from { opacity: 0; transform: translateY(8px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
        </div >
    );
}
