import { redirect } from 'next/navigation'
import { createClient } from '@/lib/supabase/server'
import KanbanBoard from '@/components/KanbanBoard'
import type { Dor } from '@/types'

export default async function DashboardPage() {
  const supabase = await createClient()

  const {
    data: { user },
  } = await supabase.auth.getUser()

  if (!user) {
    redirect('/login')
  }

  const { data: dores } = await supabase
    .from('dores')
    .select('*')
    .order('created_at', { ascending: false })

  return (
    <KanbanBoard
      initialDores={(dores as Dor[]) ?? []}
      userId={user.id}
      userEmail={user.email ?? ''}
    />
  )
}
