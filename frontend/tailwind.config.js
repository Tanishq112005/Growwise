/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      keyframes: {
        wiggle: {
          '0%, 100%': { transform: 'rotate(-8deg)' },
          '50%': { transform: 'rotate(8deg)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '200% 0' },
          '100%': { backgroundPosition: '-200% 0' },
        },
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(6px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        wiggle: 'wiggle 1s ease-in-out infinite',
        shimmer: 'shimmer 2s linear infinite',
        'fade-in-up': 'fadeInUp 0.25s ease-out',
      },
      colors: {
        groww: {
          green: "#00D09C",
          darkGreen: "#00B386",
          darkBg: "#12161A",
          surface: "#1E222B",
          card: "#262C36",
          border: "#333A48",
          textSecondary: "#9CA3AF"
        }
      }
    },
  },
  plugins: [],
}
