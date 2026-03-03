// Pega a URL do Railway (pode ou não ter /api no final)
const rawUrl = process.env.NEXT_PUBLIC_API_URL || "https://agilizagestaofinanceirabackend.up.railway.app";

// Remove barra final e garante que termina com /api (sem duplicar)
const cleanUrl = rawUrl.replace(/\/+$/, '');
export const API_BASE = cleanUrl.endsWith('/api') ? cleanUrl : `${cleanUrl}/api`;