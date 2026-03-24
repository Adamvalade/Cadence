"use client";

import { Button } from "@/components/ui/button";
import { API_BASE_URL } from "@/lib/api";

export function SpotifyAuthButton() {
  return (
    <Button
      variant="outline"
      size="lg"
      className="w-full border-[#1DB954] bg-[#1DB954] text-white hover:bg-[#1ed760] hover:text-white hover:border-[#1ed760]"
      nativeButton={false}
      render={<a href={`${API_BASE_URL}/auth/spotify`} />}
    >
      Continue with Spotify
    </Button>
  );
}
