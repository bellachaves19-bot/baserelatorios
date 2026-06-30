'use client'

import { useState } from 'react'
import { X } from 'lucide-react'
import type { NewDorData } from '@/types'

interface NewCardModalProps {
  onClose: () => void
  onCreate: (data: NewDorData) => void
}

export default function NewCardModal({ onClose, onCreate }: NewCardModalProps) {
  const [title, setTitle]     = useState('')
  const [who, setWho]         = useState('')
  const [impact, setImpact]   = useState('')
  const [priority, setPriority] = useState<'alta' | 'media' | 'baixa'>('media')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim()) return
    onCreate({
      title:    title.trim(),
      who:      who.trim() || null,
      impact:   impact.trim() || null,
      priority,
    })
    onClose()
  }

  const inputClass =
    'w-full px-3 py-2.5 border-2 border-gray-200 rounded-xl text-fius-navy text-sm ' +
    'focus:outline-none focus:border-fius-blue transition-colors placeholder:text-gray-300'

  return (
    <div
      className="fixed inset-0 flex items-center justify-center p-4 z-50"
      style={{ background: 'rgba(17,29,48,0.55)' }}
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl w-full max-w-md max-h-[90vh] overflow-y-auto shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 pt-5 pb-3">
          <div className="flex items-center gap-2">
            <span className="text-fius-blue font-bold">[ ]</span>
            <h2 className="text-base font-bold text-fius-navy">Nova dor</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-fius-navy rounded-lg p-1 transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="px-5 pb-5 flex flex-col gap-3">
          <div>
            <label className="block text-[11px] font-bold text-fius-gray uppercase tracking-wider mb-1.5">
              Qual a dor?
            </label>
            <textarea
              autoFocus
              required
              rows={3}
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Ex: Cadastro de processo busca dados em 4 sistemas diferentes"
              className={inputClass + ' resize-none'}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] font-bold text-fius-gray uppercase tracking-wider mb-1.5">
                Quem relatou
              </label>
              <input
                value={who}
                onChange={(e) => setWho(e.target.value)}
                placeholder="Nome"
                className={inputClass}
              />
            </div>
            <div>
              <label className="block text-[11px] font-bold text-fius-gray uppercase tracking-wider mb-1.5">
                Prioridade
              </label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value as typeof priority)}
                className={inputClass + ' bg-white'}
              >
                <option value="alta">Alta</option>
                <option value="media">Média</option>
                <option value="baixa">Baixa</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-bold text-fius-gray uppercase tracking-wider mb-1.5">
              Impacto percebido
            </label>
            <input
              value={impact}
              onChange={(e) => setImpact(e.target.value)}
              placeholder="Ex: ~6h/semana da equipe"
              className={inputClass}
            />
          </div>

          <div className="flex gap-2 justify-end pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2.5 rounded-xl text-sm font-semibold text-fius-gray
                         bg-gray-100 hover:bg-gray-200 transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="px-4 py-2.5 rounded-xl text-sm font-semibold text-white
                         bg-fius-blue hover:bg-fius-navy transition-colors"
            >
              Adicionar ao Banco de Dores
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
