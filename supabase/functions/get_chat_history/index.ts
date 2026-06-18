import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
import { MongoClient } from "npm:mongodb";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  let mongoClient;
  try {
    const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
    const supabaseAnonKey = Deno.env.get("SUPABASE_ANON_KEY")!;
    const supabase = createClient(supabaseUrl, supabaseAnonKey);

    const { session_id } = await req.json();

    // Verify User
    const authHeader = req.headers.get('Authorization');
    if (!authHeader) {
        return new Response(JSON.stringify({ error: "Missing Auth Header" }), { status: 401, headers: corsHeaders });
    }
    const { data: { user }, error: authError } = await supabase.auth.getUser(authHeader.replace('Bearer ', ''));
    if (authError || !user) {
        return new Response(JSON.stringify({ error: "Unauthorized" }), { status: 401, headers: corsHeaders });
    }

    const MONGODB_URI = Deno.env.get("MONGODB_URI");
    if (!MONGODB_URI) throw new Error("Missing MONGODB_URI");

    mongoClient = new MongoClient(MONGODB_URI);
    await mongoClient.connect();
    const db = mongoClient.db("chat_logs_db");
    const messagesCollection = db.collection("chat_messages");

    const history = await messagesCollection.find({ session_id }).sort({ created_at: 1 }).toArray();
    const formattedHistory = history.map(msg => ({
      id: msg._id.toString(),
      role: msg.role === 'assistant' ? 'ai' : 'user',
      content: msg.content
    }));

    return new Response(JSON.stringify({ messages: formattedHistory }), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });

  } catch (error) {
    console.error(error);
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" }
    });
  } finally {
    if (mongoClient) {
      await mongoClient.close();
    }
  }
});
