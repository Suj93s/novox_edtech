import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const supabase = createClient(
  Deno.env.get('SUPABASE_URL') ?? '',
  Deno.env.get('SUPABASE_ANON_KEY') ?? '' // Note: Requires SERVICE_ROLE_KEY for queue updates in production
);

const GEMINI_API_KEY = Deno.env.get('GEMINI_API_KEY') ?? '';

serve(async (req) => {
  console.log("Mastery Worker Started");
  try {
    // 1. Fetch up to 5 pending jobs from the queue SAFELY using SKIP LOCKED
    const { data: jobs, error: fetchError } = await supabase
      .rpc('claim_mastery_jobs', { p_limit: 5 });

    if (fetchError) throw fetchError;
    if (!jobs || jobs.length === 0) {
      console.log("No pending jobs found.");
      return new Response("No pending jobs", { status: 200 });
    }

    console.log(`Processing ${jobs.length} jobs...`);

    const CANONICAL_TOPICS = [
        "javascript", "typescript", "react", "nodejs", "express", "mongodb", "sql", "git", "system_design", "python", "django", "docker",
        "ui_design", "ux_research", "typography", "color_theory", "figma", "accessibility",
        "seo", "paid_ads", "content_marketing", "analytics", "conversion_optimization"
    ];

    // 2. Process each job
    for (const job of jobs) {
      try {
        const evaluationPrompt = `
          You are an AI Mastery Evaluator for the "${job.layer}" layer.
          Analyze the following recent conversation.
          Identify which technical topics were discussed.
          You MUST use ONLY the following exact canonical snake_case names: ${JSON.stringify(CANONICAL_TOPICS)}.
          If the user discussed React Hooks, map it to "react". If they discussed CSS, map it to "ui_design".
          Do NOT invent new topics.
          For each topic, evaluate the student's demonstrated understanding.
          Output ONLY valid JSON in this format:
          [
            { "topic": "react", "delta": 5 }
          ]
          Rules for delta:
          - Highly correct/advanced understanding: +5 to +10
          - Minor corrections needed: +1 to +3
          - Complete misunderstanding: -2 to -5
          
          Conversation:
          ${JSON.stringify(job.recent_messages)}
        `;

        const geminiRes = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${GEMINI_API_KEY}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            contents: [{ role: "user", parts: [{ text: evaluationPrompt }] }],
            generationConfig: { response_mime_type: "application/json" }
          })
        });

        if (!geminiRes.ok) throw new Error("Gemini API failed");
        
        const geminiData = await geminiRes.json();
        const text = geminiData.candidates[0].content.parts[0].text;
        const evaluations: { topic: string; delta: number }[] = JSON.parse(text.replace(/```json/g, '').replace(/```/g, ''));

        // Call RPC for each topic
        for (const evalResult of evaluations) {
          if (!CANONICAL_TOPICS.includes(evalResult.topic)) continue; // Extra safety guard
          const { error: rpcError } = await supabase.rpc('update_topic_mastery', {
            p_user_id: job.user_id,
            p_topic: evalResult.topic,
            p_delta: evalResult.delta
          });
          if (rpcError) throw rpcError;
        }

        // Mark complete
        await supabase.from('mastery_evaluation_queue')
          .update({ status: 'completed', processed_at: new Date().toISOString() })
          .eq('id', job.id);
          
        console.log(`Job ${job.id} completed successfully.`);

      } catch (jobError: any) {
        console.error(`Job ${job.id} failed:`, jobError.message);
        // Mark failed for retry, fetch current retry_count first
        const { data: currentJob } = await supabase.from('mastery_evaluation_queue').select('retry_count').eq('id', job.id).single();
        const newRetryCount = (currentJob?.retry_count || 0) + 1;
        await supabase.from('mastery_evaluation_queue')
          .update({ 
            status: 'failed', 
            error_log: jobError.message,
            processed_at: new Date().toISOString(),
            retry_count: newRetryCount
          })
          .eq('id', job.id);
      }
    }

    return new Response(JSON.stringify({ success: true, processed: jobs.length }), {
      headers: { "Content-Type": "application/json" },
    });

  } catch (error: any) {
    console.error("Worker Global Error:", error.message);
    return new Response(error.message, { status: 500 });
  }
});
