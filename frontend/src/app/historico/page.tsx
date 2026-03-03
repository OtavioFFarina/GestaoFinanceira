"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import AppNav from "@/components/layout/AppNav";
import GlobalLoader from "@/components/ui/GlobalLoader";
import { API_BASE } from "@/lib/apiConfig";

const C = {
    bg: "var(--bg)", surface: "var(--surface)", border: "var(--border)",
    muted: "var(--muted)", avocado: "var(--avocado)", avocadoLight: "var(--avocado-light)",
    danger: "var(--danger)", warning: "var(--warning)", text: "var(--text)"
};

const MONTHS = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
];


interface CicloResumo {
    ciclo_id: number;
    ano: number;
    mes: number;
    renda_total: number;
    total_gasto: number;
    saldo_livre: number;
    taxa_poupanca: number;
}

function Skeleton({ className = "" }: { className?: string }) {
    return <div className={`animate-pulse rounded-xl ${className}`} style={{ backgroundColor: "#1E2530" }} />;
}

export default function HistoricoPage() {
    const { user, loading: authLoading } = useAuth();
    const router = useRouter();
    const [ciclos, setCiclos] = useState<CicloResumo[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!authLoading && !user) router.replace("/login");
    }, [user, authLoading, router]);

    useEffect(() => {
        if (!user) return;
        fetch(`${API_BASE}/historico/${user.usuario_id}`)
            .then((r) => r.json())
            .then(setCiclos)
            .catch(console.error)
            .finally(() => setLoading(false));
    }, [user]);

    const fmt = (v: number) => v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

    if (authLoading) return <GlobalLoader />;
    if (!user) return null;


    return (
        <div className="min-h-screen font-sans antialiased" style={{ backgroundColor: "var(--bg)", color: "var(--text)" }}>
            <AppNav activeItem="Histórico" />

            <main className="max-w-5xl mx-auto px-4 md:px-6 py-6 md:py-8">
                <h1 className="text-2xl font-bold mt-1 mb-6">Histórico Financeiro</h1>

                {loading ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {[...Array(6)].map((_, i) => <Skeleton key={i} className="h-44" />)}
                    </div>
                ) : ciclos.length === 0 ? (
                    <div className="text-center py-20" style={{ color: C.muted }}>
                        <p className="text-4xl mb-3">📅</p>
                        <p className="text-lg font-medium">Nenhum mês registrado ainda</p>
                        <p className="text-sm mt-1">Registre o mês atual no Dashboard para começar.</p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {ciclos.map((c) => {
                            const gastoPct = c.renda_total > 0 ? Math.min((c.total_gasto / c.renda_total) * 100, 100) : 0;
                            const positive = c.saldo_livre >= 0;
                            return (
                                <div key={c.ciclo_id}
                                    className="rounded-2xl p-5 flex flex-col gap-3 hover:scale-[1.01] transition-transform cursor-default"
                                    style={{ backgroundColor: C.surface, border: `1px solid ${C.border}` }}>
                                    <div className="flex items-start justify-between">
                                        <div>
                                            <p className="text-sm font-semibold">{MONTHS[c.mes - 1]} {c.ano}</p>
                                            <p className="text-xs mt-0.5" style={{ color: C.muted }}>Renda: {fmt(c.renda_total)}</p>
                                        </div>
                                        <span className="text-xs px-2 py-1 rounded-md font-medium"
                                            style={{ backgroundColor: positive ? `${C.avocado}20` : "#F8514920", color: positive ? C.avocado : "#F85149" }}>
                                            {positive ? `+${fmt(c.saldo_livre)}` : fmt(c.saldo_livre)}
                                        </span>
                                    </div>

                                    {/* Gasto progress */}
                                    <div>
                                        <div className="flex justify-between text-xs mb-1.5" style={{ color: C.muted }}>
                                            <span>Gasto</span>
                                            <span>{gastoPct.toFixed(0)}% da renda</span>
                                        </div>
                                        <div className="h-1.5 rounded-full overflow-hidden" style={{ backgroundColor: "#1E2530" }}>
                                            <div className="h-full rounded-full transition-all"
                                                style={{ width: `${gastoPct}%`, backgroundColor: gastoPct > 90 ? "#F85149" : C.avocado }} />
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-2 gap-2 pt-1">
                                        <div className="rounded-lg p-2.5 text-center" style={{ backgroundColor: "#1E2530" }}>
                                            <p className="text-xs" style={{ color: C.muted }}>Total Gasto</p>
                                            <p className="text-sm font-semibold mt-0.5">{fmt(c.total_gasto)}</p>
                                        </div>
                                        <div className="rounded-lg p-2.5 text-center" style={{ backgroundColor: "#1E2530" }}>
                                            <p className="text-xs" style={{ color: C.muted }}>Poupança</p>
                                            <p className="text-sm font-semibold mt-0.5" style={{ color: positive ? C.avocado : "#F85149" }}>
                                                {Number(c.taxa_poupanca).toFixed(1)}%
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </main>
        </div>
    );
}
