export type Priority = 'alta' | 'media' | 'baixa'
export type ColumnId = 'dor' | 'definir' | 'andamento' | 'resolvida'

export interface Dor {
  id: string
  title: string
  who: string | null
  impact: string | null
  priority: Priority
  column: ColumnId
  created_at: string
  created_by: string | null
}

export type NewDorData = Omit<Dor, 'id' | 'created_at' | 'created_by' | 'column'>
