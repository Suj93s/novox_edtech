import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

serve(async (req) => {
  // Handle CORS
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
    const supabaseAnonKey = Deno.env.get("SUPABASE_ANON_KEY")!;
    const supabase = createClient(supabaseUrl, supabaseAnonKey);

    const { message, session_id } = await req.json();

    // Verify User via Auth Header
    const authHeader = req.headers.get('Authorization');
    if (!authHeader) {
        return new Response(JSON.stringify({ error: "Missing Auth Header" }), { status: 401, headers: corsHeaders });
    }
    const { data: { user }, error: authError } = await supabase.auth.getUser(authHeader.replace('Bearer ', ''));
    if (authError || !user) {
        return new Response(JSON.stringify({ error: "Unauthorized" }), { status: 401, headers: corsHeaders });
    }

    // 1. Initial Routing using a Lightweight Model
    const GEMINI_API_KEY = Deno.env.get("GEMINI_API_KEY");
    const GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions";
    
    const routerPrompt = `
      Analyze the user's message and categorize it into exactly one of the following routes:
      1. placement_relation
      2. malicious
      3. doubts
      4. course_walkthrough
      5. behavior_update
      Message: "${message}"
      Reply ONLY with the route name.
    `;

    // Fetch initial routing decision using Gemini API directly (OpenAI compatibility endpoint)
    const routeRes = await fetch(GEMINI_API_URL, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${GEMINI_API_KEY}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        model: "gemini-2.5-flash", // Using the lightweight Flash model
        messages: [{ role: "user", content: routerPrompt }]
      })
    });
    
    const routeData = await routeRes.json();
    const route = routeData.choices?.[0]?.message?.content?.trim() || "doubts";

    // 2. Fetch Global Context and Mastery
    const { data: sessionData } = await supabase.from('chat_sessions').select('global_context').eq('id', session_id).single();
    const globalContext = sessionData?.global_context || "";
    
    const { data: masteryData } = await supabase.from('student_mastery').select('module_id, proficiency_score').eq('user_id', user.id);
    const masteryString = masteryData ? JSON.stringify(masteryData) : "No mastery data";

    // 3. Prepare System Prompt based on Route
    let systemPrompt = `You are the Novox AI Mentor. User's Global Context: ${globalContext}. Student Mastery: ${masteryString}. `;
    let targetModel = "gemini-2.5-pro"; // Default to stronger model for final response

    if (route === "malicious") {
        systemPrompt += "The user has asked a malicious query. Intercept it professionally and firmly. Do not answer the query.";
        targetModel = "gemini-2.5-flash"; // Fast rejection
    } else if (route === "behavior_update") {
        // Update behavior in DB immediately
        await supabase.from('chat_sessions').update({ global_context: `${globalContext}\nUser requested: ${message}` }).eq('id', session_id);
        systemPrompt += "Acknowledge the user's new behavioral preference and confirm you will follow it henceforth.";
    } else if (route === "placement_relation") {
        // Simulate GitHub Scraping here
        const mockGithubData = "GitHub Profile: 5 repos, 100 commits. Needs more open-source contributions.";
        systemPrompt += `You are evaluating a student's portfolio. Analyze this scraped GitHub data: ${mockGithubData}. Provide guidance on how to improve.`;
    } else if (route === "course_walkthrough") {
        systemPrompt += "The user wants a course walkthrough. Lay out a roadmap, mark milestones, and explain concepts without giving explicit final answers.";
    } else {
        // Default: Doubts
        systemPrompt += "The user has a doubt. Do NOT give explicit final answers. Guide them using the Socratic method and provide hints based on their proficiency score.";
    }

    // 4. Fetch Chat History (Last 10 messages)
    const { data: history } = await supabase.from('messages')
      .select('role, content')
      .eq('session_id', session_id)
      .order('created_at', { ascending: false })
      .limit(10);
      
    const chatHistory = (history || []).reverse().map(msg => ({
      role: msg.role === 'assistant' ? 'assistant' : 'user',
      content: msg.content
    }));

    const messages = [
      { role: "system", content: systemPrompt },
      ...chatHistory,
      { role: "user", content: message }
    ];

    // 5. Generate Streaming Response using direct Gemini API
    const streamRes = await fetch(GEMINI_API_URL, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${GEMINI_API_KEY}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        model: targetModel,
        messages: messages,
        stream: true
      })
    });

    if (!streamRes.ok) {
        throw new Error(`Gemini API Error: ${streamRes.statusText}`);
    }

    // Return the ReadableStream directly to the client
    return new Response(streamRes.body, {
      headers: {
        ...corsHeaders,
        "Content-Type": "text/event-stream"
      }
    });

  } catch (error) {
    console.error(error);
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" }
    });
  }
});
