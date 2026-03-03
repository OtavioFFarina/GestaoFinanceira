/**
 * Centralized API configuration.
 * Uses NEXT_PUBLIC_API_URL env var, falls back to the production backend URL.
 * Ensures HTTPS in production — never hardcodes ports or HTTP protocol.
 */
export const API_BASE: string =
    process.env.NEXT_PUBLIC_API_URL ||
    "https://agilizagestaofinanceirabackend.up.railway.app/api";
