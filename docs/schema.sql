CREATE TABLE hcps (
  id SERIAL PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  specialty VARCHAR(120) NOT NULL,
  territory VARCHAR(120) NOT NULL,
  segment VARCHAR(50) NOT NULL DEFAULT 'B',
  preferred_channel VARCHAR(50) NOT NULL DEFAULT 'In-person',
  last_contacted_at TIMESTAMP NULL
);

CREATE TABLE interactions (
  id SERIAL PRIMARY KEY,
  hcp_id INTEGER NOT NULL REFERENCES hcps(id),
  interaction_type VARCHAR(60) NOT NULL,
  channel VARCHAR(60) NOT NULL,
  occurred_at TIMESTAMP NOT NULL,
  product_discussed VARCHAR(120) NOT NULL,
  objective VARCHAR(200) NOT NULL,
  notes TEXT NOT NULL,
  summary TEXT NOT NULL,
  sentiment VARCHAR(30) NOT NULL DEFAULT 'neutral',
  commitment VARCHAR(240) NOT NULL DEFAULT '',
  next_step VARCHAR(240) NOT NULL DEFAULT '',
  follow_up_date VARCHAR(20) NOT NULL DEFAULT '',
  compliance_flags JSON NOT NULL,
  entities JSON NOT NULL,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL
);

CREATE TABLE agent_runs (
  id SERIAL PRIMARY KEY,
  user_message TEXT NOT NULL,
  selected_tool VARCHAR(120) NOT NULL,
  result JSON NOT NULL,
  created_at TIMESTAMP NOT NULL
);
