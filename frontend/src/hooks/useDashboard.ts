"use client";
import { useCallback, useEffect, useState } from "react";
import { API_BASE } from "@/lib/apiConfig";

// ─── Types (mirror backend schemas) ─────────────────────────────────────────
export interface CategoriaAlocacao {
    categoria_id: string;
    categoria: string;
    slug: string;
    cor_hex: string | null;
    valor_planejado: number;
    percentual_planejado: number;
    valor_realizado: number;
    percentual_realizado: number;
}

export interface DashboardData {
    ciclo_id: string | null;
    usuario_id: string;
    ano: number;
    mes: number;
    renda_total: number;
    total_gasto: number;
    saldo_livre: number;
    taxa_poupanca: number;
    alocacoes: CategoriaAlocacao[];
}

export interface Categoria {
    id: string;
    nome: string;
    slug: string;
    cor_hex: string | null;
    icone: string | null;
    tipo: string;
}

// ─── Hook ────────────────────────────────────────────────────────────────────
export function useDashboard(usuarioId: string, ano: number, mes: number) {
    const [data, setData] = useState<DashboardData | null>(null);
    const [categorias, setCategorias] = useState<Categoria[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchDashboard = useCallback(async (forceLoad = false) => {
        // Guard: don't fetch if auth is not yet hydrated
        if (!usuarioId) {
            setLoading(false);
            return;
        }

        if (!data || forceLoad) setLoading(true); // Only show full loader if NO previous data OR user clicked refresh
        setError(null);

        try {
            // Fetch dashboard data (always returns 200 with zeros if month is empty)
            const dashRes = await fetch(`${API_BASE}/dashboard/${usuarioId}/${ano}/${mes}`);
            if (!dashRes.ok) throw new Error(`Erro HTTP ${dashRes.status} ao buscar dashboard`);
            const dashJson: DashboardData = await dashRes.json();
            setData(dashJson);

            // Fetch categories separately — don't let it block dashboard
            try {
                const catRes = await fetch(`${API_BASE}/categorias?tipo=saida`);
                if (catRes.ok) {
                    const catJson: Categoria[] = await catRes.json();
                    setCategorias(catJson);
                }
            } catch {
                // Categories failing shouldn't crash the dashboard
                console.warn("Não foi possível carregar categorias");
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : "Erro desconhecido");
        } finally {
            if (!data || forceLoad) setLoading(false);
        }
    }, [usuarioId, ano, mes, data]);

    useEffect(() => {
        fetchDashboard();
    }, [fetchDashboard]);

    return { data, categorias, loading, error, refetch: fetchDashboard };
}
