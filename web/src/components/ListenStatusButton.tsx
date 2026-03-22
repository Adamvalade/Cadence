"use client";

import { useState } from "react";
import { Headphones, Clock, CheckCircle2, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

type Status = "want_to_listen" | "listening" | "listened" | null;

const STATUS_CONFIG = {
  want_to_listen: { label: "Want to Listen", icon: Clock, color: "text-blue-500" },
  listening: { label: "Listening", icon: Headphones, color: "text-yellow-500" },
  listened: { label: "Listened", icon: CheckCircle2, color: "text-green-500" },
} as const;

interface ListenStatusButtonProps {
  albumId: string;
  initialStatus: Status;
}

export default function ListenStatusButton({ albumId, initialStatus }: ListenStatusButtonProps) {
  const [status, setStatus] = useState<Status>(initialStatus);
  const [updating, setUpdating] = useState(false);

  const handleSet = async (newStatus: "want_to_listen" | "listening" | "listened") => {
    if (newStatus === status) return;
    setUpdating(true);
    try {
      await api.put("/listen-status", { album_id: albumId, status: newStatus });
      setStatus(newStatus);
    } catch {
      // not authenticated or server error
    } finally {
      setUpdating(false);
    }
  };

  const handleRemove = async () => {
    setUpdating(true);
    try {
      await api.delete(`/listen-status/${albumId}`);
      setStatus(null);
    } catch {
      // already removed or not found
    } finally {
      setUpdating(false);
    }
  };

  const current = status ? STATUS_CONFIG[status] : null;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        render={
          <Button
            variant={status ? "outline" : "secondary"}
            size="sm"
            disabled={updating}
            className={cn(status && "gap-1.5")}
          />
        }
      >
        {current ? (
          <>
            <current.icon className={cn("h-4 w-4", current.color)} />
            {current.label}
          </>
        ) : (
          <>
            <Clock className="h-4 w-4 mr-1" />
            Track status
          </>
        )}
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start">
        {(Object.entries(STATUS_CONFIG) as [keyof typeof STATUS_CONFIG, (typeof STATUS_CONFIG)[keyof typeof STATUS_CONFIG]][]).map(
          ([key, config]) => (
            <DropdownMenuItem
              key={key}
              onClick={() => handleSet(key)}
              className={cn(status === key && "bg-accent")}
            >
              <config.icon className={cn("mr-2 h-4 w-4", config.color)} />
              {config.label}
              {status === key && (
                <CheckCircle2 className="ml-auto h-3.5 w-3.5 text-muted-foreground" />
              )}
            </DropdownMenuItem>
          )
        )}
        {status && (
          <>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleRemove} className="text-muted-foreground">
              <X className="mr-2 h-4 w-4" />
              Remove status
            </DropdownMenuItem>
          </>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
