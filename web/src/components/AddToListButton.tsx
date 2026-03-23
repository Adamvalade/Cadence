"use client";

import { useEffect, useState } from "react";
import { ListPlus, Plus, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { api } from "@/lib/api";
import type { UserList } from "@/lib/types";

interface AddToListButtonProps {
  albumId: string;
}

export default function AddToListButton({ albumId }: AddToListButtonProps) {
  const [open, setOpen] = useState(false);
  const [lists, setLists] = useState<UserList[]>([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [addedTo, setAddedTo] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (!open) return;
    setLoading(true);
    api.get<UserList[]>("/lists/mine")
      .then(setLists)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [open]);

  const handleAddToList = async (listId: string) => {
    if (addedTo.has(listId)) return;
    try {
      await api.post(`/lists/${listId}/items`, { album_id: albumId, position: 0 });
      setAddedTo((prev) => new Set(prev).add(listId));
    } catch {
      // already in list or error
    }
  };

  const handleCreateList = async () => {
    if (!newTitle.trim()) return;
    setCreating(true);
    try {
      const list = await api.post<UserList>("/lists", { title: newTitle.trim() });
      await api.post(`/lists/${list.id}/items`, { album_id: albumId, position: 0 });
      setLists((prev) => [list, ...prev]);
      setAddedTo((prev) => new Set(prev).add(list.id));
      setNewTitle("");
    } catch {
      // error
    } finally {
      setCreating(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger render={<Button variant="outline" size="sm" />}>
        <ListPlus className="h-4 w-4 mr-1" />
        Add to list
      </DialogTrigger>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>Add to list</DialogTitle>
          <DialogDescription>Choose a list or create a new one.</DialogDescription>
        </DialogHeader>

        <div className="space-y-2 max-h-48 overflow-y-auto">
          {loading ? (
            <p className="text-sm text-muted-foreground py-4 text-center">Loading lists...</p>
          ) : lists.length === 0 ? (
            <p className="text-sm text-muted-foreground py-4 text-center">No lists yet. Create one below.</p>
          ) : (
            lists.map((list) => (
              <button
                key={list.id}
                onClick={() => handleAddToList(list.id)}
                className="w-full flex items-center gap-3 p-2 rounded-md hover:bg-accent/50 transition-colors text-left"
              >
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{list.title}</p>
                  {!list.is_public && (
                    <span className="text-xs text-muted-foreground">Private</span>
                  )}
                </div>
                {addedTo.has(list.id) && (
                  <Check className="h-4 w-4 text-green-500 shrink-0" />
                )}
              </button>
            ))
          )}
        </div>

        <div className="border-t pt-3 space-y-2">
          <Label htmlFor="newList" className="text-sm">Create new list</Label>
          <div className="flex gap-2">
            <Input
              id="newList"
              placeholder="List name..."
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleCreateList()}
              className="flex-1"
            />
            <Button size="sm" onClick={handleCreateList} disabled={creating || !newTitle.trim()}>
              <Plus className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
