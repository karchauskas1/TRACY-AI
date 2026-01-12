// Для static export Next.js требуется generateStaticParams
export async function generateStaticParams() {
  // Возвращаем пустой массив, так как списки создаются динамически
  return []
}

import { TodoListWrapper } from "./TodoListWrapper"

export default function TodoListDetailPage() {
  return <TodoListWrapper />
}
