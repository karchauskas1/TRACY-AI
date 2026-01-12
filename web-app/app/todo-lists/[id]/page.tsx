import { useParams } from "next/navigation"
import { TodoListDetailClient } from "./TodoListDetailClient"

// Для static export Next.js требуется generateStaticParams
export async function generateStaticParams() {
  // Возвращаем пустой массив, так как списки создаются динамически
  return []
}

export default function TodoListDetailPage() {
  const params = useParams()
  const listId = params?.id ? parseInt(params.id as string) : null
  
  if (!listId) {
    return <div>Invalid list ID</div>
  }
  
  return <TodoListDetailClient listId={listId} />
}
