"use client";
import { useCallback, useEffect, useState } from "react";
import { API_BASE } from "@/lib/apiConfig";

// ─── Types (mirror backend schemas) ─────────────────────────────────────────
export interface CategoriaAlocacao {
    categoria_id: number;
    categoria: string;
    slug: string;
    cor_hex: string | null;
    valor_planejado: number;
    percentual_planejado: number;
    valor_realizado: number;
    percentual_realizado: number;
}

export interface DashboardData {
    ciclo_id: number | null;
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
    id: number;
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

    const fetchDashboard = useCallback(async () => {
        // Guard: don't fetch if auth is not yet hydrated
        if (!usuarioId) {
            setLoading(false);
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const [dashRes, catRes] = await Promise.all([
                fetch(`${API_BASE}/dashboard/${usuarioId}/${ano}/${mes}`),
                fetch(`${API_BASE}/categorias?tipo=saida`),
            ]);

            if (!dashRes.ok) throw new Error(`Erro HTTP ${dashRes.status} ao buscar dashboard`);
            if (!catRes.ok) throw new Error(`Erro HTTP ${catRes.status} ao buscar categorias`);

            const dashJson: DashboardData = await dashRes.json();
            const catJson: Categoria[] = await catRes.json();

            setData(dashJson);
            setCategorias(catJson);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Erro desconhecido");
        } finally {
            setLoading(false);
        }
    }, [usuarioId, ano, mes]);

    useEffect(() => {
        fetchDashboard();
    }, [fetchDashboard]);

    return { data, categorias, loading, error, refetch: fetchDashboard };
}
