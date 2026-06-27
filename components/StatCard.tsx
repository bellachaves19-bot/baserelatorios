import type { LucideIcon } from 'lucide-react'

interface StatCardProps {
  icon: LucideIcon
  label: string
  value: number
  accent: string
}

export default function StatCard({ icon: Icon, label, value, accent }: StatCardProps) {
  return (
    <div className="bg-white rounded-2xl p-4 border border-gray-100 flex items-center gap-3">
      <div
        className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
        style={{ background: `${accent}1A`, color: accent }}
      >
        <Icon size={18} strokeWidth={2} />
      </div>
      <div>
        <p className="text-xl font-extrabold text-fius-navy leading-none">{value}</p>
        <p className="text-[11px] text-fius-gray mt-0.5">{label}</p>
      </div>
    </div>
  )
}
