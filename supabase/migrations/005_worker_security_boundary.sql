-- 1. Create the salesos_worker role
DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE  rolname = 'salesos_worker') THEN
      CREATE ROLE salesos_worker WITH LOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE PASSWORD 'worker';
   END IF;
END
$do$;

-- 2. Grant privileges on the schema
GRANT USAGE ON SCHEMA public TO salesos_worker;

-- 3. Grant table-specific permissions to salesos_worker
GRANT SELECT, UPDATE ON jobs TO salesos_worker;
GRANT SELECT ON sequence_enrollments TO salesos_worker;

-- 4. Restore salesos_backend jobs RLS to strict tenant isolation (Remove salesos.is_worker)
DROP POLICY IF EXISTS "tenant_isolation_jobs_select" ON jobs;
DROP POLICY IF EXISTS "tenant_isolation_jobs_insert" ON jobs;
DROP POLICY IF EXISTS "tenant_isolation_jobs_update" ON jobs;
DROP POLICY IF EXISTS "tenant_isolation_jobs_delete" ON jobs;

CREATE POLICY "tenant_isolation_jobs_select" ON jobs FOR SELECT TO salesos_backend
USING (workspace_id = get_app_workspace_id());
CREATE POLICY "tenant_isolation_jobs_insert" ON jobs FOR INSERT TO salesos_backend
WITH CHECK (workspace_id = get_app_workspace_id());
CREATE POLICY "tenant_isolation_jobs_update" ON jobs FOR UPDATE TO salesos_backend
USING (workspace_id = get_app_workspace_id()) WITH CHECK (workspace_id = get_app_workspace_id());
CREATE POLICY "tenant_isolation_jobs_delete" ON jobs FOR DELETE TO salesos_backend
USING (workspace_id = get_app_workspace_id());

-- 5. Create explicit RLS policies for salesos_worker
DROP POLICY IF EXISTS "worker_jobs_select" ON jobs;
DROP POLICY IF EXISTS "worker_jobs_update" ON jobs;
DROP POLICY IF EXISTS "worker_enrollments_select" ON sequence_enrollments;

CREATE POLICY "worker_jobs_select" ON jobs FOR SELECT TO salesos_worker USING (true);
CREATE POLICY "worker_jobs_update" ON jobs FOR UPDATE TO salesos_worker USING (true) WITH CHECK (true);
CREATE POLICY "worker_enrollments_select" ON sequence_enrollments FOR SELECT TO salesos_worker USING (true);

