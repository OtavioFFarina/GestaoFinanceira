"use client";

import { useState } from "react";

const API_BASE =
    process.env.NEXT_PUBLIC_API_URL ||
    (typeof window !== "undefined" ? `http://${window.location.hostname}:8000/api` : "http://localhost:8000/api");

// ─── Colors ───────────────────────────────────────────────────────────────────
const C = {
    surface: "var(--surface)", elevated: "var(--elevated)", border: "var(--border)",
    muted: "var(--muted)", text: "var(--text)", avocado: "var(--avocado)", avocadoLight: "var(--avocado-light)"
};

interface Props {
    isOpen: boolean;
    onClose: () => void;
    usuarioId: string;
    onSuccess: () => void;
}

const MONTHS = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
];

export default function RegisterMonthModal({ isOpen, onClose, usuarioId, onSuccess }: Props) {
    const now = new Date();
    const [ano, setAno] = useState(now.getFullYear());
    const [mes, setMes] = useState(now.getMonth() + 1);
    const [renda, setRenda] = useState("");
    const [obs, setObs] = useState("");
    const [loading, setLoading] = useState(false);
    const [erro, setErro] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        const valor = parseFloat(renda.replace(",", "."));
        if (isNaN(valor) || valor <= 0) {
            setErro("Informe uma renda válida e positiva.");
            return;
        }
        setLoading(true);
        setErro(null);
        try {
            const res = await fetch(`${API_BASE}/ciclos`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ usuario_id: usuarioId, ano, mes, renda_total: valor, observacoes: obs || null }),
            });
            if (!res.ok) throw new Error(`Erro ${res.status}`);
            onSuccess();
            onClose();
        } catch (err) {
            setErro(err instanceof Error ? err.message : "Erro ao salvar.");
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        // Overlay
        <div
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
            style={{ backgroundColor: "rgba(0,0,0,0.65)", backdropFilter: "blur(4px)" }}
            onClick={(e) => e.target === e.currentTarget && onClose()}
        >
            {/* Modal Card */}
            <div
                className="w-full max-w-md rounded-2xl p-6 shadow-2xl"
                style={{
                    backgroundColor: C.surface,
                    border: `1px solid ${C.border}`,
                    animation: "modal-in 0.2s ease-out",
                }}
            >
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h2 className="text-lg font-bold">Registrar Mês</h2>
                        <p className="text-xs mt-0.5" style={{ color: C.muted }}>
                            Defina a renda recebida no período
                        </p>
                    </div>
                    <button
                        onClick={onClose}
                        className="w-8 h-8 rounded-lg flex items-center justify-center text-lg hover:opacity-70 transition-opacity"
                        style={{ backgroundColor: C.elevated, color: C.muted }}
                    >
                        ✕
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    {/* Mês + Ano */}
                    <div className="grid grid-cols-2 gap-3">
                        <div>
                            <label className="text-xs font-medium mb-1.5 block" style={{ color: C.muted }}>
                                Mês
                            </label>
                            <select
                                value={mes}
                                onChange={(e) => setMes(Number(e.target.value))}
                                className="w-full rounded-xl px-3 py-2.5 text-sm outline-none"
                                style={{ backgroundColor: C.elevated, border: `1px solid ${C.border}` }}
                            >
                                {MONTHS.map((m, i) => (
                                    <option key={i} value={i + 1}>{m}</option>
                                ))}
                            </select>
                        </div>
                        <div>
                            <label className="text-xs font-medium mb-1.5 block" style={{ color: C.muted }}>
                                Ano
                            </label>
                            <input
                                type="number"
                                value={ano}
                                onChange={(e) => setAno(Number(e.target.value))}
                                min={2000}
                                max={2100}
                                className="w-full rounded-xl px-3 py-2.5 text-sm outline-none"
                                style={{ backgroundColor: C.elevated, border: `1px solid ${C.border}` }}
                            />
                        </div>
                    </div>

                    {/* Renda */}
                    <div>
                        <label className="text-xs font-medium mb-1.5 block" style={{ color: C.muted }}>
                            Renda Total Recebida (R$)
                        </label>
                        <div className="relative">
                            <span
                                className="absolute left-3 top-1/2 -translate-y-1/2 text-sm font-semibold"
                                style={{ color: C.avocado }}
                            >
                                R$
                            </span>
                            <input
                                type="text"
                                inputMode="decimal"
                                placeholder="0,00"
                                value={renda}
                                onChange={(e) => setRenda(e.target.value)}
                                className="w-full rounded-xl pl-10 pr-3 py-2.5 text-sm outline-none"
                                style={{ backgroundColor: C.elevated, border: `1px solid ${C.border}` }}
                                required
                            />
                        </div>
                    </div>

                    {/* Observações */}
                    <div>
                        <label className="text-xs font-medium mb-1.5 block" style={{ color: C.muted }}>
                            Observações (opcional)
                        </label>
                        <textarea
                            value={obs}
                            onChange={(e) => setObs(e.target.value)}
                            rows={2}
                            placeholder="Ex: Mês com 13º salário..."
                            className="w-full rounded-xl px-3 py-2.5 text-sm outline-none resize-none"
                            style={{ backgroundColor: C.elevated, border: `1px solid ${C.border}` }}
                        />
                    </div>

                    {/* Error */}
                    {erro && (
                        <p className="text-xs text-red-400 bg-red-400/10 px-3 py-2 rounded-lg">{erro}</p>
                    )}

                    {/* Actions */}
                    <div className="flex gap-3 pt-2">
                        <button
                            type="button"
                            onClick={onClose}
                            className="flex-1 py-2.5 rounded-xl text-sm font-medium transition-opacity hover:opacity-80"
                            style={{ backgroundColor: C.elevated, color: C.muted, border: `1px solid ${C.border}` }}
                        >
                            Cancelar
                        </button>
                        <button
                            type="submit"
                            disabled={loading}
                            className="flex-1 py-2.5 rounded-xl text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-50"
                            style={{ backgroundColor: C.avocado }}
                        >
                            {loading ? "Salvando..." : "Salvar Mês"}
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
