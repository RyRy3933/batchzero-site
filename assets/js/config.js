/* Batch Zero — runtime config. Safe to commit: the anon key is public by design
   (the database only lets it INSERT into `applications`, never read). */
window.B0_CONFIG = {
  SUPABASE_URL: "https://lzinyfukedgytwvgszna.supabase.co",        // e.g. "https://abcdefghijklmnop.supabase.co"
  SUPABASE_ANON_KEY: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx6aW55ZnVrZWRneXR3dmdzem5hIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODg5NzIxNjEsImV4cCI6MjEwNDU0ODE2MX0.ilAmaqe_ZrHVHQ13oWWWd6Rl1gLVdN75aggmh43Dgt4",   // Project Settings → API → anon public
  TABLE: "applications",
};
