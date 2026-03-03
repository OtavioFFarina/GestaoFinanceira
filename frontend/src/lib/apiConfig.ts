// Pega a URL limpa do Railway (sem o /api)
const rawUrl = process.env.NEXT_PUBLIC_API_URL || "https://agilizagestaofinanceirabackend.up.railway.app";

// Remove qualquer barra sobrando no final e força o /api, ficando à prova de balas
export const API_BASE = `${rawUrl.replace(/\/$/, '')}/api`;