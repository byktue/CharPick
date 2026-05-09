import { createClient } from "@supabase/supabase-js";

const supabaseUrl = "https://qwoogykgizcfsvkkcmdq.supabase.co";
const supabaseKey =
  import.meta.env.VITE_SUPABASE_KEY ||
  import.meta.env.VITE_SUPABASE_ANON_KEY ||
  (typeof process !== "undefined" ? process.env.SUPABASE_KEY : undefined);

if (!supabaseKey) {
  console.warn("Missing Supabase key. Set VITE_SUPABASE_KEY or VITE_SUPABASE_ANON_KEY in .env or .env.local.");
}

export const supabase = supabaseKey ? createClient(supabaseUrl, supabaseKey) : null;

export function getSupabaseClient() {
  if (!supabase) {
    throw new Error("Supabase key 未配置。请在 frontend_vue/.env.local 中设置 VITE_SUPABASE_KEY。配置后重启 npm run dev。");
  }
  return supabase;
}

export async function ensureAnonymousSession() {
  const client = getSupabaseClient();
  const { data: sessionData, error: sessionError } = await client.auth.getSession();
  if (sessionError) {
    throw sessionError;
  }
  if (sessionData?.session) {
    return sessionData.session;
  }

  const { data, error } = await client.auth.signInAnonymously();
  if (error) {
    throw error;
  }
  return data?.session || null;
}

export async function testSupabaseConnection() {
  const client = getSupabaseClient();
  const { data, error } = await client.from("users").select("*");

  if (error) {
    console.error("连接失败:", error.message);
    return { ok: false, data: null, error };
  }

  console.log("连接成功!", data);
  return { ok: true, data, error: null };
}
