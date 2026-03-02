"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import AppNav from "@/components/layout/AppNav";
import GlobalLoader from "@/components/ui/GlobalLoader";
import { User } from "lucide-react"; // Added import for User icon

const C = {
    bg: "var(--bg)", surface: "var(--surface)", elevated: "var(--elevated)",
    border: "var(--border)", muted: "var(--muted)", avocado: "var(--avocado)",
    danger: "var(--danger)", text: "var(--text)", warning: "var(--warning)"
};

const API_BASE =
    typeof window !== "undefined"
        ? `http://${window.location.hostname}:8000/api`
        : "http://localhost:8000/api";

function Toggle({ value, onChange }: { value: boolean; onChange: (v: boolean) => void }) {
    return (
        <div onClick={() => onChange(!value)}
            className="w-12 h-6 rounded-full relative cursor-pointer transition-colors"
            style={{ backgroundColor: value ? C.avocado : C.elevated, border: `1px solid ${C.border}` }}>
            <div className="absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform"
                style={{ transform: value ? "translateX(26px)" : "translateX(2px)" }} />
        </div>
    );
}

export default function ConfiguracoesPage() {
    const { user, updateUser, loading: authLoading } = useAuth();
    const router = useRouter();
    const [tema, setTema] = useState<"dark" | "light">("dark");
    const [mesesHistorico, setMesesHistorico] = useState(12);
    const [nomeExibicao, setNomeExibicao] = useState("");
    const [saving, setSaving] = useState(false);
    const [saved, setSaved] = useState(false);

    useEffect(() => {
        if (!authLoading && !user) router.replace("/login");
        if (user) {
            setNomeExibicao(user.nome_exibicao);
            setTema(user.tema);
        }
    }, [user, authLoading, router]);

    const saveSettings = async () => {
        if (!user) return;
        setSaving(true);
        try {
            await fetch(`${API_BASE}/perfil/${user.usuario_id}`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ nome_exibicao: nomeExibicao, tema, meses_historico: mesesHistorico }),
            });
            updateUser({ nome_exibicao: nomeExibicao, tema });
            setSaved(true);
            setTimeout(() => setSaved(false), 3000);
        } finally { setSaving(false); }
    };

    const deleteData = async () => {
        if (!user) return;
        if (!confirm("Tem certeza? Esta ação apagará todas as suas transações, metas e ciclos permanetemente. O seu perfil e login serão mantidos.")) return;
        setSaving(true);
        try {
            const res = await fetch(`${API_BASE}/perfil/${user.usuario_id}/dados`, { method: "DELETE" });
            if (!res.ok) throw new Error("Erro ao excluir dados.");
            alert("Dados excluídos com sucesso. A página será recarregada.");
            window.location.href = "/";
        } catch (err) {
            alert(err instanceof Error ? err.message : "Erro.");
        } finally {
            setSaving(false);
        }
    };


    if (authLoading) return <GlobalLoader />;
    if (!user) return null;

    return (
        <div className="min-h-screen font-sans antialiased" style={{ backgroundColor: "var(--bg)", color: "var(--text)" }}>
            <AppNav activeItem="Configurações" />

            <main className="max-w-2xl mx-auto px-4 md:px-6 py-6 md:py-8">
                <h1 className="text-2xl font-bold mt-1 mb-6">Configurações</h1>

                {/* Profile Section */}
                <div className="rounded-2xl p-5 mb-4" style={{ backgroundColor: C.surface, border: `1px solid ${C.border}` }}>
                    <h2 className="text-sm font-semibold mb-4 flex items-center gap-2" style={{ color: "var(--text)" }}>
                        <User size={16} style={{ color: "var(--avocado)" }} /> Perfil
                    </h2>
                    <div className="space-y-4">
                        <div>
                            <label className="block text-xs font-medium mb-1.5" style={{ color: "var(--muted)" }}>Nome de exibição</label>
                            <input
                                type="text"
                                value={nomeExibicao}
                                onChange={e => setNomeExibicao(e.target.value)}
                                className="w-full rounded-xl px-4 py-2.5 text-sm transition-colors focus:outline-none"
                                style={{ backgroundColor: "var(--elevated)", border: `1px solid var(--border)`, color: "var(--text)" }}
                            />
                        </div>
                        <div>
                            <label className="block text-xs font-medium mb-1.5" style={{ color: "var(--muted)" }}>Email</label>
                            <input
                                type="email"
                                value={user.email}
                                disabled
                                className="w-full rounded-xl px-4 py-2.5 text-sm opacity-50 cursor-not-allowed"
                                style={{ backgroundColor: "var(--elevated)", border: `1px solid var(--border)`, color: "var(--text)" }}
                            />
                            <p className="text-xs mt-1.5" style={{ color: "var(--muted)" }}>Não é possível alterar o email agora.</p>
                        </div>
                    </div>
                </div>

                {/* Appearance Section */}
                <Section title="🎨 Aparência">
                    <Field label="Tema da interface">
                        <div className="flex gap-3">
                            {(["dark", "light"] as const).map(t => (
                                <button key={t} onClick={() => setTema(t)}
                                    className="flex-1 py-2.5 rounded-xl text-sm font-medium border transition-all"
                                    style={{
                                        backgroundColor: tema === t ? `${C.avocado}20` : C.elevated,
                                        borderColor: tema === t ? C.avocado : C.border,
                                        color: tema === t ? C.avocado : C.muted,
                                    }}>
                                    {t === "dark" ? "🌙 Dark" : "☀️ Light"}
                                </button>
                            ))}
                        </div>
                    </Field>
                </Section>

                {/* Data Section */}
                <Section title="📊 Dados">
                    <Field label="Retenção de histórico" hint={`Manter os últimos ${mesesHistorico} meses de dados.`}>
                        <div className="flex items-center gap-3">
                            <input type="range" min={1} max={60} value={mesesHistorico}
                                onChange={e => setMesesHistorico(Number(e.target.value))}
                                className="flex-1 accent-avocado"
                                style={{ accentColor: C.avocado }} />
                            <span className="text-sm font-semibold w-16 text-right">{mesesHistorico} meses</span>
                        </div>
                    </Field>
                </Section>

                {/* Danger Zone */}
                <Section title="⚠️ Zona de Perigo">
                    <div className="rounded-xl p-4" style={{ backgroundColor: `${C.danger}10`, border: `1px solid ${C.danger}40` }}>
                        <p className="text-sm font-medium mb-1">Excluir todos os dados</p>
                        <p className="text-xs mb-3" style={{ color: C.muted }}>
                            Remove permanentemente todos os ciclos, transações e metas. Irreversível.
                        </p>
                        <button onClick={deleteData} disabled={saving} className="px-4 py-2 rounded-xl text-xs font-medium hover:opacity-80 transition-opacity disabled:opacity-50"
                            style={{ backgroundColor: `${C.danger}20`, color: C.danger, border: `1px solid ${C.danger}40` }}>
                            Excluir meus dados
                        </button>
                    </div>
                </Section>

                {/* Save Button */}
                <div className="flex items-center gap-3 justify-end mt-6">
                    {saved && <span className="text-sm" style={{ color: C.avocado }}>✓ Salvo com sucesso!</span>}
                    <button onClick={saveSettings} disabled={saving}
                        className="px-6 py-2.5 rounded-xl text-sm font-semibold text-white hover:opacity-90 disabled:opacity-50 transition-opacity"
                        style={{ backgroundColor: C.avocado }}>
                        {saving ? "Salvando..." : "Salvar Configurações"}
                    </button>
                </div>
            </main>
        </div>
    );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
    return (
        <div className="rounded-2xl p-5 mb-4" style={{ backgroundColor: C.surface, border: `1px solid ${C.border}` }}>
            <h2 className="text-sm font-semibold mb-4">{title}</h2>
            <div className="space-y-4">{children}</div>
        </div>
    );
}

function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
    return (
        <div>
            <label className="text-xs font-medium block mb-1.5" style={{ color: C.muted }}>{label}</label>
            {children}
            {hint && <p className="text-xs mt-1.5" style={{ color: C.muted + "99" }}>{hint}</p>}
        </div>
    );
}
