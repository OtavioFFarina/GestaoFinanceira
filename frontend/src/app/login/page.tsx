"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import GlobalLoader from "@/components/ui/GlobalLoader";

const C = {
    bg: "var(--bg)", surface: "var(--surface)", elevated: "var(--elevated)",
    border: "var(--border)", muted: "var(--muted)", text: "var(--text)",
    avocado: "var(--avocado)", avocadoLight: "var(--avocado-light)", danger: "var(--danger)",
};

export default function LoginPage() {
    const { login, user, loading } = useAuth();
    const router = useRouter();

    const [email, setEmail] = useState("");
    const [senha, setSenha] = useState("");
    const [erro, setErro] = useState<string | null>(null);
    const [submitting, setSubmitting] = useState(false);
    const [showPwd, setShowPwd] = useState(false);

    // Redirect if already logged in
    useEffect(() => {
        if (!loading && user) router.replace("/");
    }, [user, loading, router]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setErro(null);
        setSubmitting(true);
        try {
            await login(email, senha);
            router.replace("/");
        } catch (err) {
            setErro(err instanceof Error ? err.message : "Erro ao entrar. Tente novamente.");
        } finally {
            setSubmitting(false);
        }
    };

    if (loading) return <GlobalLoader />;

    return (
        <div
            className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden"
            style={{ backgroundColor: C.bg }}
        >
            {/* Background orbs */}
            <div style={{
                position: "absolute", top: "-20%", left: "-10%",
                width: "500px", height: "500px", borderRadius: "50%",
                background: `radial-gradient(circle, ${C.avocado}18 0%, transparent 70%)`,
                pointerEvents: "none",
            }} />
            <div style={{
                position: "absolute", bottom: "-10%", right: "-5%",
                width: "400px", height: "400px", borderRadius: "50%",
                background: `radial-gradient(circle, ${C.avocadoLight}12 0%, transparent 70%)`,
                pointerEvents: "none",
            }} />

            <div className="w-full max-w-sm relative z-10">
                {/* Logo */}
                <div className="text-center mb-8">
                    <div
                        className="w-16 h-16 rounded-2xl flex items-center justify-center text-3xl mx-auto mb-4 shadow-lg"
                        style={{ backgroundColor: C.avocado }}
                    >
                        🥑
                    </div>
                    <h1 className="text-2xl font-bold">GestãoFinanceira</h1>
                    <p className="text-sm mt-1" style={{ color: C.muted }}>
                        Entre para acessar seu painel financeiro
                    </p>
                </div>

                {/* Card */}
                <div
                    className="rounded-2xl p-6"
                    style={{ backgroundColor: C.surface, border: `1px solid ${C.border}` }}
                >
                    <form onSubmit={handleSubmit} className="space-y-4">
                        {/* Email */}
                        <div>
                            <label className="text-xs font-medium block mb-1.5" style={{ color: C.muted }}>
                                Email
                            </label>
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="seu@email.com"
                                required
                                autoComplete="email"
                                className="w-full rounded-xl px-4 py-3 text-sm outline-none transition-all"
                                style={{
                                    backgroundColor: C.elevated,
                                    border: `1px solid ${C.border}`,
                                }}
                                onFocus={(e) => (e.currentTarget.style.borderColor = C.avocado)}
                                onBlur={(e) => (e.currentTarget.style.borderColor = C.border)}
                            />
                        </div>

                        {/* Password */}
                        <div>
                            <label className="text-xs font-medium block mb-1.5" style={{ color: C.muted }}>
                                Senha
                            </label>
                            <div className="relative">
                                <input
                                    type={showPwd ? "text" : "password"}
                                    value={senha}
                                    onChange={(e) => setSenha(e.target.value)}
                                    placeholder="••••••••"
                                    required
                                    autoComplete="current-password"
                                    className="w-full rounded-xl px-4 py-3 pr-11 text-sm outline-none transition-all"
                                    style={{ backgroundColor: C.elevated, border: `1px solid ${C.border}` }}
                                    onFocus={(e) => (e.currentTarget.style.borderColor = C.avocado)}
                                    onBlur={(e) => (e.currentTarget.style.borderColor = C.border)}
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPwd(!showPwd)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-lg"
                                    style={{ color: C.muted }}
                                >
                                    {showPwd ? "🙈" : "👁️"}
                                </button>
                            </div>
                        </div>

                        {/* Error */}
                        {erro && (
                            <div
                                className="text-xs px-3 py-2.5 rounded-lg flex items-center gap-2"
                                style={{ backgroundColor: `${C.danger}18`, color: C.danger, border: `1px solid ${C.danger}40` }}
                            >
                                ⚠️ {erro}
                            </div>
                        )}

                        {/* Submit */}
                        <button
                            type="submit"
                            disabled={submitting}
                            className="w-full py-3 rounded-xl text-sm font-semibold text-white transition-all hover:opacity-90 disabled:opacity-50 mt-2"
                            style={{ backgroundColor: C.avocado }}
                        >
                            {submitting ? "Entrando..." : "Entrar"}
                        </button>
                    </form>

                    {/* Demo hint 
                    <div
                        className="mt-4 px-3 py-2.5 rounded-lg text-xs text-center"
                        style={{ backgroundColor: `${C.avocado}14`, color: C.avocado, border: `1px solid ${C.avocado}30` }}
                    >
                        🥑 Conta demo pré-preenchida — clique em <strong>Entrar</strong>
                    </div>
                    */}
                </div>

                <p className="text-center text-xs mt-6" style={{ color: C.muted }}>
                    GestãoFinanceira v2.0 — Todos os direitos reservados
                </p>
            </div>

            <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(12px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        form > * { animation: fadeIn 0.3s ease-out both; }
        form > *:nth-child(1) { animation-delay: 0.05s; }
        form > *:nth-child(2) { animation-delay: 0.10s; }
        form > *:nth-child(3) { animation-delay: 0.15s; }
        form > *:nth-child(4) { animation-delay: 0.20s; }
      `}</style>
        </div>
    );
}
