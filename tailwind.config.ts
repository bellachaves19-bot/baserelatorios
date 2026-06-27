import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        fius: {
          blue:   '#009EDB',
          navy:   '#111D30',
          gray:   '#6D6E71',
          light:  '#F3F3F3',
          green:  '#58B031',
          orange: '#EA5627',
          purple: '#75398E',
        },
      },
      fontFamily: {
        sans: ['Verdana', 'Geneva', 'Tahoma', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

export default config
