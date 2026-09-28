# supabase/

SQL for batchzero.co. Run these in **Supabase → SQL Editor**, in this order. Every file is
idempotent — running one twice is safe.

| file | what it does | run it? |
|---|---|---|
| `schema.sql` | `public.applications` + its insert-only RLS policy. The five application forms write here. | once, at setup |
| `ambassadors.sql` | Adds `'ambassador'` to the allowed types, in **both** the column CHECK and the insert policy. Without it every ambassador application is rejected. | ✅ run 2026-09-27 |
| `mentor-invites.sql` | **Documentation**, not a migration. Describes what is live for the mentor invite flow, read out of the catalog. Section 1 refuses to run if `public.mentors` already exists. | don't run |
| `mentor-roster.sql` | `list_mentors()`, `save_mentor_photo()`, the `listed_at` trigger, and the `photo_url` / `published` / `listed_at` columns. This is what puts a mentor on `/network/`. | ✅ run 2026-09-27 |
| `ambassador-roster.sql` | `public.ambassadors`, the three invite functions, `list_ambassadors()`. Lifts the admin key out of `create_mentor_invite()` into `private.settings` so both invite tools share one key. | ✅ run 2026-09-27 |

## The two rules everything here follows

1. **The anon key never reads a table directly.** It may only `execute` `security definer`
   functions that return exactly the columns a public page shows. `public.applications`,
   `public.mentors` and `public.ambassadors` all have RLS on and no select policy for `anon`.
2. **An invite token is a password for one row.** Never post one publicly, and never widen a
   `get_*_invite()` function to return more than the signup form needs to prefill itself.

## Checking what's live

```sql
-- every function the public key can call, and what it returns
select p.proname, pg_get_function_identity_arguments(p.oid) as args, p.prosecdef as security_definer
  from pg_proc p join pg_namespace n on n.oid = p.pronamespace
 where n.nspname = 'public'
 order by 1;

-- who is on the site right now
select * from public.list_mentors();
select * from public.list_ambassadors();
```

## The admin key

`create_mentor_invite()` checks a constant declared in its own body. `create_ambassador_invite()`
checks `private.settings` where key `= 'ambassador_admin_key'`. `ambassador-roster.sql` copied the
first into the second so there is one key to remember — **if you rotate it, change both.**
