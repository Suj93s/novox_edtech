-- Enable vector extension if needed later, but primarily focused on requirements
CREATE EXTENSION IF NOT EXISTS vector;

-- novox_curriculum: Static table for course, module, and concepts
CREATE TABLE IF NOT EXISTS novox_curriculum (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_name TEXT NOT NULL,
    module_title TEXT NOT NULL,
    concepts JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (course_name, module_title)
);

-- student_mastery: Tracks proficiency score 0.0 to 1.0
CREATE TABLE IF NOT EXISTS student_mastery (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    module_id UUID REFERENCES novox_curriculum(id) ON DELETE CASCADE NOT NULL,
    proficiency_score NUMERIC(3, 2) NOT NULL DEFAULT 0.00 CHECK (proficiency_score >= 0.00 AND proficiency_score <= 1.00),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (user_id, module_id)
);

-- chat_sessions: Groups messages by session, stores global_context summary
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    course_name TEXT, -- optional to link to a course tile
    global_context TEXT, -- used for long-term memory of quirks/learning habits
    created_at TIMESTAMPTZ DEFAULT now()
);

-- messages: Raw chat logs
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- RLS
ALTER TABLE novox_curriculum ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_mastery ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can read curriculum" ON novox_curriculum FOR SELECT USING (true);
CREATE POLICY "Users can access their own mastery" ON student_mastery FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can access their own sessions" ON chat_sessions FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can access their own messages" ON messages FOR ALL USING (
    EXISTS (
        SELECT 1 FROM chat_sessions 
        WHERE chat_sessions.id = messages.session_id 
        AND chat_sessions.user_id = auth.uid()
    )
);
