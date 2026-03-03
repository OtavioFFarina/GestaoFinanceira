"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { API_BASE } from "@/lib/apiConfig";
import {
    AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
    XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from "recharts";
import {
    TrendingUp, Wallet, ShieldCheck, Bot, Send,
    ChevronRight, ArrowUpRight, ArrowDownRight, Sparkles, Plus, RefreshCw,
} from "lucide-react";

import { useDashboard } from "@/hooks/useDashboard";
import { useModal } from "@/hooks/useModal";
import { useAuth } from "@/lib/auth";
import AppNav from "@/components/layout/AppNav";
import RegisterMonthModal from "@/components/modals/RegisterMonthModal";
import NewTransactionModal from "@/components/modals/NewTransactionModal";
import TransacoesModal from "@/components/modals/TransacoesModal";

import AnimatedGreeting from "@/components/ui/AnimatedGreeting";
import GlobalLoader from "@/components/ui/GlobalLoader";

const C = {
    avocado: "var(--avocado)", avocadoLight: "var(--avocado-light)",
    danger: "var(--danger)", warning: "var(--warning)",
    bg: "var(--bg)", surface: "var(--surface)", elevated: "var(--elevated)",
    border: "var(--border)", muted: "var(--muted)",
    text: "var(--text)",
};

// ─── Skeleton loader ──────────────────────────────────────────────────────────
function Skeleton({ className = "" }: { className?: string }) {
    return (
        <div
            className={`animate-pulse rounded-xl ${className}`}
            style={{ backgroundColor: C.elevated }}
        />
    );
}

// ─── KPI Card ─────────────────────────────────────────────────────────────────
interface KpiCardProps {
    title: string; value: string; subtitle: string;
    icon: React.ReactNode; trend?: "up" | "down"; trendValue?: string;
    onClick?: () => void;
}
function KpiCard({ title, value, subtitle, icon, trend, trendValue, onClick }: KpiCardProps) {
    const trendColor = trend === "up" ? C.avocado : C.danger;
    return (
        <div
            onClick={onClick}
            className={`rounded-2xl p-5 flex flex-col gap-3 transition-transform hover:scale-[1.02] ${onClick ? "cursor-pointer hover:ring-1 ring-avocado" : "cursor-default"}`}
            style={{ backgroundColor: C.surface, border: `1px solid ${onClick ? C.avocado + "60" : C.border}` }}
        >
            <div className="flex items-center justify-between">
                <span className="text-sm font-medium" style={{ color: C.muted }}>{title}</span>
                <span className="w-9 h-9 rounded-xl flex items-center justify-center" style={{ backgroundColor: C.elevated }}>{icon}</span>
            </div>
            <div>
                <p className="text-2xl font-bold tracking-tight">{value}</p>
                <p className="text-xs mt-1" style={{ color: C.muted }}>{subtitle}</p>
            </div>
            {trend && trendValue && (
                <div className="flex items-center gap-1">
                    {trend === "up"
                        ? <ArrowUpRight size={14} style={{ color: trendColor }} />
                        : <ArrowDownRight size={14} style={{ color: trendColor }} />}
                    <span className="text-xs font-medium" style={{ color: trendColor }}>{trendValue}</span>
                </div>
            )}
        </div>
    );
}

// ─── Custom Tooltip ───────────────────────────────────────────────────────────
interface TooltipItem { color: string; name: string; value: number; }
function CustomTooltip({ active, payload, label }: { active?: boolean; payload?: TooltipItem[]; label?: string }) {
    if (!active || !payload?.length) return null;
    return (
        <div className="rounded-xl px-3 py-2 text-sm shadow-xl" style={{ backgroundColor: C.elevated, border: `1px solid ${C.border}` }}>
            {label && <p className="font-semibold mb-1">{label}</p>}
            {payload.map((e, i) => <p key={i} style={{ color: e.color }}>{e.name}: {e.value}%</p>)}
        </div>
    );
}

// ─── Chat Sidebar ─────────────────────────────────────────────────────────────
interface ChatMsg { role: "user" | "assistant"; content: string; }

const API_CHAT = `${API_BASE}/chat`;

/** Simple markdown renderer: **bold** and line breaks */
function MsgContent({ text }: { text: string }) {
    const parts = text.split(/(\*\*[^*]+\*\*)/g);
    return (
        <span>
            {parts.map((p, i) =>
                p.startsWith("**") && p.endsWith("**")
                    ? <strong key={i}>{p.slice(2, -2)}</strong>
                    : p.split("\n").map((line, j) =>
                        j === 0 ? line : <span key={j}><br />{line}</span>
                    )
            )}
        </span>
    );
}

function TypingIndicator() {
    return (
        <div className="flex justify-start">
            <div className="rounded-xl px-3 py-2.5 flex items-center gap-1.5"
                style={{ backgroundColor: C.elevated, border: `1px solid ${C.border}` }}>
                {[0, 1, 2].map(i => (
                    <span
                        key={i}
                        className="w-1.5 h-1.5 rounded-full"
                        style={{
                            backgroundColor: C.muted,
                            animation: `typing-dot 1.2s ease-in-out infinite`,
                            animationDelay: `${i * 0.2}s`,
                        }}
                    />
                ))}
            </div>
        </div>
    );
}

function AIChatSidebar() {
    const { user } = useAuth();
    const [messages, setMessages] = useState<ChatMsg[]>([{
        role: "assistant",
        content: "Olá! 🥑 Sou o Avocado, seu consultor financeiro pessoal.\n\nPosso analisar seus dados e responder dúvidas sobre gastos, investimentos e dívidas. O que quer saber?",
    }]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const bottomRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, loading]);

    const sendMessage = async () => {
        const text = input.trim();
        if (!text || loading || !user) return;

        const newUserMsg: ChatMsg = { role: "user", content: text };
        const nextMessages = [...messages, newUserMsg];
        setMessages(nextMessages);
        setInput("");
        setLoading(true);

        try {
            // Send conversation history (last 8 turns) for multi-turn context
            const historico = nextMessages.slice(-8).map(m => ({
                role: m.role,
                content: m.content,
            }));

            const res = await fetch(API_CHAT, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    usuario_id: user.usuario_id,
                    mensagem: text,
                    historico: historico.slice(0, -1), // exclude last user msg (sent as "mensagem")
                }),
            });

            const data = await res.json();
            setMessages(prev => [...prev, { role: "assistant", content: data.resposta ?? "Sem resposta." }]);
        } catch {
            setMessages(prev => [...prev, {
                role: "assistant",
                content: "😔 Tive um problema de conexão. Verifique o backend e tente novamente.",
            }]);
        } finally {
            setLoading(false);
            setTimeout(() => inputRef.current?.focus(), 50);
        }
    };

    return (
        <div className="flex flex-col h-full rounded-2xl overflow-hidden" style={{ backgroundColor: C.surface, border: `1px solid ${C.border}` }}>
            {/* Header */}
            <div className="px-4 py-3 flex items-center gap-2 flex-shrink-0" style={{ borderBottom: `1px solid ${C.border}` }}>
                <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0" style={{ backgroundColor: `${C.avocado}20` }}>
                    <Bot size={16} style={{ color: C.avocado }} />
                </div>
                <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold">Avocado AI</p>
                    <p className="text-xs" style={{ color: loading ? C.warning : C.avocado }}>
                        {loading ? "⏳ Pensando..." : "● Online"}
                    </p>
                </div>
                <Sparkles size={14} className="flex-shrink-0" style={{ color: C.muted }} />
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-3 space-y-3 min-h-0">
                {messages.map((msg, i) => (
                    <div key={`msg-${i}`} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                        <div
                            className="max-w-[88%] rounded-xl px-3 py-2 text-sm leading-relaxed"
                            style={{
                                backgroundColor: msg.role === "user" ? C.avocado : C.elevated,
                                color: msg.role === "user" ? "white" : C.muted,
                                border: msg.role === "assistant" ? `1px solid ${C.border}` : "none",
                            }}
                        >
                            <MsgContent text={msg.content} />
                        </div>
                    </div>
                ))}
                {loading && <TypingIndicator />}
                <div ref={bottomRef} />
            </div>

            {/* Input */}
            <div className="p-3 flex-shrink-0" style={{ borderTop: `1px solid ${C.border}` }}>
                <div className="flex items-center gap-2 rounded-xl px-3 py-2" style={{ backgroundColor: C.elevated, border: `1px solid ${C.border}` }}>
                    <input
                        ref={inputRef}
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); } }}
                        placeholder={loading ? "Aguardando resposta..." : "Pergunte sobre suas finanças..."}
                        disabled={loading}
                        className="flex-1 bg-transparent text-sm placeholder-gray-500 outline-none disabled:opacity-50"
                    />
                    <button
                        onClick={sendMessage}
                        disabled={loading || !input.trim()}
                        className="w-7 h-7 rounded-lg flex items-center justify-center transition-opacity disabled:opacity-40 hover:opacity-80"
                        style={{ backgroundColor: C.avocado }}
                    >
                        <Send size={13} color="white" />
                    </button>
                </div>
            </div>

            <style>{`
                @keyframes typing-dot {
                    0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
                    40% { transform: scale(1); opacity: 1; }
                }
            `}</style>
        </div>
    );
}

