"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import GlobalLoader from "@/components/ui/GlobalLoader";
import AppNav from "@/components/layout/AppNav";

const C = {
    bg: "var(--bg)", surface: "var(--surface)", elevated: "var(--elevated)",
    border: "var(--border)", muted: "var(--muted)", text: "var(--text)", textSecondary: "var(--text-secondary)",
    avocado: "var(--avocado)", avocadoLight: "var(--avocado-light)"
};
const MONTHS = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
];

function getApiBase() {
    if (typeof window === "undefined") return "http://localhost:8000/api";
    return `http://${window.location.hostname}:8000/api`;
}

interface ReservaData {
    saldo_total: number;
    total_aportes: number;
    ultimo_aporte: string | null;
    historico: { ano: number; mes: number; valor: number }[];
}

function Skeleton({ className = "" }: { className?: string }) {
    return <div className={`animate-pulse rounded-xl ${className}`} style={{ backgroundColor: "var(--elevated)" }} />;
}

export default function ReservaPage() {
    const { user, loading: authLoading } = useAuth();
    const router = useRouter();
    const [reserva, setReserva] = useState<ReservaData | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!authLoading && !user) router.replace("/login");
    }, [user, authLoading, router]);

    useEffect(() => {
        if (!user) return;
        fetch(`${getApiBase()}/reserva/${user.usuario_id}`)
            .then(r => r.json()).then(setReserva).catch(console.error).finally(() => setLoading(false));
    }, [user]);

    const fmt = (v: number) => v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

    if (authLoading) return <GlobalLoader />;
    if (!user) return null;

    const maxVal = reserva?.historico.reduce((m, r) => Math.max(m, r.valor), 0) ?? 1;
    const totalMeses = reserva?.historico.length ?? 0;
    const mediaAporte = reserva && totalMeses > 0 ? reserva.saldo_total / totalMeses : 0;

    return (
        <div className="min-h-screen font-sans antialiased" style={{ backgroundColor: "var(--bg)", color: "var(--text)" }}>
            <AppNav activeItem="Reserva" />

            <main className="max-w-4xl mx-auto px-4 md:px-6 py-6 md:py-8">
                <h1 className="text-2xl font-bold mt-1 mb-6" style={{ color: "var(--text)" }}>Reserva de Emergência 🛡️</h1>

                {loading ? (
                    <div className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            {[...Array(3)].map((_, i) => <Skeleton key={i} className="h-28" />)}
                        </div>
                        <Skeleton className="h-64" />
                    </div>
                ) : (
                    <>
                        {/* KPIs */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                            {[
                                {
                                    label: "Saldo Acumulado", value: fmt(reserva?.saldo_total ?? 0),
                                    sub: "Total na reserva", icon: "🏦", highlight: true,
                                },
                                {
                                    label: "Aportes Realizados", value: `${reserva?.total_aportes ?? 0}`, sub: "Transações registradas", icon: "📥"
                                },
                                {
                                    label: "Média por Mês", value: fmt(mediaAporte), sub: "Nos meses com aporte", icon: "📊"
                                },
                            ].map(kpi => (
                                <div key={kpi.label} className="rounded-2xl p-5 flex flex-col gap-2"
                                    style={{
                                        backgroundColor: "var(--surface)",
                                        border: `1px solid ${kpi.highlight ? "var(--avocado)" : "var(--border)"}`,
                                        boxShadow: kpi.highlight ? "0 0 20px var(--avocado)20" : "none",
                                    }}>
                                    <div className="flex items-center justify-between">
                                        <span className="text-xs font-medium" style={{ color: "var(--muted)" }}>{kpi.label}</span>
                                        <span className="text-lg">{kpi.icon}</span>
                                    </div>
                                    <p className="text-2xl font-bold" style={{ color: kpi.highlight ? "var(--avocado)" : "var(--text)" }}>
                                        {kpi.value}
                                    </p>
                                    <p className="text-xs" style={{ color: "var(--muted)" }}>{kpi.sub}</p>
                                </div>
                            ))}
                        </div>

                        {/* Emergency Rule Indicator */}
                        <div className="rounded-2xl p-5 mb-6" style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border)" }}>
                            <div className="flex items-center justify-between mb-3">
                                <div>
                                    <p className="text-sm font-semibold" style={{ color: "var(--text)" }}>Meta de Emergência</p>
                                    <p className="text-xs mt-0.5" style={{ color: "var(--muted)" }}>
                                        Regra: 6 meses de gastos essenciais. Registre sua renda mensal para calcular.
                                    </p>
                                </div>
                                <span className="text-xs px-3 py-1.5 rounded-lg font-medium"
                                    style={{ backgroundColor: "var(--elevated)", color: "var(--muted)" }}>
                                    Configure no Dashboard →
                                </span>
                            </div>
                            <div className="rounded-xl p-4 text-sm" style={{ backgroundColor: "var(--elevated)" }}>
                                <p style={{ color: "var(--muted)" }}>
                                    💡 <strong style={{ color: "var(--text)" }}>Dica:</strong> A reserva de emergência ideal é equivalent a
                                    3–6 meses de seus gastos fixos mensais. Você acumulou{" "}
                                    <strong style={{ color: "var(--avocado)" }}>{fmt(reserva?.saldo_total ?? 0)}</strong> até agora.
                                    Continue registrando aportes na categoria <strong>Reserva</strong> nas transações mensais.
                                </p>
                            </div>
                        </div>

                        {/* Monthly History */}
                        <div className="rounded-2xl p-5" style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border)" }}>
                            <h2 className="text-sm font-semibold mb-4" style={{ color: "var(--text)" }}>Histórico de Aportes</h2>

                            {(!reserva?.historico.length) ? (
                                <div className="text-center py-10" style={{ color: "var(--muted)" }}>
                                    <p className="text-3xl mb-3">🏦</p>
                                    <p className="font-medium" style={{ color: "var(--text)" }}>Nenhum aporte registrado</p>
                                    <p className="text-sm mt-1">Adicione transações na categoria <strong>Reserva</strong> mensalmente.</p>
                                </div>
                            ) : (
                                <div className="space-y-2">
                                    {reserva.historico.map((h, i) => {
                                        const pct = maxVal > 0 ? (h.valor / maxVal) * 100 : 0;
                                        const acumulado = reserva.historico.slice(i).reduce((a, r) => a + r.valor, 0);
                                        return (
                                            <div key={`${h.ano}-${h.mes}`} className="flex items-center gap-4">
                                                <span className="text-xs w-24 flex-shrink-0" style={{ color: "var(--muted)" }}>
                                                    {MONTHS[h.mes - 1].slice(0, 3)} {h.ano}
                                                </span>
                                                <div className="flex-1 h-2 rounded-full overflow-hidden" style={{ backgroundColor: "var(--elevated)" }}>
                                                    <div className="h-full rounded-full transition-all"
                                                        style={{ width: `${pct}%`, backgroundColor: "var(--avocado)" }} />
                                                </div>
                                                <span className="text-xs font-semibold w-24 text-right" style={{ color: "var(--avocado)" }}>
                                                    {fmt(h.valor)}
                                                </span>
                                            </div>
                                        );
                                    })}
                                </div>
                            )}
                        </div>
                    </>
                )}
            </main>
        </div>
    );
}
