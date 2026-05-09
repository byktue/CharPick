import { getSupabaseClient } from "../../lib/supabase";
import {
  buildUserScopedQuery,
  isMissingRelationError,
  pickFirst,
  resolveCurrentUserId,
} from "../core";

export function createCardApi() {
  return {
    async getCardList(bookId, settings) {
      const supabase = getSupabaseClient();
      const userId = await resolveCurrentUserId(supabase, settings?.auth_token);

      const query = buildUserScopedQuery({
        supabase,
        table: "card",
        select: "id, card_id, user_id, book_id, type, name, intro, content_local_url, content_oss_url, created_at, updated_at",
        userId,
        bookId,
        orders: [
          ["updated_at", false],
          ["created_at", false],
        ],
      });

      const { data, error } = await query;
      if (error) {
        if (isMissingRelationError(error, "card")) {
          return { cards: [] };
        }
        throw error;
      }

      return {
        cards: (data || []).map((item) => ({
          id: pickFirst(item, ["card_id", "id"]),
          user_id: item.user_id,
          book_id: item.book_id,
          type: item.type || "character",
          name: item.name || "未命名卡片",
          intro: item.intro || "",
          content_local_url: item.content_local_url || null,
          content_oss_url: item.content_oss_url || null,
          created_at: item.created_at || null,
          updated_at: item.updated_at || null,
        })),
      };
    },
  };
}
