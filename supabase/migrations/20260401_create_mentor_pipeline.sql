CREATE TABLE IF NOT EXISTS mentor_pipeline (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT,
  phone TEXT,
  stage TEXT NOT NULL DEFAULT 'applied',
  hs_stage TEXT,
  tg_score INTEGER,
  tg_done BOOLEAN DEFAULT FALSE,
  application_message TEXT,
  location TEXT,
  age TEXT,
  source TEXT,
  why_mentor TEXT,
  has_laptop TEXT,
  hours_week TEXT,
  three_month_commit TEXT,
  notes JSONB DEFAULT '{}',
  checklist JSONB DEFAULT '{}',
  scores JSONB DEFAULT '{}',
  interview_date TEXT,
  interview_session TEXT,
  created_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  synced_from_hs_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_updated_at ON mentor_pipeline;
CREATE TRIGGER set_updated_at
  BEFORE UPDATE ON mentor_pipeline
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

ALTER TABLE mentor_pipeline ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow anon read" ON mentor_pipeline;
DROP POLICY IF EXISTS "Allow anon update" ON mentor_pipeline;
DROP POLICY IF EXISTS "Allow anon insert" ON mentor_pipeline;
CREATE POLICY "Allow anon read" ON mentor_pipeline FOR SELECT USING (true);
CREATE POLICY "Allow anon update" ON mentor_pipeline FOR UPDATE USING (true);
CREATE POLICY "Allow anon insert" ON mentor_pipeline FOR INSERT WITH CHECK (true);

ALTER PUBLICATION supabase_realtime ADD TABLE mentor_pipeline;
