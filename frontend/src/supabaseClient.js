import { createClient } from '@supabase/supabase-js';

export const getSupabaseClient = (url, key) => {
  return createClient(url, key);
};
