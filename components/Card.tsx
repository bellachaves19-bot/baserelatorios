'use client'

import { Trash2, ChevronRight } from 'lucide-react'
import type { Dor } from '@/types'

const PRIORITY_CONFIG = {
  alta:  { label: 'Alta',  color: '#EA5627' },
  media: { label: 'Média', color: '#009EDB' },
  baixa: { label: 'Baixa', color: '#58B031' },
}

function timeAgo(dateStr: string) {
  const days = Math.floor((Date.now() - new Date(dateStr).getTime()) / 86_400_000)
  if (days <= 0) return 'hoje'
  if (days === 1) return '1 dia atrás'
  return `${days} dias atrás`
}

interface CardProps {
  dor: Dor
  isFirst: boolean
  isLast: boolean
  onMove: (id: string, dir: 1 | -1) => void
  onDelete: (id: string) => void
}

export default function Card({ dor, isFirst, isLast, onMove, onDelete }: CardProps) {
  const priority = PRIORITY_CONFIG[dor.priority] ?? PRIORITY_CONFIG.media

  return (
    <div className="bg-white rounded-xl p-3.5 border border-gray-100 shadow-sm">
      {/* Priority row */}
      <div className="flex items-center gap-1.5 mb-2">
        <span
          className="inline-block w-2.5 h-2.5 rounded-sm flex-shrink-0"
          style={{ background: priority.color, transform: 'rotate(45deg)' }}
        />
        <span
          className="text-[10px] font-bold uppercase tracking-wider flex-1"
          style={{ color: priority.color }}
        >
          {priority.label}
        </span>
        <button
          onClick={() => onDelete(dor.id)}
          className="text-gray-300 hover:text-fius-orange rounded-md p-1 transition-colors"
          style={{ background: 'transparent' }}
          onMouseEnter={(e) => (e.currentTarget.style.background = '#EA562710')}
          onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
          aria-label="Excluir card"
        >
          <Trash2 size={13} />
        </button>
      </div>

      <p className="text-sm font-semibold text-fius-navy leading-snug mb-1.5">{dor.title}</p>

      {dor.impact && (
        <p className="text-xs text-fius-gray leading-relaxed mb-3">{dor.impact}</p>
      )}

      <div className="flex items-center justify-between text-[11px] mb-3">
        <span className="font-semibold text-fius-gray">{dor.who || '—'}</span>
        <span className="text-gray-400">{timeAgo(dor.created_at)}</span>
      </div>

      {/* Action buttons */}
      <div className="flex gap-1.5 justify-end">
        {!isFirst && (
          <button
            onClick={() => onMove(dor.id, -1)}
            className="flex items-center gap-0.5 text-[11px] font-semibold text-fius-gray
                       bg-gray-100 hover:bg-gray-200 rounded-lg px-2 py-1.5 transition-colors"
          >
            <ChevronRight size={13} className="rotate-180" />
            Voltar
          </button>
        )}
        {!isLast && (
          <button
            onClick={() => onMove(dor.id, 1)}
            className="flex items-center gap-0.5 text-[11px] font-semibold text-white
                       rounded-lg px-2.5 py-1.5 transition-colors hover:opacity-90"
            style={{ background: '#009EDB' }}
          >
            Avançar <ChevronRight size={13} />
          </button>
        )}
      </div>
    </div>
  )
}
