"use client"

import { useParams } from "next/navigation"
import { TodoListDetailClient } from "./TodoListDetailClient"

export function TodoListWrapper() {
  const params = useParams()
  const listId = params?.id ? parseInt(params.id as string) : null
  
  if (!listId) {
    return <div>Invalid list ID</div>
  }
  
  return <TodoListDetailClient listId={listId} />
}

