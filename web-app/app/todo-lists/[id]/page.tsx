import { TodoListWrapper } from "./TodoListWrapper"

// Для static export Next.js требуется generateStaticParams
export async function generateStaticParams() {
  // Возвращаем пустой массив, так как списки создаются динамически
  return []
}

export default function TodoListDetailPage() {
  return <TodoListWrapper />
}
