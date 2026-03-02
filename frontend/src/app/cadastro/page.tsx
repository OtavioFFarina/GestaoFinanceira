"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import GlobalLoader from "@/components/ui/GlobalLoader";

const C = {
    bg: "var(--bg)", surface: "var(--surface)", elevated: "var(--elevated)",
    border: "var(--border)", muted: "var(--muted)", text: "var(--text)",
    avocado: "var(--avocado)", avocadoLight: "var(--avocado-light)",
    success: "var(--success)", danger: "var(--danger)",
};

export default function CadastroPage() {
    const { user, loading } = useAuth();
    const router = useRouter();

    const [nome, setNome] = useState("");
    const [email, setEmail] = useState("");
    const [senha, setSenha] = useState("");
    const [confirmarSenha, setConfirmarSenha] = useState("");
    const [erro, setErro] = useState<string | null>(null);
    const [sucesso, setSucesso] = useState<string | null>(null);
    const [submitting, setSubmitting] = useState(false);
    const [showPwd, setShowPwd] = useState(false);

    // Redirect if already logged in
    useEffect(() => {
        if (!loading && user) router.replace("/");
    }, [user, loading, router]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setErro(null);
        setSucesso(null);

        // Client-side validations
        if (senha.length < 6) {
            setErro("A senha precisa ter no mínimo 6 caracteres.");
            return;
        }
        if (senha !== confirmarSenha) {
            setErro("As senhas não coincidem.");
            return;
        }

        setSubmitting(true);
        try {
            const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
            const response = await fetch(`${apiBase}/auth/register`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ nome, email, senha }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "Erro ao criar conta.");
            }

            setSucesso("Conta criada com sucesso! Redirecionando...");
            setTimeout(() => {
                router.push("/login");
            }, 2000);
        } catch (err) {
            setErro(err instanceof Error ? err.message : "Erro desconhecido.");
            setSubmitting(false); // Only re-enable button if error (success redirects)
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

            <div className="w-full max-w-sm relative z-10 my-8">
                {/* Logo */}
                <div className="text-center mb-8">
                    <div
                        className="w-16 h-16 rounded-2xl flex items-center justify-center text-3xl mx-auto mb-4 shadow-lg"
                        style={{ backgroundColor: C.avocado }}
                    >
                        🥑
                    </div>
                    <h1 className="text-2xl font-bold">Criar Conta</h1>
                    <p className="text-sm mt-1" style={{ color: C.muted }}>
                        Comece a gerenciar suas finanças hoje
                    </p>
                </div>

                {/* Card */}
                <div
                    className="rounded-2xl p-6"
                    style={{ backgroundColor: C.surface, border: `1px solid ${C.border}` }}
                >
                    <form onSubmit={handleSubmit} className="space-y-4">
                        {/* Nome */}
                        <div>
                            <label className="text-xs font-medium block mb-1.5" style={{ color: C.muted }}>
                                Nome
                            </label>
                            <input
                                type="text"
                                value={nome}
                                onChange={(e) => setNome(e.target.value)}
                                placeholder="Seu nome"
                                required
                                minLength={2}
                                className="w-full rounded-xl px-4 py-3 text-sm outline-none transition-all"
                                style={{
                                    backgroundColor: C.elevated,
                                    border: `1px solid ${C.border}`,
                                }}
                                onFocus={(e) => (e.currentTarget.style.borderColor = C.avocado)}
                                onBlur={(e) => (e.currentTarget.style.borderColor = C.border)}
                            />
                        </div>

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

                        {/* Senha */}
                        <div>
                            <label className="text-xs font-medium block mb-1.5" style={{ color: C.muted }}>
                                Senha
                            </label>
                            <div className="relative">
                                <input
                                    type={showPwd ? "text" : "password"}
                                    value={senha}
                                    onChange={(e) => setSenha(e.target.value)}
                                    placeholder="Mínimo 6 caracteres"
                                    required
                                    minLength={6}
                                    autoComplete="new-password"
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

                        {/* Confirmar Senha */}
                        <div>
                            <label className="text-xs font-medium block mb-1.5" style={{ color: C.muted }}>
                                Confirmar Senha
                            </label>
                            <div className="relative">
                                <input
                                    type={showPwd ? "text" : "password"}
                                    value={confirmarSenha}
                                    onChange={(e) => setConfirmarSenha(e.target.value)}
                                    placeholder="Repita sua senha"
                                    required
                                    minLength={6}
                                    autoComplete="new-password"
                                    className="w-full rounded-xl px-4 py-3 pr-11 text-sm outline-none transition-all"
                                    style={{ backgroundColor: C.elevated, border: `1px solid ${C.border}` }}
                                    onFocus={(e) => (e.currentTarget.style.borderColor = C.avocado)}
                                    onBlur={(e) => (e.currentTarget.style.borderColor = C.border)}
                                />
                            </div>
                        </div>

                        {/* Erro */}
                        {erro && (
                            <div
                                className="text-xs px-3 py-2.5 rounded-lg flex items-center gap-2"
                                style={{ backgroundColor: `${C.danger}18`, color: C.danger, border: `1px solid ${C.danger}40` }}
                            >
                                ⚠️ {erro}
                            </div>
                        )}

                        {/* Sucesso */}
                        {sucesso && (
                            <div
                                className="text-xs px-3 py-2.5 rounded-lg flex items-center gap-2 font-medium"
                                style={{ backgroundColor: `${C.success}18`, color: C.success, border: `1px solid ${C.success}40` }}
                            >
                                ✅ {sucesso}
                            </div>
                        )}

                        {/* Submit */}
                        <button
                            type="submit"
                            disabled={submitting || !!sucesso}
                            className="w-full py-3 rounded-xl text-sm font-semibold text-white transition-all hover:opacity-90 disabled:opacity-50 mt-2"
                            style={{ backgroundColor: C.avocado }}
                        >
                            {submitting ? "Criando conta..." : "Cadastrar"}
                        </button>
                    </form>

                    <div className="mt-5 text-center text-sm" style={{ color: C.muted }}>
                        Já possui uma conta?{" "}
                        <a href="/login" className="font-semibold transition-colors hover:underline" style={{ color: C.avocado }}>
                            Faça login
                        </a>
                    </div>
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
        form > *:nth-child(5) { animation-delay: 0.25s; }
      `}</style>
        </div>
    );
}
