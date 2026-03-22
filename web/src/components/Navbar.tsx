"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Music, Search, LogOut, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { useAuth } from "@/lib/auth";

export default function Navbar() {
  const { user, logout } = useAuth();
  const router = useRouter();

  const handleLogout = async () => {
    await logout();
    router.push("/");
  };

  return (
    <nav className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center gap-2 font-bold text-lg">
            <Music className="h-5 w-5" />
            Cadence
          </Link>
          <Link href="/search" className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors">
            <Search className="h-4 w-4" />
            Search
          </Link>
          <Link href="/discover" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
            Discover
          </Link>
          {user && (
            <Link href="/feed" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Feed
            </Link>
          )}
        </div>

        <div className="flex items-center gap-3">
          {user ? (
            <DropdownMenu>
              <DropdownMenuTrigger
                render={<Button variant="ghost" className="relative h-8 w-8 rounded-full" />}
              >
                <Avatar className="h-8 w-8">
                  <AvatarImage src={user.avatar_url || undefined} alt={user.username} />
                  <AvatarFallback>{user.username[0].toUpperCase()}</AvatarFallback>
                </Avatar>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                <DropdownMenuItem onClick={() => router.push(`/${user.username}`)}>
                  <User className="mr-2 h-4 w-4" />
                  Profile
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => router.push("/settings")}>
                  Settings
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout}>
                  <LogOut className="mr-2 h-4 w-4" />
                  Log out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="sm" render={<Link href="/auth/login" />}>Log in</Button>
              <Button size="sm" render={<Link href="/auth/register" />}>Sign up</Button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}
