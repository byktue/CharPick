import { getSupabaseClient } from "../../lib/supabase";
import {
  buildUserScopedQuery,
  isMissingRelationError,
  pickFirst,
  resolveCurrentUserId,
  summaryNameByType,
} from "../core";

export function createSummaryApi() {
  return {
    async getSummaryList(bookId, settings) {
      const supabase = getSupabaseClient();
      const userId = await resolveCurrentUserId(supabase, settings?.auth_token);

      const query = buildUserScopedQuery({
        supabase,
        table: "summary",
        select: "id, summary_id, user_id, book_id, type, name, content_local_url, content_oss_url, created_at, updated_at",
        userId,
        bookId,
        orders: [
          ["updated_at", false],
          ["created_at", false],
        ],
      });

      const { data, error } = await query;
      if (error) {
        if (isMissingRelationError(error, "summary")) {
          return { summaries: [] };
        }
        throw error;
      }

      return {
        summaries: (data || []).map((item) => ({
          id: pickFirst(item, ["summary_id", "id"]),
          user_id: item.user_id,
          book_id: item.book_id,
          type: item.type || "",
          name: item.name || summaryNameByType(item.type),
          content_local_url: item.content_local_url || null,
          content_oss_url: item.content_oss_url || null,
          created_at: item.created_at || null,
          updated_at: item.updated_at || null,
        })),
      };
    },
  };
}
