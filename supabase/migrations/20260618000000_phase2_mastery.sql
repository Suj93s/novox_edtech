-- Step 1: Schema Updates
ALTER TABLE student_mastery 
ADD COLUMN IF NOT EXISTS topic_scores JSONB DEFAULT '{}'::jsonb;

CREATE INDEX IF NOT EXISTS idx_student_mastery_user_id ON student_mastery(user_id);

CREATE TABLE IF NOT EXISTS mastery_evaluation_queue (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    module_id UUID,
    course_id UUID,
    mentor_type VARCHAR(50),
    recent_messages JSONB NOT NULL,
    layer VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    error_log TEXT,
    retry_count INT DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_mastery_queue_status ON mastery_evaluation_queue(status);

-- Step 2: PostgreSQL RPC Function for Atomic JSONB Mastery Updates
CREATE OR REPLACE FUNCTION update_topic_mastery(
    p_user_id UUID,
    p_topic VARCHAR,
    p_delta NUMERIC
) RETURNS JSONB AS $$
DECLARE
    v_current_scores JSONB;
    v_topic_data JSONB;
    v_score NUMERIC;
    v_confidence NUMERIC;
    v_interaction_count INT;
    v_streak INT;
    v_last_delta NUMERIC;
    v_last_seen TIMESTAMP;
    v_decay_applied_at TIMESTAMP;
    v_base_confidence NUMERIC;
    v_volatility_penalty NUMERIC;
BEGIN
    -- BUGFIX: Safe Upsert to prevent INSERT race conditions
    INSERT INTO student_mastery (user_id, topic_scores) 
    VALUES (p_user_id, '{}'::jsonb) 
    ON CONFLICT (user_id) DO NOTHING;

    -- Fetch current JSONB, lock the row for update to prevent race conditions
    SELECT topic_scores INTO v_current_scores 
    FROM student_mastery 
    WHERE user_id = p_user_id 
    FOR UPDATE;

    -- Extract specific topic data or initialize defaults
    v_topic_data := COALESCE(v_current_scores->p_topic, '{
        "score": 50,
        "confidence": 0.1,
        "interaction_count": 0,
        "streak": 0,
        "last_delta": 0,
        "last_seen": "1970-01-01T00:00:00Z",
        "decay_applied_at": "1970-01-01T00:00:00Z"
    }'::jsonb);

    v_score := (v_topic_data->>'score')::NUMERIC;
    v_confidence := (v_topic_data->>'confidence')::NUMERIC;
    v_interaction_count := (v_topic_data->>'interaction_count')::INT;
    v_streak := (v_topic_data->>'streak')::INT;
    v_last_delta := (v_topic_data->>'last_delta')::NUMERIC;

    -- Calculate new score (clamped 0-100)
    v_score := GREATEST(0, LEAST(100, v_score + p_delta));
    
    -- Update interaction count and last seen
    v_interaction_count := v_interaction_count + 1;
    v_last_seen := NOW();

    -- Calculate Streak
    IF p_delta > 0 THEN
        v_streak := v_streak + 1;
    ELSIF p_delta < 0 THEN
        v_streak := 0;
    END IF;

    -- Calculate Confidence
    v_base_confidence := 1.0 - (1.0 / (1.0 + 0.3 * v_interaction_count));
    v_volatility_penalty := 0;
    
    IF SIGN(p_delta) != SIGN(v_last_delta) AND v_last_delta != 0 THEN
        v_volatility_penalty := 0.15;
    END IF;
    
    v_confidence := GREATEST(0.1, LEAST(1.0, v_base_confidence - v_volatility_penalty));

    -- Construct new topic object
    v_topic_data := jsonb_build_object(
        'score', v_score,
        'confidence', v_confidence,
        'interaction_count', v_interaction_count,
        'streak', v_streak,
        'last_delta', p_delta,
        'last_seen', v_last_seen,
        'decay_applied_at', COALESCE(v_topic_data->>'decay_applied_at', v_last_seen::TEXT)
    );

    -- Merge back into the full JSONB object
    v_current_scores := jsonb_set(v_current_scores, ARRAY[p_topic], v_topic_data);

    -- Update table
    UPDATE student_mastery 
    SET topic_scores = v_current_scores 
    WHERE user_id = p_user_id;

    RETURN v_topic_data;
END;
$$ LANGUAGE plpgsql;

-- Step 2.5: Queue Processor Function
-- BUGFIX: Resolves the JS concurrency race condition by locking queue rows safely
CREATE OR REPLACE FUNCTION claim_mastery_jobs(p_limit INT)
RETURNS TABLE (id INT, user_id UUID, module_id UUID, course_id UUID, mentor_type VARCHAR, recent_messages JSONB, layer VARCHAR) AS $$
BEGIN
    RETURN QUERY
    UPDATE mastery_evaluation_queue
    SET status = 'processing'
    WHERE id IN (
        SELECT q.id FROM mastery_evaluation_queue q
        WHERE q.status = 'pending' OR (q.status = 'failed' AND q.retry_count < 3)
        ORDER BY q.created_at ASC
        FOR UPDATE SKIP LOCKED
        LIMIT p_limit
    )
    RETURNING mastery_evaluation_queue.id, mastery_evaluation_queue.user_id, mastery_evaluation_queue.module_id, mastery_evaluation_queue.course_id, mastery_evaluation_queue.mentor_type, mastery_evaluation_queue.recent_messages, mastery_evaluation_queue.layer;
END;
$$ LANGUAGE plpgsql;

-- Step 3: pg_cron Job for Mastery Decay
CREATE EXTENSION IF NOT EXISTS pg_cron;

CREATE OR REPLACE FUNCTION apply_mastery_decay() RETURNS VOID AS $$
DECLARE
    r RECORD;
    v_topic_scores JSONB;
    v_topic TEXT;
    v_topic_data JSONB;
    v_days_inactive INT;
    v_weeks_inactive INT;
    v_confidence NUMERIC;
    v_score NUMERIC;
    v_weekly_decay_rate NUMERIC;
    v_total_decay NUMERIC;
BEGIN
    FOR r IN SELECT user_id, topic_scores FROM student_mastery LOOP
        v_topic_scores := r.topic_scores;
        
        FOR v_topic, v_topic_data IN SELECT * FROM jsonb_each(v_topic_scores) LOOP
            v_days_inactive := EXTRACT(EPOCH FROM (NOW() - (v_topic_data->>'last_seen')::TIMESTAMP)) / 86400;
            
            -- Check if grace period (30 days) passed and decay hasn't been applied in the last 7 days
            IF v_days_inactive > 30 AND EXTRACT(EPOCH FROM (NOW() - (v_topic_data->>'decay_applied_at')::TIMESTAMP)) / 86400 > 7 THEN
                v_weeks_inactive := FLOOR(v_days_inactive / 7);
                v_confidence := (v_topic_data->>'confidence')::NUMERIC;
                v_score := (v_topic_data->>'score')::NUMERIC;
                
                -- Formula: Base 2 points/wk, mitigated by confidence
                v_weekly_decay_rate := 2.0 * (1.1 - v_confidence);
                v_total_decay := v_weekly_decay_rate * v_weeks_inactive;
                
                -- Apply Decay
                v_score := GREATEST(0, v_score - v_total_decay);
                
                -- Update topic data
                v_topic_data := jsonb_set(v_topic_data, '{score}', to_jsonb(v_score));
                v_topic_data := jsonb_set(v_topic_data, '{decay_applied_at}', to_jsonb(NOW()));
                
                v_topic_scores := jsonb_set(v_topic_scores, ARRAY[v_topic], v_topic_data);
            END IF;
        END LOOP;
        
        -- Write back to DB
        UPDATE student_mastery SET topic_scores = v_topic_scores WHERE user_id = r.user_id;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

SELECT cron.schedule('mastery-decay-job', '0 0 * * *', 'SELECT apply_mastery_decay()');
