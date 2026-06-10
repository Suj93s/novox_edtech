-- SQL schema with Supabase Auth, Row Level Security (RLS), and pgvector

-- Enable vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Create chat_sessions table linked to authenticated users
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Index for chat_sessions lookup by user_id
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id);

-- 2. Create chat_messages table
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Index for faster lookup of messages by session
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);

-- 3. Create student_profiles table linked to auth.users
CREATE TABLE IF NOT EXISTS student_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    behavioral_chart JSONB NOT NULL DEFAULT '{"explicit_directives": [], "inferred_traits": []}'::jsonb,
    system_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Index for faster lookup of profiles by user_id
CREATE UNIQUE INDEX IF NOT EXISTS idx_student_profiles_user_id ON student_profiles(user_id);

-- 4. Create novox_curriculum table (Course management, independent of individual user ownership)
CREATE TABLE IF NOT EXISTS novox_curriculum (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_name TEXT NOT NULL,
    module_title TEXT NOT NULL,
    concepts JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (course_name, module_title)
);

-- Index for lookup by course and module
CREATE INDEX IF NOT EXISTS idx_novox_curriculum_course_module ON novox_curriculum(course_name, module_title);

-- 5. Create student_mastery table linked to auth.users and novox_curriculum
CREATE TABLE IF NOT EXISTS student_mastery (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    module_id UUID REFERENCES novox_curriculum(id) ON DELETE CASCADE NOT NULL,
    proficiency_score NUMERIC(3, 2) NOT NULL DEFAULT 0.00 CHECK (proficiency_score >= 0.00 AND proficiency_score <= 1.00),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (user_id, module_id)
);

-- Index for faster lookup of mastery by user and module
CREATE UNIQUE INDEX IF NOT EXISTS idx_student_mastery_user_module ON student_mastery(user_id, module_id);

-- 6. Create document_chunks table with User Ownership
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    document_id UUID NOT NULL,
    document_name TEXT NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding VECTOR(1536) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes for document chunks
CREATE INDEX IF NOT EXISTS idx_document_chunks_user_id ON document_chunks(user_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding ON document_chunks USING hnsw (embedding vector_cosine_ops);


-- ==========================================
-- SQL SIMILARITY SEARCH FUNCTION
-- ==========================================

CREATE OR REPLACE FUNCTION match_document_chunks (
    query_embedding VECTOR(1536),
    match_threshold FLOAT,
    match_count INT,
    p_user_id UUID
)
RETURNS TABLE (
    id UUID,
    document_id UUID,
    document_name TEXT,
    chunk_text TEXT,
    similarity FLOAT
)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT
        document_chunks.id,
        document_chunks.document_id,
        document_chunks.document_name,
        document_chunks.chunk_text,
        1 - (document_chunks.embedding <=> query_embedding) AS similarity
    FROM document_chunks
    WHERE document_chunks.user_id = p_user_id
      AND 1 - (document_chunks.embedding <=> query_embedding) > match_threshold
    ORDER BY document_chunks.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;


-- ==========================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ==========================================

-- Enable Row Level Security (RLS) on all user-owned tables
ALTER TABLE student_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_mastery ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;

-- student_profiles policies
CREATE POLICY "Users can only view their own student profile" ON student_profiles
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can only update their own student profile" ON student_profiles
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own student profile" ON student_profiles
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- student_mastery policies
CREATE POLICY "Users can only view their own student mastery" ON student_mastery
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can only modify/all their own student mastery" ON student_mastery
    FOR ALL USING (auth.uid() = user_id);

-- chat_sessions policies
CREATE POLICY "Users can only view/all their own chat sessions" ON chat_sessions
    FOR ALL USING (auth.uid() = user_id);

-- chat_messages policies (authorized by verifying ownership of parent chat session)
CREATE POLICY "Users can only access messages in their own sessions" ON chat_messages
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM chat_sessions 
            WHERE chat_sessions.id = chat_messages.session_id 
            AND chat_sessions.user_id = auth.uid()
        )
    );

-- document_chunks policies
CREATE POLICY "Users can only view their own document chunks" ON document_chunks
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can only modify/all their own document chunks" ON document_chunks
    FOR ALL USING (auth.uid() = user_id);
