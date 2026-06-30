'use client'

import { useState } from 'react'
import { createClient } from '@/lib/supabase/client'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [status, setStatus] = useState<'idle' | 'loading' | 'sent' | 'error'>('idle')
  const [errorMsg, setErrorMsg] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrorMsg('')

    if (!email.toLowerCase().endsWith('@fius.com.br')) {
      setStatus('error')
      setErrorMsg('Acesso restrito a e-mails @fius.com.br')
      return
    }

    setStatus('loading')
    const supabase = createClient()

    const { error } = await supabase.auth.signInWithOtp({
      email: email.toLowerCase(),
      options: {
        emailRedirectTo: `${window.location.origin}/auth/callback`,
      },
    })

    if (error) {
      setStatus('error')
      setErrorMsg(error.message)
    } else {
      setStatus('sent')
    }
  }

  return (
    <div className="min-h-screen bg-fius-light flex flex-col">
      {/* Barra de marca */}
      <div className="h-1 w-full bg-fius-blue" />

      {/* Header */}
      <header className="bg-fius-navy text-white py-4 px-6">
        <div className="max-w-6xl mx-auto flex items-center gap-3">
          <span className="text-fius-blue font-bold text-2xl leading-none tracking-tighter">[ ]</span>
          <div>
            <p className="text-[11px] tracking-widest text-gray-400 uppercase">Finocchio & Ustra</p>
            <p className="text-sm font-semibold">Controladoria Jurídica</p>
          </div>
        </div>
      </header>

      {/* Conteúdo */}
      <main className="flex-1 flex items-center justify-center px-4 py-16">
        <div className="w-full max-w-md">
          <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8">
            {status === 'sent' ? (
              <div className="text-center py-4">
                <div
                  className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-5"
                  style={{ background: '#58B03115' }}
                >
                  <svg className="w-8 h-8" fill="none" stroke="#58B031" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                    />
                  </svg>
                </div>
                <h2 className="text-xl font-bold text-fius-navy mb-2">Link enviado!</h2>
                <p className="text-fius-gray text-sm leading-relaxed">
                  Verifique a caixa de entrada de{' '}
                  <span className="font-semibold text-fius-navy">{email}</span>{' '}
                  e clique no link para acessar.
                </p>
                <button
                  onClick={() => { setStatus('idle'); setEmail('') }}
                  className="mt-6 text-fius-blue text-sm hover:underline"
                >
                  Usar outro e-mail
                </button>
              </div>
            ) : (
              <>
                <div className="mb-8">
                  <p className="text-fius-blue font-bold text-sm tracking-widest uppercase mb-3">
                    Pipeline de Inovação
                  </p>
                  <h1 className="text-2xl font-bold text-fius-navy leading-tight">
                    Acesse com seu<br />e-mail corporativo
                  </h1>
                  <p className="text-fius-gray text-sm mt-2">
                    Enviaremos um link de acesso seguro para @fius.com.br.
                  </p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                  <div>
                    <label
                      htmlFor="email"
                      className="block text-[11px] font-bold text-fius-gray uppercase tracking-wider mb-1.5"
                    >
                      E-mail corporativo
                    </label>
                    <input
                      id="email"
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="seu.nome@fius.com.br"
                      className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl text-fius-navy text-sm
                                 focus:outline-none focus:border-fius-blue transition-colors placeholder:text-gray-300"
                    />
                  </div>

                  {status === 'error' && (
                    <div className="rounded-xl px-4 py-3 text-sm border"
                         style={{ background: '#EA562710', borderColor: '#EA562730', color: '#EA5627' }}>
                      {errorMsg}
                    </div>
                  )}

                  <button
                    type="submit"
                    disabled={status === 'loading'}
                    className="w-full bg-fius-blue text-white py-3 rounded-xl font-semibold text-sm
                               hover:bg-fius-navy transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {status === 'loading' ? 'Enviando...' : 'Enviar link de acesso'}
                  </button>
                </form>
              </>
            )}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-fius-navy py-4 text-center">
        <p className="text-gray-500 text-[11px] tracking-widest uppercase">FINOCCHIO & USTRA</p>
      </footer>
    </div>
  )
}
