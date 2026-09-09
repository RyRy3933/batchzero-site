/* Batch Zero — runtime config. Safe to commit: the anon key is public by design
   (the database only lets it INSERT into `applications`, never read). */
window.B0_CONFIG = {
  SUPABASE_URL: "",        // e.g. "https://abcdefghijklmnop.supabase.co"
  SUPABASE_ANON_KEY: "",   // Project Settings → API → anon public
  TABLE: "applications",
};