// ─── Main Dashboard ───────────────────────────────────────────────────────────
export default function MainDashboard() {
    const { user, loading: authLoading } = useAuth();
    const router = useRouter();
    const now = new Date();
    const [ano] = useState(now.getFullYear());
    const [mes] = useState(now.getMonth() + 1);

    // Redirect to login if not authenticated
    useEffect(() => {
        if (!authLoading && !user) router.replace("/login");
    }, [user, authLoading, router]);

    const usuarioId = user?.usuario_id ?? "";
    const { data, categorias, loading, error, refetch } = useDashboard(usuarioId, ano, mes);
    const monthModal = useModal();
    const txModal = useModal();
    const txListModal = useModal(); // New: opens TransacoesModal

    const fmt = (v: number) =>
        v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

    if (authLoading) return <GlobalLoader />;
    if (!user) return null;

    const mesNome = new Intl.DateTimeFormat("pt-BR", { month: "long" }).format(new Date(ano, mes - 1, 1));
    const mesLabel = `${mesNome.charAt(0).toUpperCase() + mesNome.slice(1)} ${ano}`;

    // Derived chart data from API
    // Alocação Ideal: use metas_alocacao data OR fallback to recommended 50/30/20 rule
    const hasPlannedData = (data?.alocacoes ?? []).some(a => a.valor_planejado > 0);
    const allocationIdeal = hasPlannedData
        ? data!.alocacoes
            .filter(a => a.valor_planejado > 0)
            .map(a => ({ name: a.categoria, value: Number(a.percentual_planejado), color: a.cor_hex ?? C.avocado }))
        : data?.renda_total
            ? [
                { name: "Necessidades", value: 50, color: "#5CA34F" },
                { name: "Desejos", value: 30, color: "#7CC96E" },
                { name: "Investimentos", value: 20, color: "#4BADE8" },
            ]
            : [];

    const spendingData = data?.alocacoes.map((a) => ({
        category: a.categoria.split(" ")[0],
        planejado: Number(a.percentual_planejado),
        realizado: Number(a.percentual_realizado),
    })) ?? [];

    const isDefaultAllocation = !hasPlannedData && data?.renda_total;
    const showPlanejado = hasPlannedData;


    return (
        <div className="min-h-screen font-sans antialiased" style={{ backgroundColor: C.bg, color: C.text }}>
            {/* ── Modals ── */}
            <RegisterMonthModal
                isOpen={monthModal.isOpen}
                onClose={monthModal.close}
                usuarioId={usuarioId}
                onSuccess={refetch}
            />
            {data?.ciclo_id && (
                <NewTransactionModal
                    isOpen={txModal.isOpen}
                    onClose={txModal.close}
                    cicloId={data.ciclo_id}
                    categorias={categorias}
                    usuarioId={usuarioId}
                    onSuccess={refetch}
                />
            )}
            {data?.ciclo_id && (
                <TransacoesModal
                    isOpen={txListModal.isOpen}
                    onClose={txListModal.close}
                    cicloId={data.ciclo_id}
                    onSuccess={refetch}
                    mesLabel={mesLabel}
                />
            )}

            {/* ── Nav ── */}
            <AppNav activeItem="Dashboard" />

            {/* ── Content ── */}
            <main className="max-w-[1400px] mx-auto px-4 md:px-6 py-4 md:py-6 grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6">
                <div className="space-y-6">
                    {/* Header */}
                    <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 md:gap-0">
                        <div>
                            <AnimatedGreeting nome={user.nome_exibicao} />
                            <p className="text-sm mt-0.5" style={{ color: C.muted }}>{mesLabel}</p>
                            <h1 className="text-xl md:text-2xl font-bold mt-0.5">Visão Geral Financeira</h1>
                        </div>
                        <div className="flex items-center gap-2 overflow-x-auto pb-1 md:pb-0 w-full md:w-auto hide-scrollbar">
                            {/* Refresh */}
                            <button
                                onClick={refetch}
                                className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 transition-opacity hover:opacity-70"
                                style={{ backgroundColor: C.surface, border: `1px solid ${C.border}` }}
                                title="Atualizar dados"
                            >
                                <RefreshCw size={14} style={{ color: C.muted }} className={loading ? "animate-spin" : ""} />
                            </button>
                            {/* Nova Transação */}
                            {data?.ciclo_id && (
                                <button
                                    onClick={txModal.open}
                                    className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium text-white whitespace-nowrap flex-shrink-0 transition-opacity hover:opacity-90"
                                    style={{ backgroundColor: C.elevated, border: `1px solid ${C.border}` }}
                                >
                                    <Plus size={14} /> Nova Transação
                                </button>
                            )}
                            {/* Registrar Mês */}
                            <button
                                onClick={monthModal.open}
                                className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium text-white whitespace-nowrap flex-shrink-0 transition-opacity hover:opacity-90"
                                style={{ backgroundColor: C.avocado }}
                            >
                                + Registrar Mês <ChevronRight size={14} />
                            </button>
                        </div>
                    </div>

                    {/* Error state */}
                    {error && (
                        <div className="rounded-xl px-4 py-3 text-sm text-red-400 flex items-center gap-2" style={{ backgroundColor: "rgba(248,81,73,0.10)", border: "1px solid #F85149" }}>
                            ⚠️ {error} — Verifique se o backend está rodando corretamente
                        </div>
                    )}

                    {/* ── KPI Cards ── */}
                    {loading ? (
                        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4">
                            {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-32" />)}
                        </div>
                    ) : (
                        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4">
                            <KpiCard
                                title="Recebido no Mês"
                                value={data ? fmt(data.renda_total) : "—"}
                                subtitle={`Renda total de ${mesNome}`}
                                icon={<Wallet size={16} style={{ color: C.avocado }} />}
                            />
                            <KpiCard
                                title="Total Gasto"
                                value={data ? fmt(data.total_gasto) : "—"}
                                subtitle={data ? `${((data.total_gasto / (data.renda_total || 1)) * 100).toFixed(0)}% da renda` : "—"}
                                icon={<TrendingUp size={16} style={{ color: C.warning }} />}
                                trend={data && data.total_gasto > data.renda_total ? "down" : "up"}
                                trendValue={data ? `${(100 - data.taxa_poupanca).toFixed(0)}% comprometido` : ""}
                                onClick={data?.ciclo_id ? txListModal.open : undefined}
                            />
                            <KpiCard
                                title="Investimentos"
                                value={data ? fmt(data.alocacoes.find(a => a.slug === "investimentos")?.valor_realizado ?? 0) : "—"}
                                subtitle="Montante aplicado"
                                icon={<ShieldCheck size={16} style={{ color: "#4BADE8" }} />}
                            />
                            <KpiCard
                                title="Saldo Livre"
                                value={data ? fmt(data.saldo_livre) : "—"}
                                subtitle={data ? `Taxa de poupança: ${data.taxa_poupanca.toFixed(1)}%` : "—"}
                                icon={<Sparkles size={16} style={{ color: C.avocadoLight }} />}
                                trend={data && data.saldo_livre >= 0 ? "up" : "down"}
                                trendValue={data && data.saldo_livre >= 0 ? "Positivo ✓" : "Atenção!"}
                            />
                        </div>
                    )}

                    {/* ── Charts ── */}
                    {loading ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <Skeleton className="h-72" />
                            <Skeleton className="h-72" />
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {/* Chart 1 — Regra 50/30/20 */}
                            <div className="rounded-2xl p-4 md:p-5" style={{ backgroundColor: C.surface, border: `1px solid ${C.border}` }}>
                                <h2 className="text-sm font-semibold">Regra 50/30/20</h2>
                                <p className="text-xs mt-0.5 mb-1" style={{ color: C.muted }}>Guia de distribuição da sua renda</p>

                                {data && data.renda_total > 0 ? (() => {
                                    const renda = data.renda_total;
                                    const slices = [
                                        { name: "Necessidades", pct: 50, color: "#5DB075", emoji: "🏠", desc: "Moradia, contas, mercado" },
                                        { name: "Desejos", pct: 30, color: "#8BC34A", emoji: "🎉", desc: "Lazer, restaurantes, assinaturas" },
                                        { name: "Investimentos", pct: 20, color: "#4BADE8", emoji: "📈", desc: "Reserva, aplicações, metas" },
                                    ];
                                    const pieData = slices.map(s => ({ ...s, value: s.pct }));

                                    const CustomPieTooltip = ({ active, payload }: { active?: boolean; payload?: { payload: typeof slices[0] }[] }) => {
                                        if (!active || !payload?.length) return null;
                                        const s = payload[0].payload;
                                        const valor = (renda * s.pct) / 100;
                                        return (
                                            <div className="rounded-xl px-3 py-2.5 text-xs shadow-xl" style={{ backgroundColor: C.elevated, border: `1px solid ${C.border}`, color: C.text }}>
                                                <p className="font-semibold mb-1">{s.emoji} {s.name}</p>
                                                <p style={{ color: s.color }} className="text-sm font-bold">{fmt(valor)}</p>
                                                <p style={{ color: C.muted }}>{s.pct}% de {fmt(renda)}</p>
                                                <p className="mt-1" style={{ color: C.muted }}>{s.desc}</p>
                                            </div>
                                        );
                                    };

                                    return (
                                        <>
                                            <ResponsiveContainer width="100%" height={180}>
                                                <PieChart>
                                                    <Pie
                                                        data={pieData}
                                                        cx="50%" cy="50%"
                                                        innerRadius={48} outerRadius={82}
                                                        paddingAngle={3}
                                                        dataKey="value"
                                                        strokeWidth={0}
                                                    >
                                                        {pieData.map((entry, i) => (
                                                            <Cell key={`c-${i}`} fill={entry.color} style={{ cursor: "pointer", outline: "none" }} />
                                                        ))}
                                                    </Pie>
                                                    <Tooltip content={<CustomPieTooltip />} />
                                                </PieChart>
                                            </ResponsiveContainer>

                                            {/* Breakdown list */}
                                            <div className="grid grid-cols-3 gap-2 mt-2">
                                                {slices.map(s => {
                                                    const valor = (renda * s.pct) / 100;
                                                    return (
                                                        <div key={s.name} className="rounded-xl px-2 py-2 text-center" style={{ backgroundColor: C.elevated }}>
                                                            <p className="text-base mb-0.5">{s.emoji}</p>
                                                            <p className="text-xs font-medium truncate" style={{ color: s.color }}>{s.name}</p>
                                                            <p className="text-xs font-bold mt-0.5">{fmt(valor)}</p>
                                                            <p className="text-xs" style={{ color: C.muted }}>{s.pct}%</p>
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        </>
                                    );
                                })() : (
                                    <div className="h-[220px] flex flex-col items-center justify-center gap-2 text-sm" style={{ color: C.muted }}>
                                        <span className="text-3xl">📊</span>
                                        <p>Registre o mês para ver a distribuição</p>
                                    </div>
                                )}
                            </div>


                            {/* Chart 2: Planned vs Actual */}
                            <div className="rounded-2xl p-5" style={{ backgroundColor: "var(--surface)", border: `1px solid var(--border)` }}>
                                <h2 className="text-sm font-semibold">{showPlanejado ? "Realizado vs. Planejado" : "Gastos por Categoria (%)"}</h2>
                                <p className="text-xs mt-0.5 mb-4" style={{ color: "var(--muted)" }}>% da renda por categoria</p>
                                {spendingData.length > 0 ? (
                                    <ResponsiveContainer width="100%" height={220}>
                                        <BarChart data={spendingData} barGap={2}>
                                            <CartesianGrid strokeDasharray="3 3" stroke={C.border} vertical={false} />
                                            <XAxis dataKey="category" tick={{ fill: C.muted, fontSize: 11 }} axisLine={false} tickLine={false} />
                                            <YAxis tick={{ fill: C.muted, fontSize: 11 }} axisLine={false} tickLine={false} unit="%" />
                                            <Tooltip content={<CustomTooltip />} cursor={{ fill: `var(--border)` }} />
                                            {showPlanejado && <Bar dataKey="planejado" name="Planejado" fill={`var(--avocado-light)`} radius={[4, 4, 0, 0] as [number, number, number, number]} maxBarSize={28} />}
                                            <Bar dataKey="realizado" name="Realizado" fill="var(--avocado)" radius={[4, 4, 0, 0] as [number, number, number, number]} maxBarSize={28} />
                                            <Legend iconType="circle" iconSize={8} formatter={(v) => <span style={{ color: C.muted, fontSize: "11px" }}>{v}</span>} />
                                        </BarChart>
                                    </ResponsiveContainer>
                                ) : (
                                    <div className="h-[220px] flex items-center justify-center text-sm" style={{ color: C.muted }}>
                                        Adicione transações para ver o gráfico
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* ── Transactions Table ── */}
                    {!loading && data && data.alocacoes.length > 0 && (
                        <div className="rounded-2xl p-5" style={{ backgroundColor: C.surface, border: `1px solid ${C.border}` }}>
                            <div className="flex items-center justify-between mb-4">
                                <h2 className="text-sm font-semibold">Resumo por Categoria</h2>
                                <span className="text-xs font-medium px-2 py-1 rounded-md" style={{ backgroundColor: `${C.avocado}20`, color: C.avocado }}>
                                    {mesLabel}
                                </span>
                            </div>
                            <div className="space-y-2">
                                {data.alocacoes.map((a) => {
                                    const pct = data.renda_total > 0
                                        ? Math.min((a.valor_realizado / data.renda_total) * 100, 100)
                                        : 0;
                                    const over = a.valor_realizado > a.valor_planejado && a.valor_planejado > 0;
                                    return (
                                        <div key={a.categoria_id} className="flex items-center gap-3">
                                            <div
                                                className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                                                style={{ backgroundColor: a.cor_hex ?? C.avocado }}
                                            />
                                            <span className="text-sm w-28 flex-shrink-0">{a.categoria}</span>
                                            <div className="flex-1 rounded-full overflow-hidden h-1.5" style={{ backgroundColor: C.elevated }}>
                                                <div
                                                    className="h-full rounded-full transition-all"
                                                    style={{ width: `${pct}%`, backgroundColor: over ? C.danger : (a.cor_hex ?? C.avocado) }}
                                                />
                                            </div>
                                            <span className="text-xs w-20 text-right font-medium" style={{ color: over ? C.danger : "white" }}>
                                                {fmt(a.valor_realizado)}
                                            </span>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    )}
                </div>

                {/* ── Right Column: AI Chat ── */}
                <div className="lg:h-[calc(100vh-88px)] lg:sticky lg:top-[72px]">
                    <AIChatSidebar />
                </div>
            </main>
        </div>
    );
}
