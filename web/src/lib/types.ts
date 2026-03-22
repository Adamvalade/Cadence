export interface UserBrief {
  id: string;
  email: string;
  username: string;
  display_name: string;
  avatar_url: string | null;
}

export interface UserProfile {
  id: string;
  username: string;
  display_name: string;
  avatar_url: string | null;
  bio: string | null;
  created_at: string;
  review_count: number;
  follower_count: number;
  following_count: number;
}

export interface Album {
  id: string;
  spotify_id: string | null;
  title: string;
  artist: string;
  release_year: number | null;
  cover_image_url: string | null;
  genre: string | null;
  created_at: string;
  avg_rating: number | null;
  review_count: number;
}

export interface AlbumSearchResult {
  spotify_id: string;
  title: string;
  artist: string;
  release_year: number | null;
  cover_image_url: string | null;
  existing_id: string | null;
}

export interface Review {
  id: string;
  user_id: string;
  album_id: string;
  rating: number;
  body: string | null;
  is_relisten: boolean;
  created_at: string;
  updated_at: string;
  like_count: number;
  liked_by_me: boolean;
  username: string;
  user_avatar_url: string | null;
  album_title: string;
  album_artist: string;
  album_cover_url: string | null;
}

export interface FeedResponse {
  items: Review[];
  has_more: boolean;
  next_cursor: string | null;
}

export interface ListItem {
  id: string;
  album_id: string;
  position: number;
  album_title: string;
  album_artist: string;
  album_cover_url: string | null;
}

export interface UserList {
  id: string;
  user_id: string;
  title: string;
  description: string | null;
  is_public: boolean;
  created_at: string;
  items: ListItem[];
}
