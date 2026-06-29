'use client'

import { useState, useCallback, useMemo } from 'react'
import { Plus, Sparkles, Clock, TrendingUp, Trophy, LogOut } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'
import type { Dor, ColumnId, NewDorData } from '@/types'
import Card from './Card'
import NewCardModal from './NewCardModal'
import StatCard from './StatCard'

const COLUMNS: { id: ColumnId; label: string; sub: string }[] = [
  { id: 'dor',       label: 'Dor',          sub: 'Banco de dores'          },
  { id: 'definir',   label: 'Definir',       sub: 'Descobrir + priorizar'   },
  { id: 'andamento', label: 'Em Andamento',  sub: 'Desenvolvendo a solução' },
  { id: 'resolvida', label: 'Resolvida',     sub: 'Vitrine de resultados'   },
]

const COLUMN_ACCENT: Record<ColumnId, string> = {
  dor:       '#6D6E71',
  definir:   '#009EDB',
  andamento: '#75398E',
  resolvida: '#58B031',
}

interface KanbanBoardProps {
  initialDores: Dor[]
  userId: string
  userEmail: string
}

export default function KanbanBoard({ initialDores, userId, userEmail }: KanbanBoardProps) {
  const [dores, setDores]         = useState<Dor[]>(initialDores)
  const [showModal, setShowModal] = useState(false)
  const [error, setError]         = useState<string | null>(null)
  const router  = useRouter()
  const supabase = useMemo(() => createClient(), [])

  const stats = useMemo(() => ({
    total:       dores.length,
    inProgress:  dores.filter((d) => d.stage === 'andamento').length,
    highPriority:dores.filter((d) => d.priority === 'alta' && d.stage !== 'resolvida').length,
    resolved:    dores.filter((d) => d.stage === 'resolvida').length,
  }), [dores])

  const handleCreate = useCallback(async (data: NewDorData) => {
    const { data: inserted, error: err } = await supabase
      .from('dores')
      .insert({ ...data, stage: 'dor', created_by: userId })
      .select()
      .single()

    if (err) { setError('Erro ao criar card. Tente novamente.'); return }
    setDores((prev) => [inserted as Dor, ...prev])
  }, [supabase, userId])

  const handleMove = useCallback(async (id: string, dir: 1 | -1) => {
    const dor = dores.find((d) => d.id === id)
    if (!dor) return

    const idx      = COLUMNS.findIndex((c) => c.id === dor.stage)
    const newIdx   = Math.min(Math.max(idx + dir, 0), COLUMNS.length - 1)
    const newColumn = COLUMNS[newIdx].id

    setDores((prev) => prev.map((d) => d.id === id ? { ...d, column: newColumn } : d))

    const { error: err } = await supabase.from('dores').update({ stage: newColumn }).eq('id', id)
    if (err) {
      setDores((prev) => prev.map((d) => d.id === id ? { ...d, column: dor.stage } : d))
      setError('Erro ao mover card.')
    }
  }, [dores, supabase])

  const handleDelete = useCallback(async (id: string) => {
    const backup = dores.find((d) => d.id === id)
    setDores((prev) => prev.filter((d) => d.id !== id))

    const { error: err } = await supabase.from('dores').delete().eq('id', id)
    if (err) {
      if (backup) setDores((prev) => [backup, ...prev])
      setError('Erro ao excluir card.')
    }
  }, [dores, supabase])

  const handleSignOut = async () => {
    await supabase.auth.signOut()
    router.push('/login')
    router.refresh()
  }

  return (
    <div className="min-h-screen bg-fius-light flex flex-col">
      {/* Barra de marca */}
      <div className="h-1 w-full bg-fius-blue" />

      {/* Header */}
      <header className="bg-fius-navy text-white">
        <div className="max-w-7xl mx-auto px-4 md:px-8 py-4 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="text-fius-blue font-bold text-xl tracking-tighter">[ ]</span>
            <div>
              <p className="text-[11px] tracking-widest text-gray-400 uppercase">Finocchio & Ustra</p>
              <p className="text-sm font-bold">Controladoria Jurídica · Comitê de Inovação</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-xs text-gray-400 hidden md:block truncate max-w-[200px]">
              {userEmail}
            </span>
            <button
              onClick={handleSignOut}
              className="flex items-center gap-1.5 text-gray-400 hover:text-white text-xs transition-colors"
            >
              <LogOut size={14} />
              <span className="hidden sm:inline">Sair</span>
            </button>
          </div>
        </div>

        {/* Sub-header com título da página */}
        <div className="border-t border-white/5">
          <div className="max-w-7xl mx-auto px-4 md:px-8 pb-6 pt-4">
            <p className="text-[11px] font-bold tracking-widest text-fius-blue uppercase mb-1">
              Pipeline de Inovação
            </p>
            <h1 className="text-2xl md:text-3xl font-bold text-white">
              Da dor ao resultado
            </h1>
            <p className="text-sm mt-1" style={{ color: '#6D6E71' }}>
              Mapeie, priorize e resolva as dores do seu time.
            </p>
          </div>
        </div>
      </header>

      {/* Conteúdo */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 md:px-8 py-8">

        {/* Erro */}
        {error && (
          <div
            className="mb-4 rounded-xl px-4 py-3 text-sm flex justify-between items-center border"
            style={{ background: '#EA562710', borderColor: '#EA562730', color: '#EA5627' }}
          >
            <span>{error}</span>
            <button onClick={() => setError(null)} className="font-bold ml-4 text-base leading-none">×</button>
          </div>
        )}

        {/* Estatísticas */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
          <StatCard icon={Sparkles}    label="Dores mapeadas" value={stats.total}        accent="#009EDB" />
          <StatCard icon={Clock}       label="Em andamento"   value={stats.inProgress}   accent="#75398E" />
          <StatCard icon={TrendingUp}  label="Prioridade alta" value={stats.highPriority} accent="#EA5627" />
          <StatCard icon={Trophy}      label="Resolvidas"     value={stats.resolved}     accent="#58B031" />
        </div>

        {/* Botão nova dor */}
        <div className="flex justify-end mb-5">
          <button
            onClick={() => setShowModal(true)}
            className="flex items-center gap-2 text-white px-4 py-2.5 rounded-xl text-sm font-semibold
                       hover:opacity-90 transition-opacity"
            style={{ background: '#009EDB' }}
          >
            <Plus size={16} />
            Nova dor
          </button>
        </div>

        {/* Board */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
          {COLUMNS.map((col, colIdx) => {
            const colDores = dores
              .filter((d) => d.stage === col.id)
              .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())

            const accent = COLUMN_ACCENT[col.id]

            return (
              <div key={col.id} className="bg-gray-200/70 rounded-2xl p-3">
                {/* Cabeçalho da coluna */}
                <div className="flex items-start justify-between mb-3 px-1">
                  <div>
                    <div className="flex items-center gap-1.5">
                      <span
                        className="inline-block w-2 h-2 rounded-full flex-shrink-0"
                        style={{ background: accent }}
                      />
                      <p className="font-bold text-fius-navy text-sm">{col.label}</p>
                    </div>
                    <p className="text-[10px] text-fius-gray uppercase tracking-wide mt-0.5 pl-3.5">
                      {col.sub}
                    </p>
                  </div>
                  <span className="bg-white text-fius-gray text-xs font-bold w-6 h-6 rounded-full
                                   flex items-center justify-center flex-shrink-0">
                    {colDores.length}
                  </span>
                </div>

                {colDores.length === 0 ? (
                  <div className="border-2 border-dashed border-gray-300 rounded-xl py-8
                                  text-center text-xs text-gray-400">
                    Nada aqui ainda
                  </div>
                ) : (
                  <div className="flex flex-col gap-2.5">
                    {colDores.map((dor) => (
                      <Card
                        key={dor.id}
                        dor={dor}
                        isFirst={colIdx === 0}
                        isLast={colIdx === COLUMNS.length - 1}
                        onMove={handleMove}
                        onDelete={handleDelete}
                      />
                    ))}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-fius-navy py-4 text-center mt-8">
        <p className="text-gray-500 text-[11px] tracking-widest uppercase">FINOCCHIO & USTRA</p>
      </footer>

      {showModal && (
        <NewCardModal onClose={() => setShowModal(false)} onCreate={handleCreate} />
      )}
    </div>
  )
}
